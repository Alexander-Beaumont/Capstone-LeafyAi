#!/usr/bin/env python3
"""
Leafy AI - Basil Slot Vision V4

Designed for a fixed NFT / vertical-farm camera.

Why this is more stable than clustering:
- You register each planted basil position ONCE by clicking its centre.
- The program creates permanent nearest-centre (Voronoi) zones.
- Plant count comes from registered planting positions, not from noisy clustering.
- Touching canopies do not merge the plant identities.
- Every plant keeps the same ID: P1, P2, P3...
- Detection is always active.
- Size calibration is optional; without it dimensions remain in pixels.

Important limitation:
If one plant completely visually hides another, a single RGB camera cannot recover
the hidden leaves. But the hidden plant's identity/count is still preserved because
its planting position is known.

Controls
--------
R       Reselect whole growing zone
S       Register/re-register plant centres
K       Calibrate known-width reference object
G       Capture optional empty background
N       Clear background calibration
M       Show/hide segmentation mask
V       Show/hide permanent plant zones
P       Save snapshot
SPACE   Pause/resume
Q/ESC   Quit
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


def parse_source(value: str):
    value = value.strip()
    return int(value) if value.isdigit() else value


def select_box(window_name, frame, message):
    view = frame.copy()

    cv2.putText(
        view,
        message,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.70,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        view,
        "Drag a rectangle, then ENTER/SPACE. C cancels.",
        (20, 74),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    x, y, w, h = [
        int(v)
        for v in cv2.selectROI(
            window_name,
            view,
            showCrosshair=True,
            fromCenter=False,
        )
    ]

    if w <= 0 or h <= 0:
        return None

    return x, y, w, h


def select_plant_centres(window_name, frame, zone_roi):
    """
    Left-click each planted basil position.
    Right-click removes the most recent point.
    C clears all points.
    ENTER/SPACE accepts.
    ESC cancels.
    """
    points = []
    x0, y0, rw, rh = zone_roi

    def on_mouse(event, x, y, flags, param):
        nonlocal points

        if event == cv2.EVENT_LBUTTONDOWN:
            if x0 <= x < x0 + rw and y0 <= y < y0 + rh:
                points.append((x, y))

        elif event == cv2.EVENT_RBUTTONDOWN:
            if points:
                points.pop()

    cv2.setMouseCallback(window_name, on_mouse)

    try:
        while True:
            display = frame.copy()

            cv2.rectangle(
                display,
                (x0, y0),
                (x0 + rw, y0 + rh),
                (255, 180, 40),
                2,
            )

            overlay = display.copy()
            cv2.rectangle(
                overlay,
                (0, 0),
                (min(display.shape[1], 900), 100),
                (18, 35, 27),
                -1,
            )
            cv2.addWeighted(overlay, 0.78, display, 0.22, 0, display)

            cv2.putText(
                display,
                "Click the centre/base position of EVERY planted basil",
                (15, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.68,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                display,
                "Left click add | Right click undo | C clear | ENTER/SPACE finish",
                (15, 62),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (230, 240, 235),
                1,
                cv2.LINE_AA,
            )

            cv2.putText(
                display,
                f"Registered plants: {len(points)}",
                (15, 88),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (80, 220, 255),
                1,
                cv2.LINE_AA,
            )

            for index, (px, py) in enumerate(points, start=1):
                cv2.circle(
                    display,
                    (px, py),
                    7,
                    (80, 190, 255),
                    -1,
                )

                cv2.putText(
                    display,
                    f"P{index}",
                    (px + 9, py - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.50,
                    (80, 190, 255),
                    2,
                    cv2.LINE_AA,
                )

            cv2.imshow(window_name, display)

            key = cv2.waitKey(20) & 0xFF

            if key in (13, ord(" ")):
                return points.copy()

            if key == ord("c"):
                points.clear()

            if key == 27:
                return None

    finally:
        cv2.setMouseCallback(
            window_name,
            lambda *args: None,
        )


def green_mask(
    image,
    lower_h,
    upper_h,
    min_s,
    min_v,
    exg_threshold,
    background=None,
    background_diff=18,
):
    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    hsv_mask = cv2.inRange(
        hsv,
        np.array(
            [lower_h, min_s, min_v],
            dtype=np.uint8,
        ),
        np.array(
            [upper_h, 255, 255],
            dtype=np.uint8,
        ),
    )

    b, g, r = cv2.split(image)

    b16 = b.astype(np.int16)
    g16 = g.astype(np.int16)
    r16 = r.astype(np.int16)

    excess_green = (
        2 * g16
        - r16
        - b16
    )

    exg_mask = np.where(
        excess_green >= exg_threshold,
        255,
        0,
    ).astype(np.uint8)

    dominant_green = np.where(
        (g16 >= r16 + 6)
        & (g16 >= b16 + 6),
        255,
        0,
    ).astype(np.uint8)

    mask = cv2.bitwise_and(
        hsv_mask,
        exg_mask,
    )

    mask = cv2.bitwise_and(
        mask,
        dominant_green,
    )

    if (
        background is not None
        and background.shape == image.shape
    ):
        difference = cv2.absdiff(
            image,
            background,
        )

        difference = cv2.cvtColor(
            difference,
            cv2.COLOR_BGR2GRAY,
        )

        _, changed = cv2.threshold(
            difference,
            background_diff,
            255,
            cv2.THRESH_BINARY,
        )

        changed = cv2.morphologyEx(
            changed,
            cv2.MORPH_OPEN,
            np.ones((3, 3), np.uint8),
        )

        mask = cv2.bitwise_and(
            mask,
            changed,
        )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        np.ones((3, 3), np.uint8),
        iterations=1,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        np.ones((5, 5), np.uint8),
        iterations=1,
    )

    return mask


def remove_small_noise(
    mask,
    minimum_pixels,
    minimum_ratio,
):
    roi_pixels = mask.size

    minimum_area = max(
        minimum_pixels,
        int(roi_pixels * minimum_ratio),
    )

    count, labels, stats, _ = (
        cv2.connectedComponentsWithStats(
            mask,
            connectivity=8,
        )
    )

    cleaned = np.zeros_like(mask)

    for component_id in range(1, count):
        area = int(
            stats[
                component_id,
                cv2.CC_STAT_AREA,
            ]
        )

        if area >= minimum_area:
            cleaned[
                labels == component_id
            ] = 255

    return cleaned


def build_slot_map(
    roi_width,
    roi_height,
    centres_local,
):
    """
    Assign every ROI pixel to the nearest registered plant centre.
    Computed only when centres/ROI change.
    """
    yy, xx = np.indices(
        (roi_height, roi_width),
        dtype=np.float32,
    )

    labels = np.zeros(
        (roi_height, roi_width),
        dtype=np.int16,
    )

    minimum_distance = np.full(
        (roi_height, roi_width),
        np.inf,
        dtype=np.float32,
    )

    for plant_index, (cx, cy) in enumerate(
        centres_local
    ):
        distance = (
            (xx - float(cx)) ** 2
            + (yy - float(cy)) ** 2
        )

        update = distance < minimum_distance

        labels[update] = plant_index
        minimum_distance[update] = distance[update]

    return labels


def slot_boundary_mask(slot_map):
    boundary = np.zeros(
        slot_map.shape,
        dtype=np.uint8,
    )

    boundary[:, 1:] |= (
        slot_map[:, 1:]
        != slot_map[:, :-1]
    ).astype(np.uint8) * 255

    boundary[1:, :] |= (
        slot_map[1:, :]
        != slot_map[:-1, :]
    ).astype(np.uint8) * 255

    return boundary


def nearest_neighbour_radii(
    centres_local,
    default_radius=35,
):
    """
    Produce a stable core radius for each plant.
    The core is used to determine whether green material is visible around
    that plant's registered base/centre.
    """
    if len(centres_local) <= 1:
        return [default_radius] * len(
            centres_local
        )

    radii = []

    for i, (x1, y1) in enumerate(
        centres_local
    ):
        nearest = None

        for j, (x2, y2) in enumerate(
            centres_local
        ):
            if i == j:
                continue

            distance = (
                (x1 - x2) ** 2
                + (y1 - y2) ** 2
            ) ** 0.5

            if (
                nearest is None
                or distance < nearest
            ):
                nearest = distance

        radius = int(
            max(
                12,
                min(
                    60,
                    nearest * 0.22,
                ),
            )
        )

        radii.append(radius)

    return radii


def plant_metrics(
    mask,
    slot_map,
    plant_index,
    centre,
    core_radius,
    state,
    ema_alpha,
    visible_core_threshold,
    visible_area_threshold,
):
    """
    Measure canopy assigned to one permanent plant slot.
    """
    slot = slot_map == plant_index

    plant_pixels = (
        (mask > 0)
        & slot
    )

    slot_area = int(
        np.count_nonzero(slot)
    )

    green_area = int(
        np.count_nonzero(plant_pixels)
    )

    coverage = (
        100.0
        * green_area
        / slot_area
        if slot_area > 0
        else 0.0
    )

    cx, cy = centre

    yy, xx = np.ogrid[
        :mask.shape[0],
        :mask.shape[1],
    ]

    core = (
        (xx - cx) ** 2
        + (yy - cy) ** 2
        <= core_radius ** 2
    )

    core = (
        core
        & slot
    )

    core_area = int(
        np.count_nonzero(core)
    )

    core_green = int(
        np.count_nonzero(
            plant_pixels
            & core
        )
    )

    core_green_ratio = (
        core_green
        / core_area
        if core_area > 0
        else 0.0
    )

    visible = (
        core_green_ratio
        >= visible_core_threshold
        or coverage
        >= visible_area_threshold
    )

    plant_binary = np.where(
        plant_pixels,
        255,
        0,
    ).astype(np.uint8)

    points = cv2.findNonZero(
        plant_binary
    )

    if points is not None:
        x, y, w, h = cv2.boundingRect(
            points
        )
    else:
        x = y = w = h = 0

    previous_coverage = state.get(
        "coverage",
        coverage,
    )

    previous_width = state.get(
        "width",
        float(w),
    )

    previous_height = state.get(
        "height",
        float(h),
    )

    smoothed_coverage = (
        ema_alpha * coverage
        + (1.0 - ema_alpha)
        * previous_coverage
    )

    smoothed_width = (
        ema_alpha * float(w)
        + (1.0 - ema_alpha)
        * previous_width
    )

    smoothed_height = (
        ema_alpha * float(h)
        + (1.0 - ema_alpha)
        * previous_height
    )

    state["coverage"] = smoothed_coverage
    state["width"] = smoothed_width
    state["height"] = smoothed_height

    return {
        "visible": visible,
        "coverage": coverage,
        "coverage_smooth": smoothed_coverage,
        "core_green_ratio": core_green_ratio,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "width_smooth": smoothed_width,
        "height_smooth": smoothed_height,
        "green_area": green_area,
        "slot_area": slot_area,
    }


def prepare_csv(path):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        csv.writer(file).writerow(
            [
                "timestamp",
                "frame",
                "configured_plant_count",
                "visible_plant_count",
                "total_canopy_percent",
                "plant_id",
                "visible",
                "plant_slot_coverage_percent",
                "core_green_ratio",
                "assigned_width_px",
                "assigned_height_px",
                "assigned_width_cm",
                "assigned_height_cm",
            ]
        )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        default="0",
    )

    parser.add_argument(
        "--width",
        type=int,
        default=1280,
    )

    parser.add_argument(
        "--height",
        type=int,
        default=720,
    )

    parser.add_argument(
        "--fps",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--lower-h",
        type=int,
        default=32,
    )

    parser.add_argument(
        "--upper-h",
        type=int,
        default=95,
    )

    parser.add_argument(
        "--min-s",
        type=int,
        default=55,
    )

    parser.add_argument(
        "--min-v",
        type=int,
        default=35,
    )

    parser.add_argument(
        "--exg-threshold",
        type=int,
        default=18,
    )

    parser.add_argument(
        "--min-green-area",
        type=int,
        default=150,
    )

    parser.add_argument(
        "--min-green-ratio",
        type=float,
        default=0.00025,
    )

    parser.add_argument(
        "--visible-core-threshold",
        type=float,
        default=0.03,
        help=(
            "Fraction of green pixels in the centre core "
            "for a plant to be considered visibly present."
        ),
    )

    parser.add_argument(
        "--visible-area-threshold",
        type=float,
        default=0.30,
        help=(
            "Slot canopy percentage for visible presence fallback."
        ),
    )

    parser.add_argument(
        "--ema-alpha",
        type=float,
        default=0.18,
        help="Smoothing strength for plant size/coverage.",
    )

    parser.add_argument(
        "--reference-width-cm",
        type=float,
        default=10.0,
    )

    parser.add_argument(
        "--background-diff",
        type=int,
        default=18,
    )

    parser.add_argument(
        "--output",
        default="output_basil_slots_v4",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    source = parse_source(
        args.source
    )

    is_webcam = isinstance(
        source,
        int,
    )

    if is_webcam:
        capture = cv2.VideoCapture(
            source,
            cv2.CAP_DSHOW,
        )

        if not capture.isOpened():
            capture.release()
            capture = cv2.VideoCapture(
                source
            )

        capture.set(
            cv2.CAP_PROP_FOURCC,
            cv2.VideoWriter_fourcc(
                *"MJPG"
            ),
        )

        capture.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            args.width,
        )

        capture.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            args.height,
        )

        capture.set(
            cv2.CAP_PROP_FPS,
            args.fps,
        )

    else:
        capture = cv2.VideoCapture(
            source
        )

    if not capture.isOpened():
        raise SystemExit(
            f"Could not open source: {source}"
        )

    output_dir = Path(
        args.output
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = (
        output_dir
        / "basil_slot_measurements.csv"
    )

    prepare_csv(
        csv_path
    )

    window_name = (
        "Leafy AI - Basil Slot Vision V4"
    )

    cv2.namedWindow(
        window_name,
        cv2.WINDOW_NORMAL,
    )

    growing_zone = None

    plant_centres_global = []
    plant_centres_local = []

    slot_map = None
    slot_boundary = None
    core_radii = []

    plant_states = []

    empty_background = None

    reference_box = None
    pixels_per_cm = None

    show_mask = True
    show_zones = True
    paused = False

    frame_number = 0
    last_frame = None

    print()
    print("Leafy AI Basil Slot Vision V4")
    print()
    print(
        "Plant count comes from registered planting positions, "
        "NOT frame-by-frame clustering."
    )
    print()
    print(
        "R zone | S plant centres | K reference | "
        "G empty background | N clear background | "
        "V zones | M mask | P snapshot | SPACE pause | Q quit"
    )
    print()

    while True:
        if (
            not paused
            or last_frame is None
        ):
            success, frame = (
                capture.read()
            )

            if not success:
                if is_webcam:
                    continue

                print(
                    "Video finished."
                )
                break

            if is_webcam:
                frame = cv2.flip(
                    frame,
                    1,
                )

            last_frame = (
                frame.copy()
            )

            frame_number += 1

        else:
            frame = (
                last_frame.copy()
            )

        frame_h, frame_w = (
            frame.shape[:2]
        )

        if growing_zone is None:
            cv2.imshow(
                window_name,
                frame,
            )

            selected = select_box(
                window_name,
                frame,
                "Select the whole basil growing zone",
            )

            growing_zone = (
                selected
                if selected is not None
                else (
                    0,
                    0,
                    frame_w,
                    frame_h,
                )
            )

            continue

        if not plant_centres_global:
            selected_centres = (
                select_plant_centres(
                    window_name,
                    frame,
                    growing_zone,
                )
            )

            if selected_centres:
                plant_centres_global = (
                    selected_centres
                )
            else:
                # Keep prompting until at least one plant is registered.
                continue

            zone_x, zone_y, zone_w, zone_h = (
                growing_zone
            )

            plant_centres_local = [
                (
                    px - zone_x,
                    py - zone_y,
                )
                for px, py
                in plant_centres_global
            ]

            slot_map = build_slot_map(
                zone_w,
                zone_h,
                plant_centres_local,
            )

            slot_boundary = (
                slot_boundary_mask(
                    slot_map
                )
            )

            core_radii = (
                nearest_neighbour_radii(
                    plant_centres_local
                )
            )

            plant_states = [
                {}
                for _
                in plant_centres_local
            ]

            continue

        zone_x, zone_y, zone_w, zone_h = (
            growing_zone
        )

        zone_x = max(
            0,
            min(
                zone_x,
                frame_w - 1,
            ),
        )

        zone_y = max(
            0,
            min(
                zone_y,
                frame_h - 1,
            ),
        )

        zone_w = max(
            1,
            min(
                zone_w,
                frame_w - zone_x,
            ),
        )

        zone_h = max(
            1,
            min(
                zone_h,
                frame_h - zone_y,
            ),
        )

        zone = frame[
            zone_y:zone_y + zone_h,
            zone_x:zone_x + zone_w,
        ]

        # Rebuild maps if ROI size changes unexpectedly.
        if (
            slot_map is None
            or slot_map.shape
            != (zone_h, zone_w)
        ):
            plant_centres_local = [
                (
                    px - zone_x,
                    py - zone_y,
                )
                for px, py
                in plant_centres_global
            ]

            slot_map = build_slot_map(
                zone_w,
                zone_h,
                plant_centres_local,
            )

            slot_boundary = (
                slot_boundary_mask(
                    slot_map
                )
            )

            core_radii = (
                nearest_neighbour_radii(
                    plant_centres_local
                )
            )

        mask = green_mask(
            zone,
            args.lower_h,
            args.upper_h,
            args.min_s,
            args.min_v,
            args.exg_threshold,
            background=empty_background,
            background_diff=args.background_diff,
        )

        mask = remove_small_noise(
            mask,
            args.min_green_area,
            args.min_green_ratio,
        )

        total_canopy_percent = (
            100.0
            * cv2.countNonZero(mask)
            / mask.size
            if mask.size > 0
            else 0.0
        )

        metrics = []

        for plant_index, centre in enumerate(
            plant_centres_local
        ):
            metric = plant_metrics(
                mask=mask,
                slot_map=slot_map,
                plant_index=plant_index,
                centre=centre,
                core_radius=core_radii[
                    plant_index
                ],
                state=plant_states[
                    plant_index
                ],
                ema_alpha=args.ema_alpha,
                visible_core_threshold=(
                    args.visible_core_threshold
                ),
                visible_area_threshold=(
                    args.visible_area_threshold
                ),
            )

            metrics.append(
                metric
            )

        visible_count = sum(
            1
            for metric in metrics
            if metric["visible"]
        )

        configured_count = len(
            plant_centres_local
        )

        display = frame.copy()

        # Growing zone.
        cv2.rectangle(
            display,
            (
                zone_x,
                zone_y,
            ),
            (
                zone_x + zone_w,
                zone_y + zone_h,
            ),
            (255, 180, 40),
            2,
        )

        # Permanent nearest-centre boundaries.
        if (
            show_zones
            and slot_boundary is not None
        ):
            boundary_points = np.where(
                slot_boundary > 0
            )

            display[
                zone_y + boundary_points[0],
                zone_x + boundary_points[1],
            ] = (
                170,
                90,
                220,
            )

        # Draw each plant identity and assigned canopy.
        for plant_index, (
            centre,
            metric,
        ) in enumerate(
            zip(
                plant_centres_local,
                metrics,
            ),
            start=1,
        ):
            local_cx, local_cy = centre

            global_cx = (
                zone_x
                + local_cx
            )

            global_cy = (
                zone_y
                + local_cy
            )

            marker_color = (
                (60, 230, 130)
                if metric["visible"]
                else (120, 120, 120)
            )

            cv2.circle(
                display,
                (
                    global_cx,
                    global_cy,
                ),
                7,
                marker_color,
                -1,
            )

            x = (
                zone_x
                + metric["x"]
            )

            y = (
                zone_y
                + metric["y"]
            )

            w = metric[
                "width_smooth"
            ]

            h = metric[
                "height_smooth"
            ]

            # Smooth dimensions are used for labels.
            smoothed_w_px = max(
                0,
                int(round(w)),
            )

            smoothed_h_px = max(
                0,
                int(round(h)),
            )

            # Current bbox location still comes from this frame.
            current_w = metric["w"]
            current_h = metric["h"]

            if (
                metric["visible"]
                and current_w > 0
                and current_h > 0
            ):
                cv2.rectangle(
                    display,
                    (x, y),
                    (
                        x + current_w,
                        y + current_h,
                    ),
                    (80, 190, 255),
                    2,
                )

            if (
                pixels_per_cm is not None
                and pixels_per_cm > 0
            ):
                width_value = (
                    smoothed_w_px
                    / pixels_per_cm
                )

                height_value = (
                    smoothed_h_px
                    / pixels_per_cm
                )

                size_label = (
                    f"{width_value:.1f}x"
                    f"{height_value:.1f}cm"
                )

            else:
                width_value = None
                height_value = None

                size_label = (
                    f"{smoothed_w_px}x"
                    f"{smoothed_h_px}px"
                )

            label = (
                f"P{plant_index} "
                f"{metric['coverage_smooth']:.1f}% "
                f"{size_label}"
            )

            cv2.putText(
                display,
                label,
                (
                    global_cx + 9,
                    max(
                        20,
                        global_cy - 9,
                    ),
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.44,
                marker_color,
                1,
                cv2.LINE_AA,
            )

        # Optional reference calibration.
        if reference_box is not None:
            rx, ry, rw, rh = (
                reference_box
            )

            cv2.rectangle(
                display,
                (rx, ry),
                (
                    rx + rw,
                    ry + rh,
                ),
                (255, 80, 220),
                3,
            )

        # Status panel.
        panel_width = min(
            920,
            frame_w,
        )

        cv2.rectangle(
            display,
            (0, 0),
            (
                panel_width,
                182,
            ),
            (18, 35, 27),
            -1,
        )

        lines = [
            "Leafy AI - Basil Slot Vision V4",
            (
                f"Registered/planted basils: "
                f"{configured_count}"
            ),
            (
                f"Currently visible green centres: "
                f"{visible_count}"
            ),
            (
                f"Whole-zone canopy coverage: "
                f"{total_canopy_percent:.2f}%"
            ),
            (
                "Size calibration: "
                + (
                    f"{pixels_per_cm:.2f} px/cm"
                    if pixels_per_cm
                    else "not set - pixel measurements still active"
                )
            ),
            (
                "Background filter: "
                + (
                    "ON"
                    if empty_background is not None
                    else "OFF"
                )
            ),
        ]

        for index, line in enumerate(
            lines
        ):
            cv2.putText(
                display,
                line,
                (
                    15,
                    28 + index * 27,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                (
                    0.64
                    if index == 0
                    else 0.50
                ),
                (240, 245, 242),
                (
                    2
                    if index == 0
                    else 1
                ),
                cv2.LINE_AA,
            )

        cv2.putText(
            display,
            (
                "R zone | S centres | K reference | "
                "G empty BG | N clear BG | V zones | "
                "M mask | P snapshot | Q quit"
            ),
            (
                15,
                173,
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.39,
            (215, 230, 222),
            1,
            cv2.LINE_AA,
        )

        if show_mask:
            mask_panel = cv2.cvtColor(
                mask,
                cv2.COLOR_GRAY2BGR,
            )

            panel_w = max(
                240,
                frame_w // 4,
            )

            panel_h = max(
                160,
                frame_h // 4,
            )

            mask_panel = cv2.resize(
                mask_panel,
                (
                    panel_w,
                    panel_h,
                ),
                interpolation=cv2.INTER_NEAREST,
            )

            px = (
                frame_w
                - panel_w
                - 10
            )

            py = (
                frame_h
                - panel_h
                - 10
            )

            if px >= 0 and py >= 0:
                display[
                    py:py + panel_h,
                    px:px + panel_w,
                ] = mask_panel

        # CSV: one row per registered plant.
        if (
            frame_number % 5 == 0
            and not paused
        ):
            with csv_path.open(
                "a",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.writer(file)

                for plant_index, metric in enumerate(
                    metrics,
                    start=1,
                ):
                    width_px = int(
                        round(
                            metric[
                                "width_smooth"
                            ]
                        )
                    )

                    height_px = int(
                        round(
                            metric[
                                "height_smooth"
                            ]
                        )
                    )

                    width_cm = (
                        width_px
                        / pixels_per_cm
                        if pixels_per_cm
                        else None
                    )

                    height_cm = (
                        height_px
                        / pixels_per_cm
                        if pixels_per_cm
                        else None
                    )

                    writer.writerow(
                        [
                            datetime.now().isoformat(
                                timespec="milliseconds"
                            ),
                            frame_number,
                            configured_count,
                            visible_count,
                            f"{total_canopy_percent:.4f}",
                            plant_index,
                            metric["visible"],
                            f"{metric['coverage_smooth']:.4f}",
                            f"{metric['core_green_ratio']:.4f}",
                            width_px,
                            height_px,
                            (
                                f"{width_cm:.3f}"
                                if width_cm is not None
                                else ""
                            ),
                            (
                                f"{height_cm:.3f}"
                                if height_cm is not None
                                else ""
                            ),
                        ]
                    )

        cv2.imshow(
            window_name,
            display,
        )

        key = cv2.waitKey(
            30 if paused else 1
        ) & 0xFF

        if key in (
            ord("q"),
            27,
        ):
            break

        elif key == ord("r"):
            selected = select_box(
                window_name,
                last_frame,
                "Select the whole basil growing zone",
            )

            if selected is not None:
                growing_zone = selected

                plant_centres_global = []
                plant_centres_local = []

                slot_map = None
                slot_boundary = None

                empty_background = None

        elif key == ord("s"):
            selected_centres = (
                select_plant_centres(
                    window_name,
                    last_frame,
                    growing_zone,
                )
            )

            if selected_centres:
                plant_centres_global = (
                    selected_centres
                )

                zone_x, zone_y, zone_w, zone_h = (
                    growing_zone
                )

                plant_centres_local = [
                    (
                        px - zone_x,
                        py - zone_y,
                    )
                    for px, py
                    in plant_centres_global
                ]

                slot_map = build_slot_map(
                    zone_w,
                    zone_h,
                    plant_centres_local,
                )

                slot_boundary = (
                    slot_boundary_mask(
                        slot_map
                    )
                )

                core_radii = (
                    nearest_neighbour_radii(
                        plant_centres_local
                    )
                )

                plant_states = [
                    {}
                    for _
                    in plant_centres_local
                ]

        elif key == ord("k"):
            selected = select_box(
                window_name,
                last_frame,
                (
                    "Select known-width reference "
                    f"({args.reference_width_cm:.1f} cm)"
                ),
            )

            if selected is not None:
                reference_box = selected

                reference_pixel_width = (
                    reference_box[2]
                )

                pixels_per_cm = (
                    reference_pixel_width
                    / args.reference_width_cm
                )

                print(
                    f"Calibration: "
                    f"{pixels_per_cm:.3f} px/cm"
                )

        elif key == ord("g"):
            bx, by, bw, bh = (
                growing_zone
            )

            empty_background = (
                last_frame[
                    by:by + bh,
                    bx:bx + bw,
                ].copy()
            )

            print(
                "Empty background captured."
            )

        elif key == ord("n"):
            empty_background = None

            print(
                "Background filter cleared."
            )

        elif key == ord("v"):
            show_zones = not show_zones

        elif key == ord("m"):
            show_mask = not show_mask

        elif key == ord("p"):
            snapshot_dir = (
                output_dir
                / "snapshots"
            )

            snapshot_dir.mkdir(
                exist_ok=True
            )

            snapshot_path = (
                snapshot_dir
                / datetime.now().strftime(
                    "basil_slots_v4_%Y%m%d_%H%M%S.jpg"
                )
            )

            cv2.imwrite(
                str(snapshot_path),
                display,
            )

            print(
                "Snapshot:",
                snapshot_path.resolve(),
            )

        elif key == ord(" "):
            paused = not paused

    capture.release()
    cv2.destroyAllWindows()

    print(
        "Measurements:",
        csv_path.resolve(),
    )


if __name__ == "__main__":
    main()
