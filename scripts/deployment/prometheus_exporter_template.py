#!/usr/bin/env python3
"""
交易系统Prometheus业务指标导出器
用于监控实盘关键指标：信号延迟、下单延迟、滑点、异常等
"""
import time
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from contextlib import contextmanager
import logging

# 业务指标定义
SIGNAL_LATENCY = Histogram(
    "signal_latency_seconds",
    "Signal calculation latency",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ORDER_LATENCY = Histogram(
    "order_latency_seconds", "Order execution latency", buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

SLIPPAGE_PERCENTAGE = Histogram(
    "slippage_percentage",
    "Price slippage percentage",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)

WEBSOCKET_HEARTBEAT_AGE = Gauge("ws_heartbeat_age_seconds", "WebSocket heartbeat age")

EXCEPTION_TOTAL = Counter(
    "exception_total", "Total exceptions by module", ["module", "exception_type"]
)

ACCOUNT_BALANCE = Gauge("account_balance_usd", "Account balance in USD")

DRAWDOWN_PERCENTAGE = Gauge("drawdown_percentage", "Current drawdown from peak")


# 导出器类
class TradingMetricsExporter:
    """交易系统指标导出器"""

    def __init__(self, port=8000):
        self.port = port
        self.logger = logging.getLogger(__name__)

    def start_server(self):
        """启动Prometheus指标服务器"""
        start_http_server(self.port)
        self.logger.info(f"Prometheus metrics server started on port {self.port}")

    @contextmanager
    def measure_signal_latency(self):
        """测量信号计算延迟"""
        start_time = time.time()
        try:
            yield
        finally:
            SIGNAL_LATENCY.observe(time.time() - start_time)

    @contextmanager
    def measure_order_latency(self):
        """测量下单延迟"""
        start_time = time.time()
        try:
            yield
        finally:
            ORDER_LATENCY.observe(time.time() - start_time)

    def record_slippage(self, expected_price: float, actual_price: float):
        """记录滑点"""
        slippage = abs(actual_price - expected_price) / expected_price * 100
        SLIPPAGE_PERCENTAGE.observe(slippage)

    def update_heartbeat_age(self, last_heartbeat_timestamp: float):
        """更新WebSocket心跳年龄"""
        age = time.time() - last_heartbeat_timestamp
        WEBSOCKET_HEARTBEAT_AGE.set(age)

    def record_exception(self, module: str, exception_type: str):
        """记录异常"""
        EXCEPTION_TOTAL.labels(module=module, exception_type=exception_type).inc()

    def update_account_balance(self, balance_usd: float):
        """更新账户余额"""
        ACCOUNT_BALANCE.set(balance_usd)

    def update_drawdown(self, current_balance: float, peak_balance: float):
        """更新回撤"""
        drawdown = (peak_balance - current_balance) / peak_balance * 100
        DRAWDOWN_PERCENTAGE.set(max(0, drawdown))


# 使用示例
if __name__ == "__main__":
    # 初始化导出器
    exporter = TradingMetricsExporter(port=8000)
    exporter.start_server()

    # 模拟业务指标
    import random

    while True:
        # 模拟信号计算
        with exporter.measure_signal_latency():
            time.sleep(random.uniform(0.1, 0.8))

        # 模拟下单
        with exporter.measure_order_latency():
            time.sleep(random.uniform(0.2, 1.5))

        # 模拟滑点
        expected = 50000.0
        actual = expected + random.uniform(-100, 100)
        exporter.record_slippage(expected, actual)

        # 模拟账户更新
        balance = random.uniform(9500, 10500)
        exporter.update_account_balance(balance)
        exporter.update_drawdown(balance, 10000)

        time.sleep(5)  # 每5秒更新一次
