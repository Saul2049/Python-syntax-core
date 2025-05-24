#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Package (监控包)

Provides comprehensive monitoring and metrics collection for trading systems
"""

from .alerting import AlertManager
from .health_checker import HealthChecker
from .metrics_collector import MetricsCollector
from .prometheus_exporter import PrometheusExporter


# Convenience function for quick setup
def get_monitoring_system(port: int = 9090, enable_alerts: bool = True):
    """
    Get a complete monitoring system setup

    Args:
        port: Prometheus exporter port
        enable_alerts: Whether to enable alerting

    Returns:
        Dictionary with monitoring components
    """
    exporter = PrometheusExporter(port=port)
    collector = MetricsCollector(exporter)
    health_checker = HealthChecker(collector)

    components = {"exporter": exporter, "collector": collector, "health_checker": health_checker}

    if enable_alerts:
        alert_manager = AlertManager(collector)
        components["alert_manager"] = alert_manager

    return components


__all__ = [
    "PrometheusExporter",
    "MetricsCollector",
    "HealthChecker",
    "AlertManager",
    "get_monitoring_system",
]
