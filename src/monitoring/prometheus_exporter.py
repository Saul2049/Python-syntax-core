#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus Exporter (Prometheus导出器)

Provides Prometheus metrics export functionality for monitoring
"""

import logging
import threading
import time
from typing import Optional

from prometheus_client import REGISTRY, CollectorRegistry, Counter, Gauge, start_http_server

logger = logging.getLogger(__name__)


class PrometheusExporter:
    """Prometheus metrics exporter class (Prometheus指标导出器)"""

    def __init__(self, port: int = 9090, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus exporter

        Args:
            port: Listening port number
            registry: Custom registry for test isolation
        """
        self.port = port
        self.server_started = False

        # Use custom registry or create new registry for testing
        if registry is not None:
            self.registry = registry
        else:
            # Use default registry in production environment
            self.registry = REGISTRY

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

    def start(self):
        """Start Prometheus metrics export server"""
        if not self.server_started:
            try:
                # Start server with custom registry
                start_http_server(self.port, registry=self.registry)
                self.server_started = True

                # Start heartbeat thread
                if self.heartbeat_thread is None:
                    self.heartbeat_thread = threading.Thread(
                        target=self._update_heartbeat, daemon=True
                    )
                    self.heartbeat_thread.start()

                logger.info(f"Prometheus exporter started on port {self.port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
        else:
            logger.warning("Prometheus server is already running")

    def _update_heartbeat(self):
        """Background thread to update heartbeat metrics"""
        while not self.stop_heartbeat:
            now = time.time()
            self.heartbeat_age.set(now - self.last_heartbeat)
            time.sleep(1)

    def stop(self):
        """Stop the exporter"""
        self.stop_heartbeat = True
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        logger.info("Prometheus exporter stopped")


# Convenience function for backward compatibility
def get_exporter(port: int = 9090) -> PrometheusExporter:
    """
    Get singleton Prometheus exporter instance

    Args:
        port: Port number for metrics server

    Returns:
        PrometheusExporter instance
    """
    return PrometheusExporter(port=port)
