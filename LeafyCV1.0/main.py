#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from leafycv import MODEL_VERSION
from leafycv.api import BackendConfigClient, CVApiClient
from leafycv.camera import capture_frame, source_description
from leafycv.config import default_config, load_config, normalized_roi_to_pixels, save_config
from leafycv.gui import close_windows, select_calibration_stick, select_roi, select_slot_centres
from leafycv.monitor import run_monitor
from leafycv.pipeline import capture_and_analyse

ROOT = Path(__file__).resolve().parent


def comma_values(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "LeafyCV1.0: offline Computer Vision for the Leafy AI basil farm. "
            "Supports RTSP cameras, webcams, NORMAL/MAGENTA processing, ROI, "
            "fixed SLOT registration, calibration-stick size conversion, canopy, "
            "visibility, crowding, growth, live preview and optional Django integration."
        ),
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Check Python/OpenCV/NumPy/Requests installation.")

    c = sub.add_parser("create-config", help="Create a local camera configuration JSON file for standalone testing.")
    c.add_argument("--output", type=Path, required=True)
    c.add_argument("--camera-name", required=True)
    c.add_argument("--source-type", choices=("WEBCAM", "RTSP", "FILE"), required=True)
    c.add_argument("--webcam-index", type=int, default=0)
    c.add_argument("--file-path", type=Path)
    c.add_argument("--rtsp-ip")
    c.add_argument("--rtsp-port", type=int, default=554)
    c.add_argument("--rtsp-path", default="")
    c.add_argument("--lighting", choices=("NORMAL", "MAGENTA"), default="NORMAL")
    c.add_argument("--overwrite", action="store_true")

    t = sub.add_parser("test-source", help="Capture one frame to verify a local camera configuration.")
    t.add_argument("--config", type=Path, required=True)
    t.add_argument("--output", type=Path, default=ROOT / "outputs" / "source_test.jpg")
    t.add_argument("--show", action="store_true")

    cal = sub.add_parser("calibrate", help="Set ROI, register SLOT centres and optionally set a calibration stick for a local config.")
    cal.add_argument("--config", type=Path, required=True)
    cal.add_argument("--slot-ids", help="Comma-separated database SLOT IDs in click order, for example UUID1,UUID2,UUID3.")
    cal.add_argument("--slot-count", type=int, help="Generate temporary SLOT IDs 1..N for standalone laptop testing.")
    cal.add_argument("--reference-length-cm", type=float, help="Known physical length of the calibration reference.")

    reg = sub.add_parser("register-slots", help="Re-register SLOT centres without changing the ROI.")
    reg.add_argument("--config", type=Path, required=True)
    reg.add_argument("--slot-ids", help="Comma-separated database SLOT IDs in click order.")
    reg.add_argument("--slot-count", type=int)

    stick = sub.add_parser("calibrate-stick", help="Set or adjust the two calibration-stick endpoints.")
    stick.add_argument("--config", type=Path, required=True)
    stick.add_argument("--reference-length-cm", type=float, required=True)

    clear = sub.add_parser("clear-stick", help="Remove the calibration stick. Pixel measurements continue to work.")
    clear.add_argument("--config", type=Path, required=True)

    light = sub.add_parser("set-lighting", help="Set a local camera processing profile to NORMAL or MAGENTA.")
    light.add_argument("--config", type=Path, required=True)
    light.add_argument("--lighting", choices=("NORMAL", "MAGENTA"), required=True)

    show = sub.add_parser("show-config", help="Print a local camera configuration.")
    show.add_argument("--config", type=Path, required=True)

    once = sub.add_parser("run-once", help="Capture and save one official CV sample, then stop.")
    _add_run_arguments(once)

    loop = sub.add_parser("run-loop", help="Production scheduler: save one CV sample every N minutes; camera is released between captures.")
    _add_run_arguments(loop)
    loop.add_argument("--interval-minutes", type=float, help="Override the configured interval. Default is 30 minutes.")
    loop.add_argument("--count", type=int, default=0, help="Number of samples. 0 means run until Ctrl+C.")

    monitor = sub.add_parser(
        "monitor",
        help="Show a continuous live preview while saving CV data only at the scheduled interval.",
    )
    _add_run_arguments(monitor)
    monitor.add_argument("--interval-minutes", type=float, help="Saved CV analysis interval. Default is 30 minutes.")
    monitor.add_argument("--fps", type=float, help="Preview rate. Default: 5 FPS webcam, 1 FPS RTSP.")
    monitor.add_argument("--duration-seconds", type=float, default=0.0, help="Optional bounded monitor duration. Direct RTSP is always bounded.")
    monitor.add_argument("--slot-ids", help="Local-config mode only: comma-separated SLOT IDs used when P is pressed.")
    monitor.add_argument("--slot-count", type=int, help="Local-config mode only: temporary SLOT IDs 1..N.")
    monitor.add_argument("--reference-length-cm", type=float, help="Local-config mode only: reference length used when C is pressed.")
    monitor.add_argument("--no-immediate", action="store_true", help="Wait one full interval before the first saved analysis.")

    demo = sub.add_parser("demo", help="Run one offline analysis using the included demo image/config.")
    demo.add_argument("--mode", choices=("NORMAL", "MAGENTA"), default="NORMAL")
    demo.add_argument("--output", type=Path, default=ROOT / "outputs")

    return p


def _add_run_arguments(p: argparse.ArgumentParser) -> None:
    p.add_argument("--config", type=Path, help="Local JSON config. Use this for standalone laptop testing.")
    p.add_argument("--backend-base-url", default=os.getenv("LEAFY_BACKEND_BASE_URL", ""), help="Django base URL for integrated mode, e.g. http://127.0.0.1:8000")
    p.add_argument("--camera-id", default=os.getenv("LEAFY_CV_CAMERA_ID", ""), help="Database CAMERA UUID for integrated mode.")
    p.add_argument("--output", type=Path, default=ROOT / "outputs")
    p.add_argument("--api-url", default=os.getenv("LEAFY_CV_API_URL", ""), help="Optional ingest URL override. Integrated mode defaults to /api/cv/ingest/.")
    p.add_argument("--api-key", default=os.getenv("LEAFY_CV_API_KEY", ""))
    p.add_argument("--api-timeout", type=float, default=float(os.getenv("LEAFY_CV_API_TIMEOUT", "5")))
    p.add_argument("--api-send-images", choices=("none", "raw", "all"), default=os.getenv("LEAFY_CV_API_SEND_IMAGES", "raw"))
    p.add_argument("--show", action="store_true", help="Show the saved annotated image after an official analysis.")


def resolve_slot_ids(args: argparse.Namespace, config: dict) -> list[str]:
    if getattr(args, "slot_ids", None):
        return comma_values(args.slot_ids)
    if getattr(args, "slot_count", None):
        if args.slot_count <= 0:
            raise ValueError("--slot-count must be greater than zero.")
        return [str(index) for index in range(1, args.slot_count + 1)]
    existing = [str(slot["slot_id"]) for slot in config.get("slots") or []]
    if existing:
        return existing
    raise ValueError("Provide --slot-ids or --slot-count for the first registration.")


def _config_source(args: argparse.Namespace) -> tuple[Callable[[], dict], Path | None, BackendConfigClient | None]:
    has_local = bool(getattr(args, "config", None))
    has_backend = bool(str(getattr(args, "backend_base_url", "") or "").strip() or str(getattr(args, "camera_id", "") or "").strip())
    if has_local and has_backend:
        raise ValueError("Use either --config OR --backend-base-url + --camera-id, not both.")
    if has_local:
        path = Path(args.config)
        return lambda: load_config(path), path, None
    base_url = str(getattr(args, "backend_base_url", "") or "").strip()
    camera_id = str(getattr(args, "camera_id", "") or "").strip()
    if not base_url or not camera_id:
        raise ValueError("Provide --config, or provide both --backend-base-url and --camera-id.")
    client = BackendConfigClient(base_url, camera_id, args.api_key, args.api_timeout)
    return client.fetch_camera_config, None, client


def _api_client(args: argparse.Namespace, backend_client: BackendConfigClient | None) -> CVApiClient:
    url = str(args.api_url or "").strip()
    if not url and backend_client is not None:
        url = backend_client.ingest_url
    return CVApiClient(url, args.api_key, args.api_timeout)


def cmd_check() -> int:
    print(f"{MODEL_VERSION} setup check")
    print("=" * 48)
    print("Python:", sys.version.split()[0])
    print("Executable:", sys.executable)
    print("Platform:", platform.platform())
    print("OpenCV:", cv2.__version__)
    print("NumPy:", np.__version__)
    try:
        import requests
        print("Requests:", requests.__version__)
    except Exception as exc:
        print("Requests: ERROR", exc)
        return 1
    ffmpeg_lines = [line.strip() for line in cv2.getBuildInformation().splitlines() if "FFMPEG:" in line]
    print("FFmpeg:", ffmpeg_lines[0] if ffmpeg_lines else "OpenCV build information did not report FFmpeg.")
    print("Status: basic Python dependencies are available.")
    return 0


def cmd_create_config(args: argparse.Namespace) -> int:
    if args.output.exists() and not args.overwrite:
        raise FileExistsError(f"Config already exists: {args.output}. Use --overwrite to replace it.")
    config = default_config()
    camera = config["camera"]
    camera["name"] = args.camera_name
    camera["source_type"] = args.source_type
    config["lighting_mode"] = args.lighting
    if args.source_type == "WEBCAM":
        camera["webcam_index"] = args.webcam_index
    elif args.source_type == "FILE":
        if not args.file_path:
            raise ValueError("--file-path is required for FILE sources.")
        camera["file_path"] = str(args.file_path)
    else:
        if not args.rtsp_ip:
            raise ValueError("--rtsp-ip is required for RTSP sources.")
        camera["rtsp"]["ip_address"] = args.rtsp_ip
        camera["rtsp"]["port"] = args.rtsp_port
        camera["rtsp"]["path"] = args.rtsp_path
    save_config(args.output, config)
    print(f"Created configuration: {args.output}")
    print("Next: test the source, then calibrate/register SLOT positions.")
    return 0


def cmd_test_source(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(f"Testing: {config['camera']['name']} ({source_description(config)})")
    frame = capture_frame(config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.output), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    print(f"Camera OK: {frame.shape[1]} x {frame.shape[0]}")
    print(f"Saved test frame: {args.output}")
    if args.show:
        cv2.imshow("LeafyCV1.0 Source Test - press any key to close", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    frame = capture_frame(config)
    try:
        roi = select_roi(frame, config.get("roi"))
        config["roi"] = roi
        roi_pixels = normalized_roi_to_pixels(roi, frame.shape[1], frame.shape[0])
        slot_ids = resolve_slot_ids(args, config)
        slots = select_slot_centres(frame, slot_ids, roi_pixels)
        if slots is None:
            print("SLOT registration cancelled. No configuration was changed.")
            return 0
        config["slots"] = slots
        if args.reference_length_cm:
            stick = select_calibration_stick(frame, args.reference_length_cm)
            if stick is not None:
                config["calibration_stick"] = stick
        save_config(args.config, config)
        print(f"Saved ROI and {len(slots)} SLOT positions to: {args.config}")
        if config.get("calibration_stick"):
            print("Calibration stick is set. Real-size estimates are enabled.")
        else:
            print("Calibration stick is not set. LeafyCV will report pixel sizes only.")
        return 0
    finally:
        close_windows()


def cmd_register_slots(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    frame = capture_frame(config)
    roi_pixels = normalized_roi_to_pixels(config.get("roi"), frame.shape[1], frame.shape[0])
    slot_ids = resolve_slot_ids(args, config)
    try:
        slots = select_slot_centres(frame, slot_ids, roi_pixels)
        if slots is None:
            print("SLOT registration cancelled. Existing positions were kept.")
            return 0
        config["slots"] = slots
        save_config(args.config, config)
        print(f"Saved {len(slots)} SLOT positions to: {args.config}")
        return 0
    finally:
        close_windows()


def cmd_calibrate_stick(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    frame = capture_frame(config)
    try:
        stick = select_calibration_stick(frame, args.reference_length_cm)
        if stick is None:
            print("Calibration-stick update cancelled. Existing calibration was kept.")
            return 0
        config["calibration_stick"] = stick
        save_config(args.config, config)
        print(f"Calibration stick updated in: {args.config}")
        return 0
    finally:
        close_windows()


def cmd_clear_stick(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    config["calibration_stick"] = None
    save_config(args.config, config)
    print("Calibration stick removed. Pixel measurements remain available; centimetre values will be null.")
    return 0


def cmd_set_lighting(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    config["lighting_mode"] = args.lighting
    save_config(args.config, config)
    print(f"Lighting mode set to {args.lighting} in: {args.config}")
    return 0


def show_summary(result: dict, files: dict) -> None:
    print("\nAnalysis complete")
    print("-" * 48)
    print("Camera:", result["camera_name"])
    print("Captured:", result["captured_at"])
    print("Lighting:", result["lighting_mode"])
    print("Size calibrated:", result["size_calibrated"])
    print("Visible plants:", result["analysis"]["visible_plant_count"])
    print("Total canopy coverage:", f"{result['analysis']['total_canopy_coverage']:.2f}%")
    print("Measurement valid:", result["analysis"]["measurement_valid"])
    print("Processing time:", f"{result['analysis']['processing_time_ms']} ms")
    for plant in result["plants"]:
        cm = "not calibrated" if plant["width_cm"] is None else f"{plant['width_cm']:.1f} x {plant['height_cm']:.1f} cm"
        print(
            f"  {plant['slot_label']} [{plant['slot_id']}]: "
            f"visible={plant['visible']} canopy={plant['canopy_coverage']:.1f}% "
            f"growth={plant['growth_change']:+.2f} pp crowding={plant['crowding_percentage']:.0f}% size={cm}"
        )
    print("Annotated image:", files["annotated"])
    print("Result JSON:", files["json"])


def _run_one(config: dict, args: argparse.Namespace, api_client: CVApiClient) -> tuple[dict, dict]:
    result, files = capture_and_analyse(
        config=config,
        output_root=args.output,
        api_client=api_client,
        api_send_images=args.api_send_images,
    )
    show_summary(result, files)
    if args.show:
        image = cv2.imread(str(files["annotated"]))
        if image is not None:
            cv2.imshow("LeafyCV1.0 Result - press any key to close", image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    return result, files


def cmd_run_once(args: argparse.Namespace) -> int:
    loader, _local_path, backend_client = _config_source(args)
    config = loader()
    _run_one(config, args, _api_client(args, backend_client))
    return 0


def cmd_run_loop(args: argparse.Namespace) -> int:
    loader, _local_path, backend_client = _config_source(args)
    initial = loader()
    interval = float(args.interval_minutes or initial["analysis"].get("interval_minutes", 30))
    if interval <= 0:
        raise ValueError("The interval must be greater than zero minutes.")
    count = int(args.count)
    api_client = _api_client(args, backend_client)
    print(f"Starting {MODEL_VERSION} scheduled loop for {initial['camera']['name']}.")
    print(f"Interval: {interval:g} minutes. Each saved sample opens/captures/releases the source independently.")
    print("Press Ctrl+C to stop.")
    completed = 0
    try:
        while count == 0 or completed < count:
            cycle_started = time.monotonic()
            config = loader()
            _run_one(config, args, api_client)
            completed += 1
            if count and completed >= count:
                break
            deadline = cycle_started + interval * 60.0
            while time.monotonic() < deadline:
                time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))
        return 0
    except KeyboardInterrupt:
        print("Stopped by user. No scheduled camera connection is intentionally left open by LeafyCV.")
        return 130


def cmd_monitor(args: argparse.Namespace) -> int:
    loader, local_path, backend_client = _config_source(args)
    config = loader()
    interval = float(args.interval_minutes or config["analysis"].get("interval_minutes", 30))
    source_type = str(config["camera"]["source_type"]).upper()
    fps = float(args.fps if args.fps is not None else (1.0 if source_type == "RTSP" else 5.0))
    if args.slot_ids:
        slot_ids = comma_values(args.slot_ids)
    elif args.slot_count:
        if args.slot_count <= 0:
            raise ValueError("--slot-count must be greater than zero.")
        slot_ids = [str(i) for i in range(1, args.slot_count + 1)]
    else:
        slot_ids = None
    print(f"Starting LeafyCV1.0 monitor for {config['camera']['name']}.")
    print(f"Live preview: {fps:g} FPS. Saved CV analysis: every {interval:g} minutes.")
    print("Live preview frames are not written to the database. Only scheduled/manual samples are saved.")
    return run_monitor(
        config_loader=loader,
        local_config_path=local_path,
        output_root=args.output,
        api_client=_api_client(args, backend_client),
        api_send_images=args.api_send_images,
        interval_minutes=interval,
        fps=fps,
        duration_seconds=float(args.duration_seconds),
        slot_ids=slot_ids,
        reference_length_cm=args.reference_length_cm,
        analyse_immediately=not args.no_immediate,
    )


def cmd_demo(args: argparse.Namespace) -> int:
    config_path = ROOT / "configs" / ("demo_normal.json" if args.mode == "NORMAL" else "demo_magenta.json")
    run_args = argparse.Namespace(
        output=args.output,
        api_send_images="none",
        show=False,
    )
    config = load_config(config_path)
    _run_one(config, run_args, CVApiClient())
    return 0


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "check":
            return cmd_check()
        if args.command == "create-config":
            return cmd_create_config(args)
        if args.command == "test-source":
            return cmd_test_source(args)
        if args.command == "calibrate":
            return cmd_calibrate(args)
        if args.command == "register-slots":
            return cmd_register_slots(args)
        if args.command == "calibrate-stick":
            return cmd_calibrate_stick(args)
        if args.command == "clear-stick":
            return cmd_clear_stick(args)
        if args.command == "set-lighting":
            return cmd_set_lighting(args)
        if args.command == "show-config":
            print(json.dumps(load_config(args.config), indent=2))
            return 0
        if args.command == "run-once":
            return cmd_run_once(args)
        if args.command == "run-loop":
            return cmd_run_loop(args)
        if args.command == "monitor":
            return cmd_monitor(args)
        if args.command == "demo":
            return cmd_demo(args)
        raise RuntimeError(f"Unknown command: {args.command}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        close_windows()


if __name__ == "__main__":
    raise SystemExit(main())
