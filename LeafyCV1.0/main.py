#!/usr/bin/env python3
"""LeafyCV1.0 command-line entry point.

LeafyCV can analyse one Camera or every enabled/CV-enabled Camera from the
Backend.  The semantic model is loaded lazily once and reused across Cameras.
Multi-camera capture synchronization belongs to the Camera service; LeafyCV
simply processes each new official CameraImage independently after upload.
"""

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
import torch

from leafycv import MODEL_VERSION
from leafycv.api import (
    BackendClient,
    latest_analysis_camera_id,
    latest_analysis_image_id,
    previous_canopy_after_baseline_reset,
)
from leafycv.outputs import save_debug_outputs
from leafycv.pipeline import analyse_image
from leafycv.semantic_segmenter import get_default_segmenter

ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "LeafyCV1.0 semantic canopy MVP: U-Net + EfficientNet-B0 on backend-owned official CameraImages."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Check packages and load the bundled semantic model.")

    file_cmd = sub.add_parser("analyse-file", help="Analyse one local image without backend integration.")
    file_cmd.add_argument("--image", type=Path, required=True)
    file_cmd.add_argument("--previous-canopy", type=float)
    file_cmd.add_argument(
        "--roi",
        help='Optional normalized ROI JSON, e.g. {"x":0.1,"y":0.1,"width":0.8,"height":0.8}',
    )
    file_cmd.add_argument("--output", type=Path, default=ROOT / "outputs")

    once = sub.add_parser(
        "run-once",
        help="Analyse newest not-yet-analysed images once. Omit --camera-id to check all Cameras.",
    )
    _add_backend_args(once)

    loop = sub.add_parser(
        "run-loop",
        help="Poll Backend and analyse new official CameraImages. Omit --camera-id for all Cameras.",
    )
    _add_backend_args(loop)
    loop.add_argument("--poll-seconds", type=float, default=60.0)
    loop.add_argument(
        "--count",
        type=int,
        default=0,
        help="Stop after N successful analyses across all Cameras; 0 = until Ctrl+C.",
    )
    return parser


def _add_backend_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend-base-url",
        default=os.getenv("LEAFY_BACKEND_BASE_URL", "http://127.0.0.1:8000"),
    )
    parser.add_argument(
        "--camera-id",
        default=os.getenv("LEAFY_CV_CAMERA_ID", ""),
        help=(
            "Optional single Camera ID. Leave blank to process every enabled and CV-enabled Camera "
            "returned by GET /api/cameras/."
        ),
    )
    parser.add_argument("--access-token", default=os.getenv("LEAFY_BACKEND_ACCESS_TOKEN", ""))
    parser.add_argument("--refresh-token", default=os.getenv("LEAFY_BACKEND_REFRESH_TOKEN", ""))
    parser.add_argument("--username", default=os.getenv("LEAFY_BACKEND_USERNAME", os.getenv("LEAFY_MVP_USERNAME", "")))
    parser.add_argument("--password", default=os.getenv("LEAFY_BACKEND_PASSWORD", os.getenv("LEAFY_MVP_PASSWORD", "")))
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("LEAFY_BACKEND_TIMEOUT", "10")),
    )
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    parser.add_argument("--no-debug-files", action="store_true")


def cmd_check(_args: argparse.Namespace | None = None) -> int:
    import requests
    import segmentation_models_pytorch as smp

    segmenter = get_default_segmenter()
    segmenter.ensure_loaded()
    print(MODEL_VERSION)
    print("Python:", sys.version.split()[0])
    print("Platform:", platform.platform())
    print("PyTorch:", torch.__version__)
    print("SMP:", smp.__version__)
    print("OpenCV:", cv2.__version__)
    print("NumPy:", np.__version__)
    print("Requests:", requests.__version__)
    print("Model:", segmenter.model_path)
    print("Encoder:", segmenter.encoder)
    print("Input size:", segmenter.input_size)
    print("Threshold:", segmenter.threshold)
    print("Device:", segmenter.device)
    print("Status: OK")
    return 0


def _print_analysis(analysis: dict[str, Any]) -> None:
    print(json.dumps(analysis, indent=2))


def cmd_analyse_file(args: argparse.Namespace) -> int:
    image = cv2.imread(str(args.image))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {args.image}")
    config: dict[str, Any] = {}
    if args.roi:
        config["roi_points"] = json.loads(args.roi)
    result = analyse_image(
        image,
        camera_config=config,
        previous_canopy=args.previous_canopy,
    )
    paths = save_debug_outputs(args.output, args.image.stem, result)
    _print_analysis(result["analysis"])
    print("Debug outputs:", {key: str(value) for key, value in paths.items()})
    return 0


def _client(args: argparse.Namespace) -> BackendClient:
    return BackendClient(
        args.backend_base_url,
        access_token=args.access_token,
        refresh_token=args.refresh_token,
        username=args.username,
        password=args.password,
        timeout=args.timeout,
    )


def _selected_camera_ids(client: BackendClient, args: argparse.Namespace) -> list[Any]:
    """Resolve one explicit Camera ID or all active Camera IDs from Backend."""
    explicit = str(args.camera_id).strip()
    if explicit:
        return [explicit]

    camera_ids: list[Any] = []
    for camera in client.get_cameras():
        camera_id = camera.get("id", camera.get("camera_id"))
        if camera_id is None:
            continue
        if not bool(camera.get("enabled", True)):
            continue
        if not bool(camera.get("cv_enabled", True)):
            continue
        camera_ids.append(camera_id)
    return camera_ids


def _run_camera_once(client: BackendClient, args: argparse.Namespace, camera_id: Any) -> bool:
    """Analyse one Camera's newest image exactly once when it is new."""
    config = client.get_camera_config(camera_id)
    if config and (not bool(config.get("enabled", True)) or not bool(config.get("cv_enabled", True))):
        print(f"Camera {camera_id}: disabled for LeafyCV; skip.")
        return False

    image_info = client.get_latest_image(camera_id)
    if image_info is None:
        print(f"Camera {camera_id}: no official image captured yet.")
        return False

    # Guard against a malformed Backend response accidentally crossing Camera
    # identities. Backend should also validate this relation during ingest.
    response_camera_id = image_info.get("camera_id")
    if response_camera_id is not None and str(response_camera_id) != str(camera_id):
        raise ValueError(
            f"latest-image camera mismatch: requested Camera {camera_id}, "
            f"received camera_id={response_camera_id}"
        )

    # Latest analysis of any validity is used only for duplicate detection.
    latest_any = client.get_latest_analysis(camera_id, valid_only=False)
    latest_any_camera_id = latest_analysis_camera_id(latest_any)
    if latest_any_camera_id is not None and str(latest_any_camera_id) != str(camera_id):
        raise ValueError(
            f"latest-analysis camera mismatch: requested Camera {camera_id}, "
            f"received camera_id={latest_any_camera_id}"
        )
    latest_image_id = latest_analysis_image_id(latest_any)
    if latest_image_id is not None and str(latest_image_id) == str(image_info["image_id"]):
        print(f"Camera {camera_id}: CameraImage {image_info['image_id']} is already analysed.")
        return False

    # Growth baseline comes from the latest valid analysis only.  Each Camera
    # therefore compares against its own previous valid canopy history.
    previous_valid = client.get_latest_analysis(camera_id, valid_only=True)
    previous_valid_camera_id = latest_analysis_camera_id(previous_valid)
    if previous_valid_camera_id is not None and str(previous_valid_camera_id) != str(camera_id):
        raise ValueError(
            f"latest valid analysis camera mismatch: requested Camera {camera_id}, "
            f"received camera_id={previous_valid_camera_id}"
        )
    # A plant/layout change does not rewrite history. Backend stores
    # Camera.growth_baseline_reset_at; LeafyCV ignores valid analyses captured
    # before that timestamp. The first valid image after reset therefore has
    # growth_change=null and becomes the new visual baseline.
    previous_canopy = previous_canopy_after_baseline_reset(previous_valid, config)

    image = client.load_image(image_info)
    result = analyse_image(
        image,
        camera_config=config,
        previous_canopy=previous_canopy,
    )

    if not args.no_debug_files:
        stem = f"camera_{camera_id}_image_{image_info['image_id']}"
        save_debug_outputs(args.output, stem, result)

    resolved_camera_id = image_info.get("camera_id", camera_id)
    response = client.post_analysis(
        resolved_camera_id,
        image_info["image_id"],
        result["analysis"],
    )
    print(f"Camera {camera_id}: analysed CameraImage {image_info['image_id']} successfully.")
    if response:
        print("Backend response:", json.dumps(response, indent=2))
    _print_analysis(result["analysis"])
    return True


def _run_backend_once(args: argparse.Namespace) -> int:
    """Run one poll across one Camera or all active Cameras."""
    client = _client(args)
    camera_ids = _selected_camera_ids(client, args)
    if not camera_ids:
        print("No enabled/CV-enabled Cameras returned by Backend.")
        return 0

    successes = 0
    for camera_id in camera_ids:
        try:
            if _run_camera_once(client, args, camera_id):
                successes += 1
        except Exception as exc:
            # One Camera analysis failure must not block other Cameras in the
            # same poll cycle.
            print(f"Camera {camera_id}: LeafyCV warning: {exc}", file=sys.stderr)
    return successes


def cmd_run_once(args: argparse.Namespace) -> int:
    _run_backend_once(args)
    return 0


def cmd_run_loop(args: argparse.Namespace) -> int:
    poll = max(5.0, float(args.poll_seconds))
    total_successes = 0
    target = "one Camera" if str(args.camera_id).strip() else "all active Cameras"
    print(f"Polling Backend every {poll:.0f}s for {target}. New CameraImage IDs are analysed once.")

    try:
        while True:
            try:
                total_successes += _run_backend_once(args)
            except Exception as exc:
                print(f"LeafyCV backend warning: {exc}", file=sys.stderr)
            if args.count > 0 and total_successes >= args.count:
                return 0
            time.sleep(poll)
    except KeyboardInterrupt:
        print("Stopped.")
        return 0


def main() -> int:
    args = build_parser().parse_args()
    commands = {
        "check": cmd_check,
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
