import os
import sys

import numpy as np
import pandas as pd
import pytest

# Add the project root to path if necessary
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from src import metrics


def test_metrics_outputs():
    s = pd.Series(
        [100, 120, 110], index=pd.date_range("2024-01-01", periods=3, freq="D")
    )
    assert metrics.max_drawdown(s) < 0  # 回撤必为负
    assert metrics.cagr(s) > -1  # CAGR 合理


def test_max_drawdown():
    # Test with known drawdown
    s = pd.Series([100, 90, 80, 85, 95])
    expected_dd = -0.20  # Max drawdown from 100 to 80
    assert abs(metrics.max_drawdown(s) - expected_dd) < 1e-10

    # Test with always increasing series
    s = pd.Series([100, 110, 120, 130])
    assert metrics.max_drawdown(s) == 0


def test_cagr():
    # Series over one year with 10% growth
    dates = pd.date_range("2023-01-01", "2024-01-01")
    s = pd.Series([100, 110], index=[dates[0], dates[-1]])
    assert (
        abs(metrics.cagr(s) - 0.10) < 1e-4
    )  # Use looser tolerance for date precision

    # Test with same start/end value
    s = pd.Series(
        [100, 90, 100],
        index=pd.date_range("2023-01-01", periods=3, freq="180D"),
    )
    assert abs(metrics.cagr(s)) < 1e-4  # Use looser tolerance


def test_sharpe_ratio():
    # Constant series should have zero Sharpe ratio (no volatility)
    s = pd.Series([100, 100, 100, 100])
    assert np.isnan(metrics.sharpe_ratio(s))

    # Simple up-down series
    s = pd.Series([100, 110, 105, 115])
    # Check that Sharpe is positive for uptrending series
    assert metrics.sharpe_ratio(s) > 0
