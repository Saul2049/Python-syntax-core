#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Package (监控包)

Provides comprehensive monitoring and metrics collection for trading systems
"""

from .metrics_collector import TradingMetricsCollector, get_metrics_collector, init_monitoring

# ---------------------------------------------------------------------------
# Export aliases
# ---------------------------------------------------------------------------

# "MetricsCollector" remains an alias to the concrete implementation class –
# **this is required** for legacy code that imported the class directly:
#   >>> from src.monitoring import MetricsCollector
# ---------------------------------------------------------------------------
MetricsCollector = TradingMetricsCollector

# Tests expect ``src.monitoring.metrics_collector`` to resolve to the *module*
# object, not the class.  Setting it to the class broke ``unittest.mock.patch``
# look-ups such as
#   patch("src.monitoring.metrics_collector.start_http_server")
# which consequently searched for the attribute on the class and failed.
# Here we explicitly expose the *sub-module* instead, while keeping the class
# alias above for backwards compatibility.
import sys as _sys  # local import to avoid polluting package namespace

# The sub-module is already imported by the ``from .metrics_collector import ...``
# statement at the top of this file, therefore it is guaranteed to be present
# in ``sys.modules``.
metrics_collector = _sys.modules[__name__ + ".metrics_collector"]  # type: ignore[assignment]
del _sys

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


def get_monitoring_system(*, port: int = 9090, enable_alerts: bool = True):
    """Create and wire a *monitoring stack* (监控系统).

    Parameters
    ----------
    port : int | str | None, default ``9090``
        Listening port forwarded verbatim to :class:`PrometheusExporter`.
    enable_alerts : Any, default ``True``
        Truthy value decides whether an :class:`AlertManager` instance is created.

    Returns
    -------
    dict
        A mapping that always contains ``exporter``, ``collector`` and
        ``health_checker``.  ``alert_manager`` is only present when
        *enable_alerts* evaluates to ``True``.
    """

    # 1️⃣ Prometheus exporter – must be first (tests assert call-order)
    exporter = PrometheusExporter(port=port)

    # 2️⃣ Metrics collector wired to exporter (legacy alias is MetricsCollector)
    collector = MetricsCollector(exporter)  # type: ignore[arg-type]

    # 3️⃣ Health checker observes the metrics collector
    health_checker = HealthChecker(collector)

    components = {
        "exporter": exporter,
        "collector": collector,
        "health_checker": health_checker,
    }

    # 4️⃣ Optional alert manager
    if bool(enable_alerts):
        if AlertManager is None:
            raise RuntimeError("AlertManager dependency is missing – cannot enable alerts")
        components["alert_manager"] = AlertManager(collector)  # type: ignore[arg-type]

    return components


__all__ = [
    # Core public classes
    "PrometheusExporter",
    "MetricsCollector",
    "HealthChecker",
    "AlertManager",
    # Aliases / helper factories
    "TradingMetricsCollector",
    "metrics_collector",
    "get_metrics_collector",
    "init_monitoring",
    "get_monitoring_system",
]
