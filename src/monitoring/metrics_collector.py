#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metrics Collector (指标收集器)

Collects and manages trading-related metrics for monitoring
"""

import logging
import time
from typing import Dict, Optional

import psutil

from .prometheus_exporter import PrometheusExporter

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Metrics collector for trading system (交易系统指标收集器)

    Collects and records various metrics for monitoring and alerting
    """

    def __init__(self, exporter: Optional[PrometheusExporter] = None):
        """
        Initialize metrics collector

        Args:
            exporter: Prometheus exporter instance
        """
        self.exporter = exporter or PrometheusExporter()
        self.logger = logging.getLogger(f"{__name__}.MetricsCollector")

        # Internal state tracking
        self._last_prices = {}
        self._error_counts = {}
        self._trade_counts = {}

        self.logger.info("Metrics collector initialized")

    def record_trade(self, symbol: str, action: str, price: float = None, quantity: float = None):
        """
        Record a trade execution

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            action: Trade action ('buy', 'sell', 'close')
            price: Trade price (optional)
            quantity: Trade quantity (optional)
        """
        try:
            # Record trade count
            self.exporter.trade_count.labels(symbol=symbol, action=action).inc()

            # Update internal tracking
            if symbol not in self._trade_counts:
                self._trade_counts[symbol] = {}
            if action not in self._trade_counts[symbol]:
                self._trade_counts[symbol][action] = 0
            self._trade_counts[symbol][action] += 1

            # Update price if provided
            if price is not None:
                self.update_price(symbol, price)

            self.logger.info(f"Recorded trade: {action} {symbol} at {price}")

        except Exception as e:
            self.logger.error(f"Failed to record trade: {e}")
            self.record_error("trade_recording")

    def record_error(self, error_type: str = "general", details: str = None):
        """
        Record an error occurrence

        Args:
            error_type: Type of error (e.g., 'connection', 'api', 'strategy')
            details: Additional error details
        """
        try:
            self.exporter.error_count.labels(type=error_type).inc()

            # Update internal tracking
            if error_type not in self._error_counts:
                self._error_counts[error_type] = 0
            self._error_counts[error_type] += 1

            log_msg = f"Recorded error: {error_type}"
            if details:
                log_msg += f" - {details}"
            self.logger.warning(log_msg)

        except Exception as e:
            self.logger.error(f"Failed to record error: {e}")

    def update_heartbeat(self):
        """Update system heartbeat timestamp"""
        try:
            self.exporter.last_heartbeat = time.time()
            self.logger.debug("Heartbeat updated")
        except Exception as e:
            self.logger.error(f"Failed to update heartbeat: {e}")

    def update_data_source_status(self, source_name: str, is_active: bool):
        """
        Update data source status

        Args:
            source_name: Name of the data source (e.g., 'binance', 'coinbase')
            is_active: Whether the data source is currently active
        """
        try:
            status_value = 1 if is_active else 0
            self.exporter.data_source_status.labels(source_name=source_name).set(status_value)

            status_str = "active" if is_active else "inactive"
            self.logger.info(f"Data source {source_name} is {status_str}")

        except Exception as e:
            self.logger.error(f"Failed to update data source status: {e}")
            self.record_error("metrics_update")

    def update_memory_usage(self, memory_mb: Optional[float] = None):
        """
        Update memory usage metric

        Args:
            memory_mb: Memory usage in MB (auto-detected if None)
        """
        try:
            if memory_mb is None:
                # Auto-detect current process memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB

            self.exporter.memory_usage.set(memory_mb)
            self.logger.debug(f"Memory usage updated: {memory_mb:.2f} MB")

        except Exception as e:
            self.logger.error(f"Failed to update memory usage: {e}")
            self.record_error("metrics_update")

    def update_price(self, symbol: str, price: float):
        """
        Update current price for a trading symbol

        Args:
            symbol: Trading symbol
            price: Current price
        """
        try:
            self.exporter.price.labels(symbol=symbol).set(price)
            self._last_prices[symbol] = price
            self.logger.debug(f"Price updated: {symbol} = {price}")

        except Exception as e:
            self.logger.error(f"Failed to update price: {e}")
            self.record_error("metrics_update")

    def update_portfolio_value(self, total_value: float):
        """
        Update total portfolio value

        Args:
            total_value: Total portfolio value in base currency
        """
        try:
            self.exporter.portfolio_value.set(total_value)
            self.logger.info(f"Portfolio value updated: {total_value}")

        except Exception as e:
            self.logger.error(f"Failed to update portfolio value: {e}")
            self.record_error("metrics_update")

    def update_strategy_returns(self, strategy_name: str, returns_pct: float):
        """
        Update strategy performance returns

        Args:
            strategy_name: Name of the trading strategy
            returns_pct: Returns percentage
        """
        try:
            self.exporter.strategy_returns.labels(strategy_name=strategy_name).set(returns_pct)
            self.logger.info(f"Strategy {strategy_name} returns: {returns_pct:.2f}%")

        except Exception as e:
            self.logger.error(f"Failed to update strategy returns: {e}")
            self.record_error("metrics_update")

    def get_trade_summary(self) -> Dict[str, Dict[str, int]]:
        """
        Get summary of trade counts by symbol and action

        Returns:
            Dictionary with trade count summary
        """
        return self._trade_counts.copy()

    def get_error_summary(self) -> Dict[str, int]:
        """
        Get summary of error counts by type

        Returns:
            Dictionary with error count summary
        """
        return self._error_counts.copy()

    def get_latest_prices(self) -> Dict[str, float]:
        """
        Get latest recorded prices for all symbols

        Returns:
            Dictionary with latest prices
        """
        return self._last_prices.copy()

    def reset_counters(self):
        """Reset internal counters (useful for testing)"""
        self._trade_counts.clear()
        self._error_counts.clear()
        self._last_prices.clear()
        self.logger.info("Metrics counters reset")

    def start_collection(self):
        """Start the metrics collection (starts Prometheus exporter)"""
        try:
            self.exporter.start()
            self.logger.info("Metrics collection started")
        except Exception as e:
            self.logger.error(f"Failed to start metrics collection: {e}")
            self.record_error("system_startup")

    def stop_collection(self):
        """Stop the metrics collection"""
        try:
            self.exporter.stop()
            self.logger.info("Metrics collection stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop metrics collection: {e}")
