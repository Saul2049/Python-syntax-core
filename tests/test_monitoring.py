#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控模块测试
Monitoring Module Tests
"""

import unittest
from unittest.mock import patch, MagicMock

import pytest
from prometheus_client import Counter, Gauge

# 导入要测试的模块
try:
    from scripts.monitoring import PrometheusExporter, get_exporter
except ImportError:
    pytest.skip("监控模块不可用，跳过测试", allow_module_level=True)


class TestPrometheusExporter(unittest.TestCase):
    """测试Prometheus导出器类"""

    def setUp(self):
        """设置测试环境"""
        self.exporter = PrometheusExporter(port=9999)  # 使用不同端口避免冲突

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.exporter.port, 9999)
        self.assertFalse(self.exporter.server_started)
        
        # 验证指标是否正确创建
        self.assertIsInstance(self.exporter.trade_count, Counter)
        self.assertIsInstance(self.exporter.error_count, Counter)
        self.assertIsInstance(self.exporter.heartbeat_age, Gauge)
        self.assertIsInstance(self.exporter.data_source_status, Gauge)
        self.assertIsInstance(self.exporter.memory_usage, Gauge)
        self.assertIsInstance(self.exporter.price, Gauge)

    @patch('prometheus_client.start_http_server')
    def test_start(self, mock_start_server):
        """测试启动服务器"""
        # 测试首次启动
        self.exporter.start()
        mock_start_server.assert_called_once_with(9999)
        self.assertTrue(self.exporter.server_started)
        
        # 测试重复启动
        mock_start_server.reset_mock()
        self.exporter.start()
        mock_start_server.assert_not_called()  # 不应该再次调用

    def test_record_trade(self):
        """测试记录交易"""
        with patch.object(self.exporter.trade_count, 'labels') as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter
            
            self.exporter.record_trade('BTC/USDT', 'BUY')
            
            mock_labels.assert_called_once_with(symbol='BTC/USDT', action='BUY')
            mock_counter.inc.assert_called_once()

    def test_record_error(self):
        """测试记录错误"""
        with patch.object(self.exporter.error_count, 'labels') as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter
            
            # 测试默认错误类型
            self.exporter.record_error()
            mock_labels.assert_called_with(type='general')
            
            # 测试自定义错误类型
            self.exporter.record_error('network')
            mock_labels.assert_called_with(type='network')

    def test_update_heartbeat(self):
        """测试更新心跳"""
        with patch('time.time') as mock_time:
            mock_time.return_value = 12345
            self.exporter.update_heartbeat()
            self.assertEqual(self.exporter.last_heartbeat, 12345)

    def test_update_data_source_status(self):
        """测试更新数据源状态"""
        with patch.object(self.exporter.data_source_status, 'labels') as mock_labels:
            mock_gauge = MagicMock()
            mock_labels.return_value = mock_gauge
            
            # 测试激活状态
            self.exporter.update_data_source_status('BinanceTestnet', True)
            mock_labels.assert_called_with(source_name='BinanceTestnet')
            mock_gauge.set.assert_called_with(1)
            
            # 测试非激活状态
            self.exporter.update_data_source_status('MockMarket', False)
            mock_labels.assert_called_with(source_name='MockMarket')
            mock_gauge.set.assert_called_with(0)

    def test_update_memory_usage(self):
        """测试更新内存使用"""
        with patch.object(self.exporter.memory_usage, 'set') as mock_set:
            self.exporter.update_memory_usage(42.5)
            mock_set.assert_called_once_with(42.5)

    def test_update_price(self):
        """测试更新价格"""
        with patch.object(self.exporter.price, 'labels') as mock_labels:
            mock_gauge = MagicMock()
            mock_labels.return_value = mock_gauge
            
            self.exporter.update_price('BTC/USDT', 30123.45)
            mock_labels.assert_called_once_with(symbol='BTC/USDT')
            mock_gauge.set.assert_called_once_with(30123.45)

    @patch('threading.Thread')
    def test_stop(self, mock_thread):
        """测试停止"""
        # 模拟线程
        mock_thread_instance = MagicMock()
        self.exporter.heartbeat_thread = mock_thread_instance
        mock_thread_instance.is_alive.return_value = True
        
        self.exporter.stop()
        
        self.assertTrue(self.exporter.stop_heartbeat)
        mock_thread_instance.join.assert_called_once_with(timeout=2)


class TestExporterSingleton(unittest.TestCase):
    """测试导出器单例"""
    
    def test_get_exporter(self):
        """测试获取导出器实例"""
        # 清除可能的全局实例
        import scripts.monitoring
        scripts.monitoring._exporter = None
        
        # 首次调用应创建新实例
        exporter1 = get_exporter(port=8888)
        self.assertEqual(exporter1.port, 8888)
        
        # 再次调用应返回相同实例
        exporter2 = get_exporter(port=9999)  # 端口参数应被忽略
        self.assertIs(exporter1, exporter2)
        self.assertEqual(exporter2.port, 8888)  # 应保持原端口 