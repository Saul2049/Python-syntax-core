# flake8: noqa
import os
import sys

import pandas as pd
import pytest

# Add project root to path if necessary
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the module to execute grid search on import
from optimize_ma import df  # 执行后 df 在模块级


def test_grid_non_empty():
    """确保网格搜索结果非空且CSV文件生成"""
    assert not df.empty and os.path.exists("grid_results.csv")


def test_grid_structure():
    """确保结果包含必需的列和正确的排序"""
    required_columns = [
        "fast",
        "slow",
        "atr",
        "cagr",
        "sharpe",
        "mdd",
        "final",
    ]
    assert all(col in df.columns for col in required_columns)

    # 排除NaN值后验证按Sharpe比率降序排列
    df_valid = df[~df["sharpe"].isna()]
    if len(df_valid) > 1:
        assert df_valid["sharpe"].iloc[0] >= df_valid["sharpe"].iloc[-1]


@pytest.mark.skipif(not os.path.exists("grid_results.csv"), reason="CSV file not generated")
def test_csv_matches_df():
    """确保CSV文件内容与DataFrame匹配"""
    csv_df = pd.read_csv("grid_results.csv")
    assert len(csv_df) == len(df)
    assert set(csv_df.columns) == set(df.columns)
