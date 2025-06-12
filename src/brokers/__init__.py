"""
经纪商模块 (Brokers Module)

提供不同经纪商的接口实现
"""

from .binance import BinanceClient
from .broker import Broker
from .exchange import ExchangeClient

# 导入异步broker
try:
    from .live_broker_async import LiveBrokerAsync
except ImportError:
    LiveBrokerAsync = None

# 导入子模块
try:
    from . import simulator
except ImportError:
    simulator = None

# 为向后兼容添加别名
try:
    # 导入broker模块而不是Broker类
    from . import broker  # 用于 src.brokers.broker 访问
except ImportError:
    broker = None

try:
    from . import live_broker_async
except ImportError:
    live_broker_async = None

# ---------------------------------------------------------------------------
# 兼容旧测试所需占位类
# ---------------------------------------------------------------------------


class AsyncBroker(Broker):
    """Legacy alias expected by archived tests.

    旧版测试套件通过 ``patch('src.brokers.AsyncBroker', ...)`` 注入 Mock。
    实际生产代码已迁移至 ``LiveBrokerAsync``，因此此处提供一个轻量包装以
    保持向后兼容，不执行任何真实 I/O。
    """

    async def init_session(self) -> None:  # noqa: D401
        pass

    async def close_session(self) -> None:  # noqa: D401
        pass


__all__ = [
    "Broker",
    "BinanceClient",
    "ExchangeClient",
    "LiveBrokerAsync",
    "broker",
    "live_broker_async",
    "simulator",
    "AsyncBroker",
]
