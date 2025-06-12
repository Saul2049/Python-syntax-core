#!/usr/bin/env python3
"""
高级覆盖率提升测试套件
Advanced Coverage Boost Test Suite

目标：
- trading_engine.py: 66% → 85%+
- async_trading_engine.py: 22% → 65%+

重点覆盖：
- 信号处理逻辑 (process_buy_signal, process_sell_signal)
- 交易循环执行 (execute_trading_cycle, start_trading_loop)
- 异步交易决策 (async_execute_trade_decision)
- WebSocket数据处理 (handle_websocket_data)
- 性能监控 (analyze_performance_metrics)
"""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest


class TestAdvancedCoverageBoost:
    """高级覆盖率提升测试"""

    def setup_method(self):
        """测试前设置"""
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"
        os.environ["TG_TOKEN"] = "test_token"

    def create_comprehensive_mock_engine(self):
        """创建综合Mock交易引擎"""
        with (
            patch("src.brokers.Broker") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            # 设置全面Mock Broker
            mock_broker = Mock()
            mock_broker.get_account_balance.return_value = {"balance": 10000.0}
            mock_broker.get_positions.return_value = {"BTC": 0.5}
            mock_broker.place_order.return_value = {"orderId": "12345", "status": "FILLED"}
            mock_broker.positions = {}
            mock_broker.update_position_stops = Mock()
            mock_broker.check_stop_loss = Mock()
            mock_broker.execute_order = Mock()
            mock_broker.notifier = Mock()
            mock_broker.notifier.notify = Mock()
            mock_broker.notifier.notify_error = Mock()

            mock_broker_class.return_value = mock_broker

            # 设置全面Mock Metrics
            mock_metrics_obj = Mock()
            mock_metrics_obj.measure_order_latency.return_value.__enter__ = Mock()
            mock_metrics_obj.measure_order_latency.return_value.__exit__ = Mock()
            mock_metrics_obj.measure_data_fetch_latency.return_value.__enter__ = Mock()
            mock_metrics_obj.measure_data_fetch_latency.return_value.__exit__ = Mock()
            mock_metrics_obj.measure_signal_latency.return_value.__enter__ = Mock()
            mock_metrics_obj.measure_signal_latency.return_value.__exit__ = Mock()
            mock_metrics_obj.observe_task_latency = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.record_price_update = Mock()
            mock_metrics.return_value = mock_metrics_obj

            # 设置全面Mock Signal Processor
            mock_signal_processor = Mock()
            mock_signal_processor.get_trading_signals_optimized.return_value = {
                "buy_signal": False,
                "sell_signal": False,
                "current_price": 50000.0,
                "fast_ma": 49500.0,
                "slow_ma": 49000.0,
                "confidence": 0.7,
            }
            mock_signal_processor.compute_atr_optimized.return_value = 1500.0
            mock_processor.return_value = mock_signal_processor

            from src.core.trading_engine import TradingEngine

            engine = TradingEngine()

            return engine, mock_broker, mock_metrics_obj, mock_signal_processor

    # ========== 交易引擎高级测试 ==========

    def test_calculate_position_size_comprehensive(self):
        """全面测试仓位大小计算"""
        engine, _, _, _ = self.create_comprehensive_mock_engine()

        # 测试正常情况
        position_size = engine.calculate_position_size(50000.0, 1500.0, "BTCUSDT")
        assert isinstance(position_size, float)
        assert position_size > 0

        # 测试零ATR情况
        zero_atr_size = engine.calculate_position_size(50000.0, 0.0, "BTCUSDT")
        assert zero_atr_size == 0.0

        # 测试负ATR情况
        negative_atr_size = engine.calculate_position_size(50000.0, -100.0, "BTCUSDT")
        assert negative_atr_size == 0.0

    def test_process_buy_signal_all_scenarios(self):
        """测试买入信号处理的所有场景"""
        engine, mock_broker, mock_metrics, _ = self.create_comprehensive_mock_engine()

        # 场景1: 成功买入
        mock_broker.positions = {}
        signals_buy = {
            "buy_signal": True,
            "current_price": 50000.0,
            "fast_ma": 50100.0,
            "slow_ma": 49900.0,
        }

        with patch.object(engine, "calculate_position_size", return_value=0.1):
            result = engine.process_buy_signal("BTCUSDT", signals_buy, 1500.0)
            assert result is True
            mock_broker.execute_order.assert_called()

        # 场景2: 无买入信号
        signals_no_buy = {
            "buy_signal": False,
            "current_price": 50000.0,
            "fast_ma": 49900.0,
            "slow_ma": 50100.0,
        }

        mock_broker.execute_order.reset_mock()
        result = engine.process_buy_signal("BTCUSDT", signals_no_buy, 1500.0)
        assert result is False
        mock_broker.execute_order.assert_not_called()

        # 场景3: 已有持仓
        mock_broker.positions = {"BTCUSDT": {"quantity": 0.1}}
        result = engine.process_buy_signal("BTCUSDT", signals_buy, 1500.0)
        assert result is False

        # 场景4: 零数量
        mock_broker.positions = {}
        with patch.object(engine, "calculate_position_size", return_value=0.0):
            result = engine.process_buy_signal("BTCUSDT", signals_buy, 1500.0)
            assert result is False

        # 场景5: 执行异常
        mock_broker.execute_order.side_effect = Exception("执行失败")
        with patch.object(engine, "calculate_position_size", return_value=0.1):
            result = engine.process_buy_signal("BTCUSDT", signals_buy, 1500.0)
            assert result is False
            mock_metrics.record_exception.assert_called()

    def test_process_sell_signal_all_scenarios(self):
        """测试卖出信号处理的所有场景"""
        engine, mock_broker, mock_metrics, _ = self.create_comprehensive_mock_engine()

        # 场景1: 成功卖出
        mock_broker.positions = {"BTCUSDT": {"quantity": 0.1, "entry_price": 49000.0}}
        signals_sell = {"sell_signal": True, "fast_ma": 49900.0, "slow_ma": 50100.0}

        result = engine.process_sell_signal("BTCUSDT", signals_sell)
        assert result is True
        mock_broker.execute_order.assert_called()

        # 场景2: 无卖出信号
        signals_no_sell = {"sell_signal": False, "fast_ma": 50100.0, "slow_ma": 49900.0}

        mock_broker.execute_order.reset_mock()
        result = engine.process_sell_signal("BTCUSDT", signals_no_sell)
        assert result is False
        mock_broker.execute_order.assert_not_called()

        # 场景3: 无持仓
        mock_broker.positions = {}
        result = engine.process_sell_signal("BTCUSDT", signals_sell)
        assert result is False

        # 场景4: 执行异常
        mock_broker.positions = {"BTCUSDT": {"quantity": 0.1}}
        mock_broker.execute_order.side_effect = Exception("卖出失败")
        result = engine.process_sell_signal("BTCUSDT", signals_sell)
        assert result is False
        mock_metrics.record_exception.assert_called()

    def test_update_positions_comprehensive(self):
        """全面测试仓位更新"""
        engine, mock_broker, _, _ = self.create_comprehensive_mock_engine()

        symbol = "BTCUSDT"
        current_price = 50000.0
        atr = 1500.0

        engine.update_positions(symbol, current_price, atr)

        # 验证调用
        mock_broker.update_position_stops.assert_called_once_with(symbol, current_price, atr)
        mock_broker.check_stop_loss.assert_called_once_with(symbol, current_price)

    def test_send_status_update_comprehensive(self):
        """全面测试状态更新发送"""
        engine, mock_broker, _, _ = self.create_comprehensive_mock_engine()

        signals = {"current_price": 50000.0, "fast_ma": 50100.0, "slow_ma": 49900.0}

        # 场景1: 间隔时间不够
        engine.last_status_update = datetime.now() - timedelta(minutes=30)
        engine.send_status_update("BTCUSDT", signals, 1500.0)
        mock_broker.notifier.notify.assert_not_called()

        # 场景2: 无持仓状态更新
        engine.last_status_update = datetime.now() - timedelta(hours=2)
        mock_broker.positions = {}
        mock_broker.notifier.notify.reset_mock()

        engine.send_status_update("BTCUSDT", signals, 1500.0)
        mock_broker.notifier.notify.assert_called_once()
        call_args = mock_broker.notifier.notify.call_args[0]
        status_msg = call_args[0]
        assert "无" in status_msg

        # 场景3: 有持仓状态更新
        mock_broker.positions = {
            "BTCUSDT": {"entry_price": 49000.0, "stop_price": 48000.0, "quantity": 0.1}
        }
        mock_broker.notifier.notify.reset_mock()

        engine.send_status_update("BTCUSDT", signals, 1500.0)
        mock_broker.notifier.notify.assert_called_once()
        call_args = mock_broker.notifier.notify.call_args[0]
        status_msg = call_args[0]
        assert "入场价" in status_msg
        assert "盈亏" in status_msg

    def test_execute_trading_cycle_comprehensive(self):
        """全面测试交易周期执行"""
        engine, mock_broker, mock_metrics, mock_signal_processor = (
            self.create_comprehensive_mock_engine()
        )

        # 场景1: 成功执行
        sample_data = pd.DataFrame(
            {
                "open": [50000.0, 50100.0, 50200.0],
                "high": [50100.0, 50200.0, 50300.0],
                "low": [49900.0, 50000.0, 50100.0],
                "close": [50050.0, 50150.0, 50250.0],
                "volume": [1000.0, 1100.0, 1200.0],
            }
        )

        mock_signals = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50250.0,
            "fast_ma": 50200.0,
            "slow_ma": 50000.0,
        }

        mock_signal_processor.get_trading_signals_optimized.return_value = mock_signals

        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch("src.core.signal_processor.validate_signal", return_value=True),
            patch.object(engine, "process_buy_signal", return_value=True),
            patch.object(engine, "process_sell_signal", return_value=False),
            patch.object(engine, "update_positions"),
            patch.object(engine, "send_status_update"),
            patch.object(engine, "_update_monitoring_metrics"),
        ):

            result = engine.execute_trading_cycle("BTCUSDT")
            assert result is True
            mock_metrics.observe_task_latency.assert_called()

        # 场景2: 空数据
        with patch("src.core.price_fetcher.fetch_price_data", return_value=None):
            result = engine.execute_trading_cycle("BTCUSDT")
            assert result is False

        # 场景3: 无效信号
        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch("src.core.signal_processor.validate_signal", return_value=False),
        ):
            result = engine.execute_trading_cycle("BTCUSDT")
            assert result is False

    def test_monitoring_metrics_update(self):
        """测试监控指标更新"""
        engine, _, mock_metrics, _ = self.create_comprehensive_mock_engine()

        symbol = "BTCUSDT"
        current_price = 50000.0

        engine._update_monitoring_metrics(symbol, current_price)
        mock_metrics.record_price_update.assert_called_with(symbol, current_price)

    def test_start_trading_loop_scenarios(self):
        """测试交易循环启动的各种场景"""
        engine, _, _, _ = self.create_comprehensive_mock_engine()

        # 场景1: 成功执行后停止
        with patch.object(engine, "execute_trading_cycle", return_value=False), patch("time.sleep"):
            engine.start_trading_loop("BTCUSDT", interval_seconds=1)

        # 场景2: 异常处理
        with (
            patch.object(engine, "execute_trading_cycle", side_effect=Exception("循环异常")),
            patch("time.sleep"),
        ):
            engine.start_trading_loop("BTCUSDT", interval_seconds=1)

    def test_trading_loop_function(self):
        """测试独立的trading_loop函数"""
        from src.core.trading_engine import trading_loop

        with patch("src.core.trading_engine.TradingEngine") as mock_engine_class:
            mock_engine = Mock()
            mock_engine.start_trading_loop = Mock()
            mock_engine_class.return_value = mock_engine

            trading_loop("BTCUSDT", 60)

            mock_engine_class.assert_called_once()
            mock_engine.start_trading_loop.assert_called_once_with("BTCUSDT", 60)

    # ========== 异步交易引擎测试 ==========

    def create_async_mock_engine(self):
        """创建异步Mock引擎"""
        with (
            patch("src.brokers.Broker") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            mock_broker = Mock()
            mock_broker.get_account_balance = AsyncMock(return_value={"balance": 10000.0})
            mock_broker.place_order_async = AsyncMock(
                return_value={"orderId": "12345", "status": "FILLED"}
            )
            mock_broker.positions = {}
            mock_broker.notifier = Mock()
            mock_broker_class.return_value = mock_broker

            mock_metrics_obj = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.observe_task_latency = Mock()
            mock_metrics.return_value = mock_metrics_obj

            mock_signal_processor = Mock()
            mock_processor.return_value = mock_signal_processor

            from src.core.async_trading_engine import AsyncTradingEngine

            engine = AsyncTradingEngine(api_key="test_key", api_secret="test_secret")

            return engine, mock_broker, mock_metrics_obj, mock_signal_processor

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_comprehensive(self):
        """全面测试异步交易决策"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 场景1: 成功分析
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

        # 场景2: 分析异常
        with patch.object(engine, "analyze_market_conditions", side_effect=Exception("分析失败")):
            result = await engine.async_execute_trade_decision("BTCUSDT")
            assert result["action"] == "error"
            mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_handle_websocket_data_comprehensive(self):
        """全面测试WebSocket数据处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        # 场景1: 价格更新数据
        price_data = {"e": "24hrTicker", "s": "BTCUSDT", "c": "50000.0", "v": "1000.0"}

        await engine.handle_websocket_data(price_data)
        assert engine.latest_prices.get("BTCUSDT") == 50000.0

        # 场景2: 订单更新数据
        order_data = {
            "e": "executionReport",
            "s": "BTCUSDT",
            "c": "order123",
            "X": "FILLED",
            "q": "0.1",
        }

        await engine.handle_websocket_data(order_data)
        assert "order123" in engine.active_orders

        # 场景3: 无效数据
        invalid_data = {"invalid": "data"}
        await engine.handle_websocket_data(invalid_data)
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_process_concurrent_orders_comprehensive(self):
        """全面测试并发订单处理"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine()

        orders = [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
            {"symbol": "ETHUSDT", "side": "SELL", "quantity": 1.0},
        ]

        # 场景1: 全部成功
        mock_broker.place_order_async.return_value = {"orderId": "success", "status": "FILLED"}
        results = await engine.process_concurrent_orders(orders)
        assert len(results) == 2
        assert all(r["status"] == "FILLED" for r in results)

        # 场景2: 部分失败
        mock_broker.place_order_async.side_effect = [
            {"orderId": "success", "status": "FILLED"},
            Exception("订单失败"),
        ]
        results = await engine.process_concurrent_orders(orders)
        assert len(results) == 2
        assert results[0]["status"] == "FILLED"
        assert "error" in results[1]

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics_comprehensive(self):
        """全面测试性能指标分析"""
        engine, _, _, _ = self.create_async_mock_engine()

        # 场景1: 有交易历史
        engine.trade_history = [
            {"timestamp": datetime.now(), "profit": 100.0, "symbol": "BTCUSDT"},
            {"timestamp": datetime.now(), "profit": -50.0, "symbol": "ETHUSDT"},
            {"timestamp": datetime.now(), "profit": 75.0, "symbol": "BTCUSDT"},
        ]

        metrics = await engine.analyze_performance_metrics()
        assert metrics["total_trades"] == 3
        assert metrics["total_profit"] == 125.0
        assert metrics["win_rate"] > 0

        # 场景2: 空历史
        engine.trade_history = []
        metrics = await engine.analyze_performance_metrics()
        assert metrics["total_trades"] == 0
        assert metrics["win_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_monitor_market_status_comprehensive(self):
        """全面测试市场状态监控"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine()

        # 场景1: 正常状态
        engine.latest_prices = {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0}
        status = await engine.monitor_market_status()
        assert status["active_symbols"] == 2

        # 场景2: 过期数据
        engine.latest_prices = {}
        engine.last_price_update = datetime.now().timestamp() - 3600
        status = await engine.monitor_market_status()
        assert status["market_health"] == "stale_data"
        mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_connection_management(self):
        """测试WebSocket连接管理"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine()

        # 成功连接
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(return_value='{"e":"24hrTicker","s":"BTCUSDT","c":"50000"}')

        with patch("websockets.connect", return_value=mock_websocket):
            await engine.start_websocket_connection(
                "wss://stream.binance.com:9443/ws/btcusdt@ticker"
            )
            mock_websocket.recv.assert_called()

        # 连接失败
        with patch("websockets.connect", side_effect=Exception("连接失败")):
            await engine.start_websocket_connection("wss://invalid-url")
            mock_metrics.record_exception.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_stale_orders(self):
        """测试清理过期订单"""
        engine, _, _, _ = self.create_async_mock_engine()

        old_timestamp = datetime.now().timestamp() - 3600
        engine.active_orders = {
            "old_order": {"timestamp": old_timestamp, "status": "PENDING"},
            "new_order": {"timestamp": datetime.now().timestamp(), "status": "PENDING"},
        }

        await engine.cleanup_stale_orders(max_age_seconds=1800)
        assert "old_order" not in engine.active_orders
        assert "new_order" in engine.active_orders

    @pytest.mark.asyncio
    async def test_batch_price_updates(self):
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
    async def test_emergency_stop_async(self):
        """测试异步紧急停止"""
        engine, mock_broker, _, _ = self.create_async_mock_engine()

        await engine.emergency_stop("系统异常")
        assert engine.is_running is False
        mock_broker.notifier.notify.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
