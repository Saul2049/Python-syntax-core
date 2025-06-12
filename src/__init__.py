# src package


# 延迟导入，避免循环导入问题
def __getattr__(name):
    """延迟加载模块属性"""
    import importlib

    # 子包映射
    subpackages = {
        "core",
        "brokers",
        "monitoring",
        "strategies",
        "indicators",
        "data",
        "config",
        "analysis",
        "tools",
        "ws",
        "notifications",
    }

    # 模块映射
    modules = {
        "backtest",
        "broker",
        "metrics",
        "signals",
        "telegram",
        "notify",
        "utils",
        "network",
        "trading_loop",
        "improved_strategy",
        "data_processor",
        "exchange_client",
        "binance_client",
        "portfolio_backtest",
    }

    if name in subpackages or name in modules:
        try:
            module = importlib.import_module(f".{name}", package=__name__)
            globals()[name] = module
            return module
        except ImportError:
            pass

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# 为向后兼容提供快捷导入
try:
    from .core.async_trading_engine import AsyncTradingEngine
    from .core.trading_engine import TradingEngine
except ImportError:
    pass

try:
    from .brokers.broker import Broker
    from .brokers.live_broker_async import LiveBrokerAsync
except ImportError:
    pass

try:
    from .monitoring.metrics_collector import get_metrics_collector, init_monitoring
except ImportError:
    pass
