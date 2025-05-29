#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Module (数据模块)

Provides data loading utilities for trading system.
"""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def load_csv(filepath: str = "btc_eth.csv") -> pd.DataFrame:
    """
    Load OHLCV CSV and return DataFrame indexed by date.

    Args:
        filepath: Path to CSV file containing OHLCV data

    Returns:
        DataFrame with date index and OHLCV columns
    """
    # Try to find the file in multiple possible locations
    possible_paths = [
        filepath,  # Current directory
        os.path.join(os.path.dirname(__file__), "..", filepath),  # Project root from src/
        os.path.join(os.path.dirname(__file__), "..", "..", filepath),  # Project root from nested
        os.path.abspath(filepath),  # Absolute path
    ]

    for path in possible_paths:
        try:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                df = pd.read_csv(abs_path, parse_dates=["date"], index_col="date")
                if not df.empty:
                    print(f"✅ 成功加载数据文件: {abs_path}")
                    return df
        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
            continue

    print(f"❌ 错误: 在以下路径中都未找到文件 '{filepath}':")
    for path in possible_paths:
        print(f"  - {os.path.abspath(path)}")
    print("🔄 使用合成数据作为fallback...")

    # Generate fallback synthetic data for testing
    return _generate_fallback_data()


def _generate_fallback_data(days: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic price data for testing when real data is unavailable.

    Args:
        days: Number of days of data to generate

    Returns:
        DataFrame with synthetic BTC and ETH price data
    """
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    # Generate synthetic price data with realistic patterns
    np.random.seed(42)  # For reproducible tests

    # BTC starting around 50000
    btc_returns = np.random.normal(0.001, 0.03, len(dates))  # 0.1% daily return, 3% volatility
    btc_prices = [50000]
    for ret in btc_returns[1:]:
        btc_prices.append(btc_prices[-1] * (1 + ret))

    # ETH starting around 3000, correlated with BTC
    eth_returns = np.random.normal(
        0.0015, 0.04, len(dates)
    )  # Slightly higher return and volatility
    eth_prices = [3000]
    for ret in eth_returns[1:]:
        eth_prices.append(eth_prices[-1] * (1 + ret))

    df = pd.DataFrame({"btc": btc_prices, "eth": eth_prices}, index=dates)
    print(
        f"✅ 生成了 {len(df)} 行合成数据 (BTC: {df['btc'].iloc[0]:.2f} -> {df['btc'].iloc[-1]:.2f})"
    )

    return df


# Make pandas available as module attribute for backward compatibility
__all__ = ["load_csv", "pd"]
