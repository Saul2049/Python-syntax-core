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

def test_cross_series():
    # 创建测试数据
    fast = pd.Series([1, 2, 3, 2], index=pd.date_range('2023-01-01', periods=4))
    slow = pd.Series([2, 2, 2, 3], index=pd.date_range('2023-01-01', periods=4))
    
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