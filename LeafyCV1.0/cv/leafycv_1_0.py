#!/usr/bin/env python3
"""LeafyCV1.0 - farm-camera computer vision aligned to Database Schema v2.

This program follows the farm owner's shared-camera rule:
- open the RTSP stream only when a sample is due;
- read a few warm-up frames;
- release the camera immediately;
- process and save the still image locally;
- wait with no camera connection open.

The segmentation and fixed-slot measurements come from the V4 light-balanced,
stable-box model in the companion Python file.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import cv2
import numpy as np

from cv_api_client import CVApiClient
from django_backend_adapter import (
    MODEL_VERSION,
    add_growth_change,
    build_django_payload,
)
from image_quality import evaluate_image_quality

from crowding import compute_crowding

from basil_slot_vision_v4_10min_light_balanced_stable_boxes import (
    build_slot_map,
    colour_masks,
    green_mask,
    nearest_neighbour_radii,
    plant_metrics,
    remove_small_noise,
    select_box,
    select_plant_centres,
    slot_boundary_mask,
)


@dataclass(frozen=True)
class Camera:
    name: str
    ip: str
    port: int = 554


CAMERAS: dict[str, Camera] = {
    "level1_camera1": Camera("level1_camera1", os.getenv("FARM_CAMERA1_IP", "")),
    "level1_camera2": Camera("level1_camera2", os.getenv("FARM_CAMERA2_IP", "")),
}

OPEN_TIMEOUT_SECONDS = 5.0
READ_TIMEOUT_SECONDS = 8.0
WARMUP_FRAMES = 3
JPEG_QUALITY = 92
WINDOW_NAME = "LeafyCV1.0 - Farm Computer Vision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture bounded RTSP still images and run Leafy AI fixed-slot basil CV."
        )
    )
    parser.add_argument("camera", choices=CAMERAS.keys())
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of bounded capture cycles. Default: 1",
    )
    parser.add_argument(
        "--sample-minutes",
        type=float,
        default=10.0,
        help="Target minutes between captures. Default: 10",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output_farm_basil_snapshot_cv"),
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Saved ROI/slot configuration JSON path.",
    )
    parser.add_argument(
        "--lighting-profile",
        choices=("normal", "auto", "magenta"),
        default="auto",
    )
    parser.add_argument("--lower-h", type=int, default=32)
    parser.add_argument("--upper-h", type=int, default=95)
    parser.add_argument("--min-s", type=int, default=55)
    parser.add_argument("--min-v", type=int, default=35)
    parser.add_argument("--exg-threshold", type=int, default=18)
    parser.add_argument("--lab-a-max", type=int, default=150)
    parser.add_argument("--lab-b-min", type=int, default=115)
    parser.add_argument("--magenta-min-s", type=int, default=60)
    parser.add_argument("--magenta-max-v", type=int, default=210)
    parser.add_argument("--min-green-area", type=int, default=150)
    parser.add_argument("--min-green-ratio", type=float, default=0.00025)
    parser.add_argument("--visible-core-threshold", type=float, default=0.03)
    parser.add_argument("--visible-area-threshold", type=float, default=0.30)
    parser.add_argument("--ema-alpha", type=float, default=0.35)
    parser.add_argument("--bbox-alpha", type=float, default=0.35)
    parser.add_argument("--bbox-history", type=int, default=5)
    parser.add_argument("--bbox-hold-samples", type=int, default=2)
    parser.add_argument("--bbox-percentile", type=float, default=2.5)
    parser.add_argument("--reference-width-cm", type=float, default=10.0)
    parser.add_argument(
        "--background-diff",
        type=int,
        default=18,
        help="Background subtraction threshold for the optional empty-background filter.",
    )
    parser.add_argument(
        "--latest-image",
        type=Path,
        default=None,
        help=(
            "Read each 10-minute CV sample from a shared latest JPEG instead of "
            "opening RTSP directly. Use this with farm_camera_shared_service.py."
        ),
    )
    parser.add_argument(
        "--crowding-gap-px",
        type=int,
        default=3,
        help=(
            "Pixel tolerance used to detect visual contact between neighbouring "
            "registered plant slots. Default: 3"
        ),
    )
    parser.add_argument(
        "--crowding-min-contact-pixels",
        type=int,
        default=25,
        help=(
            "Minimum dilated-mask overlap pixels before a neighbouring slot pair "
            "is reported as touching/crowded. Default: 25"
        ),
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("LEAFY_CV_API_URL", ""),
        help=(
            "Backend endpoint that receives one CV sample. "
            "If omitted, API sending is disabled."
        ),
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("LEAFY_CV_API_KEY", ""),
        help="Optional bearer token. Prefer LEAFY_CV_API_KEY environment variable.",
    )
    parser.add_argument(
        "--api-send-images",
        choices=("none", "raw", "all"),
        default=os.getenv("LEAFY_CV_API_SEND_IMAGES", "raw"),
        help=(
            "none = metadata JSON only; raw = Django metadata + raw camera JPEG; "
            "all = raw + annotated + mask for debugging. Default: raw"
        ),
    )
    parser.add_argument(
        "--min-blur-score",
        type=float,
        default=15.0,
        help="Lenient image validity threshold. Default: 15",
    )
    parser.add_argument(
        "--min-mean-brightness",
        type=float,
        default=10.0,
        help="Extreme darkness validity threshold. Default: 10",
    )
    parser.add_argument(
        "--max-mean-brightness",
        type=float,
        default=245.0,
        help="Extreme overexposure validity threshold. Default: 245",
    )
    parser.add_argument(
        "--api-timeout",
        type=float,
        default=float(os.getenv("LEAFY_CV_API_TIMEOUT", "5")),
        help="HTTP API timeout in seconds. Default: 5",
    )
    return parser.parse_args()


def build_rtsp_url(camera: Camera) -> str:
    if not camera.ip:
        raise RuntimeError(
            f"Set the IP environment variable for {camera.name} before running."
        )
    username = os.getenv("FARM_CAMERA_USER", "")
    password = os.getenv("FARM_CAMERA_PASSWORD", "")
    path = os.getenv("FARM_CAMERA_RTSP_PATH", "")

    if not username or not password:
        raise RuntimeError(
            "Set FARM_CAMERA_USER and FARM_CAMERA_PASSWORD before running."
        )

    if path and not path.startswith("/"):
        path = "/" + path

    return (
        f"rtsp://{quote(username, safe='')}:{quote(password, safe='')}"
        f"@{camera.ip}:{camera.port}{path}"
    )


def capture_fresh_frame(camera: Camera) -> np.ndarray:
    """Open RTSP, decode a fresh frame, and always release immediately."""
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        "rtsp_transport;tcp"
        f"|stimeout;{int(OPEN_TIMEOUT_SECONDS * 1_000_000)}"
    )

    capture: cv2.VideoCapture | None = None
    try:
        capture = cv2.VideoCapture(build_rtsp_url(camera), cv2.CAP_FFMPEG)
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not capture.isOpened():
            raise ConnectionError(
                f"Could not open {camera.name} at {camera.ip}:{camera.port}. "
                "Check credentials, RTSP path, port 554 and FFmpeg support."
            )

        deadline = time.monotonic() + READ_TIMEOUT_SECONDS
        latest = None
        successful = 0

        while time.monotonic() < deadline:
            ok, frame = capture.read()
            if ok and frame is not None:
                latest = frame
                successful += 1
                if successful >= WARMUP_FRAMES:
                    return latest
            else:
                time.sleep(0.05)

        if latest is not None:
            return latest

        raise TimeoutError("RTSP opened, but no frame was decoded.")
    finally:
        if capture is not None:
            capture.release()


def read_latest_shared_image(path: Path) -> np.ndarray:
    """Read an atomically published latest JPEG from the shared camera service."""
    for _ in range(10):
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is not None and frame.size > 0:
            return frame
        time.sleep(0.1)
    raise FileNotFoundError(
        f"Could not read shared latest image: {path}. "
        "Start farm_camera_shared_service.py first and confirm latest.jpg is updating."
    )


def get_sample_frame(camera: Camera, latest_image: Path | None) -> np.ndarray:
    if latest_image is not None:
        return read_latest_shared_image(latest_image)
    return capture_fresh_frame(camera)


def save_config(
    path: Path,
    camera: Camera,
    frame_shape: tuple[int, ...],
    growing_zone: tuple[int, int, int, int],
    centres: list[tuple[int, int]],
    pixels_per_cm: float | None,
) -> dict[str, Path]:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "camera_name": camera.name,
        "camera_ip": camera.ip,
        "frame_width": int(frame_shape[1]),
        "frame_height": int(frame_shape[0]),
        "growing_zone": [int(v) for v in growing_zone],
        "plant_centres": [[int(x), int(y)] for x, y in centres],
        "pixels_per_cm": pixels_per_cm,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_config(
    path: Path,
    camera: Camera,
    frame_shape: tuple[int, ...],
) -> tuple[tuple[int, int, int, int], list[tuple[int, int]], float | None] | None:
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("camera_name") != camera.name:
        print("Saved configuration belongs to another camera; reconfiguring.")
        return None

    if (
        int(payload.get("frame_width", -1)) != int(frame_shape[1])
        or int(payload.get("frame_height", -1)) != int(frame_shape[0])
    ):
        print("Camera resolution changed; reconfiguring ROI and plant centres.")
        return None

    zone = tuple(int(v) for v in payload["growing_zone"])
    centres = [tuple(int(v) for v in p) for p in payload["plant_centres"]]
    pixels_per_cm = payload.get("pixels_per_cm")
    return zone, centres, float(pixels_per_cm) if pixels_per_cm else None


def configure_layout(
    frame: np.ndarray,
) -> tuple[tuple[int, int, int, int], list[tuple[int, int]]]:
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.imshow(WINDOW_NAME, frame)

    selected = select_box(WINDOW_NAME, frame, "Select the whole basil growing zone")
    if selected is None:
        selected = (0, 0, frame.shape[1], frame.shape[0])

    centres = select_plant_centres(WINDOW_NAME, frame, selected)
    if not centres:
        raise RuntimeError("At least one planted basil centre must be registered.")

    return selected, centres


def prepare_csv(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow(
            [
                "model_version",
                "captured_at",
                "camera_name",
                "sample_number",
                "total_canopy_coverage",
                "visible_plant_count",
                "image_measurement_valid",
                "processing_time_ms",
                "size_calibrated",
                "slot_id",
                "canopy_coverage",
                "width_px",
                "height_px",
                "width_cm",
                "height_cm",
                "green_percentage",
                "yellow_percentage",
                "crowding_percentage",
                "growth_change",
                "visible",
                "measurement_valid",
                "brown_percentage_local_only",
                "touching_neighbor_count_local_only",
                "touching_neighbors_local_only",
                "raw_image",
                "annotated_image",
                "mask_image",
            ]
        )


def process_frame(
    frame: np.ndarray,
    camera: Camera,
    sample_number: int,
    captured_at: datetime,
    growing_zone: tuple[int, int, int, int],
    centres_global: list[tuple[int, int]],
    pixels_per_cm: float | None,
    plant_states: list[dict],
    args: argparse.Namespace,
    background: np.ndarray | None = None,
    show_zones: bool = True,
) -> tuple[np.ndarray, np.ndarray, list[dict], float, int, dict]:
    frame_h, frame_w = frame.shape[:2]
    zone_x, zone_y, zone_w, zone_h = growing_zone

    zone_x = max(0, min(zone_x, frame_w - 1))
    zone_y = max(0, min(zone_y, frame_h - 1))
    zone_w = max(1, min(zone_w, frame_w - zone_x))
    zone_h = max(1, min(zone_h, frame_h - zone_y))

    zone = frame[zone_y : zone_y + zone_h, zone_x : zone_x + zone_w]
    image_quality = evaluate_image_quality(
        zone,
        min_blur_score=args.min_blur_score,
        min_mean_brightness=args.min_mean_brightness,
        max_mean_brightness=args.max_mean_brightness,
    )
    centres_local = [(x - zone_x, y - zone_y) for x, y in centres_global]
    slot_map = build_slot_map(zone_w, zone_h, centres_local)
    boundary = slot_boundary_mask(slot_map)
    core_radii = nearest_neighbour_radii(centres_local)

    masks = colour_masks(
        zone,
        args.lower_h,
        args.upper_h,
        args.min_s,
        args.min_v,
        args.exg_threshold,
        lighting_profile=args.lighting_profile,
        lab_a_max=args.lab_a_max,
        lab_b_min=args.lab_b_min,
        magenta_min_s=args.magenta_min_s,
        magenta_max_v=args.magenta_max_v,
        background=background,
        background_diff=args.background_diff,
    )

    masks = {
        key: remove_small_noise(value, args.min_green_area, args.min_green_ratio)
        for key, value in masks.items()
    }

    mask = masks["combined"]

    total_canopy = (
        100.0 * cv2.countNonZero(mask) / mask.size if mask.size else 0.0
    )

    while len(plant_states) < len(centres_local):
        plant_states.append({})
    if len(plant_states) > len(centres_local):
        del plant_states[len(centres_local) :]

    metrics: list[dict] = []
    for index, centre in enumerate(centres_local):
        metrics.append(
            plant_metrics(
                mask=mask,
                slot_map=slot_map,
                plant_index=index,
                centre=centre,
                core_radius=core_radii[index],
                state=plant_states[index],
                ema_alpha=args.ema_alpha,
                visible_core_threshold=args.visible_core_threshold,
                visible_area_threshold=args.visible_area_threshold,
                bbox_alpha=args.bbox_alpha,
                bbox_history_size=args.bbox_history,
                bbox_hold_frames=args.bbox_hold_samples,
                bbox_percentile=args.bbox_percentile,
                green_mask=masks["green"],
                yellow_mask=masks["yellow"],
                brown_mask=masks["brown"],
            )
        )

    visible_count = sum(1 for metric in metrics if metric["visible"])

    crowding = compute_crowding(
        mask=mask,
        slot_map=slot_map,
        plant_count=len(centres_local),
        gap_px=args.crowding_gap_px,
        min_contact_pixels=args.crowding_min_contact_pixels,
    )

    # Attach each plant's visual contact neighbours to its normal metrics.
    for plant_number, metric in enumerate(metrics, start=1):
        plant_id = f"P{plant_number}"
        neighbours = crowding["per_plant_touching_neighbors"].get(plant_id, [])
        metric["touching_neighbors"] = list(neighbours)
        metric["touching_neighbor_count"] = len(neighbours)
        metric["neighbor_count"] = int(
            crowding["per_plant_neighbor_count"].get(plant_id, 0)
        )
        metric["crowding_percentage"] = float(
            crowding["per_plant_crowding_percent"].get(plant_id, 0.0)
        )

    annotated = frame.copy()

    cv2.rectangle(
        annotated,
        (zone_x, zone_y),
        (zone_x + zone_w, zone_y + zone_h),
        (255, 180, 40),
        2,
    )

    if show_zones:
        yy, xx = np.where(boundary > 0)
        annotated[zone_y + yy, zone_x + xx] = (170, 90, 220)

    # Draw reported visual contact/encroachment between neighbouring slots.
    for contact in crowding["touching_pairs"]:
        a = int(contact["plant_a"][1:]) - 1
        b = int(contact["plant_b"][1:]) - 1
        if 0 <= a < len(centres_local) and 0 <= b < len(centres_local):
            ax, ay = centres_local[a]
            bx, by = centres_local[b]
            pa = (zone_x + ax, zone_y + ay)
            pb = (zone_x + bx, zone_y + by)
            cv2.line(annotated, pa, pb, (40, 120, 255), 3, cv2.LINE_AA)
            mx, my = (pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2
            cv2.putText(
                annotated,
                "CONTACT",
                (mx + 4, my - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (40, 120, 255),
                1,
                cv2.LINE_AA,
            )

    for plant_number, (centre, metric) in enumerate(
        zip(centres_local, metrics), start=1
    ):
        cx, cy = centre
        global_cx, global_cy = zone_x + cx, zone_y + cy
        marker_colour = (80, 230, 50) if metric["visible"] else (120, 120, 120)
        cv2.circle(annotated, (global_cx, global_cy), 7, marker_colour, -1)

        if metric["box_active"] and metric["w"] > 0 and metric["h"] > 0:
            x1 = zone_x + metric["x"]
            y1 = zone_y + metric["y"]
            cv2.rectangle(
                annotated,
                (x1, y1),
                (x1 + metric["w"], y1 + metric["h"]),
                (80, 190, 255),
                2,
            )

        width_px = int(round(metric["width_smooth"]))
        height_px = int(round(metric["height_smooth"]))
        if pixels_per_cm:
            size_text = f"{width_px / pixels_per_cm:.1f}x{height_px / pixels_per_cm:.1f}cm"
        else:
            size_text = f"{width_px}x{height_px}px"

        cv2.putText(
            annotated,
            (
                f"P{plant_number} {metric['coverage_smooth']:.1f}% {size_text}"
                + (
                    f" touch:{metric['touching_neighbor_count']}"
                    if metric.get('touching_neighbor_count', 0)
                    else ""
                )
            ),
            (global_cx + 8, max(22, global_cy - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            marker_colour,
            1,
            cv2.LINE_AA,
        )

    panel_h = min(215, frame_h)
    cv2.rectangle(annotated, (0, 0), (min(920, frame_w), panel_h), (18, 35, 27), -1)
    lines = [
        f"{MODEL_VERSION} - Farm Computer Vision",
        f"Camera: {camera.name} ({camera.ip})",
        f"Captured: {captured_at.astimezone().isoformat(timespec='seconds')}",
        f"Registered plants: {len(centres_global)} | Visible slots: {visible_count}",
        f"Whole-zone canopy coverage: {total_canopy:.2f}%",
        (
            f"Visual crowding contacts: {crowding['touching_pair_count']}/"
            f"{crowding['neighbor_pair_count']} neighbour pairs "
            f"({crowding['crowding_percent']:.1f}%)"
        ),
        (
            "Measurement valid: "
            + ("YES" if image_quality["measurement_valid"] else "NO")
            + f" | blur={image_quality['blur_score']:.1f}"
        ),
        "Calibration: "
        + (
            f"{pixels_per_cm:.2f} px/cm"
            if pixels_per_cm
            else "not set - pixel measurements still active"
        ),
        "Background filter: " + ("ON" if background is not None else "OFF"),
        "R reselect zone + plants | S re-register plants | Q/Esc stop",
    ]
    for i, line in enumerate(lines):
        cv2.putText(
            annotated,
            line,
            (15, 28 + i * 27),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.62 if i == 0 else 0.48,
            (240, 245, 242),
            2 if i == 0 else 1,
            cv2.LINE_AA,
        )

    return annotated, mask, metrics, total_canopy, visible_count, crowding, image_quality


def write_sample(
    output: Path,
    csv_path: Path,
    camera: Camera,
    sample_number: int,
    captured_at: datetime,
    frame: np.ndarray,
    annotated: np.ndarray,
    mask: np.ndarray,
    metrics: list[dict],
    total_canopy: float,
    visible_count: int,
    pixels_per_cm: float | None,
    processing_time_ms: int,
    image_measurement_valid: bool,
) -> dict[str, Path]:
    stamp = captured_at.astimezone().strftime("%Y%m%d_%H%M%S_%f")
    raw_path = output / "raw" / f"{camera.name}_{stamp}.jpg"
    annotated_path = output / "annotated" / f"{camera.name}_{stamp}_annotated.jpg"
    mask_path = output / "masks" / f"{camera.name}_{stamp}_mask.png"

    for path in (raw_path, annotated_path, mask_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    if not cv2.imwrite(
        str(raw_path), frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
    ):
        raise OSError(f"Could not save {raw_path}")
    if not cv2.imwrite(
        str(annotated_path),
        annotated,
        [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY],
    ):
        raise OSError(f"Could not save {annotated_path}")
    if not cv2.imwrite(str(mask_path), mask):
        raise OSError(f"Could not save {mask_path}")

    captured_text = captured_at.astimezone().isoformat(timespec="seconds")
    size_calibrated = bool(pixels_per_cm)

    with csv_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for slot_id, metric in enumerate(metrics, start=1):
            width_px = float(metric["width_smooth"])
            height_px = float(metric["height_smooth"])
            width_cm = width_px / pixels_per_cm if pixels_per_cm else 0.0
            height_cm = height_px / pixels_per_cm if pixels_per_cm else 0.0
            plant_valid = bool(
                image_measurement_valid and metric["visible"]
            )

            writer.writerow(
                [
                    MODEL_VERSION,
                    captured_text,
                    camera.name,
                    sample_number,
                    f"{total_canopy:.4f}",
                    visible_count,
                    image_measurement_valid,
                    processing_time_ms,
                    size_calibrated,
                    slot_id,
                    f"{metric['coverage_smooth']:.4f}",
                    f"{width_px:.4f}",
                    f"{height_px:.4f}",
                    f"{width_cm:.4f}",
                    f"{height_cm:.4f}",
                    f"{metric['green_percent']:.4f}",
                    f"{metric['yellow_percent']:.4f}",
                    f"{metric.get('crowding_percentage', 0.0):.4f}",
                    f"{metric.get('growth_change', 0.0):.4f}",
                    metric["visible"],
                    plant_valid,
                    f"{metric['brown_percent']:.4f}",
                    metric.get("touching_neighbor_count", 0),
                    json.dumps(
                        metric.get("touching_neighbors", []),
                        separators=(",", ":"),
                    ),
                    str(raw_path),
                    str(annotated_path),
                    str(mask_path),
                ]
            )

    print(f"Saved {MODEL_VERSION} sample {sample_number}: {annotated_path}")
    return {
        "raw": raw_path,
        "annotated": annotated_path,
        "mask": mask_path,
    }


def wait_for_command(deadline: float) -> str:
    """Keep result window responsive while waiting for the next sample."""
    while time.monotonic() < deadline:
        key = cv2.waitKey(100) & 0xFF
        if key in (ord("q"), ord("Q"), 27):
            return "quit"
        if key in (ord("r"), ord("R")):
            return "reconfigure_all"
        if key in (ord("s"), ord("S")):
            return "reconfigure_centres"
        if key in (ord("k"), ord("K")):
            return "reference"
        if key in (ord("g"), ord("G")):
            return "background"
        if key in (ord("n"), ord("N")):
            return "clear_background"
        if key in (ord("v"), ord("V")):
            return "toggle_zones"
        time.sleep(0.02)
    return "next"


def main() -> int:
    args = parse_args()
    if args.count < 1:
        print("--count must be at least 1", file=sys.stderr)
        return 2
    if args.sample_minutes <= 0:
        print("--sample-minutes must be greater than 0", file=sys.stderr)
        return 2

    camera = CAMERAS[args.camera]
    api_client = CVApiClient(
        url=args.api_url,
        api_key=args.api_key,
        timeout=args.api_timeout,
    )
    if api_client.enabled:
        print(f"{MODEL_VERSION} Django API enabled: {args.api_url}")
        print(f"CV API image mode: {args.api_send_images}")
    else:
        print(f"{MODEL_VERSION} API disabled; local CSV/images will still be saved.")
    args.output.mkdir(parents=True, exist_ok=True)
    config_path = args.config or args.output / f"{camera.name}_layout.json"
    csv_path = args.output / "leafycv_measurements.csv"
    prepare_csv(csv_path)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    plant_states: list[dict] = []
    previous_saved_coverages: dict[int, float] = {}
    growing_zone = None
    centres_global: list[tuple[int, int]] = []
    pixels_per_cm = None

    interval_seconds = args.sample_minutes * 60.0

    empty_background: np.ndarray | None = None
    reference_box: tuple[int, int, int, int] | None = None
    show_zones = True

    def render_preview(
        frame: np.ndarray,
        sample_number: int,
        captured_at: datetime,
    ) -> np.ndarray:
        nonlocal plant_states
        annotated, _mask, _metrics, _total_canopy, _visible_count, _crowding, _image_quality = process_frame(
            frame=frame,
            camera=camera,
            sample_number=sample_number,
            captured_at=captured_at,
            growing_zone=growing_zone,
            centres_global=centres_global,
            pixels_per_cm=pixels_per_cm,
            plant_states=plant_states,
            args=args,
            background=empty_background,
            show_zones=show_zones,
        )
        cv2.imshow(WINDOW_NAME, annotated)
        cv2.waitKey(1)
        return annotated

    def fresh_control_frame() -> tuple[np.ndarray, datetime]:
        """Get the newest camera image for interactive reconfiguration.

        In shared-image mode this reads the current atomically published JPEG.
        In direct snapshot mode it opens RTSP briefly and releases it immediately.
        """
        current = get_sample_frame(camera, args.latest_image)
        return current, datetime.now().astimezone()

    try:
        for sample_number in range(1, args.count + 1):
            cycle_started = time.monotonic()
            captured_at = datetime.now().astimezone()

            if args.latest_image is None:
                print(
                    f"Opening {camera.name} ({camera.ip}) for sample "
                    f"{sample_number}/{args.count} ..."
                )
                frame = get_sample_frame(camera, None)
                print(
                    f"Fresh frame decoded; RTSP connection released for sample "
                    f"{sample_number}."
                )
            else:
                print(
                    f"Reading shared latest image for sample "
                    f"{sample_number}/{args.count}: {args.latest_image}"
                )
                frame = get_sample_frame(camera, args.latest_image)

            if growing_zone is None:
                loaded = load_config(config_path, camera, frame.shape)
                if loaded is None:
                    growing_zone, centres_global = configure_layout(frame)
                    pixels_per_cm = None
                    save_config(
                        config_path,
                        camera,
                        frame.shape,
                        growing_zone,
                        centres_global,
                        pixels_per_cm,
                    )
                    print(f"Saved layout configuration: {config_path}")
                else:
                    growing_zone, centres_global, pixels_per_cm = loaded
                    print(f"Loaded layout configuration: {config_path}")

            analysis_started = time.perf_counter()
            annotated, mask, metrics, total_canopy, visible_count, crowding, image_quality = process_frame(
                frame=frame,
                camera=camera,
                sample_number=sample_number,
                captured_at=captured_at,
                growing_zone=growing_zone,
                centres_global=centres_global,
                pixels_per_cm=pixels_per_cm,
                plant_states=plant_states,
                args=args,
                background=empty_background,
                show_zones=show_zones,
            )
            processing_time_ms = int(round((time.perf_counter() - analysis_started) * 1000.0))

            add_growth_change(metrics, previous_saved_coverages)

            saved_files = write_sample(
                output=args.output,
                csv_path=csv_path,
                camera=camera,
                sample_number=sample_number,
                captured_at=captured_at,
                frame=frame,
                annotated=annotated,
                mask=mask,
                metrics=metrics,
                total_canopy=total_canopy,
                visible_count=visible_count,
                pixels_per_cm=pixels_per_cm,
                processing_time_ms=processing_time_ms,
                image_measurement_valid=bool(image_quality["measurement_valid"]),
            )

            if api_client.enabled:
                payload = build_django_payload(
                    camera_name=camera.name,
                    captured_at=captured_at,
                    metrics=metrics,
                    total_canopy=total_canopy,
                    visible_count=visible_count,
                    pixels_per_cm=pixels_per_cm,
                    processing_time_ms=processing_time_ms,
                    image_measurement_valid=bool(
                        image_quality["measurement_valid"]
                    ),
                )
                api_client.send_sample(
                    payload=payload,
                    raw_path=saved_files["raw"],
                    annotated_path=saved_files["annotated"],
                    mask_path=saved_files["mask"],
                    image_mode=args.api_send_images,
                )

            cv2.imshow(WINDOW_NAME, annotated)
            cv2.waitKey(1)

            if sample_number < args.count:
                deadline = cycle_started + interval_seconds
                print(
                    f"Waiting for the next {args.sample_minutes:g}-minute sample. "
                    "Press R to reselect the growing zone + plant centres, "
                    "S to re-register plant centres only, K to recalibrate size, "
                    "or Q/Escape to stop."
                )

                while True:
                    action = wait_for_command(deadline)

                    if action == "quit":
                        return 0

                    if action == "next":
                        break

                    if action == "reconfigure_all":
                        print("Refreshing camera image, then reselecting growing zone and planted positions...")
                        frame, captured_at = fresh_control_frame()
                        new_zone, new_centres = configure_layout(frame)
                        growing_zone = new_zone
                        centres_global = new_centres
                        pixels_per_cm = None
                        empty_background = None
                        reference_box = None
                        plant_states.clear()
                        previous_saved_coverages.clear()
                        save_config(
                            config_path,
                            camera,
                            frame.shape,
                            growing_zone,
                            centres_global,
                            pixels_per_cm,
                        )
                        render_preview(frame, sample_number, captured_at)
                        print(f"Updated layout saved: {config_path}")
                        continue

                    if action == "reconfigure_centres":
                        print("Refreshing camera image, then re-registering planted positions...")
                        frame, captured_at = fresh_control_frame()
                        new_centres = select_plant_centres(
                            WINDOW_NAME,
                            frame,
                            growing_zone,
                        )
                        if new_centres:
                            centres_global = new_centres
                            plant_states.clear()
                            previous_saved_coverages.clear()
                            save_config(
                                config_path,
                                camera,
                                frame.shape,
                                growing_zone,
                                centres_global,
                                pixels_per_cm,
                            )
                            render_preview(frame, sample_number, captured_at)
                            print(f"Updated plant centres saved: {config_path}")
                        else:
                            print("Plant-centre update cancelled; keeping old centres.")
                        continue

                    if action == "reference":
                        print("Refreshing camera image, then selecting known-width reference...")
                        frame, captured_at = fresh_control_frame()
                        selected = select_box(
                            WINDOW_NAME,
                            frame,
                            f"Select known-width reference ({args.reference_width_cm:.1f} cm)",
                        )
                        if selected is not None:
                            reference_box = selected
                            reference_pixel_width = reference_box[2]
                            pixels_per_cm = reference_pixel_width / args.reference_width_cm
                            save_config(
                                config_path,
                                camera,
                                frame.shape,
                                growing_zone,
                                centres_global,
                                pixels_per_cm,
                            )
                            print(f"Calibration: {pixels_per_cm:.3f} px/cm (saved)")
                            render_preview(frame, sample_number, captured_at)
                        else:
                            print("Reference calibration cancelled.")
                        continue

                    if action == "background":
                        if growing_zone is not None:
                            print("Refreshing camera image for empty-background capture...")
                            frame, captured_at = fresh_control_frame()
                            bx, by, bw, bh = growing_zone
                            empty_background = frame[by:by + bh, bx:bx + bw].copy()
                            print("Empty background captured. Only use this when the selected zone is actually empty.")
                            render_preview(frame, sample_number, captured_at)
                        else:
                            print("No growing zone available to capture background.")
                        continue

                    if action == "clear_background":
                        empty_background = None
                        print("Background filter cleared.")
                        render_preview(frame, sample_number, captured_at)
                        continue

                    if action == "toggle_zones":
                        show_zones = not show_zones
                        print(f"Zone overlay {'enabled' if show_zones else 'disabled'}.")
                        render_preview(frame, sample_number, captured_at)
                        continue

        return 0
    except KeyboardInterrupt:
        print("Stopped by user.")
        return 130
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    finally:
        cv2.destroyAllWindows()
        if args.latest_image is None:
            print("Finished. No RTSP stream is left open.")
        else:
            print("Finished CV sampling. Shared camera service, if running, is separate.")


if __name__ == "__main__":
    raise SystemExit(main())
