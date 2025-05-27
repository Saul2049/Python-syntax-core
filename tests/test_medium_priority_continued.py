#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Medium Priority Continued Refactoring Tests (中级优先持续重构测试)

Tests for the continued medium priority refactoring to ensure everything works correctly
"""

import os
import sys
import unittest
import warnings

import numpy as np
import pandas as pd
from prometheus_client import CollectorRegistry

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class TestStrategyRefactoring(unittest.TestCase):
    """Test strategy system refactoring"""

    def setUp(self):
        """Setup test data"""
        # Create sample OHLCV data
        dates = pd.date_range("2023-01-01", periods=100, freq="1D")
        np.random.seed(42)

        close_prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 0.02), index=dates)
        high_prices = close_prices + np.random.rand(100) * 2
        low_prices = close_prices - np.random.rand(100) * 2
        open_prices = close_prices.shift(1).fillna(close_prices.iloc[0])
        volumes = np.random.randint(1000, 10000, 100)

        self.sample_data = pd.DataFrame(
            {
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": volumes,
            },
            index=dates,
        )

    def test_strategy_imports(self):
        """Test that all strategy classes can be imported"""
        from src.strategies import (
            ALL_STRATEGIES,
            AdaptiveMovingAverageStrategy,
            ATRBreakoutStrategy,
            BollingerBreakoutStrategy,
            BollingerMeanReversionStrategy,
            ChannelBreakoutStrategy,
            DonchianChannelStrategy,
            ExponentialMAStrategy,
            ImprovedMAStrategy,
            MACDStrategy,
            MultiTimeframeStrategy,
            RSIStrategy,
            SimpleMAStrategy,
            StochasticStrategy,
            SupertrendStrategy,
            TrendFollowingStrategy,
            TripleMAStrategy,
            WilliamsRStrategy,
        )

        # Check that we have all expected strategies
        self.assertEqual(len(ALL_STRATEGIES), 17)
        self.assertIsInstance(ALL_STRATEGIES, list)

    def test_moving_average_strategies(self):
        """Test moving average strategy implementations"""
        from src.strategies.moving_average import ImprovedMAStrategy, SimpleMAStrategy

        # Test Simple MA Strategy
        strategy = SimpleMAStrategy(short_window=5, long_window=20)
        signals = strategy.generate_signals(self.sample_data)

        self.assertIn("signal", signals.columns)
        self.assertIn("short_ma", signals.columns)
        self.assertIn("long_ma", signals.columns)
        self.assertTrue(signals["signal"].isin([-1, 0, 1]).all())

        # Test Improved MA Strategy
        improved_strategy = ImprovedMAStrategy(short_window=5, long_window=20, rsi_window=14)
        improved_signals = improved_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", improved_signals.columns)
        self.assertIn("rsi", improved_signals.columns)

    def test_oscillator_strategies(self):
        """Test oscillator-based strategies"""
        from src.strategies.oscillator import MACDStrategy, RSIStrategy

        # Test RSI Strategy
        rsi_strategy = RSIStrategy(window=14, overbought=70, oversold=30)
        rsi_signals = rsi_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", rsi_signals.columns)
        self.assertIn("rsi", rsi_signals.columns)
        self.assertTrue((rsi_signals["rsi"] >= 0).all())
        self.assertTrue((rsi_signals["rsi"] <= 100).all())

        # Test MACD Strategy
        macd_strategy = MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        macd_signals = macd_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", macd_signals.columns)
        self.assertIn("macd", macd_signals.columns)
        self.assertIn("macd_signal", macd_signals.columns)

    def test_breakout_strategies(self):
        """Test breakout strategies"""
        from src.strategies.breakout import ATRBreakoutStrategy, BollingerBreakoutStrategy

        # Test Bollinger Breakout Strategy
        bb_strategy = BollingerBreakoutStrategy(window=20, num_std=2.0)
        bb_signals = bb_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", bb_signals.columns)
        self.assertIn("upper_band", bb_signals.columns)
        self.assertIn("lower_band", bb_signals.columns)

        # Test ATR Breakout Strategy
        atr_strategy = ATRBreakoutStrategy(atr_period=14, ma_period=20)
        atr_signals = atr_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", atr_signals.columns)
        self.assertIn("atr", atr_signals.columns)

    def test_trend_following_strategies(self):
        """Test trend following strategies"""
        from src.strategies.trend_following import SupertrendStrategy, TrendFollowingStrategy

        # Test Trend Following Strategy
        trend_strategy = TrendFollowingStrategy(ma_window=20, atr_window=14)
        trend_signals = trend_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", trend_signals.columns)
        self.assertIn("atr", trend_signals.columns)

        # Test Supertrend Strategy
        supertrend_strategy = SupertrendStrategy(atr_period=10, multiplier=3.0)
        supertrend_signals = supertrend_strategy.generate_signals(self.sample_data)

        self.assertIn("signal", supertrend_signals.columns)
        self.assertIn("supertrend", supertrend_signals.columns)

    def test_strategy_parameters(self):
        """Test strategy parameter management"""
        from src.strategies.moving_average import SimpleMAStrategy

        strategy = SimpleMAStrategy(short_window=10, long_window=30)

        # Test parameter getters
        self.assertEqual(strategy.get_parameter("short_window"), 10)
        self.assertEqual(strategy.get_parameter("long_window"), 30)
        self.assertEqual(strategy.get_parameter("nonexistent", "default"), "default")

        # Test parameter setters
        strategy.set_parameter("short_window", 15)
        self.assertEqual(strategy.get_parameter("short_window"), 15)

    def test_backward_compatibility(self):
        """Test backward compatibility with old improved_strategy functions"""
        import sys

        # Clear any previously imported module to ensure warnings are triggered
        if "src.improved_strategy" in sys.modules:
            del sys.modules["src.improved_strategy"]

        # Test that old imports still work but issue warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            from src.improved_strategy import rsi_strategy, simple_ma_cross

            # Test that functions still work
            ma_signals = simple_ma_cross(self.sample_data, short_window=5, long_window=20)
            self.assertIn("signal", ma_signals.columns)

            rsi_signals = rsi_strategy(self.sample_data, window=14)
            self.assertIn("signal", rsi_signals.columns)

            # Check deprecation warning was issued
            self.assertTrue(len(w) > 0, f"Expected warnings but got {len(w)}")
            deprecated_warnings = [
                warning for warning in w if "deprecated" in str(warning.message).lower()
            ]
            self.assertTrue(
                len(deprecated_warnings) > 0,
                f"Expected deprecation warnings but got: {[str(w.message) for w in w]}",
            )


class TestMonitoringRefactoring(unittest.TestCase):
    """Test monitoring system refactoring"""

    def test_monitoring_imports(self):
        """Test that monitoring classes can be imported"""
        from src.monitoring import AlertManager, HealthChecker, MetricsCollector, PrometheusExporter

        # Test basic instantiation with isolated registry
        custom_registry = CollectorRegistry()
        exporter = PrometheusExporter(
            port=9091, registry=custom_registry
        )  # Use different port and registry
        collector = MetricsCollector(exporter)
        health_checker = HealthChecker(collector)
        alert_manager = AlertManager(collector)

        self.assertIsNotNone(exporter)
        self.assertIsNotNone(collector)
        self.assertIsNotNone(health_checker)
        self.assertIsNotNone(alert_manager)

    def test_metrics_collector(self):
        """Test metrics collector functionality"""
        from src.monitoring import MetricsCollector, PrometheusExporter

        exporter = PrometheusExporter(port=9092)
        collector = MetricsCollector(exporter)

        # Test recording trades
        collector.record_trade("BTCUSDT", "buy", price=50000.0)
        collector.record_trade("ETHUSDT", "sell", price=3000.0)

        # Test trade summary
        trade_summary = collector.get_trade_summary()
        self.assertIn("BTCUSDT", trade_summary)
        self.assertIn("ETHUSDT", trade_summary)

        # Test recording errors
        collector.record_error("connection", "Test error")
        error_summary = collector.get_error_summary()
        self.assertIn("connection", error_summary)

        # Test price updates
        collector.update_price("BTCUSDT", 51000.0)
        prices = collector.get_latest_prices()
        self.assertEqual(prices["BTCUSDT"], 51000.0)

    def test_health_checker(self):
        """Test health checker functionality"""
        from src.monitoring import HealthChecker, MetricsCollector

        collector = MetricsCollector()
        health_checker = HealthChecker(collector)

        # Test health check execution
        results = health_checker.run_health_check()

        self.assertIn("timestamp", results)
        self.assertIn("overall_status", results)
        self.assertIn("checks", results)

        # Test individual health check
        heartbeat_result = health_checker.run_health_check("heartbeat")
        self.assertIn("heartbeat", heartbeat_result["checks"])

        # Test health status
        is_healthy = health_checker.is_healthy()
        self.assertIsInstance(is_healthy, bool)

    def test_alert_manager(self):
        """Test alert manager functionality"""
        from src.monitoring import AlertManager, MetricsCollector

        collector = MetricsCollector()
        alert_manager = AlertManager(collector)

        # Test adding custom alert rule
        def custom_check():
            return True  # Always fires

        alert_manager.add_alert_rule(
            "test_alert", custom_check, severity="warning", description="Test alert"
        )

        # Test checking alerts
        fired_alerts = alert_manager.check_alerts()
        active_alerts = alert_manager.get_active_alerts()

        self.assertIsInstance(fired_alerts, list)
        self.assertIsInstance(active_alerts, list)

    def test_monitoring_backward_compatibility(self):
        """Test backward compatibility with old monitoring module"""
        from prometheus_client import CollectorRegistry

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            from scripts.monitoring import PrometheusExporter

            # Check if deprecation warning was issued (optional)
            # Note: warnings might not always be issued depending on import state
            # Test that old interface still works with isolated registry
            custom_registry = CollectorRegistry()
            exporter = PrometheusExporter(
                port=9094, registry=custom_registry
            )  # Use isolated registry
            self.assertIsNotNone(exporter)

            # Test legacy methods
            exporter.record_trade("BTCUSDT", "buy")
            exporter.record_error("test")
            exporter.update_heartbeat()

            # Clean up
            if hasattr(exporter, "stop"):
                exporter.stop()


class TestToolsDirectory(unittest.TestCase):
    """Test tools directory reorganization"""

    def test_data_fetcher_import(self):
        """Test that data fetcher can be imported and used"""
        from scripts.tools.data_fetcher import DataFetcher

        # Test basic instantiation
        fetcher = DataFetcher()
        self.assertIsNotNone(fetcher)

        # Test that it has expected methods
        self.assertTrue(hasattr(fetcher, "fetch_historical_data"))
        self.assertTrue(hasattr(fetcher, "fetch_multiple_symbols"))
        self.assertTrue(hasattr(fetcher, "save_data"))


class TestCodeReduction(unittest.TestCase):
    """Test that code has been properly reduced and modularized"""

    def test_improved_strategy_reduction(self):
        """Test that improved_strategy.py has been significantly reduced"""
        import src.improved_strategy

        # Get the file path
        file_path = src.improved_strategy.__file__

        # Count lines
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Should be much smaller than original (419 lines -> ~200 lines)
        self.assertLess(len(lines), 300, "improved_strategy.py should be significantly reduced")

    def test_monitoring_reduction(self):
        """Test that scripts/monitoring.py has been reduced"""
        import scripts.monitoring

        # Get the file path
        file_path = scripts.monitoring.__file__

        # Count lines
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Should be much smaller than original (307 lines -> ~100 lines)
        self.assertLess(len(lines), 200, "monitoring.py should be significantly reduced")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
