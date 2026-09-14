#!/usr/bin/env python3
"""Command-line entry point for the standalone LeafyAI Camera service."""

from __future__ import annotations

import argparse
import time

from .backend_client import BackendClient
from .camera_collector import CameraCollector
from .config import SETTINGS
from .lighting_client import HttpLightingController


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LeafyAI standalone Camera service.")
    parser.add_argument("--once", action="store_true", help="Check cameras once and exit.")
    parser.add_argument("--camera-id", type=int, help="Limit processing to one backend Camera ID.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass interval/active-hours. Allowed only together with --once.",
    )
    parser.add_argument("--poll-seconds", type=float, default=SETTINGS.poll_seconds)
    parser.add_argument("--backend-base-url", default=SETTINGS.backend_base_url)
    parser.add_argument("--access-token", default=SETTINGS.access_token)
    parser.add_argument("--refresh-token", default=SETTINGS.refresh_token)
    return parser


def _build_lighting_controller() -> HttpLightingController | None:
    """Create the optional switch client only when explicitly enabled."""
    if not SETTINGS.lighting_enabled:
        return None

    return HttpLightingController(
        SETTINGS.lighting_base_url,
        state_path=SETTINGS.lighting_state_path,
        access_token=SETTINGS.lighting_access_token,
        timeout=SETTINGS.lighting_timeout_seconds,
        require_confirmation=SETTINGS.lighting_require_confirmation,
    )


def main() -> int:
    args = build_parser().parse_args()

    # --force in a permanent loop could repeatedly capture every poll cycle.
    # Restrict it to an explicit one-shot integration test.
    if args.force and not args.once:
        raise SystemExit("ERROR: --force is allowed only with --once.")

    backend = BackendClient(
        args.backend_base_url,
        access_token=args.access_token,
        refresh_token=args.refresh_token,
        username=SETTINGS.backend_username,
        password=SETTINGS.backend_password,
        timeout=SETTINGS.timeout_seconds,
    )

    collector = CameraCollector(
        backend,
        timezone_name=SETTINGS.timezone_name,
        jpeg_quality=SETTINGS.jpeg_quality,
        warmup_frames=SETTINGS.warmup_frames,
        default_rtsp_username=SETTINGS.default_rtsp_username,
        default_rtsp_password=SETTINGS.default_rtsp_password,
        lighting=_build_lighting_controller(),
        pre_capture_light_off_seconds=SETTINGS.pre_capture_light_off_seconds,
        post_capture_restore_seconds=SETTINGS.post_capture_restore_seconds,
    )

    if args.once:
        collector.process_all(camera_id=args.camera_id, force=args.force)
        return 0

    poll = max(5.0, float(args.poll_seconds))
    print(f"Leafy Camera service running. Poll interval: {poll:.0f}s")
    try:
        while True:
            try:
                collector.process_all(camera_id=args.camera_id, force=False)
            except Exception as exc:
                print(f"Camera service warning: {exc}")
            time.sleep(poll)
    except KeyboardInterrupt:
        print("Stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
