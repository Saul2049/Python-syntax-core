import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from data import load_csv  # 导入根目录的data模块
from src import broker


def test_backtest_snapshot_btc():
    """
    回测快照测试：确保回测结果的稳定性

    这个测试会验证回测结果的最终值是否符合预期。任何算法变更导致
    回测结果变化时，测试将失败并提醒开发者审查变更影响。
    """
    # 加载测试数据
    df = load_csv()

    # 执行回测
    result = broker.backtest_single(
        df["btc"],
        fast_win=7,
        slow_win=20,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )

    # 验证最终权益值
    # 记录当前的最终权益值
    final_equity = result.iloc[-1]

    # 储存预期值 - 这个值是基于当前实现生成的
    # 在修改算法时，如果这个值变化，测试将失败
    expected_equity = 150781.99  # 实际运行值

    # 允许0.01%的误差
    assert (
        abs(final_equity - expected_equity) / expected_equity < 0.0001
    ), f"回测结果变化: 预期 {expected_equity:.2f}, 实际 {final_equity:.2f}"

    # 打印当前值，以便需要更新期望值时参考
    print(f"当前回测最终权益: {final_equity:.2f}")


def test_backtest_snapshot_eth():
    """以太坊回测快照测试"""
    # 加载测试数据
    df = load_csv()

    # 执行回测
    result = broker.backtest_single(
        df["eth"],
        fast_win=7,
        slow_win=20,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )

    # 验证最终权益值
    final_equity = result.iloc[-1]
    expected_equity = 131810.99  # 实际运行值

    # 允许0.01%的误差
    assert (
        abs(final_equity - expected_equity) / expected_equity < 0.0001
    ), f"回测结果变化: 预期 {expected_equity:.2f}, 实际 {final_equity:.2f}"


# 参数化测试 - 测试不同参数组合的回测结果
@pytest.mark.parametrize(
    "asset,fast_win,slow_win,atr_win,use_trailing_stop,expected_equity",
    [
        # 基本配置
        ("btc", 7, 20, 14, True, 150781.99),
        ("eth", 7, 20, 14, True, 131810.99),
        # 不同的快线周期
        ("btc", 5, 20, 14, True, 141158.63),
        # 不同的慢线周期
        ("btc", 7, 25, 14, True, 118135.82),
        # 不使用移动止损
        ("btc", 7, 20, 14, False, 386979.84),
    ],
)
def test_backtest_different_params(
    asset, fast_win, slow_win, atr_win, use_trailing_stop, expected_equity
):
    """表格测试：验证不同参数组合下的回测结果"""
    # 加载测试数据
    df = load_csv()

    # 执行回测
    result = broker.backtest_single(
        df[asset],
        fast_win=fast_win,
        slow_win=slow_win,
        atr_win=atr_win,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=use_trailing_stop,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )

    # 验证最终权益值
    final_equity = result.iloc[-1]

    # 为参数化测试允许更大的误差容忍度（0.5%）
    # 因为我们只是估算不同参数下的预期值
    assert abs(final_equity - expected_equity) / expected_equity < 0.005, (
        f"回测结果变化 ({asset}, fast={fast_win}, slow={slow_win}, trailing={use_trailing_stop}): "
        f"预期 {expected_equity:.2f}, 实际 {final_equity:.2f}"
    )


if __name__ == "__main__":
    """用于生成期望值的辅助功能"""

    print("生成基本回测期望值...")
    df = load_csv()

    # 基本回测
    btc_result = broker.backtest_single(
        df["btc"],
        fast_win=7,
        slow_win=20,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )
    eth_result = broker.backtest_single(
        df["eth"],
        fast_win=7,
        slow_win=20,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )

    print(f"BTC回测 (标准参数): {btc_result.iloc[-1]:.2f}")
    print(f"ETH回测 (标准参数): {eth_result.iloc[-1]:.2f}")

    # 生成参数化测试的期望值
    print("\n生成参数化测试的期望值...")

    # 不同的快线周期
    btc_fast5 = broker.backtest_single(
        df["btc"],
        fast_win=5,
        slow_win=20,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )
    print(f"BTC回测 (fast_win=5): {btc_fast5.iloc[-1]:.2f}")

    # 不同的慢线周期
    btc_slow25 = broker.backtest_single(
        df["btc"],
        fast_win=7,
        slow_win=25,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )
    print(f"BTC回测 (slow_win=25): {btc_slow25.iloc[-1]:.2f}")

    # 不使用移动止损
    btc_no_trail = broker.backtest_single(
        df["btc"],
        fast_win=7,
        slow_win=20,
        atr_win=14,
        risk_frac=0.02,
        init_equity=100_000.0,
        use_trailing_stop=False,
        breakeven_r=1.0,
        trail_r=2.0,
        verbose=False,
    )
    print(f"BTC回测 (无移动止损): {btc_no_trail.iloc[-1]:.2f}")
