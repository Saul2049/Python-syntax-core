#!/usr/bin/env python3
"""
实际异步交易引擎测试
Real Async Trading Engine Tests

基于async_trading_engine.py中实际存在的方法
"""

import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest


class TestAsyncEngineReal:
    """基于实际方法的异步引擎测试"""

    def setup_method(self):
        """测试前设置"""
        os.environ["API_KEY"] = "test"
        os.environ["API_SECRET"] = "test"
        os.environ["TG_TOKEN"] = "test"

    def create_real_async_mock_engine(self):
        """创建基于实际方法的Mock异步引擎"""
        with (
            patch("src.ws.binance_ws_client.BinanceWSClient") as mock_ws,
            patch("src.brokers.live_broker_async.LiveBrokerAsync") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            # Mock WebSocket Client
            mock_ws_client = Mock()
            mock_ws.return_value = mock_ws_client

            # Mock LiveBrokerAsync
            mock_broker = Mock()
            mock_broker.init_session = AsyncMock()
            mock_broker.place_order = AsyncMock(return_value={"orderId": "123", "status": "FILLED"})
            mock_broker.get_account_balance = AsyncMock(return_value={"balance": 10000.0})
            mock_broker_class.return_value = mock_broker

            # Mock Metrics
            mock_metrics_obj = Mock()
            mock_metrics_obj.measure_signal_latency.return_value.__enter__ = Mock()
            mock_metrics_obj.measure_signal_latency.return_value.__exit__ = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.update_concurrent_tasks = Mock()
            mock_metrics_obj.record_ws_message = Mock()
            mock_metrics.return_value = mock_metrics_obj

            # Mock Signal Processor
            mock_signal_processor = Mock()
            mock_signal_processor.get_trading_signals_optimized.return_value = {
                "buy_signal": False,
                "sell_signal": False,
                "current_price": 50000.0,
            }
            mock_signal_processor.compute_atr_optimized.return_value = 1500.0
            mock_processor.return_value = mock_signal_processor

            from src.core.async_trading_engine import AsyncTradingEngine

            engine = AsyncTradingEngine(api_key="test_key", api_secret="test_secret")

            return engine, mock_broker, mock_metrics_obj, mock_signal_processor

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """测试成功初始化"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        await engine.initialize()

        # 验证初始化调用
        mock_broker.init_session.assert_called_once()
        assert engine.ws_client is not None
        assert engine.broker is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """测试初始化失败"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # Mock初始化失败
        mock_broker.init_session.side_effect = Exception("连接失败")

        with pytest.raises(Exception):
            await engine.initialize()

    @pytest.mark.asyncio
    async def test_handle_market_data_closed_kline(self):
        """测试处理完成的K线数据"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 完成的K线数据
        kline_data = {
            "symbol": "BTCUSDT",
            "is_closed": True,
            "timestamp": datetime.now(),
            "open": 50000.0,
            "high": 50100.0,
            "low": 49900.0,
            "close": 50050.0,
            "volume": 1000.0,
        }

        await engine._handle_market_data(kline_data)

        # 验证数据被添加到缓存
        assert "BTCUSDT" in engine.market_data
        assert len(engine.market_data["BTCUSDT"]) > 0

        # 验证监控调用
        mock_metrics.update_concurrent_tasks.assert_called()
        mock_metrics.record_ws_message.assert_called_with("BTCUSDT", "kline")

    @pytest.mark.asyncio
    async def test_handle_market_data_incomplete_kline(self):
        """测试处理未完成的K线数据"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 未完成的K线数据
        kline_data = {
            "symbol": "BTCUSDT",
            "is_closed": False,  # 未完成
            "timestamp": datetime.now(),
            "open": 50000.0,
            "high": 50100.0,
            "low": 49900.0,
            "close": 50050.0,
            "volume": 1000.0,
        }

        await engine._handle_market_data(kline_data)

        # 未完成的K线不应该被处理
        assert len(engine.market_data.get("BTCUSDT", pd.DataFrame())) == 0

    @pytest.mark.asyncio
    async def test_handle_market_data_exception(self):
        """测试市场数据处理异常"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 无效数据导致异常
        invalid_kline_data = {
            "symbol": "BTCUSDT",
            "is_closed": True,
            # 缺少必要字段
        }

        await engine._handle_market_data(invalid_kline_data)

        # 应该记录异常
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_process_trading_signal_insufficient_data(self):
        """测试数据不足的信号处理"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 数据不足（少于所需窗口大小）
        engine.market_data["BTCUSDT"] = pd.DataFrame(
            {"close": [50000.0, 50100.0]}  # 只有2个数据点，少于fast_win=7
        )

        await engine._process_trading_signal("BTCUSDT")

        # 数据不足时不应该处理信号
        mock_metrics.update_concurrent_tasks.assert_called_with("signal_processing", 1)

    @pytest.mark.asyncio
    async def test_process_trading_signal_success(self):
        """测试成功的信号处理"""
        engine, mock_broker, mock_metrics, mock_signal_processor = (
            self.create_real_async_mock_engine()
        )

        # 足够的市场数据
        engine.market_data["BTCUSDT"] = pd.DataFrame(
            {
                "open": [50000.0] * 30,
                "high": [50100.0] * 30,
                "low": [49900.0] * 30,
                "close": [50050.0] * 30,
                "volume": [1000.0] * 30,
            }
        )

        await engine._process_trading_signal("BTCUSDT")

        # 验证信号处理调用
        mock_signal_processor.get_trading_signals_optimized.assert_called()
        mock_signal_processor.compute_atr_optimized.assert_called()

        # 验证信号缓存
        assert "BTCUSDT" in engine.last_signals
        assert engine.signal_count > 0

    @pytest.mark.asyncio
    async def test_process_trading_signal_exception(self):
        """测试信号处理异常"""
        engine, mock_broker, mock_metrics, mock_signal_processor = (
            self.create_real_async_mock_engine()
        )

        # 设置足够数据
        engine.market_data["BTCUSDT"] = pd.DataFrame({"close": [50000.0] * 30})

        # Mock信号处理异常
        mock_signal_processor.get_trading_signals_optimized.side_effect = Exception("信号处理失败")

        await engine._process_trading_signal("BTCUSDT")

        # 应该记录异常
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_execute_trading_logic_buy_signal(self):
        """测试买入信号的交易逻辑"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        signals = {"buy_signal": True, "sell_signal": False, "current_price": 50000.0}

        # 确保没有现有持仓
        engine.positions = {}

        with patch.object(engine, "_execute_buy_order", new_callable=AsyncMock) as mock_buy:
            await engine._execute_trading_logic("BTCUSDT", signals, 1500.0)
            mock_buy.assert_called_once_with("BTCUSDT", 50000.0, 1500.0)

    @pytest.mark.asyncio
    async def test_execute_trading_logic_sell_signal(self):
        """测试卖出信号的交易逻辑"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        signals = {"buy_signal": False, "sell_signal": True, "current_price": 50000.0}

        # 设置现有持仓
        engine.positions = {"BTCUSDT": {"quantity": 0.1}}

        with patch.object(engine, "_execute_sell_order", new_callable=AsyncMock) as mock_sell:
            await engine._execute_trading_logic("BTCUSDT", signals, 1500.0)
            mock_sell.assert_called_once_with("BTCUSDT", 50000.0)

    @pytest.mark.asyncio
    async def test_execute_trading_logic_with_position_monitoring(self):
        """测试带持仓监控的交易逻辑"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        signals = {"buy_signal": False, "sell_signal": False, "current_price": 50000.0}

        # 设置现有持仓
        engine.positions = {"BTCUSDT": {"quantity": 0.1}}

        with patch.object(
            engine, "_update_position_monitoring", new_callable=AsyncMock
        ) as mock_monitor:
            await engine._execute_trading_logic("BTCUSDT", signals, 1500.0)
            mock_monitor.assert_called_once_with("BTCUSDT", 50000.0, 1500.0)

    @pytest.mark.asyncio
    async def test_execute_buy_order_success(self):
        """测试成功执行买入订单"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        await engine._execute_buy_order("BTCUSDT", 50000.0, 1500.0)

        # 验证订单执行
        mock_broker.place_order.assert_called()

        # 验证持仓记录
        assert "BTCUSDT" in engine.positions
        assert engine.order_count > 0

    @pytest.mark.asyncio
    async def test_execute_buy_order_exception(self):
        """测试买入订单执行异常"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # Mock订单执行失败
        mock_broker.place_order.side_effect = Exception("订单失败")

        await engine._execute_buy_order("BTCUSDT", 50000.0, 1500.0)

        # 应该记录异常
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_execute_sell_order_success(self):
        """测试成功执行卖出订单"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置现有持仓
        engine.positions = {"BTCUSDT": {"quantity": 0.1, "entry_price": 49000.0}}

        await engine._execute_sell_order("BTCUSDT", 50000.0)

        # 验证订单执行
        mock_broker.place_order.assert_called()

        # 验证持仓移除
        assert "BTCUSDT" not in engine.positions
        assert engine.order_count > 0

    @pytest.mark.asyncio
    async def test_execute_sell_order_exception(self):
        """测试卖出订单执行异常"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置现有持仓
        engine.positions = {"BTCUSDT": {"quantity": 0.1}}

        # Mock订单执行失败
        mock_broker.place_order.side_effect = Exception("卖出失败")

        await engine._execute_sell_order("BTCUSDT", 50000.0)

        # 应该记录异常
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_update_position_monitoring(self):
        """测试持仓监控更新"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置持仓
        engine.positions = {"BTCUSDT": {"quantity": 0.1, "entry_price": 49000.0}}

        await engine._update_position_monitoring("BTCUSDT", 50000.0, 1500.0)

        # 验证持仓数据更新（具体逻辑取决于实现）
        assert "BTCUSDT" in engine.positions

    @pytest.mark.asyncio
    async def test_run_engine_initialization(self):
        """测试引擎运行初始化"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # Mock各种异步循环
        with (
            patch.object(engine, "initialize", new_callable=AsyncMock),
            patch.object(engine, "_status_monitoring_loop", new_callable=AsyncMock),
            patch.object(engine, "_performance_monitoring_loop", new_callable=AsyncMock),
            patch("asyncio.gather", new_callable=AsyncMock),
        ):

            # 设置运行状态
            engine.running = True

            # 由于run方法包含无限循环，我们只测试初始化部分
            await engine.initialize()

    @pytest.mark.asyncio
    async def test_status_monitoring_loop(self):
        """测试状态监控循环"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置运行状态
        engine.running = True

        # Mock asyncio.sleep来避免无限等待
        with patch("asyncio.sleep", side_effect=[None, asyncio.CancelledError()]):
            try:
                await engine._status_monitoring_loop()
            except asyncio.CancelledError:
                pass  # 预期的取消异常

    @pytest.mark.asyncio
    async def test_performance_monitoring_loop(self):
        """测试性能监控循环"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置运行状态和一些统计数据
        engine.running = True
        engine.cycle_count = 5
        engine.signal_count = 10
        engine.order_count = 3

        # Mock asyncio.sleep来避免无限等待
        with patch("asyncio.sleep", side_effect=[None, asyncio.CancelledError()]):
            try:
                await engine._performance_monitoring_loop()
            except asyncio.CancelledError:
                pass  # 预期的取消异常

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """测试引擎清理"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置一些需要清理的状态
        engine.running = True
        engine.concurrent_tasks = {"BTCUSDT": Mock()}
        engine.ws_client = Mock()
        engine.ws_client.close = AsyncMock()

        await engine.cleanup()

        # 验证清理操作
        assert engine.running is False
        engine.ws_client.close.assert_called_once()

    def test_get_performance_stats(self):
        """测试获取性能统计"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        # 设置一些统计数据
        engine.cycle_count = 100
        engine.signal_count = 50
        engine.order_count = 10
        engine.positions = {"BTCUSDT": {"quantity": 0.1}}

        stats = engine.get_performance_stats()

        # 验证统计数据
        assert isinstance(stats, dict)
        assert "cycle_count" in stats["engine"]
        assert "signal_count" in stats["engine"]
        assert "order_count" in stats["engine"]
        assert "active_positions" in stats["engine"]
        assert stats["engine"]["cycle_count"] == 100
        assert stats["engine"]["signal_count"] == 50
        assert stats["engine"]["order_count"] == 10
        assert stats["engine"]["active_positions"] == 1

    def test_batch_update_metrics(self):
        """测试批量更新指标"""
        engine, mock_broker, mock_metrics, _ = self.create_real_async_mock_engine()

        stats = {"cycle_count": 50, "signal_count": 25, "order_count": 5, "active_positions": 2}

        engine._batch_update_metrics(stats)

        # 验证指标更新（具体验证取决于实现）
        # 至少确保方法执行无异常
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
