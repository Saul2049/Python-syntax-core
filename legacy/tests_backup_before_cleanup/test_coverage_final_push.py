#!/usr/bin/env python3
"""
最终覆盖率推进测试 - 针对具体未覆盖代码
Final Coverage Push Tests - Targeting Specific Uncovered Code

专门针对:
1. trading_engine.py 中未覆盖的边缘情况和错误处理
2. async_trading_engine.py 中的核心异步功能
3. 复杂的条件分支和异常处理路径
"""

import asyncio
import os
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pandas as pd
import pytest


class TestCoverageFinalPush:
    """最终覆盖率推进测试"""

    def setup_method(self):
        """测试前设置"""
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"
        os.environ["TG_TOKEN"] = "test_token"

    def create_mock_engine_with_detailed_setup(self):
        """创建详细设置的Mock引擎"""
        with (
            patch("src.brokers.Broker") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            # 详细Mock设置
            mock_broker = Mock()
            mock_broker.get_account_balance.return_value = {"balance": 10000.0}
            mock_broker.get_positions.return_value = {}
            mock_broker.positions = {}
            mock_broker.update_position_stops = Mock()
            mock_broker.check_stop_loss = Mock()
            mock_broker.execute_order = Mock()
            mock_broker.notifier = Mock()
            mock_broker.notifier.notify = Mock()
            mock_broker.notifier.notify_error = Mock()
            mock_broker_class.return_value = mock_broker

            # 详细Mock Metrics
            mock_metrics_obj = Mock()

            # 创建可用的上下文管理器
            class MockContextManager:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False

            mock_metrics_obj.measure_order_latency.return_value = MockContextManager()
            mock_metrics_obj.measure_data_fetch_latency.return_value = MockContextManager()
            mock_metrics_obj.measure_signal_latency.return_value = MockContextManager()
            mock_metrics_obj.observe_task_latency = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.record_price_update = Mock()
            mock_metrics.return_value = mock_metrics_obj

            # 详细Mock Signal Processor
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

    # ========== 交易引擎深度覆盖测试 ==========

    def test_calculate_position_size_edge_cases(self):
        """测试仓位计算的边缘情况"""
        engine, _, _, _ = self.create_mock_engine_with_detailed_setup()

        # 测试多种边缘情况
        test_cases = [
            # (current_price, atr, expected_result_condition)
            (50000.0, 1500.0, lambda x: x > 0),  # 正常情况
            (50000.0, 0.0, lambda x: x == 0.0),  # 零ATR
            (50000.0, -100.0, lambda x: x == 0.0),  # 负ATR
            (0.0, 1500.0, lambda x: x >= 0.0),  # 零价格
            (50000.0, 0.001, lambda x: x > 0),  # 极小ATR
        ]

        for price, atr, condition in test_cases:
            result = engine.calculate_position_size(price, atr, "BTCUSDT")
            assert condition(result), f"Failed for price={price}, atr={atr}, result={result}"

    def test_process_buy_signal_with_reason_generation(self):
        """测试买入信号处理和理由生成"""
        engine, mock_broker, mock_metrics, _ = self.create_mock_engine_with_detailed_setup()

        mock_broker.positions = {}

        signals = {
            "buy_signal": True,
            "current_price": 50000.0,
            "fast_ma": 50100.0,
            "slow_ma": 49900.0,
        }

        # Mock计算仓位大小
        with patch.object(engine, "calculate_position_size", return_value=0.1):
            result = engine.process_buy_signal("BTCUSDT", signals, 1500.0)

            assert result is True

            # 验证execute_order被调用时包含了正确的理由
            mock_broker.execute_order.assert_called_once()
            call_args = mock_broker.execute_order.call_args
            assert call_args[1]["symbol"] == "BTCUSDT"
            assert call_args[1]["side"] == "BUY"
            assert call_args[1]["quantity"] == 0.1
            assert "MA交叉" in call_args[1]["reason"]
            assert "50100.00" in call_args[1]["reason"]  # 快线价格
            assert "49900.00" in call_args[1]["reason"]  # 慢线价格

    def test_process_sell_signal_with_reason_generation(self):
        """测试卖出信号处理和理由生成"""
        engine, mock_broker, mock_metrics, _ = self.create_mock_engine_with_detailed_setup()

        mock_broker.positions = {"BTCUSDT": {"quantity": 0.15, "entry_price": 49000.0}}

        signals = {"sell_signal": True, "fast_ma": 49800.0, "slow_ma": 50200.0}

        result = engine.process_sell_signal("BTCUSDT", signals)

        assert result is True
        mock_broker.execute_order.assert_called_once()
        call_args = mock_broker.execute_order.call_args
        assert call_args[1]["side"] == "SELL"
        assert call_args[1]["quantity"] == 0.15
        assert "MA交叉" in call_args[1]["reason"]
        assert "下穿" in call_args[1]["reason"]

    def test_send_status_update_detailed_position_info(self):
        """测试详细持仓信息的状态更新"""
        engine, mock_broker, _, _ = self.create_mock_engine_with_detailed_setup()

        # 设置超过1小时的更新时间
        engine.last_status_update = datetime.now() - timedelta(hours=2)

        # 设置详细持仓信息
        mock_broker.positions = {
            "BTCUSDT": {"entry_price": 48000.0, "stop_price": 47000.0, "quantity": 0.25}
        }

        signals = {"current_price": 52000.0, "fast_ma": 51500.0, "slow_ma": 51000.0}  # 盈利状态

        engine.send_status_update("BTCUSDT", signals, 1500.0)

        # 验证通知被调用
        mock_broker.notifier.notify.assert_called_once()
        call_args = mock_broker.notifier.notify.call_args[0]
        status_msg = call_args[0]

        # 验证消息内容
        assert "52000.00000000" in status_msg  # 当前价格
        assert "48000.00000000" in status_msg  # 入场价
        assert "47000.00000000" in status_msg  # 止损价
        assert "0.25000000" in status_msg  # 数量

        # 计算预期的盈亏
        expected_pnl = (52000.0 - 48000.0) * 0.25  # 1000.0 USDT
        assert "1000.00000000" in status_msg

        # 计算预期的盈亏百分比
        expected_pnl_percent = ((52000.0 - 48000.0) / 48000.0) * 100  # 8.33%
        assert "8.33%" in status_msg

    def test_execute_trading_cycle_full_flow(self):
        """测试完整交易周期流程"""
        engine, mock_broker, mock_metrics, mock_signal_processor = (
            self.create_mock_engine_with_detailed_setup()
        )

        # 创建真实的价格数据
        sample_data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=100, freq="1min"),
                "open": np.random.uniform(49000, 51000, 100),
                "high": np.random.uniform(50000, 52000, 100),
                "low": np.random.uniform(48000, 50000, 100),
                "close": np.random.uniform(49500, 50500, 100),
                "volume": np.random.uniform(1000, 2000, 100),
            }
        )

        # 设置买入信号
        buy_signals = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50250.0,
            "fast_ma": 50300.0,
            "slow_ma": 50000.0,
        }

        mock_signal_processor.get_trading_signals_optimized.return_value = buy_signals
        mock_signal_processor.compute_atr_optimized.return_value = 1200.0

        # Mock各种依赖
        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch("src.core.signal_processor.validate_signal", return_value=True),
            patch.object(engine, "calculate_position_size", return_value=0.08),
        ):

            result = engine.execute_trading_cycle("BTCUSDT", fast_win=5, slow_win=20)

            assert result is True

            # 验证各种调用
            mock_signal_processor.get_trading_signals_optimized.assert_called_with(
                sample_data, 5, 20
            )
            mock_signal_processor.compute_atr_optimized.assert_called_with(sample_data)
            mock_metrics.observe_task_latency.assert_called_with("trading_cycle", unittest.mock.ANY)
            mock_broker.execute_order.assert_called_once()  # 应该执行买入

    def test_execute_trading_cycle_error_scenarios(self):
        """测试交易周期的各种错误场景"""
        engine, mock_broker, mock_metrics, mock_signal_processor = (
            self.create_mock_engine_with_detailed_setup()
        )

        # 场景1: fetch_price_data返回空DataFrame
        empty_df = pd.DataFrame()
        with patch("src.core.price_fetcher.fetch_price_data", return_value=empty_df):
            result = engine.execute_trading_cycle("BTCUSDT")
            assert result is False
            mock_metrics.record_exception.assert_called()

        # 场景2: signal validation失败
        sample_data = pd.DataFrame({"close": [50000, 50100, 50200]})
        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch("src.core.signal_processor.validate_signal", return_value=False),
        ):
            result = engine.execute_trading_cycle("BTCUSDT")
            assert result is False

        # 场景3: signal_processor抛出异常
        mock_signal_processor.get_trading_signals_optimized.side_effect = Exception("信号处理异常")
        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch("src.core.signal_processor.validate_signal", return_value=True),
        ):
            result = engine.execute_trading_cycle("BTCUSDT")
            assert result is False

    def test_start_trading_loop_interruption_handling(self):
        """测试交易循环的中断处理"""
        engine, _, _, _ = self.create_mock_engine_with_detailed_setup()

        call_count = 0

        def mock_execute_cycle(symbol):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True  # 第一次成功
            elif call_count == 2:
                raise KeyboardInterrupt("用户中断")  # 第二次用户中断
            else:
                return False  # 不应该到达这里

        with (
            patch.object(engine, "execute_trading_cycle", side_effect=mock_execute_cycle),
            patch("time.sleep") as mock_sleep,
        ):

            # 应该优雅地处理KeyboardInterrupt
            engine.start_trading_loop("BTCUSDT", interval_seconds=1)

            assert call_count == 2
            mock_sleep.assert_called_once_with(1)

    # ========== 异步引擎覆盖测试 ==========

    def create_async_mock_engine_detailed(self):
        """创建详细的异步Mock引擎"""
        with (
            patch("src.brokers.Broker") as mock_broker_class,
            patch("src.monitoring.metrics_collector.get_metrics_collector") as mock_metrics,
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
            ) as mock_processor,
        ):

            # 异步Broker设置
            mock_broker = Mock()
            mock_broker.get_account_balance = AsyncMock(return_value={"balance": 15000.0})
            mock_broker.get_positions = AsyncMock(return_value={"BTC": 0.3})
            mock_broker.place_order_async = AsyncMock(
                return_value={
                    "orderId": "async_order_123",
                    "status": "FILLED",
                    "executedQty": "0.12",
                }
            )
            mock_broker.positions = {}
            mock_broker.notifier = Mock()
            mock_broker.notifier.notify = Mock()
            mock_broker.notifier.notify_error = Mock()
            mock_broker_class.return_value = mock_broker

            # 异步Metrics设置
            mock_metrics_obj = Mock()
            mock_metrics_obj.record_exception = Mock()
            mock_metrics_obj.observe_task_latency = Mock()
            mock_metrics_obj.record_price_update = Mock()
            mock_metrics.return_value = mock_metrics_obj

            # 异步Signal Processor设置
            mock_signal_processor = Mock()
            mock_signal_processor.get_trading_signals_optimized.return_value = {
                "buy_signal": False,
                "sell_signal": False,
                "current_price": 51000.0,
                "confidence": 0.75,
            }
            mock_processor.return_value = mock_signal_processor

            from src.core.async_trading_engine import AsyncTradingEngine

            engine = AsyncTradingEngine(api_key="test_key", api_secret="test_secret")

            return engine, mock_broker, mock_metrics_obj, mock_signal_processor

    @pytest.mark.asyncio
    async def test_async_execute_trade_decision_detailed_flow(self):
        """测试异步交易决策的详细流程"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine_detailed()

        # 设置市场分析结果 - 强买入信号
        strong_buy_analysis = {
            "status": "success",
            "current_price": 51000.0,
            "trend": "strong_bullish",
            "volatility": "low",
            "signals": {
                "buy_signal": True,
                "sell_signal": False,
                "confidence": 0.95,
                "strength": "strong",
            },
            "risk_assessment": "low",
            "market_sentiment": "bullish",
        }

        with patch.object(engine, "analyze_market_conditions", return_value=strong_buy_analysis):
            result = await engine.async_execute_trade_decision("BTCUSDT")

            assert isinstance(result, dict)
            assert "action" in result
            assert "timestamp" in result
            assert "market_analysis" in result

            # 应该基于强信号执行买入决策
            assert result["action"] in ["buy", "hold"]  # 取决于具体实现

    @pytest.mark.asyncio
    async def test_handle_websocket_data_comprehensive_scenarios(self):
        """测试WebSocket数据处理的全面场景"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine_detailed()

        # 初始化必要属性
        engine.latest_prices = {}
        engine.active_orders = {}
        engine.last_price_update = datetime.now().timestamp()

        # 场景1: 24小时ticker数据
        ticker_data = {
            "e": "24hrTicker",
            "s": "BTCUSDT",
            "c": "51500.00",  # 收盘价
            "o": "50000.00",  # 开盘价
            "h": "52000.00",  # 最高价
            "l": "49500.00",  # 最低价
            "v": "1500.50",  # 成交量
            "q": "76502500.00",  # 成交额
            "P": "3.00",  # 价格变动百分比
            "p": "1500.00",  # 价格变动
            "c": "51500.00",  # 当前价格
        }

        await engine.handle_websocket_data(ticker_data)
        assert engine.latest_prices.get("BTCUSDT") == 51500.0

        # 场景2: 订单执行报告
        execution_report = {
            "e": "executionReport",
            "s": "BTCUSDT",
            "c": "client_order_id_123",
            "S": "BUY",
            "o": "MARKET",
            "f": "GTC",
            "q": "0.10000000",
            "p": "0.00000000",
            "P": "0.00000000",
            "F": "0.00000000",
            "g": -1,
            "C": "null",
            "x": "TRADE",
            "X": "FILLED",
            "r": "NONE",
            "i": "order_id_456",
            "l": "0.10000000",
            "z": "0.10000000",
            "L": "51500.00000000",
            "n": "0.00051500",
            "N": "BNB",
            "T": 1640995200000,
            "a": 0,
            "t": "trade_id_789",
            "m": False,
            "M": False,
        }

        await engine.handle_websocket_data(execution_report)
        assert "client_order_id_123" in engine.active_orders
        assert engine.active_orders["client_order_id_123"]["status"] == "FILLED"

        # 场景3: 深度数据更新
        depth_data = {
            "e": "depthUpdate",
            "s": "BTCUSDT",
            "U": 157,
            "u": 160,
            "b": [["51400.00000000", "0.25000000"], ["51300.00000000", "0.50000000"]],
            "a": [["51500.00000000", "0.30000000"], ["51600.00000000", "0.40000000"]],
        }

        await engine.handle_websocket_data(depth_data)
        # 深度数据应该更新订单簿信息

    @pytest.mark.asyncio
    async def test_process_concurrent_orders_performance(self):
        """测试并发订单处理性能"""
        engine, mock_broker, mock_metrics, _ = self.create_async_mock_engine_detailed()

        # 创建大量订单测试并发性能
        orders = []
        for i in range(10):
            orders.append(
                {
                    "symbol": f"BTC{i}USDT",
                    "side": "BUY" if i % 2 == 0 else "SELL",
                    "quantity": 0.1 + (i * 0.01),
                    "order_id": f"concurrent_order_{i}",
                }
            )

        # Mock异步订单执行
        async def mock_place_order_async(**kwargs):
            await asyncio.sleep(0.01)  # 模拟网络延迟
            return {
                "orderId": kwargs.get("order_id", "default_id"),
                "status": "FILLED",
                "executedQty": str(kwargs.get("quantity", 0.1)),
            }

        mock_broker.place_order_async.side_effect = mock_place_order_async

        start_time = time.time()
        results = await engine.process_concurrent_orders(orders)
        end_time = time.time()

        # 验证结果
        assert len(results) == 10
        assert all(result["status"] == "FILLED" for result in results)

        # 验证并发执行比顺序执行快
        # 如果是顺序执行，至少需要 10 * 0.01 = 0.1 秒
        # 并发执行应该接近 0.01 秒
        execution_time = end_time - start_time
        assert execution_time < 0.05  # 应该明显快于顺序执行

    @pytest.mark.asyncio
    async def test_analyze_performance_metrics_detailed(self):
        """测试详细的性能指标分析"""
        engine, _, _, _ = self.create_async_mock_engine_detailed()

        # 设置复杂的交易历史数据
        engine.trade_history = []

        # 添加各种类型的交易
        trade_types = [
            {"profit": 150.0, "symbol": "BTCUSDT", "duration": 3600},  # 盈利交易
            {"profit": -75.0, "symbol": "ETHUSDT", "duration": 1800},  # 亏损交易
            {"profit": 200.0, "symbol": "BTCUSDT", "duration": 7200},  # 大盈利
            {"profit": -25.0, "symbol": "ADAUSDT", "duration": 600},  # 小亏损
            {"profit": 50.0, "symbol": "ETHUSDT", "duration": 2400},  # 小盈利
            {"profit": -100.0, "symbol": "BTCUSDT", "duration": 5400},  # 中亏损
            {"profit": 300.0, "symbol": "BTCUSDT", "duration": 10800},  # 最大盈利
        ]

        base_time = datetime.now()
        for i, trade in enumerate(trade_types):
            trade["timestamp"] = base_time - timedelta(hours=i)
            engine.trade_history.append(trade)

        metrics = await engine.analyze_performance_metrics()

        # 验证基本指标
        assert metrics["total_trades"] == 7
        assert metrics["total_profit"] == 500.0  # 150-75+200-25+50-100+300
        assert metrics["win_rate"] == 4 / 7  # 4胜3负

        # 验证高级指标
        assert "average_profit_per_trade" in metrics
        assert "max_profit" in metrics
        assert "max_loss" in metrics
        assert "profit_factor" in metrics
        assert "sharpe_ratio" in metrics

        assert metrics["max_profit"] == 300.0
        assert metrics["max_loss"] == -100.0
        assert metrics["average_profit_per_trade"] == 500.0 / 7

    @pytest.mark.asyncio
    async def test_monitor_market_status_detailed(self):
        """测试详细的市场状态监控"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine_detailed()

        # 设置复杂的市场数据
        engine.latest_prices = {
            "BTCUSDT": 51000.0,
            "ETHUSDT": 3200.0,
            "ADAUSDT": 1.25,
            "BNBUSDT": 420.0,
            "SOLUSDT": 180.0,
        }

        # 设置价格历史用于波动性计算
        engine.price_history = {
            "BTCUSDT": [50000.0, 50500.0, 51000.0, 50800.0, 51000.0],
            "ETHUSDT": [3000.0, 3100.0, 3200.0, 3150.0, 3200.0],
            "ADAUSDT": [1.20, 1.22, 1.25, 1.23, 1.25],
        }

        engine.last_price_update = datetime.now().timestamp()

        status = await engine.monitor_market_status()

        # 验证基本状态
        assert status["market_health"] == "healthy"
        assert status["active_symbols"] == 5
        assert "total_market_cap" in status
        assert "average_volatility" in status

        # 验证具体币种状态
        assert "symbol_status" in status
        assert "BTCUSDT" in status["symbol_status"]
        assert "ETHUSDT" in status["symbol_status"]

    @pytest.mark.asyncio
    async def test_websocket_connection_resilience(self):
        """测试WebSocket连接的弹性和恢复能力"""
        engine, _, mock_metrics, _ = self.create_async_mock_engine_detailed()

        # 场景1: 连接成功然后断开
        mock_websocket = AsyncMock()

        # 模拟接收几条消息后连接断开
        message_count = 0

        async def mock_recv():
            nonlocal message_count
            message_count += 1
            if message_count <= 3:
                return f'{{"e":"24hrTicker","s":"BTCUSDT","c":"{50000 + message_count * 100}"}}'
            else:
                raise Exception("Connection lost")

        mock_websocket.recv = mock_recv
        mock_websocket.close = AsyncMock()

        with patch("websockets.connect", return_value=mock_websocket):
            await engine.start_websocket_connection(
                "wss://stream.binance.com:9443/ws/btcusdt@ticker"
            )

            # 应该记录异常但不崩溃
            mock_metrics.record_exception.assert_called()
            assert message_count == 4  # 应该处理了3条消息，第4条导致异常

    @pytest.mark.asyncio
    async def test_cleanup_stale_orders_detailed(self):
        """测试详细的过期订单清理"""
        engine, _, _, _ = self.create_async_mock_engine_detailed()

        current_time = datetime.now().timestamp()

        # 设置各种状态和时间的订单
        engine.active_orders = {
            "recent_pending": {
                "timestamp": current_time - 300,  # 5分钟前
                "status": "PENDING",
                "symbol": "BTCUSDT",
            },
            "old_pending": {
                "timestamp": current_time - 3600,  # 1小时前
                "status": "PENDING",
                "symbol": "ETHUSDT",
            },
            "recent_filled": {
                "timestamp": current_time - 600,  # 10分钟前
                "status": "FILLED",
                "symbol": "ADAUSDT",
            },
            "very_old_pending": {
                "timestamp": current_time - 7200,  # 2小时前
                "status": "PENDING",
                "symbol": "BNBUSDT",
            },
            "old_cancelled": {
                "timestamp": current_time - 5400,  # 1.5小时前
                "status": "CANCELLED",
                "symbol": "SOLUSDT",
            },
        }

        # 清理30分钟以上的订单
        await engine.cleanup_stale_orders(max_age_seconds=1800)

        # 验证清理结果
        remaining_orders = engine.active_orders

        # 应该保留的订单
        assert "recent_pending" in remaining_orders
        assert "recent_filled" in remaining_orders

        # 应该被清理的订单
        assert "old_pending" not in remaining_orders
        assert "very_old_pending" not in remaining_orders
        assert "old_cancelled" not in remaining_orders

    @pytest.mark.asyncio
    async def test_emergency_stop_comprehensive(self):
        """测试全面的紧急停止功能"""
        engine, mock_broker, _, _ = self.create_async_mock_engine_detailed()

        # 设置引擎运行状态
        engine.is_running = True
        engine.active_orders = {"order1": {"status": "PENDING"}, "order2": {"status": "PENDING"}}

        # 设置一些活跃任务
        engine.active_tasks = [
            asyncio.create_task(asyncio.sleep(10)),
            asyncio.create_task(asyncio.sleep(20)),
        ]

        reason = "检测到异常市场条件"
        await engine.emergency_stop(reason)

        # 验证停止状态
        assert engine.is_running is False

        # 验证通知被发送
        mock_broker.notifier.notify.assert_called()
        call_args = mock_broker.notifier.notify.call_args[0]
        emergency_msg = call_args[0]
        assert "紧急停止" in emergency_msg or "Emergency Stop" in emergency_msg
        assert reason in emergency_msg

        # 验证任务被取消
        for task in engine.active_tasks:
            assert task.cancelled()


if __name__ == "__main__":
    # 导入unittest.mock用于某些测试
    import unittest.mock

    pytest.main([__file__, "-v", "--tb=short"])
