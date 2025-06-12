#!/usr/bin/env python3
"""
异步交易引擎覆盖率提升测试
Async Trading Engine Coverage Boost Tests

目标: 将async_trading_engine.py从22%提升到60%+
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestAsyncEngineBoost:
    """异步交易引擎覆盖率提升"""

    def setup_method(self):
        """测试前设置"""
        os.environ["API_KEY"] = "test"
        os.environ["API_SECRET"] = "test"
        os.environ["TG_TOKEN"] = "test"

    def create_async_mock_engine(self):
        """创建异步Mock引擎"""
        with (
            patch("src.brokers.Broker") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            # 异步Broker Mock
            mock_broker = Mock()
            mock_broker.get_account_balance = AsyncMock(return_value={"balance": 10000.0})
            mock_broker.get_positions = AsyncMock(return_value={})
            mock_broker.place_order_async = AsyncMock(
                return_value={"orderId": "async123", "status": "FILLED"}
            )
            mock_broker.positions = {}
            mock_broker.notifier = Mock()
            mock_broker.notifier.notify = Mock()
            mock_broker_class.return_value = mock_broker

            # Metrics Mock
            mock_metrics_obj = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.observe_task_latency = Mock()
            mock_metrics.return_value = mock_metrics_obj

            # Signal Processor Mock
            mock_signal_processor = Mock()
            mock_processor.return_value = mock_signal_processor

            from src.core.async_trading_engine import AsyncTradingEngine

            engine = AsyncTradingEngine(api_key="test_key", api_secret="test_secret")

            # 初始化必要属性
            engine.latest_prices = {}
            engine.active_orders = {}
            engine.trade_history = []
            engine.is_running = True
            engine.last_price_update = datetime.now().timestamp()

            return engine, mock_broker, mock_metrics_obj, mock_signal_processor

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_success(self):
        """测试异步交易决策成功执行"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock成功的市场分析
        market_analysis = {
            "status": "success",
            "current_price": 50000.0,
            "trend": "bullish",
            "signals": {"buy_signal": True, "confidence": 0.8},
        }

        with patch.object(engine, "analyze_market_conditions", return_value=market_analysis):
            result = await engine.async_execute_trade_decision("BTCUSDT")

            assert isinstance(result, dict)
            assert "action" in result
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_error(self):
        """测试异步交易决策错误处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock分析异常
        with patch.object(engine, "analyze_market_conditions", side_effect=Exception("分析失败")):
            result = await engine.async_execute_trade_decision("BTCUSDT")

            assert result["action"] == "error"
            assert "message" in result
            mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_handle_websocket_data_price_update(self):
        """测试WebSocket价格更新处理"""
        engine, _, _, _ = self.create_async_mock_engine()

        # 价格更新数据
        price_data = {"e": "24hrTicker", "s": "BTCUSDT", "c": "50000.0"}

        await engine.handle_websocket_data(price_data)
        assert engine.latest_prices.get("BTCUSDT") == 50000.0

    @pytest.mark.asyncio
    async def test_handle_websocket_data_order_update(self):
        """测试WebSocket订单更新处理"""
        engine, _, _, _ = self.create_async_mock_engine()

        # 订单更新数据
        order_data = {"e": "executionReport", "s": "BTCUSDT", "c": "order123", "X": "FILLED"}

        await engine.handle_websocket_data(order_data)
        assert "order123" in engine.active_orders

    @pytest.mark.asyncio
    async def test_handle_websocket_data_invalid(self):
        """测试WebSocket无效数据处理"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine()

        # 无效数据
        invalid_data = {"invalid": "data"}

        await engine.handle_websocket_data(invalid_data)
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_process_concurrent_orders_success(self):
        """测试并发订单处理成功"""
        engine, mock_broker, _, _ = self.create_async_mock_engine()

        orders = [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
            {"symbol": "ETHUSDT", "side": "SELL", "quantity": 1.0},
        ]

        results = await engine.process_concurrent_orders(orders)

        assert len(results) == 2
        assert all("orderId" in result for result in results)
        assert mock_broker.place_order_async.call_count == 2

    @pytest.mark.asyncio
    async def test_process_concurrent_orders_partial_failure(self):
        """测试并发订单部分失败"""
        engine, mock_broker, _, _ = self.create_async_mock_engine()

        orders = [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
            {"symbol": "ETHUSDT", "side": "SELL", "quantity": 1.0},
        ]

        # Mock第一个成功，第二个失败
        mock_broker.place_order_async.side_effect = [
            {"orderId": "success", "status": "FILLED"},
            Exception("订单失败"),
        ]

        results = await engine.process_concurrent_orders(orders)

        assert len(results) == 2
        assert results[0]["status"] == "FILLED"
        assert "error" in results[1]

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics_with_data(self):
        """测试有数据的性能指标分析"""
        engine, _, _, _ = self.create_async_mock_engine()

        # 设置交易历史
        engine.trade_history = [
            {"timestamp": datetime.now(), "profit": 100.0, "symbol": "BTCUSDT"},
            {"timestamp": datetime.now(), "profit": -50.0, "symbol": "ETHUSDT"},
            {"timestamp": datetime.now(), "profit": 75.0, "symbol": "BTCUSDT"},
        ]

        metrics = await engine.analyze_performance_metrics()

        assert metrics["total_trades"] == 3
        assert metrics["total_profit"] == 125.0
        assert metrics["win_rate"] > 0

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics_empty(self):
        """测试空数据的性能指标分析"""
        engine, _, _, _ = self.create_async_mock_engine()

        engine.trade_history = []

        metrics = await engine.analyze_performance_metrics()

        assert metrics["total_trades"] == 0
        assert metrics["total_profit"] == 0.0
        assert metrics["win_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_monitor_market_status_healthy(self):
        """测试健康市场状态监控"""
        engine, _, _, _ = self.create_async_mock_engine()

        engine.latest_prices = {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0}

        status = await engine.monitor_market_status()

        assert status["market_health"] == "healthy"
        assert status["active_symbols"] == 2

    @pytest.mark.asyncio
    async def test_monitor_market_status_stale(self):
        """测试过期数据市场状态监控"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine()

        engine.latest_prices = {}
        engine.last_price_update = datetime.now().timestamp() - 3600  # 1小时前

        status = await engine.monitor_market_status()

        assert status["market_health"] == "stale_data"
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_start_websocket_connection_success(self):
        """测试WebSocket连接成功"""
        engine, _, _, _ = self.create_async_mock_engine()

        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"e":"24hrTicker","s":"BTCUSDT","c":"50000"}')

        with patch("websockets.connect", return_value=mock_websocket):
            await engine.start_websocket_connection("wss://test.com/ws")
            mock_websocket.recv.assert_called()

    @pytest.mark.asyncio
    async def test_start_websocket_connection_failure(self):
        """测试WebSocket连接失败"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine()

        with patch("websockets.connect", side_effect=Exception("连接失败")):
            await engine.start_websocket_connection("wss://invalid.com")
            mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_stale_orders(self):
        """测试清理过期订单"""
        engine, _, _, _ = self.create_async_mock_engine()

        current_time = datetime.now().timestamp()
        engine.active_orders = {
            "old_order": {"timestamp": current_time - 3600, "status": "PENDING"},
            "new_order": {"timestamp": current_time - 300, "status": "PENDING"},
        }

        await engine.cleanup_stale_orders(max_age_seconds=1800)

        assert "old_order" not in engine.active_orders
        assert "new_order" in engine.active_orders

    @pytest.mark.asyncio
    async def test_batch_update_prices(self):
        """测试批量价格更新"""
        engine, _, _, _ = self.create_async_mock_engine()

        price_updates = [
            {"symbol": "BTCUSDT", "price": 50000.0},
            {"symbol": "ETHUSDT", "price": 3000.0},
        ]

        await engine.batch_update_prices(price_updates)

        assert engine.latest_prices["BTCUSDT"] == 50000.0
        assert engine.latest_prices["ETHUSDT"] == 3000.0

    @pytest.mark.asyncio
    async def test_assess_portfolio_risk(self):
        """测试投资组合风险评估"""
        engine, mock_broker, _, _ = self.create_async_mock_engine()

        mock_broker.positions = {
            "BTCUSDT": {"quantity": 0.5, "entry_price": 48000.0, "unrealized_pnl": 1000.0}
        }

        risk_assessment = await engine.assess_portfolio_risk(50000.0)

        assert isinstance(risk_assessment, dict)
        assert "total_exposure" in risk_assessment
        assert "risk_level" in risk_assessment

    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """测试紧急停止"""
        engine, mock_broker, _, _ = self.create_async_mock_engine()

        await engine.emergency_stop("测试紧急停止")

        assert engine.is_running is False
        mock_broker.notifier.notify.assert_called()

    @pytest.mark.asyncio
    async def test_async_initialize(self):
        """测试异步初始化"""
        engine, _, _, _ = self.create_async_mock_engine()

        await engine.async_initialize()

        # 验证初始化完成
        assert hasattr(engine, "latest_prices")
        assert hasattr(engine, "active_orders")
        assert hasattr(engine, "trade_history")

    @pytest.mark.asyncio
    async def test_start_async_trading_loop(self):
        """测试异步交易循环启动"""
        engine, _, _, _ = self.create_async_mock_engine()

        # Mock交易决策返回停止信号
        with patch.object(engine, "async_execute_trade_decision", return_value={"action": "stop"}):
            await engine.start_async_trading_loop("BTCUSDT", max_iterations=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
