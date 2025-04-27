# test_crossovers.py
import numpy as np
import pandas as pd
from crossovers import bullish_cross_indices

def test_simple():
    # fast crosses slow upwards at index 2 (3 ≥ 2)
    fast = pd.Series([1, 2, 3, 4])
    slow = pd.Series([2, 2, 2, 2])
    expected = np.array([2])
    result = bullish_cross_indices(fast, slow)
    assert np.array_equal(result, expected) 