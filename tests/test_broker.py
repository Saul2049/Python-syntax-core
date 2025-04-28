from math import isfinite

import numpy as np
import pandas as pd
import pytest

from src import broker


def test_position_size():
    """测试常规仓位计算"""
    assert (
        broker.compute_position_size(100_000, 500) == 4
    )  # 2% risk: 100000 * 0.02 / 500 = 4


def test_position_size_minimum():
    """测试最小手数保护"""
    # 大ATR导致计算值小于1时应该返回1
    assert (
        broker.compute_position_size(100, 500) == 1
    )  # 理论值是0.004，应返回1
    assert (
        broker.compute_position_size(1000, 5000) == 1
    )  # 理论值是0.004，应返回1


def test_position_size_zero_atr():
    """测试ATR为零或负数时的处理"""
    assert broker.compute_position_size(100_000, 0) == 1  # ATR为零应该返回1
    assert broker.compute_position_size(100_000, -10) == 1  # 负ATR应该返回1


def test_stop_price():
    """测试止损价格计算"""
    assert (
        broker.compute_stop_price(100, 5) == 95
    )  # 入场100，ATR为5，止损价应为95


def test_stop_price_multiplier():
    """测试不同乘数的止损价格"""
    assert (
        broker.compute_stop_price(100, 5, multiplier=2.0) == 90
    )  # 2倍ATR止损


def test_stop_price_zero_atr():
    """测试ATR为零或负数的止损价格"""
    assert (
        broker.compute_stop_price(100, 0) == 100
    )  # ATR为零，止损应等于入场价
    assert broker.compute_stop_price(100, -5) == 100  # 负ATR被处理为0


def test_trailing_stop_below_breakeven():
    entry = 100.0
    current_price = 105.0
    initial_stop = 90.0
    breakeven_r = 2.0
    trail_r = 3.0

    # 盈利0.5R (10/20)，应保持初始止损
    stop = broker.compute_trailing_stop(
        entry, current_price, initial_stop, breakeven_r, trail_r
    )
    assert stop == initial_stop


def test_trailing_stop_at_breakeven():
    entry = 100.0
    current_price = 120.0
    initial_stop = 90.0
    breakeven_r = 1.0
    trail_r = 2.0

    # 盈利1.0R (20/20)，应移至保本位
    stop = broker.compute_trailing_stop(
        entry, current_price, initial_stop, breakeven_r, trail_r
    )
    assert stop == entry


def test_trailing_stop_beyond_trail():
    entry = 100.0
    current_price = 150.0
    initial_stop = 90.0
    breakeven_r = 1.0
    trail_r = 2.0

    # 盈利2.5R (50/20)，应使用跟踪止损
    stop = broker.compute_trailing_stop(
        entry, current_price, initial_stop, breakeven_r, trail_r
    )
    assert stop > initial_stop
    assert stop < current_price

    # 确认使用基于初始风险的百分比跟踪
    expected_stop = current_price - (entry - initial_stop) * 0.5
    assert stop == expected_stop


def test_trailing_stop_with_atr():
    entry = 100.0
    current_price = 150.0
    initial_stop = 90.0
    breakeven_r = 1.0
    trail_r = 2.0
    atr = 5.0

    # 使用ATR作为跟踪距离
    stop = broker.compute_trailing_stop(
        entry, current_price, initial_stop, breakeven_r, trail_r, atr
    )
    assert stop == current_price - atr


def test_trailing_stop_negative_gain():
    entry = 100.0
    current_price = 95.0
    initial_stop = 90.0

    # 价格低于入场价，应保持初始止损
    stop = broker.compute_trailing_stop(entry, current_price, initial_stop)
    assert stop == initial_stop


def test_trailing_stop_invalid_risk():
    entry = 100.0
    current_price = 110.0
    initial_stop = 100.0  # 无风险(止损与入场价相同)

    # 防御性处理，应返回初始止损
    stop = broker.compute_trailing_stop(entry, current_price, initial_stop)
    assert stop == initial_stop


def test_backtest_with_trailing_stop():
    # 创建简单的价格序列进行回测
    price = pd.Series(
        [
            100.0,
            101.0,
            102.0,
            103.0,
            104.0,
            105.0,
            110.0,
            115.0,
            120.0,
            125.0,
            130.0,
            128.0,
            126.0,
            124.0,
        ]
    )

    # 不使用移动止损的回测
    equity_no_trail = broker.backtest_single(
        price, fast_win=2, slow_win=4, atr_win=3, use_trailing_stop=False
    )

    # 使用移动止损的回测
    equity_with_trail = broker.backtest_single(
        price,
        fast_win=2,
        slow_win=4,
        atr_win=3,
        use_trailing_stop=True,
        breakeven_r=1.0,
        trail_r=2.0,
    )

    # 此测试主要验证函数运行而不是具体结果
    # 在完整回测中，移动止损可能会产生不同的结果
    assert len(equity_no_trail) == len(price)
    assert len(equity_with_trail) == len(price)
