#!/usr/bin/env python3
"""
🧪 指标收集器增强测试 - 修复版 (Metrics Collector Enhanced Tests - Fixed)

修复测试问题并提升metrics_collector.py模块测试覆盖率
当前覆盖率: 56% -> 目标: 80%+
"""

import time
import unittest
from unittest.mock import Mock, patch


from src.monitoring.metrics_collector import (
    MetricsConfig,
    TradingMetricsCollector,
    _create_fallback_prometheus_classes,
    _setup_prometheus_imports,
    get_metrics_collector,
    init_monitoring,
)


class TestMetricsConfigFixed(unittest.TestCase):
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


class TestTradingMetricsCollectorBasic(unittest.TestCase):
    """测试TradingMetricsCollector基本功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

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
        collector = TradingMetricsCollector(config)
        self.assertFalse(collector.config.enabled)

    def test_has_required_metrics(self):
        """测试是否有必需的指标"""
        collector = TradingMetricsCollector()
        # 验证关键指标存在
        self.assertTrue(hasattr(collector, "signal_latency"))
        self.assertTrue(hasattr(collector, "order_latency"))
        self.assertTrue(hasattr(collector, "data_fetch_latency"))
        self.assertTrue(hasattr(collector, "slippage"))
        self.assertTrue(hasattr(collector, "exceptions"))
        self.assertTrue(hasattr(collector, "account_balance"))
        self.assertTrue(hasattr(collector, "api_calls"))


class TestServerManagementFixed(unittest.TestCase):
    """测试服务器管理功能"""

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


class TestBasicMetricsRecording(unittest.TestCase):
    """测试基本指标记录功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_record_slippage(self):
        """测试滑点记录"""
        # 不使用Mock，直接测试方法执行
        try:
            self.collector.record_slippage(100.0, 101.0)
            # 验证没有异常
        except Exception as e:
            self.fail(f"滑点记录失败: {e}")

    def test_record_exception(self):
        """测试异常记录"""
        try:
            exception = ValueError("Test error")
            self.collector.record_exception("trading_engine", exception)
            # 验证没有异常
        except Exception as e:
            self.fail(f"异常记录失败: {e}")

    def test_update_account_balance(self):
        """测试账户余额更新"""
        try:
            self.collector.update_account_balance(5000.50)
            # 验证没有异常
        except Exception as e:
            self.fail(f"账户余额更新失败: {e}")

    def test_update_drawdown(self):
        """测试回撤更新"""
        try:
            self.collector.update_drawdown(9000.0, 10000.0)
            # 验证没有异常
        except Exception as e:
            self.fail(f"回撤更新失败: {e}")

    def test_update_position_count(self):
        """测试持仓数量更新"""
        try:
            self.collector.update_position_count(5)
            # 验证没有异常
        except Exception as e:
            self.fail(f"持仓数量更新失败: {e}")

    def test_record_api_call(self):
        """测试API调用记录"""
        try:
            self.collector.record_api_call("/api/orders", "success")
            # 验证没有异常
        except Exception as e:
            self.fail(f"API调用记录失败: {e}")


class TestContextManagersFixed(unittest.TestCase):
    """测试上下文管理器"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_measure_signal_latency_execution(self):
        """测试信号延迟测量执行"""
        try:
            with self.collector.measure_signal_latency():
                time.sleep(0.001)  # 短暂延迟
            # 验证上下文管理器正常执行
        except Exception as e:
            self.fail(f"信号延迟测量失败: {e}")

    def test_measure_order_latency_execution(self):
        """测试订单延迟测量执行"""
        try:
            with self.collector.measure_order_latency():
                time.sleep(0.001)  # 短暂延迟
            # 验证上下文管理器正常执行
        except Exception as e:
            self.fail(f"订单延迟测量失败: {e}")

    def test_measure_data_fetch_latency_execution(self):
        """测试数据获取延迟测量执行"""
        try:
            with self.collector.measure_data_fetch_latency():
                time.sleep(0.001)  # 短暂延迟
            # 验证上下文管理器正常执行
        except Exception as e:
            self.fail(f"数据获取延迟测量失败: {e}")

    def test_measure_ws_processing_time_execution(self):
        """测试WebSocket处理时间测量执行"""
        try:
            with self.collector.measure_ws_processing_time():
                time.sleep(0.001)  # 短暂延迟
            # 验证上下文管理器正常执行
        except Exception as e:
            self.fail(f"WebSocket处理时间测量失败: {e}")

    def test_measure_task_latency_execution(self):
        """测试任务延迟测量执行"""
        try:
            with self.collector.measure_task_latency("test_task"):
                time.sleep(0.001)  # 短暂延迟
            # 验证上下文管理器正常执行
        except Exception as e:
            self.fail(f"任务延迟测量失败: {e}")

    def test_context_managers_exception_handling(self):
        """测试上下文管理器的异常处理"""
        try:
            with self.collector.measure_signal_latency():
                raise ValueError("Test exception")
        except ValueError:
            pass  # 预期的异常
        except Exception as e:
            self.fail(f"上下文管理器异常处理失败: {e}")


class TestWebSocketMetricsFixed(unittest.TestCase):
    """测试WebSocket相关指标"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    @patch("time.time")
    def test_update_ws_heartbeat_age(self, mock_time):
        """测试WebSocket心跳更新"""
        mock_time.return_value = 1000.0
        try:
            self.collector.update_ws_heartbeat_age(995.0)
            # 验证没有异常
        except Exception as e:
            self.fail(f"WebSocket心跳更新失败: {e}")

    def test_observe_ws_latency(self):
        """测试WebSocket延迟观察"""
        try:
            self.collector.observe_ws_latency(0.05)
            # 验证没有异常
        except Exception as e:
            self.fail(f"WebSocket延迟观察失败: {e}")

    def test_record_ws_reconnect(self):
        """测试WebSocket重连记录"""
        try:
            self.collector.record_ws_reconnect("BTCUSDT", "network_error")
            # 验证没有异常
        except Exception as e:
            self.fail(f"WebSocket重连记录失败: {e}")

    def test_record_ws_connection_success(self):
        """测试WebSocket连接成功记录"""
        try:
            self.collector.record_ws_connection_success()
            # 验证没有异常
        except Exception as e:
            self.fail(f"WebSocket连接成功记录失败: {e}")

    def test_record_ws_connection_error(self):
        """测试WebSocket连接错误记录"""
        try:
            self.collector.record_ws_connection_error()
            # 验证没有异常
        except Exception as e:
            self.fail(f"WebSocket连接错误记录失败: {e}")

    def test_record_ws_message(self):
        """测试WebSocket消息记录"""
        try:
            self.collector.record_ws_message("ETHUSDT", "kline")
            # 验证没有异常
        except Exception as e:
            self.fail(f"WebSocket消息记录失败: {e}")


class TestPerformanceMetricsFixed(unittest.TestCase):
    """测试性能监控指标"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_record_price_update(self):
        """测试价格更新记录"""
        try:
            self.collector.record_price_update("BTCUSDT", 45000.0, "ws")
            # 验证没有异常
        except Exception as e:
            self.fail(f"价格更新记录失败: {e}")

    def test_observe_msg_lag(self):
        """测试消息延迟观察"""
        try:
            self.collector.observe_msg_lag(0.025)
            # 验证没有异常
        except Exception as e:
            self.fail(f"消息延迟观察失败: {e}")

    def test_observe_order_roundtrip_latency(self):
        """测试订单往返延迟"""
        try:
            self.collector.observe_order_roundtrip_latency(1.5)
            # 验证没有异常
        except Exception as e:
            self.fail(f"订单往返延迟失败: {e}")

    def test_update_concurrent_tasks(self):
        """测试并发任务数更新"""
        try:
            self.collector.update_concurrent_tasks("order_execution", 3)
            # 验证没有异常
        except Exception as e:
            self.fail(f"并发任务数更新失败: {e}")

    def test_observe_task_latency(self):
        """测试任务延迟观察"""
        try:
            self.collector.observe_task_latency("data_analysis", 2.3)
            # 验证没有异常
        except Exception as e:
            self.fail(f"任务延迟观察失败: {e}")


class TestMemoryMonitoringFixed(unittest.TestCase):
    """测试内存监控功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_update_process_memory_stats_execution(self):
        """测试更新进程内存统计执行"""
        try:
            self.collector.update_process_memory_stats()
            # 验证没有异常（即使psutil不可用也应该静默失败）
        except Exception as e:
            self.fail(f"进程内存统计更新失败: {e}")

    def test_record_memory_allocation(self):
        """测试内存分配记录"""
        try:
            self.collector.record_memory_allocation(1024 * 1024)  # 1MB
            # 验证没有异常
        except Exception as e:
            self.fail(f"内存分配记录失败: {e}")

    def test_update_memory_growth_rate(self):
        """测试内存增长率更新"""
        try:
            self.collector.update_memory_growth_rate(5.2)
            # 验证没有异常
        except Exception as e:
            self.fail(f"内存增长率更新失败: {e}")

    def test_update_fd_growth_rate(self):
        """测试文件描述符增长率更新"""
        try:
            self.collector.update_fd_growth_rate(0.5)
            # 验证没有异常
        except Exception as e:
            self.fail(f"文件描述符增长率更新失败: {e}")

    def test_monitor_memory_allocation_context(self):
        """测试内存分配监控上下文管理器"""
        try:
            with self.collector.monitor_memory_allocation("test_operation"):
                pass
            # 验证上下文管理器正常执行
        except Exception as e:
            self.fail(f"内存分配监控上下文失败: {e}")

    def test_get_memory_health_status(self):
        """测试获取内存健康状态"""
        try:
            status = self.collector.get_memory_health_status()
            self.assertIsInstance(status, dict)
            # 无论是否成功，都应该返回字典
        except Exception as e:
            self.fail(f"获取内存健康状态失败: {e}")


class TestTradeMonitoringFixed(unittest.TestCase):
    """测试交易监控功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_record_trade(self):
        """测试交易记录"""
        try:
            self.collector.record_trade("BTCUSDT", "BUY", 45000.0, 0.1)
            # 验证没有异常
        except Exception as e:
            self.fail(f"交易记录失败: {e}")

    def test_get_trade_summary(self):
        """测试获取交易摘要"""
        try:
            summary = self.collector.get_trade_summary()
            self.assertIsInstance(summary, dict)
            # 应该返回字典类型
        except Exception as e:
            self.fail(f"获取交易摘要失败: {e}")

    def test_record_error(self):
        """测试错误记录"""
        try:
            self.collector.record_error("network", "Connection timeout")
            # 验证没有异常
        except Exception as e:
            self.fail(f"错误记录失败: {e}")

    def test_update_price(self):
        """测试价格更新"""
        try:
            self.collector.update_price("ETHUSDT", 3000.50)
            # 验证没有异常
        except Exception as e:
            self.fail(f"价格更新失败: {e}")

    def test_get_latest_prices(self):
        """测试获取最新价格"""
        try:
            prices = self.collector.get_latest_prices()
            self.assertIsInstance(prices, dict)
            # 应该返回字典类型
        except Exception as e:
            self.fail(f"获取最新价格失败: {e}")


class TestLegacyCompatibilityFixed(unittest.TestCase):
    """测试向后兼容性功能"""

    def setUp(self):
        """设置测试"""
        self.collector = TradingMetricsCollector()

    def test_update_heartbeat(self):
        """测试心跳更新"""
        try:
            self.collector.update_heartbeat()
            # 验证没有异常
        except Exception as e:
            self.fail(f"心跳更新失败: {e}")

    def test_update_data_source_status(self):
        """测试数据源状态更新"""
        try:
            self.collector.update_data_source_status("binance", True)
            # 验证没有异常
        except Exception as e:
            self.fail(f"数据源状态更新失败: {e}")

    def test_update_memory_usage(self):
        """测试内存使用更新"""
        try:
            self.collector.update_memory_usage(150.5)
            # 验证没有异常
        except Exception as e:
            self.fail(f"内存使用更新失败: {e}")


class TestGlobalFunctions(unittest.TestCase):
    """测试全局函数"""

    def test_get_metrics_collector(self):
        """测试获取指标收集器"""
        try:
            collector = get_metrics_collector()
            self.assertIsInstance(collector, TradingMetricsCollector)
        except Exception as e:
            self.fail(f"获取指标收集器失败: {e}")

    def test_init_monitoring(self):
        """测试初始化监控"""
        try:
            collector = init_monitoring()
            self.assertIsInstance(collector, TradingMetricsCollector)
        except Exception as e:
            self.fail(f"初始化监控失败: {e}")


class TestPrometheusHelpersFixed(unittest.TestCase):
    """测试Prometheus辅助函数"""

    def test_setup_prometheus_imports(self):
        """测试Prometheus导入设置"""
        try:
            result = _setup_prometheus_imports()
            self.assertEqual(len(result), 5)
            # 应该返回5个组件（可能是实际的或回退的）
        except Exception as e:
            self.fail(f"Prometheus导入设置失败: {e}")

    def test_create_fallback_prometheus_classes(self):
        """测试创建回退Prometheus类"""
        try:
            result = _create_fallback_prometheus_classes()
            registry, counter, gauge, histogram, start_server = result

            # 测试回退类可以实例化和使用
            counter_instance = counter("test", "desc")
            gauge_instance = gauge("test", "desc")
            histogram_instance = histogram("test", "desc")

            # 测试方法调用不会报错
            counter_instance.labels().inc()
            gauge_instance.set(1.0)
            histogram_instance.observe(1.0)
            start_server(8000)

        except Exception as e:
            self.fail(f"创建回退Prometheus类失败: {e}")


if __name__ == "__main__":
    unittest.main()
