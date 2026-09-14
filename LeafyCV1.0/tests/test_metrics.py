import numpy as np

from leafycv.metrics import colour_percentages, crowding_index, growth_change, percentage


def test_percentage_half_mask():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[:, :5] = 255
    assert percentage(mask) == 50.0


def test_growth_change():
    assert growth_change(55.0, 50.0) == 10.0
    assert growth_change(50.0, None) is None


def test_crowding_dense_mask():
    mask = np.full((120, 180), 255, dtype=np.uint8)
    assert crowding_index(mask) == 100.0


def test_colour_percentages_use_canopy_denominator():
    canopy = np.zeros((10, 10), dtype=np.uint8)
    canopy[:, :5] = 255  # 50 canopy pixels
    green = np.zeros_like(canopy)
    green[:, :4] = 255  # 40 / 50 canopy pixels
    yellow = np.zeros_like(canopy)
    yellow[:, 4:5] = 255  # 10 / 50 canopy pixels
    brown = np.zeros_like(canopy)
    values = colour_percentages(
        {"combined": canopy, "green": green, "yellow": yellow, "brown": brown}
    )
    assert values == (80.0, 20.0, 0.0)
