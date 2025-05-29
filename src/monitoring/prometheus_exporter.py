#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus Exporter (Prometheus导出器)

Provides Prometheus metrics export functionality for monitoring
"""

import logging
import time
from typing import Optional

try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, start_http_server
except ImportError:
    CollectorRegistry = None
    start_http_server = None

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """Prometheus metrics exporter class (Prometheus指标导出器)"""

    def __init__(self, port: int = 8000, registry: Optional[object] = None):
        """
        Initialize Prometheus exporter

        Args:
            port: Listening port number
            registry: Custom registry for test isolation
        """
        self.port = port
        self.registry = registry or (CollectorRegistry() if CollectorRegistry else None)
        self.logger = logging.getLogger(__name__)
        self._server_started = False

        # Initialize metrics with duplicate check
        self._initialize_metrics()

        # Last heartbeat time
        self.last_heartbeat = time.time()

        # Start heartbeat update thread
        self.heartbeat_thread = None
        self.stop_heartbeat = False

        logger.info(f"Initialized Prometheus metrics exporter on port: {port}")

    def _initialize_metrics(self):
        """Initialize metrics with duplicate checking"""
        try:
            # Trade count metrics
            self.trade_count = Counter(
                "trading_trade_count_total",
                "Total number of trades",
                ["symbol", "action"],  # Labels: trading pair and action type
                registry=self.registry,
            )

            # Error counter
            self.error_count = Counter(
                "trading_error_count_total",
                "Total number of errors",
                ["type"],  # Labels: error type
                registry=self.registry,
            )

            # Heartbeat age
            self.heartbeat_age = Gauge(
                "trading_heartbeat_age_seconds",
                "Seconds since last heartbeat",
                registry=self.registry,
            )

            # Data source status metrics
            self.data_source_status = Gauge(
                "trading_data_source_status",
                "Data source status: 1=active, 0=inactive",
                ["source_name"],  # Labels: data source name
                registry=self.registry,
            )

            # Memory usage
            self.memory_usage = Gauge(
                "trading_memory_usage_mb", "Memory usage in MB", registry=self.registry
            )

            # Trading pair prices
            self.price = Gauge(
                "trading_price",
                "Current price",
                ["symbol"],  # Labels: trading pair
                registry=self.registry,
            )

            # Portfolio metrics
            self.portfolio_value = Gauge(
                "trading_portfolio_value", "Current portfolio value", registry=self.registry
            )

            # Strategy performance metrics
            self.strategy_returns = Gauge(
                "trading_strategy_returns",
                "Strategy returns percentage",
                ["strategy_name"],
                registry=self.registry,
            )

            # 🔥 M5-W2: GC Performance Metrics
            self.gc_collections_total = Counter(
                "gc_collections_total",
                "Total number of GC collections",
                ["generation"],  # Labels: GC generation (0, 1, 2)
                registry=self.registry,
            )

            self.gc_collected_objects = Counter(
                "gc_collected_objects_total",
                "Total number of objects collected by GC",
                ["generation"],
                registry=self.registry,
            )

            self.gc_pause_duration_seconds = Gauge(
                "gc_pause_duration_seconds",
                "Current GC pause duration in seconds",
                ["generation"],
                registry=self.registry,
            )

            self.gc_objects_tracked = Gauge(
                "gc_objects_tracked",
                "Number of objects currently tracked by GC",
                ["generation"],
                registry=self.registry,
            )

            # Memory optimization metrics
            self.cache_hit_rate = Gauge(
                "cache_hit_rate",
                "Cache hit rate percentage",
                ["cache_type"],  # Labels: ma, atr, window
                registry=self.registry,
            )

            self.memory_allocation_rate = Gauge(
                "memory_allocation_rate_per_second",
                "Memory allocation rate per second",
                registry=self.registry,
            )

        except ValueError as e:
            if "Duplicated timeseries" in str(e):
                logger.warning(f"Metrics already registered: {e}")
                # Try to get existing metrics from registry
                self._get_existing_metrics()
            else:
                raise e

    def _get_existing_metrics(self):
        """Get existing metrics from registry"""
        # Define metric name mappings
        metric_mappings = {
            "trading_trade_count_total": "trade_count",
            "trading_error_count_total": "error_count",
            "trading_heartbeat_age_seconds": "heartbeat_age",
            "trading_data_source_status": "data_source_status",
            "trading_memory_usage_mb": "memory_usage",
            "trading_price": "price",
            "trading_portfolio_value": "portfolio_value",
            "trading_strategy_returns": "strategy_returns",
        }

        # Find and assign existing metrics
        self._assign_existing_metrics(metric_mappings)

        # Create fallback metrics for any missing ones
        if not self._all_metrics_found(metric_mappings.values()):
            self._create_fallback_metrics()

    def _assign_existing_metrics(self, metric_mappings: dict):
        """Assign existing metrics from registry"""
        for collector in list(self.registry._collector_to_names.keys()):
            if hasattr(collector, "_name"):
                name = collector._name
                if name in metric_mappings:
                    attr_name = metric_mappings[name]
                    setattr(self, attr_name, collector)

    def _all_metrics_found(self, metric_attributes: list) -> bool:
        """Check if all required metrics were found"""
        return all(hasattr(self, attr) for attr in metric_attributes)

    def _create_fallback_metrics(self):
        """Create fallback metrics with unique names"""
        unique_id = id(self)

        self.trade_count = Counter(
            f"trading_trade_count_total_{unique_id}",
            "Total number of trades",
            ["symbol", "action"],
            registry=self.registry,
        )

        self.error_count = Counter(
            f"trading_error_count_total_{unique_id}",
            "Total number of errors",
            ["type"],
            registry=self.registry,
        )

        self.heartbeat_age = Gauge(
            f"trading_heartbeat_age_seconds_{unique_id}",
            "Seconds since last heartbeat",
            registry=self.registry,
        )

        self.data_source_status = Gauge(
            f"trading_data_source_status_{unique_id}",
            "Data source status: 1=active, 0=inactive",
            ["source_name"],
            registry=self.registry,
        )

        self.memory_usage = Gauge(
            f"trading_memory_usage_mb_{unique_id}", "Memory usage in MB", registry=self.registry
        )

        self.price = Gauge(
            f"trading_price_{unique_id}", "Current price", ["symbol"], registry=self.registry
        )

        self.portfolio_value = Gauge(
            f"trading_portfolio_value_{unique_id}",
            "Current portfolio value",
            registry=self.registry,
        )

        self.strategy_returns = Gauge(
            f"trading_strategy_returns_{unique_id}",
            "Strategy returns percentage",
            ["strategy_name"],
            registry=self.registry,
        )

        # 🔥 M5-W2: GC Performance Metrics
        self.gc_collections_total = Counter(
            f"gc_collections_total_{unique_id}",
            "Total number of GC collections",
            ["generation"],  # Labels: GC generation (0, 1, 2)
            registry=self.registry,
        )

        self.gc_collected_objects = Counter(
            f"gc_collected_objects_total_{unique_id}",
            "Total number of objects collected by GC",
            ["generation"],
            registry=self.registry,
        )

        self.gc_pause_duration_seconds = Gauge(
            f"gc_pause_duration_seconds_{unique_id}",
            "Current GC pause duration in seconds",
            ["generation"],
            registry=self.registry,
        )

        self.gc_objects_tracked = Gauge(
            f"gc_objects_tracked_{unique_id}",
            "Number of objects currently tracked by GC",
            ["generation"],
            registry=self.registry,
        )

        # Memory optimization metrics
        self.cache_hit_rate = Gauge(
            f"cache_hit_rate_{unique_id}",
            "Cache hit rate percentage",
            ["cache_type"],  # Labels: ma, atr, window
            registry=self.registry,
        )

        self.memory_allocation_rate = Gauge(
            f"memory_allocation_rate_per_second_{unique_id}",
            "Memory allocation rate per second",
            registry=self.registry,
        )

    def start_server(self) -> bool:
        """Start Prometheus metrics export server"""
        if self._server_started:
            return True

        try:
            if start_http_server:
                start_http_server(self.port, registry=self.registry)
                self._server_started = True
                self.logger.info(f"Prometheus exporter started on port {self.port}")
                return True
            else:
                self.logger.warning("prometheus_client未安装，无法启动服务器")
                return False
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus server: {e}")
            return False

    def _update_heartbeat(self):
        """Background thread to update heartbeat metrics"""
        while not self.stop_heartbeat:
            now = time.time()
            self.heartbeat_age.set(now - self.last_heartbeat)
            time.sleep(1)

    def stop_server(self) -> bool:
        """Stop the exporter"""
        self.stop_heartbeat = True
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        self.logger.info("Prometheus exporter stopped")
        self._server_started = False
        return True


# Convenience function for backward compatibility
def get_exporter(port: int = 8000) -> PrometheusExporter:
    """
    Get singleton Prometheus exporter instance

    Args:
        port: Port number for metrics server

    Returns:
        PrometheusExporter instance
    """
    return PrometheusExporter(port=port)
