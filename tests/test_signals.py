import pandas as pd
import numpy as np
from src import signals

def test_moving_average():
    s = pd.Series([1, 2, 3, 4])
    assert signals.moving_average(s, 2).iloc[-1] == 3.5

def test_crosses():
    fast = pd.Series([1, 2, 3, 4])
    slow = pd.Series([2, 2, 2, 2])
    assert np.array_equal(signals.bullish_cross_indices(fast, slow), np.array([2]))
    assert np.array_equal(signals.bearish_cross_indices(slow, fast), np.array([2])) 