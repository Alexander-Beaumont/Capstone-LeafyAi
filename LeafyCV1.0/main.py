#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from leafycv import MODEL_VERSION
from leafycv.api import BackendClient, latest_analysis_image_id, previous_canopy_from_latest
from leafycv.outputs import save_debug_outputs
from leafycv.pipeline import analyse_image

ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "LeafyCV1.0 final MVP: analyse the overall basil growth area from an "
            "image already captured by the backend. No production camera acquisition, "
            "SLOT registration, calibration-stick conversion, per-plant tracking, "
            "growth-stage classification or MAGENTA mode."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Check required Python packages.")

    demo = sub.add_parser("demo", help="Analyse the included normal-light demo image.")
    demo.add_argument("--previous-canopy", type=float)
    demo.add_argument("--output", type=Path, default=ROOT / "outputs")

    file_cmd = sub.add_parser("analyse-file", help="Analyse one local image without the backend.")
    file_cmd.add_argument("--image", type=Path, required=True)
    file_cmd.add_argument("--previous-canopy", type=float)
    file_cmd.add_argument(
        "--roi",
        help='Optional normalized growth area JSON, e.g. {"x":0.1,"y":0.1,"width":0.8,"height":0.8}',
    )
    file_cmd.add_argument("--output", type=Path, default=ROOT / "outputs")

    once = sub.add_parser("run-once", help="Fetch the latest backend image, analyse it once, and POST the result.")
    _add_backend_args(once)
    once.add_argument(
        "--force",
        action="store_true",
        help="Re-process even if latest-analysis already references the same image_id. Use for testing only.",
    )

    loop = sub.add_parser("run-loop", help="Poll backend and analyse each new official CameraImage once.")
    _add_backend_args(loop)
    loop.add_argument("--poll-seconds", type=float, default=60.0)
    loop.add_argument("--count", type=int, default=0, help="Stop after N new analyses. 0 = run until Ctrl+C.")
    return parser


def _add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--backend-base-url", default=os.getenv("LEAFY_BACKEND_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--camera-id", default=os.getenv("LEAFY_CV_CAMERA_ID", ""))
    parser.add_argument("--access-token", default=os.getenv("LEAFY_BACKEND_ACCESS_TOKEN", ""))
    parser.add_argument("--refresh-token", default=os.getenv("LEAFY_BACKEND_REFRESH_TOKEN", ""))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("LEAFY_BACKEND_TIMEOUT", "10")))
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    parser.add_argument("--no-debug-files", action="store_true")


def cmd_check(args: argparse.Namespace | None = None) -> int:
    import requests
    print(MODEL_VERSION)
    print("Python:", sys.version.split()[0])
    print("Platform:", platform.platform())
    print("OpenCV:", cv2.__version__)
    print("NumPy:", np.__version__)
    print("Requests:", requests.__version__)
    print("Status: OK")
    return 0


def _print_analysis(analysis: dict[str, Any]) -> None:
    print(json.dumps(analysis, indent=2))


def cmd_demo(args: argparse.Namespace) -> int:
    image_path = ROOT / "demo" / "demo_normal.jpg"
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(
            f"Demo image is not included at {image_path}. Use analyse-file with a farm image instead."
        )
    result = analyse_image(image, previous_canopy=args.previous_canopy)
    paths = save_debug_outputs(args.output, "demo", result)
    _print_analysis(result["analysis"])
    print("Debug outputs:", paths)
    return 0


def cmd_analyse_file(args: argparse.Namespace) -> int:
    image = cv2.imread(str(args.image))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {args.image}")
    config: dict[str, Any] = {}
    if args.roi:
        config["roi_points"] = json.loads(args.roi)
    result = analyse_image(image, camera_config=config, previous_canopy=args.previous_canopy)
    paths = save_debug_outputs(args.output, args.image.stem, result)
    _print_analysis(result["analysis"])
    print("Debug outputs:", paths)
    return 0


def _client(args: argparse.Namespace) -> BackendClient:
    if not str(args.camera_id).strip():
        raise ValueError("--camera-id is required for backend mode (or set LEAFY_CV_CAMERA_ID).")
    return BackendClient(
        args.backend_base_url,
        access_token=args.access_token,
        refresh_token=args.refresh_token,
        timeout=args.timeout,
    )


def _run_backend_once(args: argparse.Namespace, *, skip_if_already_analysed: bool = True) -> bool:
    client = _client(args)
    camera_id = args.camera_id
    config = client.get_camera_config(camera_id)
    image_info = client.get_latest_image(camera_id)

    # Latest analysis of any validity is used for duplicate-image protection.
    latest = client.get_latest_analysis(camera_id)
    if skip_if_already_analysed:
        previous_image_id = latest_analysis_image_id(latest)
        if previous_image_id is not None and str(previous_image_id) == str(image_info["image_id"]):
            print(f"No new image: CameraImage {image_info['image_id']} is already analysed.")
            return False

    # Growth baseline must come from the most recent VALID analysis.
    previous_valid = client.get_latest_analysis(camera_id, valid_only=True)
    previous_canopy = previous_canopy_from_latest(previous_valid)

    image = client.load_image(image_info)
    result = analyse_image(image, camera_config=config, previous_canopy=previous_canopy)

    if not args.no_debug_files:
        stem = f"camera_{camera_id}_image_{image_info['image_id']}"
        save_debug_outputs(args.output, stem, result)

    resolved_camera_id = image_info.get("camera_id", camera_id)
    response = client.post_analysis(resolved_camera_id, image_info["image_id"], result["analysis"])
    print(f"Analysed CameraImage {image_info['image_id']} and posted result successfully.")
    if response:
        print("Backend response:", json.dumps(response, indent=2))
    _print_analysis(result["analysis"])
    return True


def cmd_run_once(args: argparse.Namespace) -> int:
    _run_backend_once(args, skip_if_already_analysed=not args.force)
    return 0


def cmd_run_loop(args: argparse.Namespace) -> int:
    poll = max(5.0, float(args.poll_seconds))
    successes = 0
    print(f"Polling backend every {poll:.0f}s. LeafyCV analyses only new CameraImage IDs.")
    try:
        while True:
            try:
                if _run_backend_once(args, skip_if_already_analysed=True):
                    successes += 1
                    if args.count > 0 and successes >= args.count:
                        return 0
            except Exception as exc:
                print(f"LeafyCV warning: {exc}", file=sys.stderr)
            time.sleep(poll)
    except KeyboardInterrupt:
        print("Stopped.")
        return 0


def main() -> int:
    args = build_parser().parse_args()
    commands = {
        "check": cmd_check,
        "demo": cmd_demo,
        "analyse-file": cmd_analyse_file,
        "run-once": cmd_run_once,
        "run-loop": cmd_run_loop,
    }
    try:
        return commands[args.command](args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
