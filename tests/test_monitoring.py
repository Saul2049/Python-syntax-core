#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitoring Module Tests
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import CollectorRegistry, Counter, Gauge

# Import modules to test
try:
    from scripts.monitoring import PrometheusExporter, get_exporter
except ImportError:
    pytest.skip("Monitoring module not available, skipping tests", allow_module_level=True)


class TestPrometheusExporter(unittest.TestCase):
    """Test Prometheus exporter class"""

    def setUp(self):
        """Setup test environment"""
        # Create independent registry for each test to avoid metric conflicts
        self.test_registry = CollectorRegistry()
        self.exporter = PrometheusExporter(port=9999, registry=self.test_registry)

    def tearDown(self):
        """Cleanup test environment"""
        if hasattr(self.exporter, "stop"):
            self.exporter.stop()

    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.exporter.port, 9999)
        self.assertFalse(self.exporter.server_started)
        self.assertEqual(self.exporter.registry, self.test_registry)

        # Verify metrics are correctly created
        self.assertIsInstance(self.exporter.trade_count, Counter)
        self.assertIsInstance(self.exporter.error_count, Counter)
        self.assertIsInstance(self.exporter.heartbeat_age, Gauge)
        self.assertIsInstance(self.exporter.data_source_status, Gauge)
        self.assertIsInstance(self.exporter.memory_usage, Gauge)
        self.assertIsInstance(self.exporter.price, Gauge)

    @patch("src.monitoring.prometheus_exporter.start_http_server")
    def test_start(self, mock_start_server):
        """Test starting server"""
        # Test first startup
        self.exporter.start()
        mock_start_server.assert_called_once_with(9999, registry=self.test_registry)
        self.assertTrue(self.exporter.server_started)

        # Test repeated startup
        mock_start_server.reset_mock()
        self.exporter.start()
        mock_start_server.assert_not_called()  # Should not call again

    def test_record_trade(self):
        """Test recording trades"""
        with patch.object(self.exporter.trade_count, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            self.exporter.record_trade("BTC/USDT", "BUY")

            mock_labels.assert_called_once_with(symbol="BTC/USDT", action="BUY")
            mock_counter.inc.assert_called_once()

    def test_record_error(self):
        """Test recording errors"""
        with patch.object(self.exporter.error_count, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            # Test default error type
            self.exporter.record_error()
            mock_labels.assert_called_with(type="general")

            # Test custom error type
            self.exporter.record_error("network")
            mock_labels.assert_called_with(type="network")

    def test_update_heartbeat(self):
        """Test updating heartbeat"""
        with patch("time.time") as mock_time:
            mock_time.return_value = 12345
            self.exporter.update_heartbeat()
            self.assertEqual(self.exporter.last_heartbeat, 12345)

    def test_update_data_source_status(self):
        """Test updating data source status"""
        with patch.object(self.exporter.data_source_status, "labels") as mock_labels:
            mock_gauge = MagicMock()
            mock_labels.return_value = mock_gauge

            # Test active status
            self.exporter.update_data_source_status("BinanceTestnet", True)
            mock_labels.assert_called_with(source_name="BinanceTestnet")
            mock_gauge.set.assert_called_with(1)

            # Test inactive status
            self.exporter.update_data_source_status("MockMarket", False)
            mock_labels.assert_called_with(source_name="MockMarket")
            mock_gauge.set.assert_called_with(0)

    def test_update_memory_usage(self):
        """Test updating memory usage"""
        with patch.object(self.exporter.memory_usage, "set") as mock_set:
            self.exporter.update_memory_usage(42.5)
            mock_set.assert_called_once_with(42.5)

    def test_update_price(self):
        """Test updating price"""
        with patch.object(self.exporter.price, "labels") as mock_labels:
            mock_gauge = MagicMock()
            mock_labels.return_value = mock_gauge

            self.exporter.update_price("BTC/USDT", 30123.45)
            mock_labels.assert_called_once_with(symbol="BTC/USDT")
            mock_gauge.set.assert_called_once_with(30123.45)

    @patch("threading.Thread")
    def test_stop(self, mock_thread):
        """Test stopping"""
        # Mock thread
        mock_thread_instance = MagicMock()
        self.exporter.heartbeat_thread = mock_thread_instance
        mock_thread_instance.is_alive.return_value = True

        self.exporter.stop()

        self.assertTrue(self.exporter.stop_heartbeat)
        mock_thread_instance.join.assert_called_once_with(timeout=2)


class TestExporterSingleton(unittest.TestCase):
    """Test exporter singleton"""

    def setUp(self):
        """Setup test environment"""
        # Clear possible global instance
        import scripts.monitoring

        scripts.monitoring._exporter = None

    def tearDown(self):
        """Cleanup test environment"""
        # Clear global instance to avoid affecting other tests
        import scripts.monitoring

        if scripts.monitoring._exporter:
            scripts.monitoring._exporter.stop()
        scripts.monitoring._exporter = None

    def test_get_exporter(self):
        """Test getting exporter instance"""
        # First call should create new instance
        exporter1 = get_exporter(port=8888)
        self.assertEqual(exporter1.port, 8888)

        # Second call should create another instance (not singleton)
        exporter2 = get_exporter(port=9999)
        self.assertIsInstance(exporter2, PrometheusExporter)
        self.assertEqual(exporter2.port, 9999)

        # Clean up
        if hasattr(exporter1, "stop"):
            exporter1.stop()
        if hasattr(exporter2, "stop"):
            exporter2.stop()
