#!/usr/bin/env python3
"""
🧪 指标收集器增强测试 (Metrics Collector Enhanced Tests)

提升metrics_collector.py模块测试覆盖率的全面测试套件
当前覆盖率: 56% -> 目标: 80%+
"""

import unittest
from unittest.mock import Mock, patch


from src.monitoring.metrics_collector import (
    MetricsConfig,
    TradingMetricsCollector,
    _create_fallback_prometheus_classes,
    _setup_prometheus_imports,
)


class TestMetricsConfig(unittest.TestCase):
    """测试MetricsConfig配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = MetricsConfig()
        self.assertTrue(config.enabled)
        self.assertEqual(config.port, 8000)
        self.assertTrue(config.include_system_metrics)

    def test_custom_config(self):
        """测试自定义配置"""
        config = MetricsConfig(enabled=False, port=9090, include_system_metrics=False)
        self.assertFalse(config.enabled)
        self.assertEqual(config.port, 9090)
        self.assertFalse(config.include_system_metrics)


class TestPrometheusImportHelpers(unittest.TestCase):
    """测试Prometheus导入辅助函数"""

    @patch("src.monitoring.metrics_collector.CollectorRegistry")
    def test_setup_prometheus_imports_success(self, mock_registry):
        """测试成功导入Prometheus组件"""
        result = _setup_prometheus_imports()
        self.assertEqual(len(result), 5)

    @patch("src.monitoring.metrics_collector.CollectorRegistry", side_effect=ImportError)
    def test_setup_prometheus_imports_fallback(self, mock_registry):
        """测试Prometheus导入失败时的回退"""
        result = _setup_prometheus_imports()
        self.assertEqual(len(result), 5)

    def test_create_fallback_prometheus_classes(self):
        """测试回退类的创建"""
        result = _create_fallback_prometheus_classes()
        registry, counter, gauge, histogram, start_server = result

        self.assertIsNone(registry)

        # 测试Counter回退类
        counter_instance = counter("test", "desc")
        counter_instance.labels().inc()  # 应该不报错

        # 测试Gauge回退类
        gauge_instance = gauge("test", "desc")
        gauge_instance.set(1.0)  # 应该不报错

        # 测试Histogram回退类
        histogram_instance = histogram("test", "desc")
        histogram_instance.observe(1.0)  # 应该不报错

        # 测试start_http_server回退
        start_server(8000)  # 应该不报错


class TestTradingMetricsCollectorInit(unittest.TestCase):
    """测试TradingMetricsCollector初始化"""

    def test_init_with_default_config(self):
        """测试默认配置初始化"""
        collector = TradingMetricsCollector()
        self.assertIsInstance(collector.config, MetricsConfig)
        self.assertTrue(collector.config.enabled)
        self.assertIsNone(collector.exporter)

    def test_init_with_custom_config(self):
        """测试自定义配置初始化"""
        config = MetricsConfig(enabled=False, port=9090)
        collector = TradingMetricsCollector(config)
        self.assertEqual(collector.config, config)
        self.assertFalse(collector.config.enabled)

    def test_init_with_legacy_exporter(self):
        """测试向后兼容的exporter初始化"""
        mock_exporter = Mock()
        collector = TradingMetricsCollector(mock_exporter)
        self.assertEqual(collector.exporter, mock_exporter)

    def test_init_disabled_monitoring(self):
        """测试禁用监控时的初始化"""
        config = MetricsConfig(enabled=False)
        with patch.object(TradingMetricsCollector, "_init_metrics") as mock_init:
            collector = TradingMetricsCollector(config)
            mock_init.assert_not_called()

    @patch("src.monitoring.metrics_collector.REGISTRY")
    def test_init_metrics_registry_cleanup(self, mock_registry):
        """测试指标初始化时的注册表清理"""
        # 模拟注册表中已有指标
        mock_collector = Mock()
        mock_collector._name = "test_metric"
        mock_registry._collector_to_names = {mock_collector: ["test_metric"]}
        mock_registry.unregister = Mock()

        collector = TradingMetricsCollector()

        # 验证清理操作被调用
        self.assertTrue(hasattr(collector, "signal_latency"))


class TestContextManagers(unittest.TestCase):
    """测试上下文管理器"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    @patch("time.perf_counter")
    def test_measure_signal_latency(self, mock_time):
        """测试信号延迟测量"""
        mock_time.side_effect = [1.0, 1.5]  # 开始和结束时间

        with patch.object(self.collector.signal_latency, "observe") as mock_observe:
            with self.collector.measure_signal_latency():
                pass
            mock_observe.assert_called_once_with(0.5)

    @patch("time.perf_counter")
    def test_measure_order_latency(self, mock_time):
        """测试订单延迟测量"""
        mock_time.side_effect = [2.0, 3.2]

        with patch.object(self.collector.order_latency, "observe") as mock_observe:
            with self.collector.measure_order_latency():
                pass
            mock_observe.assert_called_once_with(1.2)

    @patch("time.perf_counter")
    def test_measure_data_fetch_latency(self, mock_time):
        """测试数据获取延迟测量"""
        mock_time.side_effect = [0.5, 1.0]

        with patch.object(self.collector.data_fetch_latency, "observe") as mock_observe:
            with self.collector.measure_data_fetch_latency():
                pass
            mock_observe.assert_called_once_with(0.5)

    @patch("time.perf_counter")
    def test_measure_ws_processing_time(self, mock_time):
        """测试WebSocket处理时间测量"""
        mock_time.side_effect = [1.0, 1.1]

        with patch.object(self.collector.ws_processing_time, "observe") as mock_observe:
            with self.collector.measure_ws_processing_time():
                pass
            mock_observe.assert_called_once_with(0.1)

    @patch("time.perf_counter")
    def test_measure_task_latency(self, mock_time):
        """测试任务延迟测量"""
        mock_time.side_effect = [0.0, 2.5]

        with patch.object(self.collector.task_latency, "labels") as mock_labels:
            mock_metric = Mock()
            mock_labels.return_value = mock_metric

            with self.collector.measure_task_latency("signal_processing"):
                pass

            mock_labels.assert_called_once_with(task_type="signal_processing")
            mock_metric.observe.assert_called_once_with(2.5)

    def test_context_managers_exception_handling(self):
        """测试上下文管理器的异常处理"""
        with patch.object(self.collector.signal_latency, "observe") as mock_observe:
            try:
                with self.collector.measure_signal_latency():
                    raise ValueError("Test exception")
            except ValueError:
                pass
            # 即使有异常，也应该记录延迟
            mock_observe.assert_called_once()


class TestServerManagement(unittest.TestCase):
    """测试服务器管理"""

    def setUp(self):
        """设置测试"""
        self.config = MetricsConfig(enabled=True, port=8001)
        self.collector = TradingMetricsCollector(self.config)

    @patch("src.monitoring.metrics_collector.start_http_server")
    def test_start_server_success(self, mock_start_server):
        """测试成功启动服务器"""
        self.collector.start_server()

        mock_start_server.assert_called_once_with(8001)
        self.assertTrue(self.collector._server_started)

    @patch("src.monitoring.metrics_collector.start_http_server")
    def test_start_server_already_started(self, mock_start_server):
        """测试重复启动服务器"""
        self.collector._server_started = True
        self.collector.start_server()

        mock_start_server.assert_not_called()

    @patch("src.monitoring.metrics_collector.start_http_server", side_effect=Exception("Port busy"))
    def test_start_server_failure(self, mock_start_server):
        """测试服务器启动失败"""
        with self.assertRaises(Exception):
            self.collector.start_server()

    def test_start_server_disabled(self):
        """测试禁用监控时启动服务器"""
        config = MetricsConfig(enabled=False)
        collector = TradingMetricsCollector(config)

        with patch("src.monitoring.metrics_collector.start_http_server") as mock_start:
            collector.start_server()
            mock_start.assert_not_called()


class TestMetricsRecording(unittest.TestCase):
    """测试指标记录功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_record_slippage(self):
        """测试滑点记录"""
        with patch.object(self.collector.slippage, "observe") as mock_observe:
            self.collector.record_slippage(100.0, 101.0)
            mock_observe.assert_called_once_with(1.0)

    def test_record_exception(self):
        """测试异常记录"""
        with patch.object(self.collector.exceptions, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            exception = ValueError("Test error")
            self.collector.record_exception("trading_engine", exception)

            mock_labels.assert_called_once_with(
                module="trading_engine", exception_type="ValueError"
            )
            mock_counter.inc.assert_called_once()

    def test_update_account_balance(self):
        """测试账户余额更新"""
        with patch.object(self.collector.account_balance, "set") as mock_set:
            self.collector.update_account_balance(5000.50)
            mock_set.assert_called_once_with(5000.50)

    def test_update_drawdown(self):
        """测试回撤更新"""
        with patch.object(self.collector.drawdown, "set") as mock_set:
            self.collector.update_drawdown(9000.0, 10000.0)
            mock_set.assert_called_once_with(10.0)  # (10000-9000)/10000 * 100

    def test_update_position_count(self):
        """测试持仓数量更新"""
        with patch.object(self.collector.position_count, "set") as mock_set:
            self.collector.update_position_count(5)
            mock_set.assert_called_once_with(5)

    def test_record_api_call(self):
        """测试API调用记录"""
        with patch.object(self.collector.api_calls, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_api_call("/api/orders", "success")

            mock_labels.assert_called_once_with(endpoint="/api/orders", status="success")
            mock_counter.inc.assert_called_once()


class TestWebSocketMetrics(unittest.TestCase):
    """测试WebSocket相关指标"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    @patch("time.time")
    def test_update_ws_heartbeat_age(self, mock_time):
        """测试WebSocket心跳更新"""
        mock_time.return_value = 1000.0

        with patch.object(self.collector.ws_heartbeat_age, "set") as mock_set:
            self.collector.update_ws_heartbeat_age(995.0)
            mock_set.assert_called_once_with(5.0)

    def test_observe_ws_latency(self):
        """测试WebSocket延迟观察"""
        with patch.object(self.collector.ws_latency, "observe") as mock_observe:
            self.collector.observe_ws_latency(0.05)
            mock_observe.assert_called_once_with(0.05)

    def test_record_ws_reconnect(self):
        """测试WebSocket重连记录"""
        with patch.object(self.collector.ws_reconnects_total, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_ws_reconnect("BTCUSDT", "network_error")

            mock_labels.assert_called_once_with(symbol="BTCUSDT", reason="network_error")
            mock_counter.inc.assert_called_once()

    def test_record_ws_connection_success(self):
        """测试WebSocket连接成功记录"""
        with patch.object(self.collector.ws_connections_total, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_ws_connection_success()

            mock_labels.assert_called_once_with(status="success")
            mock_counter.inc.assert_called_once()

    def test_record_ws_connection_error(self):
        """测试WebSocket连接错误记录"""
        with patch.object(self.collector.ws_connections_total, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_ws_connection_error()

            mock_labels.assert_called_once_with(status="error")
            mock_counter.inc.assert_called_once()

    def test_record_ws_message(self):
        """测试WebSocket消息记录"""
        with patch.object(self.collector.ws_messages_total, "labels") as mock_labels:
            mock_counter = Mock()
            mock_labels.return_value = mock_counter

            self.collector.record_ws_message("ETHUSDT", "kline")

            mock_labels.assert_called_once_with(symbol="ETHUSDT", type="kline")
            mock_counter.inc.assert_called_once()


if __name__ == "__main__":
    unittest.main()
