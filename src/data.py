#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Module (数据模块)

Provides data loading utilities for trading system.
"""

import pandas as pd


def load_csv(filepath: str = "btc_eth.csv") -> pd.DataFrame:
    """
    Load OHLCV CSV and return DataFrame indexed by date.

    Args:
        filepath: Path to CSV file containing OHLCV data

    Returns:
        DataFrame with date index and OHLCV columns
    """
    try:
        return pd.read_csv(filepath, parse_dates=["date"], index_col="date")
    except FileNotFoundError:
        # Return empty DataFrame if file not found
        return pd.DataFrame()


# Make pandas available as module attribute for backward compatibility
__all__ = ["load_csv", "pd"]
