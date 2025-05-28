#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易系统监控指标收集器
集成业务指标到现有的交易系统组件中
"""

import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Generator, Optional

from .prometheus_exporter import PrometheusExporter


def _setup_prometheus_imports():
    """设置Prometheus导入，提供回退机制以降低复杂度"""
    try:
        from prometheus_client import (
            CollectorRegistry,
            Counter,
            Gauge,
            Histogram,
            start_http_server,
        )

        return CollectorRegistry, Counter, Gauge, Histogram, start_http_server
    except ImportError:
        return _create_fallback_prometheus_classes()


def _create_fallback_prometheus_classes():
    """创建Prometheus的回退类实现"""

    class Counter:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def labels(self, *args: Any, **kwargs: Any) -> "Counter":
            return self

        def inc(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Histogram:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def observe(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Gauge:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def set(self, *args: Any, **kwargs: Any) -> None:
            pass

    def start_http_server(*args: Any, **kwargs: Any) -> None:
        pass

    return None, Counter, Gauge, Histogram, start_http_server


# 设置Prometheus组件
CollectorRegistry, Counter, Gauge, Histogram, start_http_server = _setup_prometheus_imports()


@dataclass
class MetricsConfig:
    """
    监控配置类 (Monitoring configuration class)

    Attributes:
        enabled: 是否启用监控 (Whether monitoring is enabled)
        port: Prometheus服务端口 (Prometheus server port)
        include_system_metrics: 是否包含系统指标 (Whether to include system metrics)
    """

    enabled: bool = True  # 监控启用状态
    port: int = 8000  # Prometheus端口
    include_system_metrics: bool = True  # 系统指标开关


class TradingMetricsCollector:
    """交易系统指标收集器"""

    def __init__(self, config: Optional[MetricsConfig] = None) -> None:
        """
        初始化指标收集器

        Args:
            config: 监控配置对象 (Monitoring configuration object)
        """
        # 向后兼容：如果config不是MetricsConfig类型，创建默认配置
        if config is not None and not isinstance(config, MetricsConfig):
            self.exporter: Optional[PrometheusExporter] = config  # 保存传入的exporter
            config = MetricsConfig()
        else:
            self.exporter: Optional[PrometheusExporter] = None

        self.config: MetricsConfig = config or MetricsConfig()
        self.logger: logging.Logger = logging.getLogger(__name__)
        self._server_started: bool = False

        if not self.config.enabled:
            self.logger.info("监控已禁用")
            return

        self._init_metrics()

    def _init_metrics(self) -> None:
        """初始化Prometheus指标"""
        # 清除现有注册表以避免重复注册错误
        from prometheus_client import REGISTRY

        try:
            # 清除所有已注册的指标（除了默认的Python进程指标）
            collectors_to_remove: list = []
            for collector in list(REGISTRY._collector_to_names.keys()):
                # 只保留默认的Python进程指标，清除其他所有指标
                if hasattr(collector, "_name"):
                    metric_names: list[str] = REGISTRY._collector_to_names.get(collector, [])
                    # 保留默认的Python进程指标（这些是由prometheus_client自动创建的）
                    is_default_process_metric: bool = any(
                        name
                        in [
                            "process_virtual_memory_bytes",
                            "process_resident_memory_bytes",
                            "process_start_time_seconds",
                            "process_cpu_seconds_total",
                            "process_open_fds",
                            "process_max_fds",
                            "python_gc_objects_collected_total",
                            "python_gc_objects_uncollectable_total",
                            "python_gc_collections_total",
                            "python_info",
                        ]
                        for name in metric_names
                    )
                    if not is_default_process_metric:
                        collectors_to_remove.append(collector)

            for collector in collectors_to_remove:
                try:
                    REGISTRY.unregister(collector)
                except (KeyError, ValueError):
                    pass  # 已经被移除或不存在
        except Exception:
            pass  # 忽略清理错误，继续初始化

        # 信号处理延迟 (Signal processing latency)
        self.signal_latency: Histogram = Histogram(
            "trading_signal_latency_seconds",
            "Time to calculate trading signals",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        )

        # 订单执行延迟 (Order execution latency)
        self.order_latency: Histogram = Histogram(
            "trading_order_latency_seconds",
            "Time to execute orders",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
        )

        # 数据获取延迟 (Data fetch latency)
        self.data_fetch_latency: Histogram = Histogram(
            "trading_data_fetch_latency_seconds",
            "Time to fetch market data",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
        )

        # 滑点监控 (Slippage monitoring)
        self.slippage: Histogram = Histogram(
            "trading_slippage_percentage",
            "Price slippage percentage",
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
        )

        # 异常计数 (Exception counter)
        self.exceptions: Counter = Counter(
            "trading_exceptions_total",
            "Total exceptions by module and type",
            ["module", "exception_type"],
        )

        # 账户余额 (Account balance)
        self.account_balance: Gauge = Gauge("trading_account_balance_usd", "Account balance in USD")

        # 回撤监控 (Drawdown monitoring)
        self.drawdown: Gauge = Gauge("trading_drawdown_percentage", "Current drawdown from peak")

        # 持仓数量 (Position count)
        self.position_count: Gauge = Gauge("trading_positions_total", "Number of open positions")

        # API调用次数 (API call counter)
        self.api_calls: Counter = Counter(
            "trading_api_calls_total", "Total API calls by endpoint", ["endpoint", "status"]
        )

        # WebSocket心跳 (WebSocket heartbeat)
        self.ws_heartbeat_age: Gauge = Gauge(
            "trading_ws_heartbeat_age_seconds", "WebSocket heartbeat age in seconds"
        )

        # ATR计算延迟 (ATR calculation latency)
        self.atr_calculation_latency: Histogram = Histogram(
            "atr_calculation_latency_seconds",
            "ATR计算延迟",
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
        )

        # M4阶段 - WebSocket相关指标 (M4 Phase - WebSocket related metrics)
        self.ws_latency: Histogram = Histogram(
            "binance_ws_latency_seconds",
            "WebSocket消息延迟",
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
        )

        self.ws_reconnects_total: Counter = Counter(
            "ws_reconnects_total", "WebSocket重连次数", ["symbol", "reason"]
        )

        self.ws_connections_total: Counter = Counter(
            "ws_connections_total", "WebSocket连接次数", ["status"]  # success, error
        )

        self.ws_messages_total: Counter = Counter(
            "ws_messages_total", "WebSocket消息计数", ["symbol", "type"]  # kline, ticker
        )

        self.price_updates_total: Counter = Counter(
            "price_updates_total", "价格更新计数", ["symbol", "source"]  # source: ws, api
        )

        self.order_roundtrip_latency: Histogram = Histogram(
            "order_roundtrip_latency_seconds",
            "订单往返延迟",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
        )

        self.concurrent_tasks: Gauge = Gauge(
            "concurrent_tasks_count", "并发任务数量", ["task_type"]  # order_execution, data_fetch
        )

        self.ws_processing_time: Histogram = Histogram(
            "ws_processing_time_seconds",
            "WebSocket消息处理时间",
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
        )

        self.msg_lag: Histogram = Histogram(
            "message_lag_seconds",
            "消息延迟（从交易所到本地处理）",
            buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
        )

        # M5阶段性能监控指标 (M5 Phase performance monitoring metrics)

        # 任务延迟指标 (Task latency metrics)
        self.task_latency: Histogram = Histogram(
            "task_latency_seconds",
            "各类任务执行延迟 (Task execution latency)",
            ["task_type"],  # signal_processing, order_placement, data_analysis
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0],
        )

        # 内存使用指标 (Memory usage metrics)
        self.process_memory_usage: Gauge = Gauge(
            "process_memory_usage_bytes", "进程内存使用量 (Process memory usage in bytes)"
        )

        self.process_memory_percent: Gauge = Gauge(
            "process_memory_percent", "进程内存使用百分比 (Process memory usage percentage)"
        )

        self.process_cpu_percent: Gauge = Gauge(
            "process_cpu_percent", "进程CPU使用百分比 (Process CPU usage percentage)"
        )

        self.process_threads: Gauge = Gauge(
            "process_threads_count", "进程线程数 (Process thread count)"
        )

        self.process_fds: Gauge = Gauge(
            "process_file_descriptors", "进程文件描述符数量 (Process file descriptor count)"
        )

        # 垃圾回收指标 (Garbage collection metrics)
        self.gc_collections: Counter = Counter(
            "gc_collections_total", "垃圾回收次数 (Garbage collection count)", ["generation"]
        )

        self.gc_collected_objects: Counter = Counter(
            "gc_collected_objects_total", "回收对象数 (Collected objects count)", ["generation"]
        )

        self.gc_pause_time: Histogram = Histogram(
            "gc_pause_time_seconds",
            "垃圾回收暂停时间 (Garbage collection pause time)",
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0],
        )

        self.gc_tracked_objects: Gauge = Gauge(
            "gc_tracked_objects", "GC跟踪对象数量 (Number of objects tracked by GC)"
        )

        # 内存分配跟踪 (Memory allocation tracking)
        self.memory_allocation_rate: Gauge = Gauge(
            "memory_allocation_rate_bytes_per_second",
            "内存分配速率 (Memory allocation rate in bytes per second)",
        )

        self.memory_peak_usage: Gauge = Gauge(
            "memory_peak_usage_bytes", "内存使用峰值 (Peak memory usage in bytes)"
        )

        # 内存增长监控 (Memory growth monitoring)
        self.memory_growth_rate: Gauge = Gauge(
            "memory_growth_rate_mb_per_minute",
            "内存增长速率 (Memory growth rate in MB per minute)",
        )

        self.fd_growth_rate: Gauge = Gauge(
            "fd_growth_rate_per_minute", "文件描述符增长速率 (FD growth rate per minute)"
        )

        # 内存健康状态 (Memory health status)
        self.memory_health_score: Gauge = Gauge(
            "memory_health_score", "内存健康评分 (Memory health score 0-100)"
        )

        # 当前价格指标 (Current price metrics) - 修复缺失的指标
        self.current_price: Gauge = Gauge(
            "trading_current_price_usd",
            "当前交易价格 (Current trading price by symbol)",
            ["symbol"],
        )

    def start_server(self) -> None:
        """
        启动Prometheus HTTP服务器

        Raises:
            Exception: 服务器启动失败时抛出异常
        """
        if not self.config.enabled or self._server_started:
            return

        try:
            port: int = self.config.port
            start_http_server(port)
            self._server_started = True
            self.logger.info(f"Prometheus指标服务器已启动在端口 {port}")
        except Exception as e:
            self.logger.error(f"启动Prometheus服务器失败: {e}")
            raise

    @contextmanager
    def measure_signal_latency(self) -> Generator[None, None, None]:
        """
        测量信号计算延迟的上下文管理器

        Yields:
            None

        Example:
            with metrics.measure_signal_latency():
                signals = strategy.generate_signals(data)
        """
        start_time: float = time.perf_counter()
        try:
            yield
        finally:
            elapsed: float = time.perf_counter() - start_time
            self.signal_latency.observe(elapsed)

    @contextmanager
    def measure_order_latency(self) -> Generator[None, None, None]:
        """
        测量订单执行延迟的上下文管理器

        Yields:
            None

        Example:
            with metrics.measure_order_latency():
                order_result = broker.place_order(...)
        """
        start_time: float = time.perf_counter()
        try:
            yield
        finally:
            elapsed: float = time.perf_counter() - start_time
            self.order_latency.observe(elapsed)

    @contextmanager
    def measure_data_fetch_latency(self) -> Generator[None, None, None]:
        """
        测量数据获取延迟的上下文管理器

        Yields:
            None

        Example:
            with metrics.measure_data_fetch_latency():
                data = fetch_price_data(symbol)
        """
        start_time: float = time.perf_counter()
        try:
            yield
        finally:
            elapsed: float = time.perf_counter() - start_time
            self.data_fetch_latency.observe(elapsed)

    def record_slippage(self, expected_price: float, actual_price: float) -> None:
        """
        记录滑点

        Args:
            expected_price: 期望价格 (Expected price)
            actual_price: 实际价格 (Actual price)
        """
        slippage_percent: float = abs(actual_price - expected_price) / expected_price * 100
        self.slippage.observe(slippage_percent)

    def record_exception(self, module: str, exception: Exception) -> None:
        """
        记录异常

        Args:
            module: 模块名 (Module name)
            exception: 异常对象 (Exception object)
        """
        exception_type: str = type(exception).__name__
        self.exceptions.labels(module=module, exception_type=exception_type).inc()

    def update_account_balance(self, balance_usd: float) -> None:
        """
        更新账户余额

        Args:
            balance_usd: 美元余额 (USD balance)
        """
        self.account_balance.set(balance_usd)

    def update_drawdown(self, current_balance: float, peak_balance: float) -> None:
        """
        更新回撤

        Args:
            current_balance: 当前余额 (Current balance)
            peak_balance: 峰值余额 (Peak balance)
        """
        drawdown_percent: float = (peak_balance - current_balance) / peak_balance * 100
        self.drawdown.set(drawdown_percent)

    def update_position_count(self, count: int) -> None:
        """
        更新持仓数量

        Args:
            count: 持仓数量 (Position count)
        """
        self.position_count.set(count)

    def record_api_call(self, endpoint: str, status: str) -> None:
        """
        记录API调用

        Args:
            endpoint: API端点 (API endpoint)
            status: 状态码 (Status code)
        """
        self.api_calls.labels(endpoint=endpoint, status=status).inc()

    def update_ws_heartbeat_age(self, last_heartbeat_timestamp: float) -> None:
        """
        更新WebSocket心跳年龄

        Args:
            last_heartbeat_timestamp: 最后心跳时间戳 (Last heartbeat timestamp)
        """
        current_time: float = time.time()
        age_seconds: float = current_time - last_heartbeat_timestamp
        self.ws_heartbeat_age.set(age_seconds)

    # M4阶段 - WebSocket指标记录方法
    def observe_ws_latency(self, latency_seconds: float):
        """记录WebSocket延迟"""
        self.ws_latency.observe(latency_seconds)

    def record_ws_reconnect(self, symbol: str = "ALL", reason: str = "connection_lost"):
        """记录WebSocket重连"""
        self.ws_reconnects_total.labels(symbol=symbol, reason=reason).inc()

    def record_ws_connection_success(self):
        """记录WebSocket连接成功"""
        self.ws_connections_total.labels(status="success").inc()

    def record_ws_connection_error(self):
        """记录WebSocket连接错误"""
        self.ws_connections_total.labels(status="error").inc()

    def record_ws_message(self, symbol: str, msg_type: str):
        """记录WebSocket消息"""
        self.ws_messages_total.labels(symbol=symbol, type=msg_type).inc()

    def record_price_update(self, symbol: str, price: float, source: str = "ws"):
        """记录价格更新"""
        self.price_updates_total.labels(symbol=symbol, source=source).inc()

        # 同时更新价格指标
        self.current_price.labels(symbol=symbol).set(price)

    def observe_msg_lag(self, lag_seconds: float):
        """记录消息滞后时间"""
        self.msg_lag.observe(lag_seconds)

    def observe_order_roundtrip_latency(self, latency_seconds: float):
        """记录订单往返延迟"""
        self.order_roundtrip_latency.observe(latency_seconds)

    def update_concurrent_tasks(self, task_type: str, count: int):
        """更新并发任务计数"""
        self.concurrent_tasks.labels(task_type=task_type).set(count)

    @contextmanager
    def measure_ws_processing_time(self):
        """测量WebSocket消息处理时间"""
        start_time = time.time()
        try:
            yield
        finally:
            processing_time = time.time() - start_time
            self.signal_latency.observe(processing_time)

    @contextmanager
    def measure_task_latency(self, task_type: str = "general"):
        """测量异步任务延迟"""
        if not self.config.enabled:
            yield
            return

        start_time = time.time()
        try:
            yield
        finally:
            latency = time.time() - start_time
            self.task_latency.labels(task_type=task_type).observe(latency)

    def observe_task_latency(self, task_type: str, latency_seconds: float):
        """直接记录任务延迟"""
        if not self.config.enabled:
            return
        self.task_latency.labels(task_type=task_type).observe(latency_seconds)

    # M5阶段 - 内存和GC监控方法
    def update_process_memory_stats(self):
        """更新进程内存统计"""
        if not self.config.enabled:
            return

        try:
            import psutil

            process = psutil.Process()

            memory_info = process.memory_info()
            self.process_memory_usage.set(memory_info.rss)
            self.process_memory_percent.set(process.memory_percent())
            self.process_cpu_percent.set(process.cpu_percent())

            # 文件描述符
            try:
                num_fds = process.num_fds()
            except AttributeError:
                # Windows不支持num_fds
                num_fds = len(process.open_files())
            self.process_fds.set(num_fds)

            # 线程数
            self.process_threads.set(process.num_threads())

            # 网络连接
            connections = process.connections()
            self.active_connections.labels(connection_type="total").set(len(connections))

            # 更新内存峰值
            current_rss = memory_info.rss
            if not hasattr(self, "_peak_rss") or current_rss > self._peak_rss:
                self._peak_rss = current_rss
                self.memory_peak_usage.set(current_rss)

        except Exception as e:
            self.logger.warning(f"⚠️ 进程内存统计更新失败: {e}")

    def record_gc_event(self, generation: int, pause_duration: float, collected_objects: int):
        """记录GC事件"""
        if not self.config.enabled:
            return

        gen_label = str(generation)
        self.gc_collections.labels(generation=gen_label).inc()
        self.gc_pause_time.labels(generation=gen_label).observe(pause_duration)
        self.gc_collected_objects.labels(generation=gen_label).inc(collected_objects)

    def update_gc_tracked_objects(self):
        """更新GC追踪的对象数量"""
        if not self.config.enabled:
            return

        try:
            import gc

            for generation in range(3):
                objects_count = len(gc.get_objects(generation))
                self.gc_tracked_objects.labels(generation=str(generation)).set(objects_count)
        except Exception as e:
            self.logger.warning(f"⚠️ GC对象统计更新失败: {e}")

    def record_memory_allocation(self, size_bytes: int):
        """记录内存分配"""
        if not self.config.enabled:
            return

        # 记录内存分配大小
        self.memory_allocation_rate.set(size_bytes)

    def update_memory_growth_rate(self, growth_mb_per_minute: float):
        """更新内存增长率"""
        if not self.config.enabled:
            return
        self.memory_growth_rate.set(growth_mb_per_minute)

    def update_fd_growth_rate(self, growth_per_minute: float):
        """更新文件描述符增长率"""
        if not self.config.enabled:
            return
        self.fd_growth_rate.set(growth_per_minute)

    @contextmanager
    def monitor_memory_allocation(self, operation_name: str = "unknown"):
        """监控内存分配的上下文管理器"""
        if not self.config.enabled:
            yield
            return

        try:
            import tracemalloc

            was_tracing = tracemalloc.is_tracing()

            if not was_tracing:
                tracemalloc.start()

            # 获取开始时的内存快照
            snapshot_start = tracemalloc.take_snapshot()

            yield

            # 获取结束时的内存快照
            snapshot_end = tracemalloc.take_snapshot()

            # 计算差异
            top_stats = snapshot_end.compare_to(snapshot_start, "lineno")

            # 记录最大的几个分配
            for stat in top_stats[:5]:
                self.record_memory_allocation(stat.size)

            if not was_tracing:
                tracemalloc.stop()

        except Exception as e:
            self.logger.warning(f"⚠️ 内存分配监控失败: {e}")

    def get_memory_health_status(self) -> Dict[str, Any]:
        """获取内存健康状态"""
        try:
            import gc

            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            # 当前状态
            current_rss_mb = memory_info.rss / 1024 / 1024
            current_vms_mb = memory_info.vms / 1024 / 1024
            memory_percent = process.memory_percent()

            # GC状态
            gc_counts = gc.get_count()
            gc_thresholds = gc.get_threshold()

            # 健康评估
            health_issues = []

            if current_rss_mb > 100:  # RSS > 100MB
                health_issues.append(f"RSS内存使用过高: {current_rss_mb:.1f}MB")

            if memory_percent > 5:  # 超过系统内存5%
                health_issues.append(f"系统内存占用过高: {memory_percent:.1f}%")

            if gc_counts[0] > gc_thresholds[0] * 0.9:  # Gen0接近阈值
                health_issues.append(f"GC Gen0接近阈值: {gc_counts[0]}/{gc_thresholds[0]}")

            return {
                "timestamp": time.time(),
                "memory": {
                    "rss_mb": current_rss_mb,
                    "vms_mb": current_vms_mb,
                    "percent": memory_percent,
                    "peak_rss_mb": getattr(self, "_peak_rss", 0) / 1024 / 1024,
                },
                "gc": {"counts": gc_counts, "thresholds": gc_thresholds},
                "health": {
                    "status": "healthy" if not health_issues else "warning",
                    "issues": health_issues,
                },
            }

        except Exception as e:
            return {"error": str(e), "timestamp": time.time()}

    def get_error_summary(self) -> Dict[str, int]:
        """获取错误统计摘要"""
        try:
            from prometheus_client import REGISTRY

            return self._extract_error_counts_from_registry(REGISTRY)
        except Exception as e:
            self.logger.warning(f"⚠️ 获取错误摘要失败: {e}")
            return {}

    def _extract_error_counts_from_registry(self, registry) -> Dict[str, int]:
        """从Prometheus注册表提取错误计数"""
        error_counts = {}

        for collector in registry._collector_to_names.keys():
            if not self._is_exception_collector(collector):
                continue

            try:
                self._process_exception_samples(collector, error_counts)
            except Exception:
                pass

        return error_counts

    def _is_exception_collector(self, collector) -> bool:
        """检查是否为异常收集器"""
        return hasattr(collector, "_name") and "exceptions" in str(collector._name)

    def _process_exception_samples(self, collector, error_counts: Dict[str, int]):
        """处理异常样本数据"""
        for sample in collector.collect():
            for metric_sample in sample.samples:
                if "exceptions_total" in metric_sample.name:
                    module = metric_sample.labels.get("module", "unknown")
                    value = int(metric_sample.value)
                    error_counts[module] = error_counts.get(module, 0) + value

    def record_trade(self, symbol: str, action: str, price: float = 0.0, quantity: float = 0.0):
        """
        记录交易事件 (向后兼容方法)

        Args:
            symbol: 交易对符号
            action: 交易动作 (buy/sell)
            price: 交易价格
            quantity: 交易数量
        """
        try:
            # 记录价格更新
            self.record_price_update(symbol, price, source="trade")

            # 记录交易价格
            if price > 0:
                self.current_price.labels(symbol=symbol).set(price)

            self.logger.info(f"📊 记录交易: {symbol} {action} @ {price} x {quantity}")

        except Exception as e:
            self.logger.error(f"❌ 记录交易失败: {e}")
            self.record_exception("metrics_collector", e)

    def get_trade_summary(self) -> Dict[str, Any]:
        """
        获取交易摘要 (向后兼容方法)

        Returns:
            交易摘要信息，包含交易对作为顶级键
        """
        try:
            from prometheus_client import REGISTRY

            return self._extract_trade_summary_from_registry(REGISTRY)
        except Exception as e:
            self.logger.error(f"❌ 获取交易摘要失败: {e}")
            return {}

    def _extract_trade_summary_from_registry(self, registry) -> Dict[str, Any]:
        """从Prometheus注册表提取交易摘要"""
        summary = {}

        for collector in registry._collector_to_names.keys():
            try:
                self._process_trade_samples(collector, summary)
            except Exception:
                pass

        return summary if summary else {}

    def _process_trade_samples(self, collector, summary: Dict[str, Any]):
        """处理交易样本数据"""
        for sample in collector.collect():
            for metric_sample in sample.samples:
                if "price_updates_total" in metric_sample.name:
                    self._update_trade_summary_for_symbol(metric_sample, summary)

    def _update_trade_summary_for_symbol(self, metric_sample, summary: Dict[str, Any]):
        """为特定交易对更新交易摘要"""
        if "symbol" not in metric_sample.labels:
            return

        symbol = metric_sample.labels["symbol"]
        if symbol not in summary:
            summary[symbol] = {"trades": 0, "price_updates": 0}

        summary[symbol]["price_updates"] += int(metric_sample.value)
        summary[symbol]["trades"] += 1

    def record_error(self, module: str, error_message: str):
        """
        记录错误 (向后兼容方法)

        Args:
            module: 模块名称
            error_message: 错误消息
        """
        try:
            # 创建一个虚拟异常来记录
            error = Exception(error_message)
            self.record_exception(module, error)

        except Exception as e:
            self.logger.error(f"❌ 记录错误失败: {e}")

    def update_price(self, symbol: str, price: float):
        """
        更新价格 (向后兼容方法)

        Args:
            symbol: 交易对符号
            price: 价格
        """
        try:
            self.current_price.labels(symbol=symbol).set(price)
            self.record_price_update(symbol, price, source="manual")

        except Exception as e:
            self.logger.error(f"❌ 更新价格失败: {e}")

    def get_latest_prices(self) -> Dict[str, float]:
        """
        获取最新价格 (向后兼容方法)

        Returns:
            符号到价格的映射
        """
        try:
            from prometheus_client import REGISTRY

            prices = {}

            # 从Prometheus注册表中获取价格数据
            for collector in REGISTRY._collector_to_names.keys():
                try:
                    for sample in collector.collect():
                        for metric_sample in sample.samples:
                            if "current_price_usd" in metric_sample.name:
                                if "symbol" in metric_sample.labels:
                                    symbol = metric_sample.labels["symbol"]
                                    prices[symbol] = float(metric_sample.value)

                except Exception:
                    pass

            return prices

        except Exception as e:
            self.logger.error(f"❌ 获取最新价格失败: {e}")
            return {}

    def update_heartbeat(self):
        """
        更新心跳 (向后兼容方法)
        """
        try:
            current_time = time.time()
            if hasattr(self, "exporter") and hasattr(self.exporter, "last_heartbeat"):
                self.exporter.last_heartbeat = current_time
            else:
                # 设置一个通用的心跳时间戳
                self._last_heartbeat = current_time

        except Exception as e:
            self.logger.error(f"❌ 更新心跳失败: {e}")

    def update_data_source_status(self, source_name: str, is_active: bool):
        """
        更新数据源状态 (向后兼容方法)

        Args:
            source_name: 数据源名称
            is_active: 是否活跃
        """
        try:
            # 使用连接状态指标
            status = 1 if is_active else 0
            self.active_connections.labels(connection_type=source_name).set(status)

        except Exception as e:
            self.logger.error(f"❌ 更新数据源状态失败: {e}")

    def update_memory_usage(self, memory_mb: float):
        """
        更新内存使用量 (向后兼容方法)

        Args:
            memory_mb: 内存使用量(MB)
        """
        try:
            memory_bytes = memory_mb * 1024 * 1024
            self.process_memory_usage.set(memory_bytes)

        except Exception as e:
            self.logger.error(f"❌ 更新内存使用量失败: {e}")


# 全局监控实例
_global_collector: Optional[TradingMetricsCollector] = None


def get_metrics_collector() -> TradingMetricsCollector:
    """获取全局监控实例"""
    global _global_collector

    if _global_collector is None:
        config = MetricsConfig(
            enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            port=int(os.getenv("PROMETHEUS_PORT", "8000")),
        )
        _global_collector = TradingMetricsCollector(config)

    return _global_collector


def init_monitoring() -> TradingMetricsCollector:
    """初始化监控系统"""
    collector = get_metrics_collector()
    collector.start_server()
    return collector
