from src import broker

def test_position_size():
    """测试常规仓位计算"""
    assert broker.compute_position_size(100_000, 500) == 4  # 2% risk: 100000 * 0.02 / 500 = 4
    
def test_position_size_minimum():
    """测试最小手数保护"""
    # 大ATR导致计算值小于1时应该返回1
    assert broker.compute_position_size(100, 500) == 1  # 理论值是0.004，应返回1
    assert broker.compute_position_size(1000, 5000) == 1  # 理论值是0.004，应返回1
    
def test_position_size_zero_atr():
    """测试ATR为零或负数时的处理"""
    assert broker.compute_position_size(100_000, 0) == 1  # ATR为零应该返回1
    assert broker.compute_position_size(100_000, -10) == 1  # 负ATR应该返回1

def test_stop_price():
    """测试止损价格计算"""
    assert broker.compute_stop_price(100, 5) == 95  # 入场100，ATR为5，止损价应为95
    
def test_stop_price_multiplier():
    """测试不同乘数的止损价格"""
    assert broker.compute_stop_price(100, 5, multiplier=2.0) == 90  # 2倍ATR止损
    
def test_stop_price_zero_atr():
    """测试ATR为零或负数的止损价格"""
    assert broker.compute_stop_price(100, 0) == 100  # ATR为零，止损应等于入场价
    assert broker.compute_stop_price(100, -5) == 100  # 负ATR被处理为0 