"""Local development smoke test for a webcam without Django or lighting."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from camera.camera_client import capture_fresh_frame, encode_jpeg


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--output", type=Path, default=Path("webcam_test.jpg"))
    args = parser.parse_args()

    camera = {"id": "local", "source_type": "WEBCAM", "webcam_index": args.index}
    frame = capture_fresh_frame(camera)
    jpeg = encode_jpeg(frame)
    args.output.write_bytes(jpeg)
    print(f"Saved {frame.shape[1]}x{frame.shape[0]} test image to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
