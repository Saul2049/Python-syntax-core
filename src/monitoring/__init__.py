#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Package (监控包)

Provides comprehensive monitoring and metrics collection for trading systems
"""

from .metrics_collector import TradingMetricsCollector, get_metrics_collector, init_monitoring

# 向后兼容别名
MetricsCollector = TradingMetricsCollector

try:
    from .alerting import AlertManager
except ImportError:
    AlertManager = None

try:
    from .health_checker import HealthChecker
except ImportError:
    HealthChecker = None

try:
    from .prometheus_exporter import PrometheusExporter
except ImportError:
    PrometheusExporter = None


# Convenience function for quick setup
def get_monitoring_system(port: int = 8000, enable_alerts: bool = False):
    """
    Get a complete monitoring system setup

    Args:
        port: Prometheus exporter port
        enable_alerts: Whether to enable alerting

    Returns:
        Dictionary with monitoring components
    """
    collector = get_metrics_collector()

    components = {
        "collector": collector,
    }

    return components


__all__ = [
    "TradingMetricsCollector",
    "MetricsCollector",  # 向后兼容
    "get_metrics_collector",
    "init_monitoring",
    "get_monitoring_system",
]
