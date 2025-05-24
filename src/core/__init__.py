"""
核心模块 (Core Module)

提供交易系统的核心功能：
- 风险管理
- 仓位管理
- 投资组合管理
- 价格数据获取
- 信号处理
"""

from .position_management import PositionManager
from .price_fetcher import (
    calculate_atr,
    fetch_price_data,
    generate_fallback_data,
)
from .risk_management import (
    compute_atr,
    compute_position_size,
    compute_stop_price,
    compute_trailing_stop,
    trailing_stop,
    update_trailing_stop_atr,
)
from .signal_processor import (
    filter_signals,
    get_trading_signals,
    validate_signal,
)

# 暂时注释以避免循环导入
# from .trading_engine import TradingEngine, trading_loop

__all__ = [
    # 风险管理
    "compute_atr",
    "compute_position_size",
    "compute_stop_price",
    "compute_trailing_stop",
    "trailing_stop",
    "update_trailing_stop_atr",
    # 仓位管理
    "PositionManager",
    # 交易引擎 - 暂时注释
    # 'TradingEngine',
    # 'trading_loop',
    # 价格数据
    "fetch_price_data",
    "generate_fallback_data",
    "calculate_atr",
    # 信号处理
    "get_trading_signals",
    "validate_signal",
    "filter_signals",
]
