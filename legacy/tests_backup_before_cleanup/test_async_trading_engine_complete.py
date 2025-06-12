#!/usr/bin/env python3
"""
异步交易引擎完整测试套件 - 显著提升覆盖率
Async Trading Engine Complete Test Suite - Significant Coverage Boost

目标: 将async_trading_engine.py从22%提升到65%+

重点测试:
- 异步交易逻辑 (async_execute_trade_decision)
- WebSocket数据处理 (handle_websocket_data)
- 并发订单执行 (process_concurrent_orders)
- 性能分析 (analyze_performance_metrics)
- 市场状态监控 (monitor_market_status)
"""

import asyncio
import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestAsyncTradingEngineComplete:
    """异步交易引擎完整测试"""

    def setup_method(self):
        """测试前设置"""
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"
        os.environ["TG_TOKEN"] = "test_token"

    def create_async_mock_engine(self):
        """创建异步Mock交易引擎"""
        with (
            patch("src.brokers.Broker") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            # 设置Mock Broker
            mock_broker = Mock()
            mock_broker.get_account_balance = AsyncMock(return_value={"balance": 10000.0})
            mock_broker.get_positions = AsyncMock(return_value={"BTC": 0.5})
            mock_broker.place_order_async = AsyncMock(
                return_value={"orderId": "12345", "status": "FILLED", "executedQty": "0.1"}
            )
            mock_broker.positions = {}
            mock_broker.notifier = Mock()
            mock_broker.notifier.notify = Mock()
            mock_broker.notifier.notify_error = Mock()

            mock_broker_class.return_value = mock_broker

            # 设置Mock Metrics
            mock_metrics_obj = Mock()
            mock_metrics_obj.measure_order_latency.return_value.__enter__ = Mock()
            mock_metrics_obj.measure_order_latency.return_value.__exit__ = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.observe_task_latency = Mock()
            mock_metrics.return_value = mock_metrics_obj

            # 设置Mock Signal Processor
            mock_signal_processor = Mock()
            mock_signal_processor.get_trading_signals_optimized.return_value = {
                "buy_signal": False,
                "sell_signal": False,
                "current_price": 50000.0,
                "confidence": 0.7,
            }
            mock_processor.return_value = mock_signal_processor

            from src.core.async_trading_engine import AsyncTradingEngine

            engine = AsyncTradingEngine()

            return engine, mock_broker, mock_metrics_obj, mock_signal_processor

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_basic(self):
        """测试基本异步交易决策执行"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock市场分析结果
        with patch.object(
            engine,
            "analyze_market_conditions",
            return_value={
                "status": "success",
                "current_price": 50000.0,
                "trend": "bullish",
                "volatility": "medium",
                "signals": {"buy_signal": True, "confidence": 0.8},
            },
        ) as mock_analysis:

            result = await engine.async_execute_trade_decision("BTCUSDT")

            assert isinstance(result, dict)
            assert "action" in result
            mock_analysis.assert_called_once_with("BTCUSDT")

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_buy_signal(self):
        """测试异步买入信号执行"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock市场分析为买入信号
        market_analysis = {
            "status": "success",
            "current_price": 50000.0,
            "trend": "bullish",
            "volatility": "low",
            "signals": {"buy_signal": True, "confidence": 0.85},
        }

        with patch.object(engine, "analyze_market_conditions", return_value=market_analysis):
            result = await engine.async_execute_trade_decision("BTCUSDT")

            assert result["action"] in ["buy", "hold"]  # 可能买入或保持

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_error_handling(self):
        """测试异步交易决策错误处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock analyze_market_conditions抛出异常
        with patch.object(
            engine, "analyze_market_conditions", side_effect=Exception("市场分析失败")
        ):
            result = await engine.async_execute_trade_decision("BTCUSDT")

            assert result["action"] == "error"
            assert "message" in result
            mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_handle_websocket_data_price_update(self):
        """测试WebSocket价格更新数据处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock WebSocket价格数据
        ws_data = {
            "e": "24hrTicker",  # 事件类型
            "s": "BTCUSDT",  # 交易对
            "c": "50000.0",  # 当前价格
            "v": "1000.0",  # 成交量
            "P": "2.5",  # 价格变动百分比
        }

        await engine.handle_websocket_data(ws_data)

        # 验证价格更新被处理
        assert engine.latest_prices.get("BTCUSDT") == 50000.0

    @pytest.mark.asyncio
    async def test_handle_websocket_data_order_update(self):
        """测试WebSocket订单更新数据处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock订单更新数据
        ws_data = {
            "e": "executionReport",  # 订单执行报告
            "s": "BTCUSDT",
            "c": "order123",  # 订单ID
            "X": "FILLED",  # 订单状态
            "q": "0.1",  # 订单数量
            "z": "0.1",  # 已执行数量
        }

        await engine.handle_websocket_data(ws_data)

        # 验证订单状态被更新
        assert "order123" in engine.active_orders

    @pytest.mark.asyncio
    async def test_handle_websocket_data_invalid_format(self):
        """测试WebSocket无效数据格式处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock无效数据
        invalid_data = {"invalid": "data"}

        await engine.handle_websocket_data(invalid_data)

        # 应该记录异常但不崩溃
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_process_concurrent_orders_success(self):
        """测试成功的并发订单处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 准备多个订单
        orders = [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
            {"symbol": "ETHUSDT", "side": "SELL", "quantity": 1.0},
            {"symbol": "ADAUSDT", "side": "BUY", "quantity": 100.0},
        ]

        # Mock订单执行成功
        mock_broker.place_order_async.return_value = {"orderId": "success123", "status": "FILLED"}

        results = await engine.process_concurrent_orders(orders)

        assert len(results) == 3
        assert all(result["status"] == "FILLED" for result in results)
        assert mock_broker.place_order_async.call_count == 3

    @pytest.mark.asyncio
    async def test_process_concurrent_orders_partial_failure(self):
        """测试部分订单失败的并发处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        orders = [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
            {"symbol": "ETHUSDT", "side": "SELL", "quantity": 1.0},
        ]

        # Mock第一个订单成功，第二个失败
        mock_broker.place_order_async.side_effect = [
            {"orderId": "success123", "status": "FILLED"},
            Exception("订单执行失败"),
        ]

        results = await engine.process_concurrent_orders(orders)

        assert len(results) == 2
        assert results[0]["status"] == "FILLED"
        assert "error" in results[1]

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics_basic(self):
        """测试基本性能指标分析"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 设置一些历史数据
        engine.trade_history = [
            {"timestamp": datetime.now(), "profit": 100.0, "symbol": "BTCUSDT"},
            {"timestamp": datetime.now(), "profit": -50.0, "symbol": "ETHUSDT"},
            {"timestamp": datetime.now(), "profit": 75.0, "symbol": "BTCUSDT"},
        ]

        metrics = await engine.analyze_performance_metrics()

        assert isinstance(metrics, dict)
        assert "total_trades" in metrics
        assert "total_profit" in metrics
        assert "win_rate" in metrics
        assert metrics["total_trades"] == 3
        assert metrics["total_profit"] == 125.0

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics_empty_history(self):
        """测试空交易历史的性能分析"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        engine.trade_history = []

        metrics = await engine.analyze_performance_metrics()

        assert metrics["total_trades"] == 0
        assert metrics["total_profit"] == 0.0
        assert metrics["win_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_monitor_market_status_normal(self):
        """测试正常市场状态监控"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock正常市场数据
        engine.latest_prices = {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0, "ADAUSDT": 1.0}

        status = await engine.monitor_market_status()

        assert isinstance(status, dict)
        assert "market_health" in status
        assert "active_symbols" in status
        assert status["active_symbols"] == 3

    @pytest.mark.asyncio
    async def test_monitor_market_status_stale_data(self):
        """测试过期数据的市场状态监控"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock过期的价格数据
        engine.latest_prices = {}
        engine.last_price_update = datetime.now().timestamp() - 3600  # 1小时前

        status = await engine.monitor_market_status()

        assert status["market_health"] == "stale_data"
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_start_async_trading_loop_single_cycle(self):
        """测试异步交易循环的单次周期"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock交易决策返回停止信号
        with patch.object(
            engine, "async_execute_trade_decision", return_value={"action": "stop"}
        ) as mock_decision:

            # 运行一个周期就停止
            await engine.start_async_trading_loop("BTCUSDT", max_iterations=1)

            mock_decision.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_connection_management(self):
        """测试WebSocket连接管理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock WebSocket连接
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"e":"24hrTicker","s":"BTCUSDT","c":"50000"}')
        mock_websocket.close = AsyncMock()

        with patch("websockets.connect", return_value=mock_websocket):
            await engine.start_websocket_connection(
                "wss://stream.binance.com:9443/ws/btcusdt@ticker"
            )

            mock_websocket.recv.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_connection_error_handling(self):
        """测试WebSocket连接错误处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock WebSocket连接失败
        with patch("websockets.connect", side_effect=Exception("连接失败")):
            await engine.start_websocket_connection("wss://invalid-url")

            mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_stale_orders(self):
        """测试清理过期订单"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 设置一些过期订单
        old_timestamp = datetime.now().timestamp() - 3600  # 1小时前
        engine.active_orders = {
            "old_order1": {"timestamp": old_timestamp, "status": "PENDING"},
            "new_order1": {"timestamp": datetime.now().timestamp(), "status": "PENDING"},
        }

        await engine.cleanup_stale_orders(max_age_seconds=1800)  # 30分钟超时

        # 过期订单应该被清理
        assert "old_order1" not in engine.active_orders
        assert "new_order1" in engine.active_orders

    @pytest.mark.asyncio
    async def test_batch_price_updates(self):
        """测试批量价格更新"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 准备批量价格数据
        price_updates = [
            {"symbol": "BTCUSDT", "price": 50000.0},
            {"symbol": "ETHUSDT", "price": 3000.0},
            {"symbol": "ADAUSDT", "price": 1.0},
        ]

        await engine.batch_update_prices(price_updates)

        # 验证所有价格都被更新
        assert engine.latest_prices["BTCUSDT"] == 50000.0
        assert engine.latest_prices["ETHUSDT"] == 3000.0
        assert engine.latest_prices["ADAUSDT"] == 1.0

    @pytest.mark.asyncio
    async def test_risk_management_async(self):
        """测试异步风险管理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # Mock当前持仓
        mock_broker.positions = {
            "BTCUSDT": {"quantity": 0.5, "entry_price": 48000.0, "unrealized_pnl": 1000.0}
        }

        current_price = 50000.0
        risk_assessment = await engine.assess_portfolio_risk(current_price)

        assert isinstance(risk_assessment, dict)
        assert "total_exposure" in risk_assessment
        assert "risk_level" in risk_assessment

    @pytest.mark.asyncio
    async def test_emergency_stop_async(self):
        """测试异步紧急停止"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 触发紧急停止
        await engine.emergency_stop("系统检测到异常")

        # 验证引擎状态
        assert engine.is_running is False
        mock_broker.notifier.notify.assert_called()

    @pytest.mark.asyncio
    async def test_async_initialization(self):
        """测试异步初始化"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        await engine.async_initialize()

        # 验证初始化完成
        assert hasattr(engine, "latest_prices")
        assert hasattr(engine, "active_orders")
        assert hasattr(engine, "trade_history")


if __name__ == "__main__":
    # 运行异步测试
    import asyncio

    async def run_tests():
        import subprocess

        result = subprocess.run(
            ["python", "-m", "pytest", __file__, "-v", "--tb=short"], capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode

    asyncio.run(run_tests())
