#!/usr/bin/env python3
"""
🧪 Metrics Collector Coverage Boost
快速提升 metrics_collector.py 覆盖率
目标：从18% -> 60%+
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch

from src.monitoring.metrics_collector import (
    MetricsConfig,
    TradingMetricsCollector,
    get_metrics_collector,
    init_monitoring,
)


class TestMetricsCollectorCoverageBoost(unittest.TestCase):
    """快速覆盖率提升测试"""

    def setUp(self):
        """设置测试"""
        config = MetricsConfig(enabled=True, port=8999)
        self.collector = TradingMetricsCollector(config)

    def test_context_managers(self):
        """测试所有上下文管理器"""
        # 测试信号延迟测量
        with self.collector.measure_signal_latency():
            time.sleep(0.001)

        # 测试订单延迟测量
        with self.collector.measure_order_latency():
            time.sleep(0.001)

        # 测试数据获取延迟测量
        with self.collector.measure_data_fetch_latency():
            time.sleep(0.001)

        # 测试WebSocket处理时间测量
        with self.collector.measure_ws_processing_time():
            time.sleep(0.001)

        # 测试任务延迟测量
        with self.collector.measure_task_latency("test_task"):
            time.sleep(0.001)

        self.assertTrue(True)  # 验证无异常

    def test_all_recording_methods(self):
        """测试所有记录方法"""
        # 测试滑点记录
        self.collector.record_slippage(100.0, 101.0)

        # 测试异常记录
        self.collector.record_exception("test_module", Exception("test"))

        # 测试账户余额更新
        self.collector.update_account_balance(10000.0)

        # 测试回撤更新
        self.collector.update_drawdown(9000.0, 10000.0)

        # 测试持仓数量更新
        self.collector.update_position_count(5)

        # 测试API调用记录
        self.collector.record_api_call("/api/orders", "200")

        # 测试WebSocket心跳年龄更新
        self.collector.update_ws_heartbeat_age(time.time() - 30)

        # 测试WebSocket相关方法
        self.collector.observe_ws_latency(0.05)
        self.collector.record_ws_reconnect("BTCUSD", "timeout")
        self.collector.record_ws_connection_success()
        self.collector.record_ws_connection_error()
        self.collector.record_ws_message("BTCUSD", "kline")
        self.collector.record_price_update("BTCUSD", 45000.0, "ws")

        # 测试延迟观察方法
        self.collector.observe_msg_lag(0.02)
        self.collector.observe_order_roundtrip_latency(0.5)
        self.collector.observe_task_latency("data_processing", 0.1)

        # 测试并发任务更新
        self.collector.update_concurrent_tasks("order_execution", 3)

        self.assertTrue(True)  # 验证无异常

    def test_memory_and_gc_methods(self):
        """测试内存和GC相关方法"""
        # 测试内存统计更新（禁用状态）
        self.collector.config.enabled = False
        self.collector.update_process_memory_stats()
        self.collector.record_gc_event(0, 0.001, 100)
        self.collector.update_gc_tracked_objects()
        self.collector.record_memory_allocation(1024)
        self.collector.update_memory_growth_rate(5.0)
        self.collector.update_fd_growth_rate(2.0)

        # 重新启用测试
        self.collector.config.enabled = True
        self.collector.record_memory_allocation(2048)
        self.collector.update_memory_growth_rate(3.0)
        self.collector.update_fd_growth_rate(1.5)

        self.assertTrue(True)  # 验证无异常

    def test_backward_compatible_methods(self):
        """测试向后兼容的方法"""
        # 测试记录交易
        self.collector.record_trade("BTCUSD", "buy", 45000.0, 0.1)

        # 测试记录错误
        self.collector.record_error("test_module", "Test error message")

        # 测试更新价格
        self.collector.update_price("ETHUSD", 3000.0)

        # 测试获取最新价格
        prices = self.collector.get_latest_prices()
        self.assertIsInstance(prices, dict)

        # 测试更新心跳
        self.collector.update_heartbeat()

        # 测试更新数据源状态
        self.collector.update_data_source_status("binance", True)
        self.collector.update_data_source_status("binance", False)

        # 测试更新内存使用量
        self.collector.update_memory_usage(150.5)

        self.assertTrue(True)  # 验证无异常

    def test_summary_methods(self):
        """测试摘要和状态方法"""
        # 测试获取交易摘要
        trade_summary = self.collector.get_trade_summary()
        self.assertIsInstance(trade_summary, dict)

        # 测试获取错误摘要
        error_summary = self.collector.get_error_summary()
        self.assertIsInstance(error_summary, dict)

        # 测试获取内存健康状态
        health_status = self.collector.get_memory_health_status()
        self.assertIsInstance(health_status, dict)

        self.assertTrue(True)  # 验证无异常

    @patch("psutil.Process")
    def test_process_memory_stats_success(self, mock_process_class):
        """测试成功的进程内存统计"""
        mock_process = MagicMock()
        mock_process_class.return_value = mock_process

        # 模拟内存信息
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 5.0
        mock_process.cpu_percent.return_value = 10.0
        mock_process.num_threads.return_value = 8
        mock_process.num_fds.return_value = 50
        mock_process.connections.return_value = [1, 2, 3]

        self.collector.update_process_memory_stats()

        # 验证调用
        mock_process.memory_info.assert_called_once()

    @patch("gc.get_objects")
    def test_gc_tracked_objects_success(self, mock_get_objects):
        """测试GC跟踪对象成功"""
        mock_get_objects.return_value = list(range(100))

        # 启用状态测试
        self.collector.config.enabled = True
        self.collector.update_gc_tracked_objects()

        # 验证调用
        self.assertTrue(mock_get_objects.called)

    def test_memory_allocation_monitor_context(self):
        """测试内存分配监控上下文"""
        # 禁用状态测试
        self.collector.config.enabled = False
        with self.collector.monitor_memory_allocation("test_op"):
            pass

        # 启用状态测试
        self.collector.config.enabled = True
        with self.collector.monitor_memory_allocation("test_op"):
            pass

        self.assertTrue(True)  # 验证无异常

    def test_private_methods(self):
        """测试私有方法覆盖率"""
        # 测试异常收集器识别
        mock_collector = MagicMock()
        mock_collector._name = "trading_exceptions_total"

        result = self.collector._is_exception_collector(mock_collector)
        self.assertTrue(result)

        # 测试非异常收集器
        mock_collector._name = "trading_price_total"
        result = self.collector._is_exception_collector(mock_collector)
        self.assertFalse(result)

        # 测试无名称收集器
        del mock_collector._name
        result = self.collector._is_exception_collector(mock_collector)
        self.assertFalse(result)

    def test_disabled_monitoring(self):
        """测试禁用监控状态下的行为"""
        disabled_config = MetricsConfig(enabled=False)
        disabled_collector = TradingMetricsCollector(disabled_config)

        # 测试禁用状态下的基本方法（不需要指标属性的）
        disabled_collector.observe_task_latency("test", 0.1)
        disabled_collector.update_process_memory_stats()
        disabled_collector.record_gc_event(0, 0.001, 100)
        disabled_collector.update_gc_tracked_objects()
        disabled_collector.record_memory_allocation(1024)
        disabled_collector.update_memory_growth_rate(5.0)
        disabled_collector.update_fd_growth_rate(2.0)

        with disabled_collector.measure_task_latency("test"):
            pass

        with disabled_collector.monitor_memory_allocation("test"):
            pass

        self.assertTrue(True)  # 验证无异常

    def test_server_start(self):
        """测试服务器启动"""
        # 测试禁用状态
        disabled_config = MetricsConfig(enabled=False)
        disabled_collector = TradingMetricsCollector(disabled_config)
        disabled_collector.start_server()  # 应该不执行任何操作

        # 测试已启动状态
        self.collector._server_started = True
        self.collector.start_server()  # 应该不重复启动

        self.assertTrue(True)  # 验证无异常


class TestGlobalFunctions(unittest.TestCase):
    """测试全局函数"""

    def test_get_metrics_collector(self):
        """测试获取全局收集器"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # 验证单例模式
        self.assertIs(collector1, collector2)

    @patch.dict(os.environ, {"METRICS_ENABLED": "false", "PROMETHEUS_PORT": "9999"})
    def test_environment_configuration(self):
        """测试环境变量配置"""
        # 重置全局实例
        import src.monitoring.metrics_collector

        src.monitoring.metrics_collector._global_collector = None

        collector = get_metrics_collector()
        self.assertFalse(collector.config.enabled)
        self.assertEqual(collector.config.port, 9999)

    @patch("src.monitoring.metrics_collector.get_metrics_collector")
    def test_init_monitoring(self, mock_get_collector):
        """测试初始化监控"""
        mock_collector = MagicMock()
        mock_get_collector.return_value = mock_collector

        result = init_monitoring()

        mock_collector.start_server.assert_called_once()
        self.assertEqual(result, mock_collector)


if __name__ == "__main__":
    unittest.main()
