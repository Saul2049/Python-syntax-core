"""
交易所客户端模块 - 向后兼容导入
(Exchange Client Module - Backward Compatible Imports)

⚠️ 已重构提示 (Refactoring Notice):
此模块已被移动到 src.brokers.exchange.client
推荐直接使用新的导入路径：

from src.brokers.exchange import ExchangeClient

为了保持向后兼容性，此文件重新导出了重构后的功能。
"""

from src.brokers.exchange import ExchangeClient

__all__ = ["ExchangeClient"]
