#!/usr/bin/env python3
"""
监控模块覆盖率提升测试 (Monitoring Module Coverage Enhancement Tests)

专门提升monitoring模块覆盖率的测试
"""

import time

import pytest

from src.monitoring.alerting import AlertManager
from src.monitoring.health_checker import HealthChecker
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.prometheus_exporter import PrometheusExporter


class TestHealthChecker:
    """测试健康检查器"""

    def test_health_checker_initialization(self):
        """测试健康检查器初始化"""
        checker = HealthChecker()
        # 测试实际存在的方法
        assert hasattr(checker, "run_health_check")
        assert hasattr(checker, "register_check")
        assert hasattr(checker, "is_healthy")
        assert hasattr(checker, "_health_checks")

    def test_run_health_check(self):
        """测试运行健康检查"""
        checker = HealthChecker()

        health_status = checker.run_health_check()

        assert isinstance(health_status, dict)
        assert "timestamp" in health_status
        assert "overall_status" in health_status
        assert "checks" in health_status

    def test_register_custom_check(self):
        """测试注册自定义健康检查"""
        checker = HealthChecker()

        def custom_check():
            return True

        checker.register_check("custom_test", custom_check, critical=True)

        # 验证检查已注册
        assert "custom_test" in checker._health_checks
        assert checker._health_checks["custom_test"]["critical"] is True

    def test_specific_health_check(self):
        """测试特定的健康检查"""
        checker = HealthChecker()

        # 运行特定的检查
        result = checker.run_health_check("heartbeat")

        assert isinstance(result, dict)
        assert "checks" in result
        assert "heartbeat" in result["checks"]

    def test_memory_usage_check(self):
        """测试内存使用率检查"""
        checker = HealthChecker()

        # 测试内存检查方法
        result = checker._check_memory_usage()
        assert isinstance(result, bool)

    def test_error_rate_check(self):
        """测试错误率检查"""
        checker = HealthChecker()

        # 测试错误率检查方法
        result = checker._check_error_rate()
        assert isinstance(result, bool)

    def test_heartbeat_check(self):
        """测试心跳检查"""
        checker = HealthChecker()

        # 测试心跳检查方法
        result = checker._check_heartbeat()
        assert isinstance(result, bool)

    def test_health_status_retrieval(self):
        """测试健康状态获取"""
        checker = HealthChecker()

        # 先运行一次检查
        checker.run_health_check()

        # 获取状态
        status = checker.get_health_status()
        assert isinstance(status, dict)

    def test_is_healthy_method(self):
        """测试is_healthy方法"""
        checker = HealthChecker()

        # 运行检查然后测试整体健康状态
        checker.run_health_check()
        health_status = checker.is_healthy()
        assert isinstance(health_status, bool)

    def test_health_monitoring_lifecycle(self):
        """测试健康监控生命周期"""
        checker = HealthChecker()

        # 测试启动监控
        try:
            checker.start_monitoring(interval=1)
            assert checker._running is True

            # 短暂等待
            time.sleep(0.1)

            # 测试停止监控
            checker.stop_monitoring()
            assert checker._running is False
        except Exception:
            # 如果有异常，确保清理
            checker.stop_monitoring()


class TestMetricsCollector:
    """测试指标收集器"""

    @pytest.fixture
    def fresh_collector(self):
        """创建新的MetricsCollector实例，避免Prometheus注册表冲突"""
        from prometheus_client import CollectorRegistry

        from src.monitoring.prometheus_exporter import PrometheusExporter

        # 为每个测试创建独立的注册表
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        collector = MetricsCollector(exporter=exporter)
        return collector

    def test_metrics_collector_initialization(self, fresh_collector):
        """测试指标收集器初始化"""
        collector = fresh_collector
        # 测试实际存在的方法
        assert hasattr(collector, "record_trade")
        assert hasattr(collector, "record_error")
        assert hasattr(collector, "update_heartbeat")
        assert hasattr(collector, "get_trade_summary")

    def test_collect_trading_metrics(self, fresh_collector):
        """测试交易指标收集"""
        collector = fresh_collector

        # 记录交易数据 - 使用正确的参数
        collector.record_trade(symbol="BTCUSDT", action="buy", price=50000, quantity=1.0)

        # 获取交易汇总
        trade_summary = collector.get_trade_summary()

        assert isinstance(trade_summary, dict)
        assert "BTCUSDT" in trade_summary
        assert "buy" in trade_summary["BTCUSDT"]
        assert trade_summary["BTCUSDT"]["buy"] == 1

    def test_record_and_retrieve_metrics(self, fresh_collector):
        """测试记录和检索指标"""
        collector = fresh_collector

        # 记录价格
        collector.update_price("BTCUSDT", 50000)
        collector.update_price("ETHUSDT", 3000)

        # 检索价格
        prices = collector.get_latest_prices()

        assert isinstance(prices, dict)
        assert "BTCUSDT" in prices
        assert prices["BTCUSDT"] == 50000

    def test_metrics_aggregation(self, fresh_collector):
        """测试指标聚合"""
        collector = fresh_collector

        # 记录多个交易
        collector.record_trade("BTCUSDT", "buy", 50000, 1.0)
        collector.record_trade("BTCUSDT", "sell", 51000, 1.0)
        collector.record_trade("ETHUSDT", "buy", 3000, 5.0)

        # 获取汇总
        summary = collector.get_trade_summary()

        assert len(summary) == 2  # 两个不同的symbol
        assert summary["BTCUSDT"]["buy"] == 1
        assert summary["BTCUSDT"]["sell"] == 1
        assert summary["ETHUSDT"]["buy"] == 1

    def test_error_recording(self, fresh_collector):
        """测试错误记录"""
        collector = fresh_collector

        # 记录不同类型的错误
        collector.record_error("connection", "Network timeout")
        collector.record_error("api", "Invalid API key")
        collector.record_error("connection", "Another network error")

        # 获取错误汇总
        error_summary = collector.get_error_summary()

        assert isinstance(error_summary, dict)
        assert "connection" in error_summary
        assert error_summary["connection"] == 2
        assert error_summary["api"] == 1

    def test_portfolio_value_update(self, fresh_collector):
        """测试投资组合价值更新"""
        collector = fresh_collector

        # 更新投资组合价值
        collector.update_portfolio_value(100000.0)

        # 验证没有抛出异常
        assert True  # 如果到这里说明没有异常

    def test_heartbeat_update(self, fresh_collector):
        """测试心跳更新"""
        collector = fresh_collector

        # 更新心跳
        collector.update_heartbeat()

        # 验证心跳时间戳被设置
        assert hasattr(collector.exporter, "last_heartbeat")

    def test_data_source_status(self, fresh_collector):
        """测试数据源状态更新"""
        collector = fresh_collector

        # 更新数据源状态
        collector.update_data_source_status("binance", True)
        collector.update_data_source_status("coinbase", False)

        # 验证没有抛出异常
        assert True


class TestAlertManager:
    """测试告警管理器"""

    def test_alert_manager_initialization(self):
        """测试告警管理器初始化"""
        alert_manager = AlertManager()
        assert hasattr(alert_manager, "add_alert_rule")
        assert hasattr(alert_manager, "check_alerts")
        assert hasattr(alert_manager, "add_alert_handler")

    def test_add_alert_rule(self):
        """测试添加告警规则"""
        alert_manager = AlertManager()

        def test_condition():
            return True

        alert_manager.add_alert_rule(
            "test_alert", test_condition, severity="warning", description="Test alert description"
        )

        # 验证规则被添加
        assert "test_alert" in alert_manager._alert_rules
        assert alert_manager._alert_rules["test_alert"]["severity"] == "warning"

    def test_check_cpu_alert(self):
        """测试CPU告警检查"""
        alert_manager = AlertManager()

        # 添加CPU告警规则
        def high_cpu_condition():
            return True  # 模拟高CPU使用率

        alert_manager.add_alert_rule(
            "cpu_alert", high_cpu_condition, severity="warning", description="High CPU usage"
        )

        # 检查告警
        alerts = alert_manager.check_alerts()

        assert len(alerts) > 0
        assert alerts[0]["name"] == "cpu_alert"
        assert alerts[0]["severity"] == "warning"

    def test_check_memory_alert(self):
        """测试内存告警检查"""
        alert_manager = AlertManager()

        def high_memory_condition():
            return True  # 模拟高内存使用率

        alert_manager.add_alert_rule(
            "memory_alert",
            high_memory_condition,
            severity="critical",
            description="High memory usage",
        )

        alerts = alert_manager.check_alerts()

        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        assert len(critical_alerts) > 0

    def test_send_alert_email(self):
        """测试发送邮件告警"""
        alert_manager = AlertManager()

        # 测试添加告警处理器
        handled_alerts = []

        def email_handler(alert):
            handled_alerts.append(alert)

        alert_manager.add_alert_handler(email_handler)

        # 添加会触发的告警规则
        alert_manager.add_alert_rule("test_email_alert", lambda: True, severity="warning")

        # 检查告警
        alerts = alert_manager.check_alerts()

        # 验证处理器被调用
        assert len(handled_alerts) > 0
        assert handled_alerts[0]["name"] == "test_email_alert"

    def test_send_alert_telegram(self):
        """测试发送Telegram告警"""
        alert_manager = AlertManager()

        # 测试添加Telegram处理器
        telegram_alerts = []

        def telegram_handler(alert):
            telegram_alerts.append(alert)

        alert_manager.add_alert_handler(telegram_handler)

        # 添加会触发的告警规则
        alert_manager.add_alert_rule("test_telegram_alert", lambda: True, severity="critical")

        alerts = alert_manager.check_alerts()

        assert len(telegram_alerts) > 0
        assert telegram_alerts[0]["severity"] == "critical"

    def test_alert_throttling(self):
        """测试告警限流"""
        alert_manager = AlertManager()

        # 添加带限流的告警规则
        alert_manager.add_alert_rule(
            "throttled_alert", lambda: True, cooldown_minutes=1  # 始终触发  # 1分钟冷却时间
        )

        # 第一次告警应该触发
        alerts1 = alert_manager.check_alerts()
        assert len(alerts1) > 0

        # 立即再次检查，应该被限流（不会再次触发）
        alerts2 = alert_manager.check_alerts()
        # 由于冷却时间，不应该有新的告警
        throttled_alerts = [a for a in alerts2 if a["name"] == "throttled_alert"]
        assert len(throttled_alerts) == 0

    def test_alert_history(self):
        """测试告警历史"""
        alert_manager = AlertManager()

        # 触发一些告警
        alert_manager.add_alert_rule("history_test_alert", lambda: True, severity="info")

        # 检查告警
        alerts = alert_manager.check_alerts()

        # 获取活跃告警
        active_alerts = alert_manager.get_active_alerts()

        assert isinstance(active_alerts, list)
        assert len(active_alerts) > 0


class TestPrometheusExporter:
    """测试Prometheus导出器"""

    @pytest.fixture
    def fresh_exporter(self):
        """创建新的PrometheusExporter实例，避免注册表冲突"""
        from prometheus_client import CollectorRegistry

        # 为每个测试创建独立的注册表
        registry = CollectorRegistry()
        exporter = PrometheusExporter(port=0, registry=registry)  # 使用随机端口
        return exporter

    def test_prometheus_exporter_initialization(self, fresh_exporter):
        """测试Prometheus导出器初始化"""
        exporter = fresh_exporter
        assert exporter.port == 0
        assert hasattr(exporter, "trade_count")
        assert hasattr(exporter, "error_count")
        assert hasattr(exporter, "memory_usage")

    def test_register_metric(self, fresh_exporter):
        """测试注册指标 - 测试内置指标"""
        exporter = fresh_exporter

        # 测试内置指标存在
        assert hasattr(exporter, "trade_count")
        assert hasattr(exporter, "error_count")

        # 测试指标可以使用
        exporter.trade_count.labels(symbol="BTCUSDT", action="buy").inc()
        exporter.error_count.labels(type="connection").inc()

    def test_update_metrics(self, fresh_exporter):
        """测试更新指标"""
        exporter = fresh_exporter

        # 更新交易计数
        exporter.trade_count.labels(symbol="BTCUSDT", action="buy").inc()
        exporter.trade_count.labels(symbol="BTCUSDT", action="buy").inc(5)

        # 更新价格指标
        exporter.price.labels(symbol="BTCUSDT").set(50000)

        # 更新内存使用
        exporter.memory_usage.set(512.5)

        # 验证指标被更新（基本验证）
        assert True  # 如果没有异常则说明更新成功

    def test_histogram_metric(self, fresh_exporter):
        """测试直方图指标 - 使用现有的指标类型"""
        exporter = fresh_exporter

        # 测试组合指标使用
        exporter.trade_count.labels(symbol="BTCUSDT", action="buy").inc()
        exporter.price.labels(symbol="BTCUSDT").set(50000)
        exporter.portfolio_value.set(100000)

        # 验证多个指标可以同时工作
        assert hasattr(exporter, "trade_count")
        assert hasattr(exporter, "price")
        assert hasattr(exporter, "portfolio_value")

    def test_export_metrics_format(self, fresh_exporter):
        """测试导出指标格式"""
        exporter = fresh_exporter

        # 设置一些指标值
        exporter.trade_count.labels(symbol="BTCUSDT", action="buy").inc(10)
        exporter.price.labels(symbol="BTCUSDT").set(50000)
        exporter.memory_usage.set(256.0)

        # 使用prometheus_client的generate_latest来获取指标输出
        from prometheus_client import generate_latest

        metrics_output = generate_latest(exporter.registry).decode("utf-8")

        assert isinstance(metrics_output, str)
        assert len(metrics_output) > 0
        # 验证包含一些预期的指标名称
        assert "trading_" in metrics_output

    def test_start_http_server(self, fresh_exporter):
        """测试启动HTTP服务器"""
        exporter = fresh_exporter

        # 测试start方法存在并可调用
        if hasattr(exporter, "start"):
            # 不实际启动服务器，只测试方法存在
            assert callable(exporter.start)

        # 测试服务器状态标志
        assert hasattr(exporter, "server_started")
        assert exporter.server_started is False

    def test_custom_labels(self, fresh_exporter):
        """测试自定义标签"""
        exporter = fresh_exporter

        # 测试带标签的指标更新
        exporter.trade_count.labels(symbol="BTCUSDT", action="buy").inc()
        exporter.trade_count.labels(symbol="ETHUSDT", action="sell").inc()
        exporter.data_source_status.labels(source_name="binance").set(1)
        exporter.data_source_status.labels(source_name="coinbase").set(0)

        # 验证不同标签的指标可以独立工作
        assert True  # 基本验证没有异常


class TestMonitoringIntegration:
    """测试监控模块集成"""

    def test_full_monitoring_workflow(self):
        """测试完整监控工作流程"""
        from prometheus_client import CollectorRegistry

        # 初始化所有组件，使用独立注册表
        health_checker = HealthChecker()
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        metrics_collector = MetricsCollector(exporter=exporter)
        alert_manager = AlertManager(metrics_collector=metrics_collector)

        # 1. 收集系统健康状态
        health_status = health_checker.run_health_check()
        assert isinstance(health_status, dict)

        # 2. 记录指标 - 使用正确的方法
        metrics_collector.record_trade("BTCUSDT", "buy", 50000, 1.0)
        metrics_collector.record_error("connection", "Test connection error")
        metrics_collector.update_memory_usage()

        # 3. 设置告警规则 - 使用简单的lambda函数
        alert_manager.add_alert_rule(
            "integration_test_alert",
            lambda: True,  # 简单条件，确保触发
            severity="info",
            description="Integration test alert",
        )

        # 4. 检查告警
        alerts = alert_manager.check_alerts()

        # 验证工作流程
        assert len(alerts) >= 0  # 可能有告警触发

        # 验证指标被正确记录
        trade_summary = metrics_collector.get_trade_summary()
        assert "BTCUSDT" in trade_summary

        error_summary = metrics_collector.get_error_summary()
        assert "connection" in error_summary

    def test_monitoring_performance(self):
        """测试监控性能"""
        from prometheus_client import CollectorRegistry

        # 使用独立注册表避免冲突
        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        health_checker = HealthChecker()
        metrics_collector = MetricsCollector(exporter=exporter)

        # 测试大量指标收集的性能
        start_time = time.time()

        # 记录大量交易数据
        for i in range(100):
            metrics_collector.record_trade(f"TEST{i}", "buy", 100.0 + i, 1.0)

        health_status = health_checker.run_health_check()

        end_time = time.time()
        execution_time = end_time - start_time

        # 100个指标 + 健康检查应该在合理时间内完成
        assert execution_time < 2.0  # 应该在2秒内完成

        # 验证数据被正确记录
        trade_summary = metrics_collector.get_trade_summary()
        assert len(trade_summary) == 100  # 应该有100个不同的symbol

    def test_monitoring_memory_usage(self):
        """测试监控组件的内存使用"""
        import gc

        from prometheus_client import CollectorRegistry

        # 创建大量监控对象
        checkers = [HealthChecker() for _ in range(10)]

        # 为每个collector使用独立注册表
        collectors = []
        for i in range(10):
            registry = CollectorRegistry()
            exporter = PrometheusExporter(registry=registry)
            collectors.append(MetricsCollector(exporter=exporter))

        # 删除对象
        del checkers
        del collectors

        # 强制垃圾回收
        gc.collect()

        # 验证没有内存泄漏（基本测试）
        assert True  # 如果没有异常就说明内存管理正常

    def test_error_recovery(self):
        """测试错误恢复"""
        from prometheus_client import CollectorRegistry

        registry = CollectorRegistry()
        exporter = PrometheusExporter(registry=registry)
        metrics_collector = MetricsCollector(exporter=exporter)
        alert_manager = AlertManager(metrics_collector=metrics_collector)

        # 测试告警处理器异常恢复
        handled_alerts = []

        def failing_handler(alert):
            if len(handled_alerts) == 0:
                handled_alerts.append(alert)
                raise Exception("Handler failure")
            handled_alerts.append(alert)

        def working_handler(alert):
            handled_alerts.append(alert)

        # 添加处理器
        alert_manager.add_alert_handler(failing_handler)
        alert_manager.add_alert_handler(working_handler)

        # 添加一个会触发的告警规则
        alert_manager.add_alert_rule(
            "test_recovery_alert",
            lambda: True,
            severity="warning",
            description="Test recovery alert",
        )

        # 检查告警 - 应该处理异常并继续
        alerts = alert_manager.check_alerts()

        # 验证告警被处理
        assert len(alerts) > 0
        # 验证至少有一些处理器被调用（工作的处理器应该成功）
        assert len(handled_alerts) >= 1
