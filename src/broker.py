"""
经纪商模块 - 向后兼容导入
(Broker Module - Backward Compatible Imports)

为了保持向后兼容性，此文件重新导出了重构后的功能。
推荐直接使用新的模块结构。
"""

# 向后兼容导入
try:
    from .brokers.broker import Broker
except ImportError:
    try:
        from src.brokers.broker import Broker
    except ImportError:
        Broker = None

try:
    from .core.risk_management import (
        compute_atr,
        compute_position_size,
        compute_stop_price,
        compute_trailing_stop,
        trailing_stop,
        update_trailing_stop_atr,
    )
except ImportError:
    try:
        from src.core.risk_management import (
            compute_atr,
            compute_position_size,
            compute_stop_price,
            compute_trailing_stop,
            trailing_stop,
            update_trailing_stop_atr,
        )
    except ImportError:
        # 提供默认的空实现
        compute_atr = compute_position_size = compute_stop_price = None
        compute_trailing_stop = trailing_stop = update_trailing_stop_atr = None

try:
    from .strategies.backtest import backtest_portfolio, backtest_single
except ImportError:
    try:
        from src.strategies.backtest import backtest_portfolio, backtest_single
    except ImportError:
        backtest_portfolio = backtest_single = None

# 保留原有的导入结构以维持兼容性
__all__ = [
    "Broker",
    "compute_atr",
    "compute_position_size",
    "compute_stop_price",
    "compute_trailing_stop",
    "trailing_stop",
    "update_trailing_stop_atr",
    "backtest_single",
    "backtest_portfolio",
]
