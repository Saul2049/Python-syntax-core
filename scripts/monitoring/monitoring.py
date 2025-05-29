#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Module - Backward Compatibility Layer (监控模块 - 向后兼容层)

This module maintains backward compatibility while delegating to the new modular monitoring package.
For new code, prefer importing from src.monitoring package directly.
"""

import logging
import os
import sys
import time
import warnings

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import new monitoring classes
from src.monitoring import MetricsCollector
from src.monitoring import PrometheusExporter as NewPrometheusExporter

# Set up logger
logger = logging.getLogger(__name__)

# Issue deprecation warning
warnings.warn(
    "Importing from scripts.monitoring is deprecated. "
    "Please use 'from src.monitoring import PrometheusExporter' instead.",
    DeprecationWarning,
    stacklevel=2,
)


# Backward compatibility alias
class PrometheusExporter(NewPrometheusExporter):
    """
    Legacy PrometheusExporter class for backward compatibility

    Delegates to the new src.monitoring.PrometheusExporter
    """

    def __init__(self, port: int = 9090, registry=None):
        """Initialize with legacy interface"""
        super().__init__(port=port, registry=registry)

    def record_trade(self, symbol: str, action: str):
        """
        Record a trade (legacy method)

        Args:
            symbol: Trading symbol
            action: Trade action
        """
        # Create a metrics collector to handle this
        if not hasattr(self, "_metrics_collector"):
            self._metrics_collector = MetricsCollector(self)

        self._metrics_collector.record_trade(symbol, action)

    def record_error(self, error_type: str = "general"):
        """
        Record an error (legacy method)

        Args:
            error_type: Type of error
        """
        if not hasattr(self, "_metrics_collector"):
            self._metrics_collector = MetricsCollector(self)

        self._metrics_collector.record_error("legacy_monitoring", error_type)

    def update_heartbeat(self):
        """Update heartbeat (legacy method)"""
        if not hasattr(self, "_metrics_collector"):
            self._metrics_collector = MetricsCollector(self)

        self._metrics_collector.update_heartbeat()

    def update_data_source_status(self, source_name: str, is_active: bool):
        """
        Update data source status (legacy method)

        Args:
            source_name: Name of data source
            is_active: Whether source is active
        """
        if not hasattr(self, "_metrics_collector"):
            self._metrics_collector = MetricsCollector(self)

        self._metrics_collector.update_data_source_status(source_name, is_active)

    def update_memory_usage(self, memory_mb: float):
        """
        Update memory usage (legacy method)

        Args:
            memory_mb: Memory usage in MB
        """
        if not hasattr(self, "_metrics_collector"):
            self._metrics_collector = MetricsCollector(self)

        self._metrics_collector.update_memory_usage(memory_mb)

    def update_price(self, symbol: str, price: float):
        """
        Update price (legacy method)

        Args:
            symbol: Trading symbol
            price: Current price
        """
        if not hasattr(self, "_metrics_collector"):
            self._metrics_collector = MetricsCollector(self)

        self._metrics_collector.update_price(symbol, price)


def get_exporter(port: int = 9090) -> PrometheusExporter:
    """
    Get singleton Prometheus exporter instance (legacy function)

    Args:
        port: Port number for metrics server

    Returns:
        PrometheusExporter instance
    """
    return PrometheusExporter(port=port)


# Export for backward compatibility
__all__ = ["PrometheusExporter", "get_exporter"]


if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)

    # Create exporter
    exporter = get_exporter(port=9091)
    exporter.start()

    # Record some test data
    exporter.record_trade("BTC/USDT", "BUY")
    exporter.record_trade("ETH/USDT", "SELL")
    exporter.record_error("network")
    exporter.update_data_source_status("BinanceTestnet", True)
    exporter.update_data_source_status("MockMarket", False)
    exporter.update_memory_usage(42.5)
    exporter.update_price("BTC/USDT", 30123.45)

    # Keep program running for a while
    logger.info("Test exporter started, visit http://localhost:9091/metrics to view metrics")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            # Update heartbeat every 5 seconds
            exporter.update_heartbeat()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Stopping test")
        exporter.stop()
