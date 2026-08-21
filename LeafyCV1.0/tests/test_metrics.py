import numpy as np
from leafycv.metrics import crowding_index, growth_change


def test_growth_change():
    assert growth_change(55.0, 50.0) == 10.0
    assert growth_change(50.0, None) is None


def test_crowding_dense_mask():
    mask = np.full((120, 180), 255, dtype=np.uint8)
    assert crowding_index(mask) == 100.0
