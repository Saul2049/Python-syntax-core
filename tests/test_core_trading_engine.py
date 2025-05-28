#!/usr/bin/env python3
"""
测试核心交易引擎模块 (Test Core Trading Engine Module)
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.core.trading_engine import TradingEngine, trading_loop


class TestTradingEngine:
    """测试交易引擎类 (Test Trading Engine Class)"""

    @pytest.fixture
    def mock_broker(self):
        """创建模拟的Broker对象"""
        broker = Mock()
        broker.positions = {}
        broker.notifier = Mock()
        broker.execute_order = Mock()
        broker.update_position_stops = Mock()
        broker.check_stop_loss = Mock()
        return broker

    @pytest.fixture
    def trading_engine(self, mock_broker):
        """创建交易引擎实例"""
        with patch("src.core.trading_engine.Broker", return_value=mock_broker):
            engine = TradingEngine(
                api_key="test_key", api_secret="test_secret", telegram_token="test_token"
            )
        return engine

    def test_trading_engine_initialization(self):
        """测试交易引擎初始化"""
        with patch("src.core.trading_engine.Broker") as mock_broker_class:
            mock_broker = Mock()
            mock_broker_class.return_value = mock_broker

            # 测试使用显式参数初始化
            engine = TradingEngine(
                api_key="test_key", api_secret="test_secret", telegram_token="test_token"
            )

            # 验证Broker被正确初始化
            mock_broker_class.assert_called_once_with(
                api_key="test_key", api_secret="test_secret", telegram_token="test_token"
            )

            # 验证默认配置
            assert engine.account_equity == 10000.0
            assert engine.risk_percent == 0.01
            assert engine.atr_multiplier == 2.0
            assert isinstance(engine.last_status_update, datetime)

    def test_calculate_position_size_normal(self, trading_engine):
        """测试正常情况下的仓位计算"""
        current_price = 100.0
        atr = 2.0
        symbol = "BTCUSDT"

        # 配置交易引擎参数
        trading_engine.account_equity = 10000.0
        trading_engine.risk_percent = 0.01
        trading_engine.atr_multiplier = 2.0

        result = trading_engine.calculate_position_size(current_price, atr, symbol)

        # 计算预期值
        _ = 10000.0 * 0.01  # 100
        _ = 100.0 - (2.0 * 2.0)  # 96
        _ = 100.0 - 96.0  # 4
        expected_quantity = 100.0 / 4.0  # 25

        assert result == round(expected_quantity, 3)

    def test_process_buy_signal_success(self, trading_engine):
        """测试成功处理买入信号"""
        symbol = "BTCUSDT"
        signals = {"buy_signal": True, "current_price": 100.0, "fast_ma": 101.0, "slow_ma": 99.0}
        atr = 2.0

        # 确保没有现有仓位
        trading_engine.broker.positions = {}

        # 模拟calculate_position_size返回值
        with patch.object(trading_engine, "calculate_position_size", return_value=10.0):
            result = trading_engine.process_buy_signal(symbol, signals, atr)

            assert result is True
            trading_engine.broker.execute_order.assert_called_once()

    def test_process_sell_signal_success(self, trading_engine):
        """测试成功处理卖出信号"""
        symbol = "BTCUSDT"
        signals = {"sell_signal": True, "fast_ma": 99.0, "slow_ma": 101.0}

        # 设置现有仓位
        position = {"quantity": 10.0, "entry_price": 98.0}
        trading_engine.broker.positions = {symbol: position}

        result = trading_engine.process_sell_signal(symbol, signals)

        assert result is True
        trading_engine.broker.execute_order.assert_called_once()

    def test_update_positions(self, trading_engine):
        """测试更新仓位状态"""
        symbol = "BTCUSDT"
        current_price = 105.0
        atr = 2.0

        trading_engine.update_positions(symbol, current_price, atr)

        # 验证调用了相应的方法
        trading_engine.broker.update_position_stops.assert_called_once_with(
            symbol, current_price, atr
        )
        trading_engine.broker.check_stop_loss.assert_called_once_with(symbol, current_price)

    def test_send_status_update_first_time(self, trading_engine):
        """测试首次发送状态更新"""
        symbol = "BTCUSDT"
        signals = {"current_price": 100.0, "fast_ma": 101.0, "slow_ma": 99.0}
        atr = 2.0

        # 设置上次更新时间为超过1小时前
        trading_engine.last_status_update = datetime.now() - timedelta(hours=2)
        trading_engine.broker.positions = {}

        trading_engine.send_status_update(symbol, signals, atr)

        trading_engine.broker.notifier.notify.assert_called_once()

    @patch("src.core.trading_engine.fetch_price_data")
    @patch("src.core.trading_engine.validate_signal")
    def test_execute_trading_cycle_success(self, mock_validate, mock_fetch, trading_engine):
        """测试成功执行交易周期"""
        symbol = "BTCUSDT"

        # 设置模拟返回值 - 返回正确的DataFrame格式
        mock_price_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.5, 101.5, 102.5, 103.5, 104.5],
                "volume": [1000, 1100, 1200, 1300, 1400],
            }
        )
        mock_fetch.return_value = mock_price_data
        mock_validate.return_value = True

        # 模拟信号处理器的方法
        mock_signals = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 104.0,
            "fast_ma": 105.0,
            "slow_ma": 103.0,
        }

        with patch.object(
            trading_engine.signal_processor,
            "get_trading_signals_optimized",
            return_value=mock_signals,
        ):
            with patch.object(
                trading_engine.signal_processor, "compute_atr_optimized", return_value=2.0
            ):
                with patch.object(trading_engine, "process_buy_signal", return_value=True):
                    with patch.object(trading_engine, "process_sell_signal", return_value=False):
                        with patch.object(trading_engine, "update_positions"):
                            with patch.object(trading_engine, "send_status_update"):
                                result = trading_engine.execute_trading_cycle(symbol)

                                assert result is True
                                mock_fetch.assert_called_once()
                                mock_validate.assert_called_once()


class TestTradingLoopFunction:
    """测试交易循环函数 (Test Trading Loop Function)"""

    @patch("src.core.trading_engine.TradingEngine")
    def test_trading_loop_function(self, mock_engine_class):
        """测试交易循环函数"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        trading_loop(symbol="ETHUSDT", interval_seconds=30)

        # 验证创建了交易引擎
        mock_engine_class.assert_called_once()

        # 验证调用了start_trading_loop - 修复：使用位置参数
        mock_engine.start_trading_loop.assert_called_once_with("ETHUSDT", 30)  # 位置参数而不是关键字参数
