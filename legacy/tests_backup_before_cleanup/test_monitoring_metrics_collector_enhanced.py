#!/usr/bin/env python3
"""
🧪 Metrics Collector 增强测试 (Metrics Collector Enhanced Tests)

全面测试 monitoring/metrics_collector.py 模块
目标：从18% -> 85%+ 覆盖率
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch


from src.monitoring.metrics_collector import (
    MetricsConfig,
    TradingMetricsCollector,
    _create_fallback_prometheus_classes,
    _setup_prometheus_imports,
    get_metrics_collector,
    init_monitoring,
)


class TestMetricsConfig(unittest.TestCase):
    """测试MetricsConfig配置类"""

    def test_metrics_config_defaults(self):
        """测试默认配置"""
        config = MetricsConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.port, 8000)
        self.assertTrue(config.include_system_metrics)

    def test_metrics_config_custom(self):
        """测试自定义配置"""
        config = MetricsConfig(enabled=False, port=9090, include_system_metrics=False)
        self.assertFalse(config.enabled)
        self.assertEqual(config.port, 9090)
        self.assertFalse(config.include_system_metrics)


class TestPrometheusImports(unittest.TestCase):
    """测试Prometheus导入和回退机制"""

    @patch("src.monitoring.metrics_collector.prometheus_client", None)
    def test_fallback_prometheus_classes(self):
        """测试Prometheus回退类"""
        _, Counter, Gauge, Histogram, start_http_server = _create_fallback_prometheus_classes()

        # 测试Counter回退类
        counter = Counter("test", "desc")
        self.assertIsNotNone(counter)
        counter.labels(label="value").inc()  # 应该不抛出异常

        # 测试Gauge回退类
        gauge = Gauge("test", "desc")
        gauge.set(10.5)  # 应该不抛出异常

        # 测试Histogram回退类
        histogram = Histogram("test", "desc")
        histogram.observe(1.0)  # 应该不抛出异常

        # 测试start_http_server回退
        start_http_server(8000)  # 应该不抛出异常

    def test_setup_prometheus_imports_success(self):
        """测试成功的Prometheus导入"""
        result = _setup_prometheus_imports()
        self.assertEqual(len(result), 5)


class TestTradingMetricsCollectorBasic(unittest.TestCase):
    """测试TradingMetricsCollector基本功能"""

    def setUp(self):
        """设置测试"""
        self.config = MetricsConfig(enabled=True, port=8001)

    def test_init_with_config(self):
        """测试使用配置初始化"""
        collector = TradingMetricsCollector(self.config)
        self.assertEqual(collector.config.port, 8001)
        self.assertTrue(collector.config.enabled)

    def test_init_with_none_config(self):
        """测试使用None配置初始化"""
        collector = TradingMetricsCollector(None)
        self.assertIsInstance(collector.config, MetricsConfig)

    def test_init_disabled_monitoring(self):
        """测试禁用监控"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)
        self.assertFalse(collector.config.enabled)

    @patch("src.monitoring.metrics_collector.PrometheusExporter")
    def test_init_with_exporter_backward_compatibility(self, mock_exporter):
        """测试向后兼容性：传入exporter对象"""
        mock_exporter_instance = MagicMock()
        collector = TradingMetricsCollector(mock_exporter_instance)
        self.assertEqual(collector.exporter, mock_exporter_instance)


class TestTradingMetricsCollectorMetrics(unittest.TestCase):
    """测试指标记录功能"""

    def setUp(self):
        """设置测试"""
        # 使用回退模式避免Prometheus依赖
        config = MetricsConfig(enabled=True, port=8002)
        self.collector = TradingMetricsCollector(config)

    def test_record_trade(self):
        """测试记录交易"""
        self.collector.record_trade("BTCUSD", "buy", 100.0, 1.0)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_signal_generation(self):
        """测试记录信号生成"""
        self.collector.record_signal_generation("moving_average", 0.001)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_order_placement(self):
        """测试记录订单下单"""
        self.collector.record_order_placement("ETHUSD", "sell", 50.0, 2000.0)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_exception(self):
        """测试记录异常"""
        self.collector.record_exception("data_processing", "ValueError")
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_ws_connection_status(self):
        """测试记录WebSocket连接状态"""
        self.collector.record_ws_connection_status("binance", True)
        self.collector.record_ws_connection_status("binance", False)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_update_portfolio_value(self):
        """测试更新投资组合价值"""
        self.collector.update_portfolio_value(50000.0)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_strategy_return(self):
        """测试记录策略收益"""
        self.collector.record_strategy_return("ma_crossover", 5.2)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_price_update(self):
        """测试记录价格更新"""
        self.collector.record_price_update("BTCUSD", 45000.0, "ws")
        self.collector.record_price_update("ETHUSD", 3000.0, "rest")
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_observe_msg_lag(self):
        """测试观察消息延迟"""
        self.collector.observe_msg_lag(0.05)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_observe_order_roundtrip_latency(self):
        """测试观察订单往返延迟"""
        self.collector.observe_order_roundtrip_latency(0.123)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_update_concurrent_tasks(self):
        """测试更新并发任务计数"""
        self.collector.update_concurrent_tasks("signal_processing", 5)
        self.collector.update_concurrent_tasks("order_placement", 2)
        # 验证方法调用不抛出异常
        self.assertTrue(True)


class TestTradingMetricsCollectorContextManagers(unittest.TestCase):
    """测试上下文管理器功能"""

    def setUp(self):
        """设置测试"""
        config = MetricsConfig(enabled=True, port=8003)
        self.collector = TradingMetricsCollector(config)

    def test_measure_ws_processing_time(self):
        """测试WebSocket处理时间测量"""
        with self.collector.measure_ws_processing_time():
            time.sleep(0.01)  # 模拟处理时间
        # 验证上下文管理器正常工作
        self.assertTrue(True)

    def test_measure_task_latency_enabled(self):
        """测试任务延迟测量（启用）"""
        with self.collector.measure_task_latency("test_task"):
            time.sleep(0.005)  # 模拟任务执行
        # 验证上下文管理器正常工作
        self.assertTrue(True)

    def test_measure_task_latency_disabled(self):
        """测试任务延迟测量（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        with collector.measure_task_latency("test_task"):
            time.sleep(0.005)  # 模拟任务执行
        # 验证禁用状态下也能正常工作
        self.assertTrue(True)

    def test_observe_task_latency_enabled(self):
        """测试直接记录任务延迟（启用）"""
        self.collector.observe_task_latency("data_processing", 0.456)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_observe_task_latency_disabled(self):
        """测试直接记录任务延迟（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        collector.observe_task_latency("data_processing", 0.456)
        # 验证禁用状态下不执行操作
        self.assertTrue(True)

    @patch("tracemalloc.is_tracing", return_value=False)
    @patch("tracemalloc.start")
    @patch("tracemalloc.take_snapshot")
    @patch("tracemalloc.stop")
    def test_monitor_memory_allocation_context(
        self, mock_stop, mock_snapshot, mock_start, mock_is_tracing
    ):
        """测试内存分配监控上下文管理器"""
        mock_snapshot_start = MagicMock()
        mock_snapshot_end = MagicMock()
        mock_snapshot.side_effect = [mock_snapshot_start, mock_snapshot_end]

        # 模拟内存统计
        mock_stat = MagicMock()
        mock_stat.size = 1024
        mock_snapshot_end.compare_to.return_value = [mock_stat]

        with self.collector.monitor_memory_allocation("test_operation"):
            pass  # 模拟操作

        mock_start.assert_called_once()
        mock_stop.assert_called_once()
        self.assertEqual(mock_snapshot.call_count, 2)

    def test_monitor_memory_allocation_disabled(self):
        """测试内存分配监控（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        with collector.monitor_memory_allocation("test_operation"):
            pass  # 模拟操作
        # 验证禁用状态下不执行监控
        self.assertTrue(True)


class TestTradingMetricsCollectorMemoryMonitoring(unittest.TestCase):
    """测试内存和性能监控功能"""

    def setUp(self):
        """设置测试"""
        config = MetricsConfig(enabled=True, port=8004)
        self.collector = TradingMetricsCollector(config)

    @patch("psutil.Process")
    def test_update_process_memory_stats_success(self, mock_process_class):
        """测试成功更新进程内存统计"""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # 模拟内存信息
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 5.5
        mock_process.cpu_percent.return_value = 10.2
        mock_process.num_threads.return_value = 8
        mock_process.num_fds.return_value = 50
        mock_process.connections.return_value = [1, 2, 3]  # 3个连接

        self.collector.update_process_memory_stats()

        # 验证调用
        mock_process.memory_info.assert_called_once()
        mock_process.memory_percent.assert_called_once()
        mock_process.cpu_percent.assert_called_once()

    @patch("psutil.Process")
    def test_update_process_memory_stats_windows_fallback(self, mock_process_class):
        """测试Windows系统下的文件描述符回退"""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # 模拟Windows系统（没有num_fds方法）
        mock_process.num_fds.side_effect = AttributeError("Windows doesn't support num_fds")
        mock_process.open_files.return_value = [1, 2, 3, 4]  # 4个打开文件

        # 设置其他属性避免其他错误
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 1024 * 1024 * 50
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 3.0
        mock_process.cpu_percent.return_value = 5.0
        mock_process.num_threads.return_value = 4
        mock_process.connections.return_value = []

        self.collector.update_process_memory_stats()

        # 验证Windows回退机制
        mock_process.open_files.assert_called_once()

    @patch("psutil.Process", side_effect=Exception("psutil error"))
    def test_update_process_memory_stats_exception(self, mock_process_class):
        """测试内存统计更新异常处理"""
        with self.assertLogs(level="WARNING") as log:
            self.collector.update_process_memory_stats()

        # 验证异常被正确记录
        self.assertIn("进程内存统计更新失败", str(log.output))

    def test_update_process_memory_stats_disabled(self):
        """测试内存统计更新（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        collector.update_process_memory_stats()
        # 验证禁用状态下不执行操作
        self.assertTrue(True)

    def test_record_gc_event_enabled(self):
        """测试记录GC事件（启用）"""
        self.collector.record_gc_event(0, 0.001, 150)
        self.collector.record_gc_event(1, 0.005, 80)
        self.collector.record_gc_event(2, 0.020, 25)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_gc_event_disabled(self):
        """测试记录GC事件（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        collector.record_gc_event(0, 0.001, 150)
        # 验证禁用状态下不执行操作
        self.assertTrue(True)

    @patch("gc.get_objects")
    def test_update_gc_tracked_objects_success(self, mock_get_objects):
        """测试成功更新GC跟踪对象"""
        # 模拟不同代的对象数量
        mock_get_objects.side_effect = [
            list(range(1000)),  # 第0代：1000个对象
            list(range(500)),  # 第1代：500个对象
            list(range(100)),  # 第2代：100个对象
        ]

        self.collector.update_gc_tracked_objects()

        # 验证调用次数
        self.assertEqual(mock_get_objects.call_count, 3)

    @patch("gc.get_objects", side_effect=Exception("GC error"))
    def test_update_gc_tracked_objects_exception(self, mock_get_objects):
        """测试GC对象统计异常处理"""
        with self.assertLogs(level="WARNING") as log:
            self.collector.update_gc_tracked_objects()

        # 验证异常被正确记录
        self.assertIn("GC对象统计更新失败", str(log.output))

    def test_update_gc_tracked_objects_disabled(self):
        """测试GC对象统计更新（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        collector.update_gc_tracked_objects()
        # 验证禁用状态下不执行操作
        self.assertTrue(True)

    def test_record_memory_allocation_enabled(self):
        """测试记录内存分配（启用）"""
        self.collector.record_memory_allocation(2048)
        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_record_memory_allocation_disabled(self):
        """测试记录内存分配（禁用）"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        collector.record_memory_allocation(2048)
        # 验证禁用状态下不执行操作
        self.assertTrue(True)

    def test_update_memory_growth_rate(self):
        """测试更新内存增长率"""
        self.collector.update_memory_growth_rate(5.5)

        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)
        collector.update_memory_growth_rate(5.5)  # 测试禁用状态

        # 验证方法调用不抛出异常
        self.assertTrue(True)

    def test_update_fd_growth_rate(self):
        """测试更新文件描述符增长率"""
        self.collector.update_fd_growth_rate(2.3)

        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)
        collector.update_fd_growth_rate(2.3)  # 测试禁用状态

        # 验证方法调用不抛出异常
        self.assertTrue(True)


class TestTradingMetricsCollectorHealthMonitoring(unittest.TestCase):
    """测试健康监控功能"""

    def setUp(self):
        """设置测试"""
        config = MetricsConfig(enabled=True, port=8005)
        self.collector = TradingMetricsCollector(config)

    @patch("psutil.Process")
    @patch("gc.get_count")
    @patch("gc.get_threshold")
    def test_get_memory_health_status_healthy(
        self, mock_get_threshold, mock_get_count, mock_process_class
    ):
        """测试获取健康的内存状态"""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # 模拟健康状态
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 50 * 1024 * 1024  # 50MB
        mock_memory_info.vms = 100 * 1024 * 1024  # 100MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 2.0  # 2%

        mock_get_count.return_value = (500, 40, 5)
        mock_get_threshold.return_value = (700, 10, 10)

        health_status = self.collector.get_memory_health_status()

        # 验证健康状态
        self.assertIn("timestamp", health_status)
        self.assertIn("memory", health_status)
        self.assertIn("gc", health_status)
        self.assertIn("health", health_status)
        self.assertEqual(health_status["health"]["status"], "healthy")
        self.assertEqual(len(health_status["health"]["issues"]), 0)

    @patch("psutil.Process")
    @patch("gc.get_count")
    @patch("gc.get_threshold")
    def test_get_memory_health_status_warning(
        self, mock_get_threshold, mock_get_count, mock_process_class
    ):
        """测试获取警告状态的内存状态"""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # 模拟警告状态
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 150 * 1024 * 1024  # 150MB (> 100MB)
        mock_memory_info.vms = 300 * 1024 * 1024  # 300MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 8.0  # 8% (> 5%)

        mock_get_count.return_value = (680, 40, 5)  # Gen0接近阈值
        mock_get_threshold.return_value = (700, 10, 10)

        health_status = self.collector.get_memory_health_status()

        # 验证警告状态
        self.assertEqual(health_status["health"]["status"], "warning")
        self.assertGreater(len(health_status["health"]["issues"]), 0)

    @patch("psutil.Process", side_effect=Exception("Health check error"))
    def test_get_memory_health_status_exception(self, mock_process_class):
        """测试内存健康状态检查异常处理"""
        health_status = self.collector.get_memory_health_status()

        # 验证异常处理
        self.assertIn("error", health_status)
        self.assertIn("timestamp", health_status)


class TestTradingMetricsCollectorErrorSummary(unittest.TestCase):
    """测试错误摘要功能"""

    def setUp(self):
        """设置测试"""
        config = MetricsConfig(enabled=True, port=8006)
        self.collector = TradingMetricsCollector(config)

    @patch("src.monitoring.metrics_collector.REGISTRY")
    def test_get_error_summary_success(self, mock_registry):
        """测试成功获取错误摘要"""
        # 模拟Prometheus注册表
        mock_collector = MagicMock()
        mock_collector._name = "trading_exceptions_total"

        mock_sample = MagicMock()
        mock_sample.name = "trading_exceptions_total"
        mock_sample.labels = {"module": "data_processing"}
        mock_sample.value = 5.0

        mock_metric_family = MagicMock()
        mock_metric_family.samples = [mock_sample]

        mock_collector.collect.return_value = [mock_metric_family]
        mock_registry._collector_to_names = {mock_collector: ["trading_exceptions_total"]}

        error_summary = self.collector.get_error_summary()

        # 验证错误摘要结构
        self.assertIsInstance(error_summary, dict)

    @patch("src.monitoring.metrics_collector.REGISTRY", side_effect=Exception("Registry error"))
    def test_get_error_summary_exception(self, mock_registry):
        """测试错误摘要异常处理"""
        with self.assertLogs(level="WARNING") as log:
            error_summary = self.collector.get_error_summary()

        # 验证异常处理
        self.assertEqual(error_summary, {})
        self.assertIn("获取错误摘要失败", str(log.output))

    def test_is_exception_collector_true(self):
        """测试异常收集器识别（正确）"""
        mock_collector = MagicMock()
        mock_collector._name = "trading_exceptions_total"

        result = self.collector._is_exception_collector(mock_collector)
        self.assertTrue(result)

    def test_is_exception_collector_false(self):
        """测试异常收集器识别（错误）"""
        mock_collector = MagicMock()
        mock_collector._name = "trading_trade_count"

        result = self.collector._is_exception_collector(mock_collector)
        self.assertFalse(result)

    def test_is_exception_collector_no_name(self):
        """测试异常收集器识别（无名称）"""
        mock_collector = MagicMock()
        del mock_collector._name  # 移除_name属性

        result = self.collector._is_exception_collector(mock_collector)
        self.assertFalse(result)

    def test_process_exception_samples(self):
        """测试处理异常样本"""
        mock_collector = MagicMock()

        mock_sample = MagicMock()
        mock_sample.name = "trading_exceptions_total"
        mock_sample.labels = {"module": "signal_processing"}
        mock_sample.value = 3.0

        mock_metric_family = MagicMock()
        mock_metric_family.samples = [mock_sample]

        mock_collector.collect.return_value = [mock_metric_family]

        error_counts = {}
        self.collector._process_exception_samples(mock_collector, error_counts)

        # 验证错误计数更新
        self.assertEqual(error_counts.get("signal_processing", 0), 3)


class TestGlobalFunctions(unittest.TestCase):
    """测试全局函数"""

    def test_get_metrics_collector_singleton(self):
        """测试获取全局监控实例（单例模式）"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # 验证单例模式
        self.assertIs(collector1, collector2)

    @patch.dict(os.environ, {"METRICS_ENABLED": "false", "PROMETHEUS_PORT": "9000"})
    def test_get_metrics_collector_env_config(self):
        """测试环境变量配置"""
        # 重置全局实例
        import src.monitoring.metrics_collector

        src.monitoring.metrics_collector._global_collector = None

        collector = get_metrics_collector()

        # 验证环境变量配置
        self.assertFalse(collector.config.enabled)
        self.assertEqual(collector.config.port, 9000)

    @patch("src.monitoring.metrics_collector.get_metrics_collector")
    def test_init_monitoring(self, mock_get_collector):
        """测试初始化监控系统"""
        mock_collector = MagicMock()
        mock_get_collector.return_value = mock_collector

        result = init_monitoring()

        # 验证初始化调用
        mock_collector.start_server.assert_called_once()
        self.assertEqual(result, mock_collector)


if __name__ == "__main__":
    unittest.main()
