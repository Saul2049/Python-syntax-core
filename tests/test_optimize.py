# flake8: noqa
import os
import sys

import pandas as pd
import pytest

# Add project root to path if necessary
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the optimization module
from scripts.utilities.optimize_ma import run_optimization


@pytest.fixture(scope="module")
def optimization_results():
    """运行优化并返回结果DataFrame"""
    return run_optimization()


def test_grid_non_empty(optimization_results):
    """确保网格搜索结果非空且CSV文件生成"""
    assert not optimization_results.empty and os.path.exists("grid_results.csv")


def test_grid_structure(optimization_results):
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
    assert all(col in optimization_results.columns for col in required_columns)

    # 排除NaN值后验证按Sharpe比率降序排列
    df_valid = optimization_results[~optimization_results["sharpe"].isna()]
    if len(df_valid) > 1:
        assert df_valid["sharpe"].iloc[0] >= df_valid["sharpe"].iloc[-1]


@pytest.mark.skipif(not os.path.exists("grid_results.csv"), reason="CSV file not generated")
def test_csv_matches_df(optimization_results):
    """确保CSV文件内容与DataFrame匹配"""
    csv_df = pd.read_csv("grid_results.csv")
    assert len(csv_df) == len(optimization_results)
    assert set(csv_df.columns) == set(optimization_results.columns)
