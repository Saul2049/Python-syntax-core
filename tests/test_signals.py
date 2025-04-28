import pandas as pd
import numpy as np
from src import signals


def test_moving_average():
    """测试简单移动平均线 (SMA)"""
    s = pd.Series([1, 2, 3, 4])
    assert signals.moving_average(s, 2).iloc[-1] == 3.5
    # 使用显式的kind参数
    assert signals.moving_average(s, 2, kind="sma").iloc[-1] == 3.5


def test_exponential_moving_average():
    """测试指数移动平均线 (EMA)"""
    s = pd.Series([1, 2, 3, 4])
    ema = signals.moving_average(s, 2, kind="ema")
    # EMA对最近的数据赋予更高权重
    assert ema.iloc[-1] > 3.5
    assert isinstance(ema, pd.Series)
    assert len(ema) == len(s)


def test_weighted_moving_average():
    """测试加权移动平均线 (WMA)"""
    s = pd.Series([1, 2, 3, 4])
    wma = signals.moving_average(s, 2, kind="wma")
    # 对于[3, 4]窗口，权重为[1, 2]，加权结果为(1*3+2*4)/(1+2) = 11/3
    assert abs(wma.iloc[-1] - 11 / 3) < 1e-10
    assert isinstance(wma, pd.Series)


def test_invalid_ma_type():
    """测试不支持的均线类型"""
    s = pd.Series([1, 2, 3, 4])
    try:
        signals.moving_average(s, 2, kind="invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        assert True


def test_crosses():
    fast = pd.Series([1, 2, 3, 4])
    slow = pd.Series([2, 2, 2, 2])
    assert np.array_equal(signals.bullish_cross_indices(fast, slow), np.array([2]))
    assert np.array_equal(signals.bearish_cross_indices(slow, fast), np.array([2]))


def test_cross_series():
    # 创建测试数据
    fast = pd.Series([1, 2, 3, 2], index=pd.date_range("2023-01-01", periods=4))
    slow = pd.Series([2, 2, 2, 3], index=pd.date_range("2023-01-01", periods=4))

    # 测试上穿Series
    bull_cross = signals.bullish_cross_series(fast, slow)
    assert isinstance(bull_cross, pd.Series)
    assert bull_cross.index.equals(fast.index)
    assert bull_cross.iloc[2] == True  # 第3个点上穿
    assert bull_cross.iloc[0] == False

    # 测试下穿Series
    bear_cross = signals.bearish_cross_series(fast, slow)
    assert isinstance(bear_cross, pd.Series)
    assert bear_cross.iloc[3] == True  # 第4个点下穿

    # 测试与其他条件组合
    condition = pd.Series([True, False, True, False], index=fast.index)
    combined = bull_cross & condition
    assert combined.iloc[2] == True
    assert combined.iloc[0] == False
