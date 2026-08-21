#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

from .backend_client import BackendClient
from .camera_collector import CameraCollector
from .config import SETTINGS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Leafy AI standalone Camera service.")
    parser.add_argument("--once", action="store_true", help="Check cameras once and exit.")
    parser.add_argument("--camera-id", type=int, help="Limit processing to one backend Camera ID.")
    parser.add_argument("--force", action="store_true", help="Bypass interval/active-hours for manual testing.")
    parser.add_argument("--poll-seconds", type=float, default=SETTINGS.poll_seconds)
    parser.add_argument("--backend-base-url", default=SETTINGS.backend_base_url)
    parser.add_argument("--access-token", default=SETTINGS.access_token)
    parser.add_argument("--refresh-token", default=SETTINGS.refresh_token)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    backend = BackendClient(
        args.backend_base_url,
        access_token=args.access_token,
        refresh_token=args.refresh_token,
        timeout=SETTINGS.timeout_seconds,
    )
    collector = CameraCollector(
        backend,
        timezone_name=SETTINGS.timezone_name,
        jpeg_quality=SETTINGS.jpeg_quality,
        warmup_frames=SETTINGS.warmup_frames,
        default_rtsp_username=SETTINGS.default_rtsp_username,
        default_rtsp_password=SETTINGS.default_rtsp_password,
    )

    if args.once:
        collector.process_all(camera_id=args.camera_id, force=args.force)
        return 0

    poll = max(5.0, float(args.poll_seconds))
    print(f"Leafy Camera service running. Poll interval: {poll:.0f}s")
    try:
        while True:
            collector.process_all(camera_id=args.camera_id, force=args.force)
            time.sleep(poll)
    except KeyboardInterrupt:
        print("Stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
