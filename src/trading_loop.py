"""
交易循环模块 - 向后兼容导入
(Trading Loop Module - Backward Compatible Imports)

⚠️ 已重构提示 (Refactoring Notice):
此模块已被重构并拆分为多个专门模块以提高代码质量。
推荐直接使用新的模块结构：

- src.core.trading_engine.TradingEngine - 核心交易引擎
- src.core.price_fetcher - 价格数据获取
- src.core.signal_processor - 信号处理

为了保持向后兼容性，此文件重新导出了重构后的功能。
"""

import os

# 向后兼容导入 - 价格数据相关
from src.core.price_fetcher import (
    calculate_atr,
    fetch_price_data,
)

# 向后兼容导入 - 信号处理相关
from src.core.signal_processor import get_trading_signals

# 向后兼容导入 - 交易引擎
from src.core.trading_engine import TradingEngine, trading_loop

# 保留原有的导入结构以维持兼容性
__all__ = [
    "fetch_price_data",
    "calculate_atr",
    "get_trading_signals",
    "trading_loop",
    "TradingEngine",
]

# 向后兼容的主函数
if __name__ == "__main__":
    # 使用环境变量检查 (Use environment variables)
    if "TG_TOKEN" not in os.environ:
        print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")

    if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
        print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")

    # 启动交易循环 (Start trading loop)
    trading_loop()
