#!/usr/bin/env python3
"""Deterministic visual-crowding measurements for fixed NFT plant slots.

The segmentation mask says which pixels look like basil tissue. The fixed slot
map says which registered planting position is nearest to each pixel. This
module DOES NOT try to infer biological leaf ownership after canopies overlap.
Instead, it reports objective visual contact/encroachment between neighbouring
registered slots.
"""
from __future__ import annotations

import cv2
import numpy as np


def adjacent_slot_pairs(slot_map: np.ndarray) -> list[tuple[int, int]]:
    """Return unique slot-label pairs that share a Voronoi boundary."""
    pairs: set[tuple[int, int]] = set()

    if slot_map.ndim != 2 or slot_map.size == 0:
        return []

    # Horizontal neighbours.
    left = slot_map[:, :-1]
    right = slot_map[:, 1:]
    changed = left != right
    if np.any(changed):
        for a, b in zip(left[changed].tolist(), right[changed].tolist()):
            ia, ib = int(a), int(b)
            if ia != ib:
                pairs.add((min(ia, ib), max(ia, ib)))

    # Vertical neighbours.
    top = slot_map[:-1, :]
    bottom = slot_map[1:, :]
    changed = top != bottom
    if np.any(changed):
        for a, b in zip(top[changed].tolist(), bottom[changed].tolist()):
            ia, ib = int(a), int(b)
            if ia != ib:
                pairs.add((min(ia, ib), max(ia, ib)))

    return sorted(pairs)


def compute_crowding(
    *,
    mask: np.ndarray,
    slot_map: np.ndarray,
    plant_count: int,
    gap_px: int = 3,
    min_contact_pixels: int = 25,
) -> dict:
    """Measure visual canopy contact between neighbouring registered slots.

    `gap_px` is a small tolerance for segmentation gaps / leaf movement. Each
    slot's detected tissue is dilated by this radius before overlap testing.
    `min_contact_pixels` suppresses one-pixel/noise contacts.

    The returned `crowding_index` is simply:
        touching neighbouring slot pairs / all neighbouring slot pairs

    It is a visual measurement, NOT an agronomic decision threshold.
    """
    if mask.ndim != 2 or slot_map.ndim != 2 or mask.shape != slot_map.shape:
        raise ValueError('mask and slot_map must be same-size 2D arrays')

    plant_count = max(0, int(plant_count))
    gap_px = max(0, int(gap_px))
    min_contact_pixels = max(1, int(min_contact_pixels))

    neighbours = [
        pair for pair in adjacent_slot_pairs(slot_map)
        if pair[0] < plant_count and pair[1] < plant_count
    ]

    tissue = mask > 0
    if gap_px > 0:
        kernel_size = gap_px * 2 + 1
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )
    else:
        kernel = None

    # Build once per plant, rather than once per pair.
    expanded: list[np.ndarray] = []
    for plant_index in range(plant_count):
        plant = np.where(
            tissue & (slot_map == plant_index), 255, 0
        ).astype(np.uint8)
        if kernel is not None:
            plant = cv2.dilate(plant, kernel, iterations=1)
        expanded.append(plant)

    touching_pairs: list[dict] = []
    per_plant: dict[str, list[str]] = {
        f'P{i + 1}': [] for i in range(plant_count)
    }
    per_plant_all_neighbours: dict[str, list[str]] = {
        f'P{i + 1}': [] for i in range(plant_count)
    }

    for a, b in neighbours:
        pa, pb = f'P{a + 1}', f'P{b + 1}'
        per_plant_all_neighbours[pa].append(pb)
        per_plant_all_neighbours[pb].append(pa)
        overlap = cv2.bitwise_and(expanded[a], expanded[b])
        contact_pixels = int(cv2.countNonZero(overlap))
        if contact_pixels >= min_contact_pixels:
            touching_pairs.append(
                {
                    'plant_a': pa,
                    'plant_b': pb,
                    'proximity_overlap_pixels': contact_pixels,
                }
            )
            per_plant[pa].append(pb)
            per_plant[pb].append(pa)

    neighbour_count = len(neighbours)
    touching_count = len(touching_pairs)
    crowding_index = touching_count / neighbour_count if neighbour_count else 0.0

    per_plant_crowding_percent: dict[str, float] = {}
    per_plant_neighbor_count: dict[str, int] = {}
    for plant_id in per_plant:
        total = len(per_plant_all_neighbours[plant_id])
        touching = len(per_plant[plant_id])
        per_plant_neighbor_count[plant_id] = total
        per_plant_crowding_percent[plant_id] = (
            100.0 * touching / total if total else 0.0
        )

    return {
        'method': 'fixed_slot_boundary_proximity',
        'gap_px': gap_px,
        'min_contact_pixels': min_contact_pixels,
        'neighbor_pair_count': neighbour_count,
        'touching_pair_count': touching_count,
        'crowding_index': float(crowding_index),
        'crowding_percent': float(crowding_index * 100.0),
        'touching_pairs': touching_pairs,
        'per_plant_touching_neighbors': per_plant,
        'per_plant_all_neighbors': per_plant_all_neighbours,
        'per_plant_neighbor_count': per_plant_neighbor_count,
        'per_plant_crowding_percent': per_plant_crowding_percent,
    }
