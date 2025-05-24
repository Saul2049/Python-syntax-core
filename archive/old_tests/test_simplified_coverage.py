#!/usr/bin/env python3
"""
简化覆盖率提升测试 (Simplified Coverage Enhancement Tests)

专门提升各模块覆盖率的测试，基于实际存在的API
"""

import numpy as np
import pandas as pd
import pytest
import os
import time
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime, timedelta

# Data transformers imports
from src.data.transformers.normalizers import DataNormalizer, normalize_data
from src.data.transformers.time_series import TimeSeriesProcessor
from src.data.transformers.splitters import DataSplitter
from src.data.transformers.missing_values import MissingValueHandler

# Brokers imports  
from src.brokers.broker import Broker
from src.brokers.exchange.client import ExchangeClient

# Monitoring imports
from src.monitoring.health_checker import HealthChecker
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.alerting import AlertManager
from src.monitoring.prometheus_exporter import PrometheusExporter


class TestDataTransformersSimplified:
    """简化的数据转换器测试"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return pd.DataFrame({
            'price': [100, 101, 102, 103, 104, 105],
            'volume': [1000, 1100, 1200, 1300, 1400, 1500]
        })

    def test_normalizer_with_sklearn_unavailable(self, sample_data):
        """测试sklearn不可用时的归一化器"""
        with patch('src.data.transformers.normalizers.HAS_SKLEARN', False):
            normalizer = DataNormalizer(method="minmax")
            result = normalizer.fit_transform(sample_data)
            assert isinstance(result, pd.DataFrame)
            
            # 测试transform方法
            result2 = normalizer.transform(sample_data)
            assert isinstance(result2, pd.DataFrame)
            
            # 测试inverse_transform方法
            restored = normalizer.inverse_transform(result)
            assert isinstance(restored, pd.DataFrame)

    def test_normalize_data_convenience_function(self, sample_data):
        """测试normalize_data便捷函数"""
        result = normalize_data(sample_data, method="minmax", feature_range=(0, 1))
        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_data.shape

    def test_time_series_processor_methods(self):
        """测试时间序列处理器的各种方法"""
        processor = TimeSeriesProcessor()
        
        # 创建测试数据
        data = pd.DataFrame({
            'value': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'price': [100, 101, 99, 102, 98, 103, 97, 104, 96, 105]
        })
        
        # 测试create_sequences
        sequences = processor.create_sequences(data['value'].values, seq_length=3)
        assert len(sequences) == 2  # X, y
        
        # 测试create_lagged_features
        lagged = processor.create_lagged_features(data, ['value'], [1, 2])
        assert 'value_lag_1' in lagged.columns
        assert 'value_lag_2' in lagged.columns
        
        # 测试create_rolling_features
        rolling = processor.create_rolling_features(data, ['value'], [3])
        assert 'value_rolling_3_mean' in rolling.columns
        
        # 测试detect_outliers_iqr
        outliers = processor.detect_outliers_iqr(data['value'])
        assert len(outliers) == len(data)
        
        # 测试remove_outliers
        cleaned = processor.remove_outliers(data, ['value'], method='iqr')
        assert isinstance(cleaned, pd.DataFrame)
        
        # 测试resample_data
        time_index_data = data.copy()
        time_index_data.index = pd.date_range('2023-01-01', periods=len(data), freq='D')
        resampled = processor.resample_data(time_index_data, '2D', 'mean')
        assert isinstance(resampled, pd.DataFrame)

    def test_data_splitter_methods(self):
        """测试数据分割器方法"""
        splitter = DataSplitter()
        data = pd.DataFrame({
            'feature': range(100),
            'target': np.random.choice([0, 1], 100)
        })
        
        # 测试train_test_split
        train, test = splitter.train_test_split(data, test_size=0.2)
        assert len(train) + len(test) == len(data)
        
        # 测试stratified_split
        train_s, test_s = splitter.stratified_split(data, 'target', test_size=0.2)
        assert len(train_s) + len(test_s) == len(data)
        
        # 测试rolling_window_split - 修正参数名称为step_size
        splits = list(splitter.rolling_window_split(data, window_size=30, step_size=10))
        assert len(splits) > 0
        
        # 测试时间序列分割 - 使用正确的API
        time_data = data.copy()
        time_data.index = range(len(time_data))  # 使用整数索引
        splits_ts = splitter.time_series_split(time_data, n_splits=3, test_size=10)
        assert len(splits_ts) > 0
        # 验证每个分割都有训练集和测试集
        for train_ts, test_ts in splits_ts:
            assert len(train_ts) > 0
            assert len(test_ts) > 0

    def test_missing_value_handler_methods(self):
        """测试缺失值处理器方法"""
        handler = MissingValueHandler()
        
        data = pd.DataFrame({
            'col1': [1, 2, np.nan, 4, 5],
            'col2': [10, np.nan, 30, 40, np.nan]
        })
        
        # 测试fill_missing_values
        filled = handler.fill_missing_values(data, method='mean')
        assert filled.isnull().sum().sum() == 0
        
        filled_median = handler.fill_missing_values(data, method='median')
        assert filled_median.isnull().sum().sum() == 0
        
        # 测试detect_missing_patterns (实际存在的方法)
        patterns = handler.detect_missing_patterns(data)
        assert isinstance(patterns, pd.DataFrame)
        
        # 测试get_missing_summary
        summary = handler.get_missing_summary(data)
        assert isinstance(summary, dict)
        assert 'total_missing' in summary


class TestBrokersSimplified:
    """简化的broker测试"""

    @pytest.fixture
    def broker_config(self):
        """broker配置"""
        return {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "telegram_token": "test_token"
        }

    @patch.dict('os.environ', {'TG_TOKEN': 'test_token', 'TG_CHAT_ID': 'test_chat_id', 'API_KEY': 'test_key', 'API_SECRET': 'test_secret'})
    def test_broker_initialization(self, broker_config):
        """测试broker初始化"""
        broker = Broker(**broker_config)
        assert broker.api_key == "test_key"
        assert broker.api_secret == "test_secret"
        assert hasattr(broker, 'position_manager')
        assert hasattr(broker, 'notifier')

    @patch.dict('os.environ', {'TG_TOKEN': 'test_token', 'TG_CHAT_ID': 'test_chat_id', 'API_KEY': 'test_key', 'API_SECRET': 'test_secret'})
    def test_broker_execute_order(self, broker_config):
        """测试broker订单执行"""
        with patch.object(Broker, '_log_trade_to_csv'), \
             patch.object(Broker, '_send_trade_notification'):
            
            broker = Broker(**broker_config)
            result = broker.execute_order("BTCUSDT", "BUY", 1.0, 50000, "test")
            
            assert isinstance(result, dict)
            assert 'order_id' in result
            assert result['symbol'] == "BTCUSDT"

    @patch.dict('os.environ', {'TG_TOKEN': 'test_token', 'TG_CHAT_ID': 'test_chat_id', 'API_KEY': 'test_key', 'API_SECRET': 'test_secret'})
    def test_broker_position_management(self, broker_config):
        """测试broker仓位管理"""
        broker = Broker(**broker_config)
        
        # 测试更新止损
        broker.update_position_stops("BTCUSDT", 50000, 1000)
        
        # 测试检查止损
        result = broker.check_stop_loss("BTCUSDT", 45000)
        assert isinstance(result, bool)

    @patch.dict('os.environ', {'TG_TOKEN': 'test_token', 'TG_CHAT_ID': 'test_chat_id', 'API_KEY': 'test_key', 'API_SECRET': 'test_secret'})
    def test_broker_trade_queries(self, broker_config):
        """测试broker交易查询"""
        with patch('pandas.read_csv', return_value=pd.DataFrame({
            'symbol': ['BTCUSDT'], 'side': ['BUY'], 'quantity': [1.0]
        })):
            broker = Broker(**broker_config)
            trades = broker.get_all_trades("BTCUSDT")
            assert isinstance(trades, pd.DataFrame)

    def test_exchange_client_initialization(self):
        """测试交易所客户端初始化"""
        client = ExchangeClient(api_key="test", api_secret="secret", demo_mode=True)
        assert client.api_key == "test"
        assert client.demo_mode is True

    def test_exchange_client_methods(self):
        """测试交易所客户端方法"""
        client = ExchangeClient(api_key="test", api_secret="secret", demo_mode=True)
        
        # 测试获取历史数据
        klines = client.get_historical_klines("BTC/USDT", "1h", limit=10)
        assert isinstance(klines, list)
        
        # 测试下单 - 使用正确的交易对格式
        order = client.place_order("BTC/USDT", "buy", 1.0, 50000)
        assert isinstance(order, dict)
        
        # 测试获取余额
        balance = client.get_account_balance()
        assert isinstance(balance, dict)


class TestMonitoringSimplified:
    """简化的监控模块测试"""

    def test_health_checker_initialization(self):
        """测试健康检查器初始化"""
        checker = HealthChecker()
        assert hasattr(checker, 'run_health_check')
        assert hasattr(checker, 'register_check')

    def test_health_checker_basic_checks(self):
        """测试健康检查器基本检查"""
        checker = HealthChecker()
        
        # 测试运行健康检查
        result = checker.run_health_check()
        assert isinstance(result, dict)
        assert 'timestamp' in result
        assert 'overall_status' in result
        assert 'checks' in result
        
        # 测试获取健康状态
        status = checker.get_health_status()
        assert isinstance(status, dict)
        
        # 测试is_healthy方法
        healthy = checker.is_healthy()
        assert isinstance(healthy, bool)

    def test_health_checker_custom_check(self):
        """测试自定义健康检查"""
        checker = HealthChecker()
        
        def custom_check():
            return True
        
        checker.register_check("custom_test", custom_check, critical=False)
        result = checker.run_health_check("custom_test")
        assert 'custom_test' in result['checks']

    def test_health_checker_monitoring(self):
        """测试健康检查监控"""
        checker = HealthChecker()
        
        # 测试启动监控
        checker.start_monitoring(interval=1)
        assert checker._running is True
        
        # 测试停止监控
        checker.stop_monitoring()
        assert checker._running is False

    def test_metrics_collector_initialization(self):
        """测试指标收集器初始化"""
        # 使用独立注册表避免冲突
        from prometheus_client import CollectorRegistry
        from src.monitoring.prometheus_exporter import PrometheusExporter
        
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        collector = MetricsCollector(exporter=exporter)
        
        assert hasattr(collector, 'record_trade')
        assert hasattr(collector, 'record_error')

    def test_metrics_collector_trade_recording(self):
        """测试指标收集器交易记录"""
        # 使用独立注册表避免冲突
        from prometheus_client import CollectorRegistry
        from src.monitoring.prometheus_exporter import PrometheusExporter
        
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        collector = MetricsCollector(exporter=exporter)
        
        # 测试记录交易 - 使用正确的参数
        collector.record_trade("BTCUSDT", "buy", 1.0, 50000)
        
        # 测试记录错误
        collector.record_error("test_error", "Test error message")
        
        # 测试获取错误摘要
        error_summary = collector.get_error_summary()
        assert isinstance(error_summary, dict)

    def test_alert_manager_initialization(self):
        """测试告警管理器初始化"""
        alert_manager = AlertManager()
        assert hasattr(alert_manager, 'add_alert_rule')
        assert hasattr(alert_manager, 'check_alerts')

    def test_alert_manager_rules(self):
        """测试告警管理器规则"""
        alert_manager = AlertManager()
        
        # 定义条件函数
        def high_cpu_condition():
            return True  # 简单的条件
        
        # 添加告警规则 - 使用正确的参数
        alert_manager.add_alert_rule("high_cpu", high_cpu_condition)
        
        # 检查告警
        alerts = alert_manager.check_alerts()
        assert isinstance(alerts, list)

    def test_prometheus_exporter_initialization(self):
        """测试Prometheus导出器初始化"""
        from src.monitoring.prometheus_exporter import PrometheusExporter
        exporter = PrometheusExporter(port=9091)  # 使用不同端口避免冲突
        
        # 检查实际存在的属性和方法
        assert hasattr(exporter, 'port')
        assert hasattr(exporter, 'start')  # 实际存在的方法
        assert hasattr(exporter, 'stop')
        assert hasattr(exporter, 'trade_count')
        assert hasattr(exporter, 'error_count')

    def test_prometheus_exporter_metrics(self):
        """测试Prometheus导出器指标"""
        from src.monitoring.prometheus_exporter import PrometheusExporter
        from prometheus_client import CollectorRegistry
        
        # 使用独立的registry避免冲突
        test_registry = CollectorRegistry()
        exporter = PrometheusExporter(port=9092, registry=test_registry)
        
        # 测试实际存在的指标操作
        assert hasattr(exporter, 'trade_count')
        assert hasattr(exporter, 'error_count')
        assert hasattr(exporter, 'heartbeat_age')
        
        # 测试指标计数功能
        # 测试trade_count是否可以正常使用
        try:
            exporter.trade_count.labels(symbol='BTCUSDT', action='buy').inc()
            # 如果没有异常说明指标正常工作
            assert True
        except Exception as e:
            assert False, f"指标操作失败: {e}"
        
        # 测试heartbeat_age设置
        try:
            exporter.heartbeat_age.set(1.0)
            assert True
        except Exception as e:
            assert False, f"Gauge指标操作失败: {e}"


class TestIntegrationSimplified:
    """简化的集成测试"""

    def test_full_data_pipeline(self):
        """测试完整数据处理流水线"""
        # 创建测试数据
        data = pd.DataFrame({
            'price': [100, 101, np.nan, 103, 104],
            'volume': [1000, np.nan, 1200, 1300, 1400]
        })
        
        # 1. 处理缺失值
        handler = MissingValueHandler()
        clean_data = handler.fill_missing_values(data, method='mean')
        assert clean_data.isnull().sum().sum() == 0
        
        # 2. 归一化
        normalizer = DataNormalizer(method='minmax')
        normalized = normalizer.fit_transform(clean_data)
        assert normalized.min().min() >= 0
        assert normalized.max().max() <= 1
        
        # 3. 分割数据
        splitter = DataSplitter()
        train, test = splitter.train_test_split(normalized, test_size=0.4)
        assert len(train) + len(test) == len(normalized)

    def test_monitoring_integration(self):
        """测试监控组件集成"""
        # 使用独立注册表避免冲突
        from prometheus_client import CollectorRegistry
        from src.monitoring.prometheus_exporter import PrometheusExporter
        
        # 初始化组件
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        metrics_collector = MetricsCollector(exporter=exporter)
        health_checker = HealthChecker()
        
        # 记录一些指标
        metrics_collector.record_trade("BTCUSDT", "buy", 1.0, 50000)
        metrics_collector.record_error("test", "test error")
        
        # 运行健康检查
        health_result = health_checker.run_health_check()
        assert isinstance(health_result, dict)
        
        # 获取错误摘要
        errors = metrics_collector.get_error_summary()
        assert isinstance(errors, dict)

    @patch.dict('os.environ', {'TG_TOKEN': 'test_token', 'TG_CHAT_ID': 'test_chat_id', 'API_KEY': 'test_key', 'API_SECRET': 'test_secret'})
    def test_broker_monitoring_integration(self):
        """测试broker与监控的集成"""
        # 使用独立注册表避免冲突
        from prometheus_client import CollectorRegistry
        from src.monitoring.prometheus_exporter import PrometheusExporter
        
        # 创建broker
        broker = Broker(
            api_key="test",
            api_secret="secret", 
            telegram_token="token"
        )
        
        # 创建监控
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        metrics_collector = MetricsCollector(exporter=exporter)
        
        # 模拟交易并记录指标
        with patch.object(broker, '_log_trade_to_csv'), \
             patch.object(broker, '_send_trade_notification'):
            
            result = broker.execute_order("BTCUSDT", "BUY", 1.0, 50000)
            
            # 记录交易指标
            metrics_collector.record_trade("BTCUSDT", "buy", 1.0, 50000)
            
            assert isinstance(result, dict)
            
        # 获取错误摘要（验证指标收集器工作正常）
        errors = metrics_collector.get_error_summary()
        assert isinstance(errors, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 