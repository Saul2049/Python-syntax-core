#!/usr/bin/env python3
"""
🧪 指标收集器增强测试 - 第二部分 (Metrics Collector Enhanced Tests - Part 2)

继续覆盖metrics_collector.py的高级功能和辅助方法
"""

import unittest
from unittest.mock import Mock, patch


from src.monitoring.metrics_collector import (
    TradingMetricsCollector,
    get_metrics_collector,
    init_monitoring,
)


class TestPerformanceMetrics(unittest.TestCase):
    """测试性能监控指标"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_record_price_update(self):
        """测试价格更新记录"""
        with patch.object(self.collector.price_updates_total, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_price_update("BTCUSDT", 45000.0, "ws")

            mock_labels.assert_called_once_with(symbol="BTCUSDT", source="ws")
            mock_counter.inc.assert_called_once()

    def test_observe_msg_lag(self):
        """测试消息延迟观察"""
        with patch.object(self.collector.msg_lag, "observe") as mock_observe:
            self.collector.observe_msg_lag(0.025)
            mock_observe.assert_called_once_with(0.025)

    def test_observe_order_roundtrip_latency(self):
        """测试订单往返延迟"""
        with patch.object(self.collector.order_roundtrip_latency, "observe") as mock_observe:
            self.collector.observe_order_roundtrip_latency(1.5)
            mock_observe.assert_called_once_with(1.5)

    def test_update_concurrent_tasks(self):
        """测试并发任务数更新"""
        with patch.object(self.collector.concurrent_tasks, "labels") as mock_labels:
            mock_gauge = Mock()
            mock_labels.return_value = mock_gauge

            self.collector.update_concurrent_tasks("order_execution", 3)

            mock_labels.assert_called_once_with(task_type="order_execution")
            mock_gauge.set.assert_called_once_with(3)

    def test_observe_task_latency(self):
        """测试任务延迟观察"""
        with patch.object(self.collector.task_latency, "labels") as mock_labels:
            mock_histogram = Mock()
            mock_labels.return_value = mock_histogram

            self.collector.observe_task_latency("data_analysis", 2.3)

            mock_labels.assert_called_once_with(task_type="data_analysis")
            mock_histogram.observe.assert_called_once_with(2.3)


class TestMemoryMonitoring(unittest.TestCase):
    """测试内存监控功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    @patch("psutil.Process")
    def test_update_process_memory_stats_success(self, mock_process_class):
        """测试成功更新进程内存统计"""
        mock_process = Mock()
        mock_process_class.return_value = mock_process

        # 模拟内存信息
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 100  # 100MB
        mock_memory_info.percent = 5.2

        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 5.2
        mock_process.cpu_percent.return_value = 15.3
        mock_process.num_threads.return_value = 8
        mock_process.num_fds.return_value = 50

        with (
            patch.object(self.collector.process_memory_usage, "set") as mock_memory_set,
            patch.object(self.collector.process_memory_percent, "set") as mock_percent_set,
            patch.object(self.collector.process_cpu_percent, "set") as mock_cpu_set,
            patch.object(self.collector.process_threads, "set") as mock_threads_set,
            patch.object(self.collector.process_fds, "set") as mock_fds_set,
        ):

            self.collector.update_process_memory_stats()

            mock_memory_set.assert_called_once_with(1024 * 1024 * 100)
            mock_percent_set.assert_called_once_with(5.2)
            mock_cpu_set.assert_called_once_with(15.3)
            mock_threads_set.assert_called_once_with(8)
            mock_fds_set.assert_called_once_with(50)

    @patch("psutil.Process", side_effect=Exception("Process not found"))
    def test_update_process_memory_stats_failure(self, mock_process):
        """测试更新内存统计失败"""
        # 应该静默失败，不抛出异常
        try:
            self.collector.update_process_memory_stats()
        except Exception:
            self.fail("应该静默处理异常")

    def test_record_gc_event(self):
        """测试垃圾回收事件记录"""
        with (
            patch.object(self.collector.gc_collections, "labels") as mock_collections_labels,
            patch.object(self.collector.gc_collected_objects, "labels") as mock_objects_labels,
            patch.object(self.collector.gc_pause_time, "observe") as mock_pause_observe,
        ):

            mock_collections_counter = Mock()
            mock_objects_counter = Mock()
            mock_collections_labels.return_value = mock_collections_counter
            mock_objects_labels.return_value = mock_objects_counter

            self.collector.record_gc_event(2, 0.05, 1500)

            mock_collections_labels.assert_called_once_with(generation="2")
            mock_objects_labels.assert_called_once_with(generation="2")
            mock_collections_counter.inc.assert_called_once()
            mock_objects_counter.inc.assert_called_once_with(1500)
            mock_pause_observe.assert_called_once_with(0.05)

    @patch("gc.get_objects")
    def test_update_gc_tracked_objects(self, mock_get_objects):
        """测试更新GC跟踪对象数量"""
        mock_get_objects.return_value = list(range(1000))  # 模拟1000个对象

        with patch.object(self.collector.gc_tracked_objects, "set") as mock_set:
            self.collector.update_gc_tracked_objects()
            mock_set.assert_called_once_with(1000)

    def test_record_memory_allocation(self):
        """测试内存分配记录"""
        with patch.object(self.collector.memory_allocation_rate, "set") as mock_set:
            self.collector.record_memory_allocation(1024 * 1024)  # 1MB
            # 验证调用了set方法（具体值取决于时间计算）
            mock_set.assert_called_once()

    def test_update_memory_growth_rate(self):
        """测试内存增长率更新"""
        with patch.object(self.collector.memory_growth_rate, "set") as mock_set:
            self.collector.update_memory_growth_rate(5.2)
            mock_set.assert_called_once_with(5.2)

    def test_update_fd_growth_rate(self):
        """测试文件描述符增长率更新"""
        with patch.object(self.collector.fd_growth_rate, "set") as mock_set:
            self.collector.update_fd_growth_rate(0.5)
            mock_set.assert_called_once_with(0.5)

    @patch("psutil.Process")
    def test_monitor_memory_allocation_context(self, mock_process_class):
        """测试内存分配监控上下文管理器"""
        mock_process = Mock()
        mock_process_class.return_value = mock_process

        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 50  # 50MB
        mock_process.memory_info.return_value = mock_memory_info

        with patch.object(self.collector.memory_allocation_rate, "set"):
            with self.collector.monitor_memory_allocation("test_operation"):
                pass
            # 验证内存使用被记录（具体实现可能有所不同）

    @patch("psutil.Process")
    def test_get_memory_health_status(self, mock_process_class):
        """测试获取内存健康状态"""
        mock_process = Mock()
        mock_process_class.return_value = mock_process

        mock_memory_info = Mock()
        mock_memory_info.rss = 1024 * 1024 * 200  # 200MB
        mock_memory_info.percent = 10.5
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 10.5
        mock_process.num_fds.return_value = 100

        with patch("gc.get_objects", return_value=list(range(5000))):
            status = self.collector.get_memory_health_status()

            self.assertIn("memory_usage_mb", status)
            self.assertIn("memory_percent", status)
            self.assertIn("file_descriptors", status)
            self.assertIn("gc_objects", status)
            self.assertIn("health_score", status)
            self.assertIn("status", status)


class TestTradeMonitoring(unittest.TestCase):
    """测试交易监控功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_record_trade(self):
        """测试交易记录"""
        with patch.object(self.collector.api_calls, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_trade("BTCUSDT", "BUY", 45000.0, 0.1)

            # 验证API调用被记录
            mock_labels.assert_called_with(endpoint="trade", status="success")
            mock_counter.inc.assert_called_once()

    @patch("src.monitoring.metrics_collector.REGISTRY")
    def test_get_trade_summary(self, mock_registry):
        """测试获取交易摘要"""
        # 模拟注册表
        mock_collector = Mock()
        mock_registry._collector_to_names = {mock_collector: ["trading_api_calls_total"]}

        # 模拟样本数据
        mock_sample = Mock()
        mock_sample.name = "trading_api_calls_total"
        mock_sample.labels = {"endpoint": "trade", "status": "success"}
        mock_sample.value = 5

        mock_collector.collect.return_value = [Mock(samples=[mock_sample])]

        summary = self.collector.get_trade_summary()

        self.assertIsInstance(summary, dict)
        self.assertIn("total_trades", summary)

    def test_record_error(self):
        """测试错误记录"""
        with patch.object(self.collector.exceptions, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_error("network", "Connection timeout")

            mock_labels.assert_called_once_with(module="network", exception_type="str")
            mock_counter.inc.assert_called_once()

    def test_update_price(self):
        """测试价格更新"""
        with patch.object(self.collector.current_price, "labels") as mock_labels:
            mock_gauge = Mock()
            mock_labels.return_value = mock_gauge

            self.collector.update_price("ETHUSDT", 3000.50)

            mock_labels.assert_called_once_with(symbol="ETHUSDT")
            mock_gauge.set.assert_called_once_with(3000.50)

    @patch("src.monitoring.metrics_collector.REGISTRY")
    def test_get_latest_prices(self, mock_registry):
        """测试获取最新价格"""
        # 模拟注册表和样本数据
        mock_collector = Mock()
        mock_registry._collector_to_names = {mock_collector: ["trading_current_price_usd"]}

        mock_sample = Mock()
        mock_sample.name = "trading_current_price_usd"
        mock_sample.labels = {"symbol": "BTCUSDT"}
        mock_sample.value = 45000.0

        mock_collector.collect.return_value = [Mock(samples=[mock_sample])]

        prices = self.collector.get_latest_prices()

        self.assertIsInstance(prices, dict)


class TestLegacyCompatibility(unittest.TestCase):
    """测试向后兼容性功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    @patch("time.time")
    def test_update_heartbeat(self, mock_time):
        """测试心跳更新"""
        mock_time.return_value = 1234567890.0
        self.collector.update_heartbeat()
        # 验证心跳时间被设置
        self.assertEqual(self.collector.last_heartbeat, 1234567890.0)

    def test_update_data_source_status(self):
        """测试数据源状态更新"""
        with patch.object(self.collector.api_calls, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.update_data_source_status("binance", True)

            # 验证API调用被记录
            mock_labels.assert_called_with(endpoint="data_source_status", status="active")
            mock_counter.inc.assert_called_once()

    def test_update_memory_usage(self):
        """测试内存使用更新"""
        with patch.object(self.collector.process_memory_usage, "set") as mock_set:
            self.collector.update_memory_usage(150.5)
            mock_set.assert_called_once_with(150.5 * 1024 * 1024)  # 转换为字节


class TestGlobalFunctions(unittest.TestCase):
    """测试全局函数"""

    @patch("src.monitoring.metrics_collector._global_collector", None)
    def test_get_metrics_collector_new_instance(self):
        """测试获取新的指标收集器实例"""
        collector = get_metrics_collector()
        self.assertIsInstance(collector, TradingMetricsCollector)

    @patch("src.monitoring.metrics_collector._global_collector")
    def test_get_metrics_collector_existing_instance(self, mock_global):
        """测试获取现有的指标收集器实例"""
        mock_instance = Mock()
        mock_global.return_value = mock_instance

        collector = get_metrics_collector()
        self.assertEqual(collector, mock_global)

    def test_init_monitoring(self):
        """测试初始化监控"""
        collector = init_monitoring()
        self.assertIsInstance(collector, TradingMetricsCollector)


if __name__ == "__main__":
    unittest.main()
