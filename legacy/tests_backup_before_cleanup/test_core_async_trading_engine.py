#!/usr/bin/env python3
"""
测试 AsyncTradingEngine 异步交易引擎
Test AsyncTradingEngine async trading engine
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.core.async_trading_engine import AsyncTradingEngine, create_async_trading_engine


class TestAsyncTradingEngine:
    """测试 AsyncTradingEngine 类"""

    @pytest.fixture
    def engine(self):
        """创建测试用的交易引擎实例"""
        return AsyncTradingEngine(
            api_key="test_key",
            api_secret="test_secret",
            symbols=["BTCUSDT", "ETHUSDT"],
            testnet=True,
        )

    @pytest.fixture
    def sample_kline_data(self):
        """样本K线数据"""
        return {
            "symbol": "BTCUSDT",
            "timestamp": pd.Timestamp("2024-01-01 12:00:00"),
            "open": 50000.0,
            "high": 50100.0,
            "low": 49900.0,
            "close": 50050.0,
            "volume": 100.0,
            "is_closed": True,
        }

    @pytest.fixture
    def sample_signals(self):
        """样本交易信号"""
        return {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50050.0,
            "latency_ms": 5.2,
        }

    def test_init(self, engine):
        """测试初始化"""
        assert engine.api_key == "test_key"
        assert engine.api_secret == "test_secret"
        assert engine.symbols == ["BTCUSDT", "ETHUSDT"]
        assert engine.testnet is True
        assert engine.max_data_points == 200
        assert engine.fast_win == 7
        assert engine.slow_win == 25
        assert engine.risk_percent == 0.01
        assert engine.account_equity == 10000.0
        assert engine.running is False
        assert engine.cycle_count == 0
        assert engine.signal_count == 0
        assert engine.order_count == 0
        assert isinstance(engine.market_data, dict)
        assert isinstance(engine.positions, dict)
        assert isinstance(engine.last_signals, dict)
        assert isinstance(engine.concurrent_tasks, dict)

    @pytest.mark.asyncio
    @patch("src.core.async_trading_engine.BinanceWSClient")
    @patch("src.core.async_trading_engine.LiveBrokerAsync")
    async def test_initialize_success(self, mock_broker_class, mock_ws_class, engine):
        """测试成功初始化"""
        # Mock WebSocket客户端
        mock_ws = AsyncMock()
        mock_ws_class.return_value = mock_ws

        # Mock异步代理
        mock_broker = AsyncMock()
        mock_broker.init_session = AsyncMock()
        mock_broker_class.return_value = mock_broker

        await engine.initialize()

        # 验证WebSocket客户端创建
        mock_ws_class.assert_called_once_with(
            symbols=["BTCUSDT", "ETHUSDT"], on_kline_callback=engine._handle_market_data
        )

        # 验证代理初始化
        mock_broker_class.assert_called_once_with(
            api_key="test_key", api_secret="test_secret", testnet=True
        )
        mock_broker.init_session.assert_called_once()

        # 验证数据结构初始化
        assert "BTCUSDT" in engine.market_data
        assert "ETHUSDT" in engine.market_data
        assert "BTCUSDT" in engine.last_signals
        assert "ETHUSDT" in engine.last_signals

    @pytest.mark.asyncio
    @patch("src.core.async_trading_engine.BinanceWSClient")
    async def test_initialize_failure(self, mock_ws_class, engine):
        """测试初始化失败"""
        mock_ws_class.side_effect = Exception("WebSocket初始化失败")

        with pytest.raises(Exception, match="WebSocket初始化失败"):
            await engine.initialize()

    @pytest.mark.asyncio
    async def test_handle_market_data_incomplete_kline(self, engine, sample_kline_data):
        """测试处理未完成的K线数据"""
        # 设置为未完成的K线
        sample_kline_data["is_closed"] = False

        # 初始化市场数据
        engine.market_data["BTCUSDT"] = pd.DataFrame()

        await engine._handle_market_data(sample_kline_data)

        # 验证未完成的K线不被处理
        assert len(engine.market_data["BTCUSDT"]) == 0

    @pytest.mark.asyncio
    @patch("asyncio.create_task")
    async def test_handle_market_data_success(self, mock_create_task, engine, sample_kline_data):
        """测试成功处理市场数据"""
        # 初始化市场数据
        engine.market_data["BTCUSDT"] = pd.DataFrame()

        # Mock异步任务
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task

        await engine._handle_market_data(sample_kline_data)

        # 验证数据被添加
        assert len(engine.market_data["BTCUSDT"]) == 1
        assert engine.market_data["BTCUSDT"].iloc[0]["close"] == 50050.0

        # 验证异步任务被创建
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_market_data_limit_data_points(self, engine, sample_kline_data):
        """测试数据点数量限制"""
        # 设置较小的最大数据点数
        engine.max_data_points = 2

        # 创建初始数据
        initial_data = pd.DataFrame(
            [
                {"open": 49000, "high": 49100, "low": 48900, "close": 49050, "volume": 50},
                {"open": 49050, "high": 49150, "low": 48950, "close": 49100, "volume": 60},
            ],
            index=[pd.Timestamp("2024-01-01 10:00:00"), pd.Timestamp("2024-01-01 11:00:00")],
        )

        engine.market_data["BTCUSDT"] = initial_data

        await engine._handle_market_data(sample_kline_data)

        # 验证只保留最近的数据点
        assert len(engine.market_data["BTCUSDT"]) == 2
        assert engine.market_data["BTCUSDT"].iloc[-1]["close"] == 50050.0

    @pytest.mark.asyncio
    async def test_handle_market_data_exception(self, engine):
        """测试处理市场数据异常"""
        # 传入无效数据
        invalid_data = {"invalid": "data"}

        with patch.object(engine.logger, "error") as mock_logger:
            await engine._handle_market_data(invalid_data)
            mock_logger.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_trading_signal_insufficient_data(self, engine):
        """测试数据不足时的信号处理"""
        # 设置不足的数据
        engine.market_data["BTCUSDT"] = pd.DataFrame(
            [{"open": 50000, "high": 50100, "low": 49900, "close": 50050, "volume": 100}]
        )

        # 应该直接返回，不处理信号
        await engine._process_trading_signal("BTCUSDT")

        assert engine.signal_count == 0

    @pytest.mark.asyncio
    @patch("src.core.async_trading_engine.OptimizedSignalProcessor")
    async def test_process_trading_signal_success(
        self, mock_processor_class, engine, sample_signals
    ):
        """测试成功处理交易信号"""
        # Mock信号处理器
        mock_processor = MagicMock()
        mock_processor.get_trading_signals_optimized.return_value = sample_signals
        mock_processor.compute_atr_optimized.return_value = 500.0
        engine.signal_processor = mock_processor

        # 创建足够的市场数据
        data = pd.DataFrame(
            [
                {
                    "open": 50000 + i,
                    "high": 50100 + i,
                    "low": 49900 + i,
                    "close": 50050 + i,
                    "volume": 100,
                }
                for i in range(30)
            ]
        )
        engine.market_data["BTCUSDT"] = data

        # Mock交易逻辑执行
        with patch.object(engine, "_execute_trading_logic", new_callable=AsyncMock) as mock_execute:
            await engine._process_trading_signal("BTCUSDT")

            # 验证信号处理
            mock_processor.get_trading_signals_optimized.assert_called_once()
            mock_processor.compute_atr_optimized.assert_called_once()

            # 验证交易逻辑被调用
            mock_execute.assert_called_once_with("BTCUSDT", sample_signals, 500.0)

            # 验证统计更新
            assert engine.signal_count == 1
            assert "BTCUSDT" in engine.last_signals

    @pytest.mark.asyncio
    async def test_execute_trading_logic_buy_signal(self, engine, sample_signals):
        """测试买入信号执行"""
        with patch.object(engine, "_execute_buy_order", new_callable=AsyncMock) as mock_buy:
            await engine._execute_trading_logic("BTCUSDT", sample_signals, 500.0)

            mock_buy.assert_called_once_with("BTCUSDT", 50050.0, 500.0)
            assert engine.cycle_count == 1

    @pytest.mark.asyncio
    async def test_execute_trading_logic_sell_signal(self, engine):
        """测试卖出信号执行"""
        # 设置卖出信号
        sell_signals = {
            "buy_signal": False,
            "sell_signal": True,
            "current_price": 50050.0,
            "latency_ms": 5.2,
        }

        # 设置现有持仓
        engine.positions["BTCUSDT"] = {"side": "LONG", "quantity": 0.1, "entry_price": 49000.0}

        with patch.object(engine, "_execute_sell_order", new_callable=AsyncMock) as mock_sell:
            await engine._execute_trading_logic("BTCUSDT", sell_signals, 500.0)

            mock_sell.assert_called_once_with("BTCUSDT", 50050.0)

    @pytest.mark.asyncio
    async def test_execute_trading_logic_position_monitoring(self, engine):
        """测试持仓监控"""
        # 设置持有信号（无买卖信号）
        hold_signals = {
            "buy_signal": False,
            "sell_signal": False,
            "current_price": 50050.0,
            "latency_ms": 5.2,
        }

        # 设置现有持仓
        engine.positions["BTCUSDT"] = {"side": "LONG", "quantity": 0.1, "entry_price": 49000.0}

        with patch.object(
            engine, "_update_position_monitoring", new_callable=AsyncMock
        ) as mock_monitor:
            await engine._execute_trading_logic("BTCUSDT", hold_signals, 500.0)

            mock_monitor.assert_called_once_with("BTCUSDT", 50050.0, 500.0)

    @pytest.mark.asyncio
    async def test_execute_buy_order_success(self, engine):
        """测试成功执行买入订单"""
        # Mock代理
        mock_broker = AsyncMock()
        mock_broker.place_order_async.return_value = {"order_id": "12345"}
        engine.broker = mock_broker

        await engine._execute_buy_order("BTCUSDT", 50000.0, 500.0)

        # 验证订单被下达
        mock_broker.place_order_async.assert_called_once()
        call_args = mock_broker.place_order_async.call_args[1]
        assert call_args["symbol"] == "BTCUSDT"
        assert call_args["side"] == "BUY"
        assert call_args["order_type"] == "MARKET"

        # 验证持仓被记录
        assert "BTCUSDT" in engine.positions
        position = engine.positions["BTCUSDT"]
        assert position["side"] == "LONG"
        assert position["entry_price"] == 50000.0
        assert position["order_id"] == "12345"
        assert engine.order_count == 1

    @pytest.mark.asyncio
    async def test_execute_buy_order_invalid_risk(self, engine):
        """测试无效风险参数的买入订单"""
        # 设置无效的ATR（导致风险计算错误）
        await engine._execute_buy_order("BTCUSDT", 50000.0, 0.0)

        # 验证没有持仓被创建
        assert "BTCUSDT" not in engine.positions
        assert engine.order_count == 0

    @pytest.mark.asyncio
    async def test_execute_buy_order_exception(self, engine):
        """测试买入订单异常"""
        # Mock代理抛出异常
        mock_broker = AsyncMock()
        mock_broker.place_order_async.side_effect = Exception("订单失败")
        engine.broker = mock_broker

        with patch.object(engine.logger, "error") as mock_logger:
            await engine._execute_buy_order("BTCUSDT", 50000.0, 500.0)

            mock_logger.assert_called_once()
            assert "BTCUSDT" not in engine.positions

    @pytest.mark.asyncio
    async def test_execute_sell_order_success(self, engine):
        """测试成功执行卖出订单"""
        # 设置现有持仓
        engine.positions["BTCUSDT"] = {"side": "LONG", "quantity": 0.1, "entry_price": 49000.0}

        # Mock代理
        mock_broker = AsyncMock()
        engine.broker = mock_broker

        await engine._execute_sell_order("BTCUSDT", 50000.0)

        # 验证订单被下达
        mock_broker.place_order_async.assert_called_once()
        call_args = mock_broker.place_order_async.call_args[1]
        assert call_args["symbol"] == "BTCUSDT"
        assert call_args["side"] == "SELL"
        assert call_args["quantity"] == 0.1

        # 验证持仓被移除
        assert "BTCUSDT" not in engine.positions
        assert engine.order_count == 1

    @pytest.mark.asyncio
    async def test_execute_sell_order_no_position(self, engine):
        """测试无持仓时的卖出订单"""
        # Mock代理
        mock_broker = AsyncMock()
        engine.broker = mock_broker

        await engine._execute_sell_order("BTCUSDT", 50000.0)

        # 验证没有订单被下达
        mock_broker.place_order_async.assert_not_called()
        assert engine.order_count == 0

    @pytest.mark.asyncio
    async def test_update_position_monitoring_stop_loss(self, engine):
        """测试止损触发"""
        # 设置持仓
        engine.positions["BTCUSDT"] = {
            "side": "LONG",
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 49500.0,
        }

        with patch.object(engine, "_execute_sell_order", new_callable=AsyncMock) as mock_sell:
            # 当前价格低于止损价
            await engine._update_position_monitoring("BTCUSDT", 49400.0, 500.0)

            mock_sell.assert_called_once_with("BTCUSDT", 49400.0)

    @pytest.mark.asyncio
    async def test_update_position_monitoring_no_stop_loss(self, engine):
        """测试未触发止损"""
        # 设置持仓
        engine.positions["BTCUSDT"] = {
            "side": "LONG",
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 49500.0,
        }

        with patch.object(engine, "_execute_sell_order", new_callable=AsyncMock) as mock_sell:
            # 当前价格高于止损价
            await engine._update_position_monitoring("BTCUSDT", 50500.0, 500.0)

            mock_sell.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_position_monitoring_no_position(self, engine):
        """测试无持仓时的监控"""
        with patch.object(engine, "_execute_sell_order", new_callable=AsyncMock) as mock_sell:
            await engine._update_position_monitoring("BTCUSDT", 50000.0, 500.0)

            mock_sell.assert_not_called()

    @pytest.mark.asyncio
    @patch("asyncio.gather")
    async def test_run_success(self, mock_gather, engine):
        """测试成功运行引擎"""
        # Mock WebSocket客户端
        mock_ws = AsyncMock()
        mock_ws.run.return_value = None
        engine.ws_client = mock_ws

        # Mock gather返回
        mock_gather.return_value = [None, None, None]

        with patch.object(engine, "cleanup", new_callable=AsyncMock) as mock_cleanup:
            await engine.run()

            # 验证gather被调用
            mock_gather.assert_called_once()
            args = mock_gather.call_args[0]
            assert len(args) == 3  # 三个并发任务

            # 验证清理被调用
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_keyboard_interrupt(self, engine):
        """测试键盘中断"""
        # Mock WebSocket客户端
        mock_ws = AsyncMock()
        mock_ws.run.side_effect = KeyboardInterrupt()
        engine.ws_client = mock_ws

        with patch.object(engine, "cleanup", new_callable=AsyncMock) as mock_cleanup:
            with patch("asyncio.gather", side_effect=KeyboardInterrupt()):
                await engine.run()

            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_monitoring_loop(self, engine):
        """测试状态监控循环"""
        # 使用更简单的方法：只运行一次循环然后停止
        engine.running = True
        loop_count = 0

        original_sleep = asyncio.sleep

        async def controlled_sleep(duration):
            nonlocal loop_count
            loop_count += 1
            if loop_count >= 2:  # 运行两次后停止
                engine.running = False
            # 使用很短的实际延迟
            await original_sleep(0.001)

        # 简单地mock sleep，不mock create_task
        with patch("asyncio.sleep", side_effect=controlled_sleep):
            await engine._status_monitoring_loop()

        # 验证循环至少运行了一次
        assert loop_count >= 1

    @pytest.mark.asyncio
    async def test_performance_monitoring_loop(self, engine):
        """测试性能监控循环"""
        # 使用更简单的方法：只运行一次循环然后停止
        engine.running = True
        loop_count = 0

        original_sleep = asyncio.sleep

        async def controlled_sleep(duration):
            nonlocal loop_count
            loop_count += 1
            if loop_count >= 2:  # 运行两次后停止
                engine.running = False
            # 使用很短的实际延迟
            await original_sleep(0.001)

        with patch.object(engine, "get_performance_stats") as mock_stats:
            mock_stats.return_value = {"engine": {"cycle_count": 10}}

            # 简单地mock sleep，不mock create_task
            with patch("asyncio.sleep", side_effect=controlled_sleep):
                await engine._performance_monitoring_loop()

            # 验证统计被获取
            assert mock_stats.call_count >= 1
            assert loop_count >= 1

    def test_batch_update_metrics(self, engine):
        """测试批量更新指标"""
        stats = {
            "engine": {"cycle_count": 100, "signal_count": 50},
            "websocket": {"queue_size": 10},
        }

        # 这个方法主要是调用metrics，我们验证它不会抛出异常
        engine._batch_update_metrics(stats)

    @pytest.mark.asyncio
    async def test_cleanup(self, engine):
        """测试资源清理"""
        # Mock WebSocket客户端
        mock_ws = AsyncMock()
        engine.ws_client = mock_ws

        # Mock代理
        mock_broker = AsyncMock()
        engine.broker = mock_broker

        # Mock并发任务
        mock_task = MagicMock()
        mock_task.done.return_value = False
        engine.concurrent_tasks["test"] = mock_task

        await engine.cleanup()

        # 验证清理操作
        assert engine.running is False
        mock_ws.close.assert_called_once()
        mock_broker.close_session.assert_called_once()
        mock_task.cancel.assert_called_once()

    def test_get_performance_stats(self, engine):
        """测试获取性能统计"""
        # Mock代理和WebSocket统计
        mock_broker = MagicMock()
        mock_broker.get_performance_stats.return_value = {"orders": 10}
        engine.broker = mock_broker

        mock_ws = MagicMock()
        mock_ws.get_stats.return_value = {"messages": 100}
        engine.ws_client = mock_ws

        # 设置一些引擎状态
        engine.running = True
        engine.cycle_count = 50
        engine.signal_count = 25
        engine.order_count = 5
        engine.positions = {"BTCUSDT": {}}

        stats = engine.get_performance_stats()

        # 验证统计结构
        assert "engine" in stats
        assert "broker" in stats
        assert "websocket" in stats

        engine_stats = stats["engine"]
        assert engine_stats["running"] is True
        assert engine_stats["cycle_count"] == 50
        assert engine_stats["signal_count"] == 25
        assert engine_stats["order_count"] == 5
        assert engine_stats["active_positions"] == 1
        assert engine_stats["symbols_monitored"] == 2

    def test_get_performance_stats_no_components(self, engine):
        """测试无组件时的性能统计"""
        stats = engine.get_performance_stats()

        # 验证即使没有broker和ws_client也能正常工作
        assert "engine" in stats
        assert "broker" in stats
        assert "websocket" in stats
        assert stats["broker"] == {}
        assert stats["websocket"] == {}


class TestAsyncTradingEngineUtilities:
    """测试工具函数"""

    @pytest.mark.asyncio
    @patch("src.core.async_trading_engine.AsyncTradingEngine")
    async def test_create_async_trading_engine(self, mock_engine_class):
        """测试创建异步交易引擎工具函数"""
        # Mock引擎实例
        mock_engine = AsyncMock()
        mock_engine.initialize = AsyncMock()
        mock_engine_class.return_value = mock_engine

        result = await create_async_trading_engine(
            api_key="test_key", api_secret="test_secret", symbols=["BTCUSDT"], testnet=True
        )

        # 验证引擎被创建和初始化
        mock_engine_class.assert_called_once_with("test_key", "test_secret", ["BTCUSDT"], True)
        mock_engine.initialize.assert_called_once()
        assert result == mock_engine


class TestAsyncTradingEngineEdgeCases:
    """测试边界情况"""

    @pytest.fixture
    def engine(self):
        """创建测试用的交易引擎实例"""
        return AsyncTradingEngine(
            api_key="test_key", api_secret="test_secret", symbols=["BTCUSDT"], testnet=True
        )

    @pytest.fixture
    def sample_kline_data(self):
        """样本K线数据"""
        return {
            "symbol": "BTCUSDT",
            "timestamp": pd.Timestamp("2024-01-01 12:00:00"),
            "open": 50000.0,
            "high": 50100.0,
            "low": 49900.0,
            "close": 50050.0,
            "volume": 100.0,
            "is_closed": True,
        }

    @pytest.mark.asyncio
    async def test_handle_market_data_new_symbol(self, engine):
        """测试处理新交易对的市场数据"""
        # 新交易对的数据
        new_symbol_data = {
            "symbol": "NEWUSDT",
            "timestamp": pd.Timestamp("2024-01-01 12:00:00"),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 50.0,
            "is_closed": True,
        }

        await engine._handle_market_data(new_symbol_data)

        # 验证新交易对数据被创建
        assert "NEWUSDT" in engine.market_data
        assert len(engine.market_data["NEWUSDT"]) == 1

    @pytest.mark.asyncio
    async def test_process_trading_signal_exception_handling(self, engine):
        """测试信号处理异常处理"""
        # 设置足够的数据但让信号处理器抛出异常
        data = pd.DataFrame(
            [
                {
                    "open": 50000 + i,
                    "high": 50100 + i,
                    "low": 49900 + i,
                    "close": 50050 + i,
                    "volume": 100,
                }
                for i in range(30)
            ]
        )
        engine.market_data["BTCUSDT"] = data

        # Mock信号处理器抛出异常
        engine.signal_processor.get_trading_signals_optimized = MagicMock(
            side_effect=Exception("信号处理失败")
        )

        with patch.object(engine.logger, "error") as mock_logger:
            await engine._process_trading_signal("BTCUSDT")

            mock_logger.assert_called_once()
            assert engine.signal_count == 0

    @pytest.mark.asyncio
    async def test_execute_trading_logic_exception_handling(self, engine):
        """测试交易逻辑异常处理"""
        signals = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50050.0,
            "latency_ms": 5.2,
        }

        # Mock买入订单抛出异常
        with patch.object(engine, "_execute_buy_order", new_callable=AsyncMock) as mock_buy:
            mock_buy.side_effect = Exception("买入失败")

            with patch.object(engine.logger, "error") as mock_logger:
                await engine._execute_trading_logic("BTCUSDT", signals, 500.0)

                mock_logger.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitoring_loops_cancellation(self, engine):
        """测试监控循环的取消处理"""
        engine.running = True

        # 测试状态监控循环的取消 - CancelledError会被捕获并break
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError()):
            # 不应该抛出异常，而是正常退出
            await engine._status_monitoring_loop()
            # 验证循环正常退出
            assert True  # 如果能到这里说明没有抛出异常

        # 重置状态
        engine.running = True

        # 测试性能监控循环的取消 - CancelledError会被捕获并break
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError()):
            # 不应该抛出异常，而是正常退出
            await engine._performance_monitoring_loop()
            # 验证循环正常退出
            assert True  # 如果能到这里说明没有抛出异常

    @pytest.mark.asyncio
    async def test_cleanup_exception_handling(self, engine):
        """测试清理过程中的异常处理"""
        # Mock WebSocket客户端抛出异常
        mock_ws = AsyncMock()
        mock_ws.close.side_effect = Exception("关闭失败")
        engine.ws_client = mock_ws

        with patch.object(engine.logger, "error") as mock_logger:
            await engine.cleanup()

            mock_logger.assert_called_once()
            assert engine.running is False

    def test_symbols_case_conversion(self):
        """测试交易对大小写转换"""
        engine = AsyncTradingEngine(
            api_key="test_key",
            api_secret="test_secret",
            symbols=["btcusdt", "EthUsdt", "ADAUSDT"],
            testnet=True,
        )

        # 验证所有交易对都被转换为大写
        assert engine.symbols == ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

    @pytest.mark.asyncio
    async def test_concurrent_task_management(self, engine, sample_kline_data):
        """测试并发任务管理"""
        # 初始化市场数据
        engine.market_data["BTCUSDT"] = pd.DataFrame()

        # 测试1：没有现有任务时应该创建新任务
        with patch("asyncio.create_task") as mock_create_task:
            mock_new_task = AsyncMock()
            mock_create_task.return_value = mock_new_task

            await engine._handle_market_data(sample_kline_data)

            # 验证创建了新任务
            mock_create_task.assert_called_once()

        # 测试2：有正在运行的任务时不应该创建新任务
        running_task = MagicMock()
        running_task.done.return_value = False
        engine.concurrent_tasks["BTCUSDT"] = running_task

        with patch("asyncio.create_task") as mock_create_task:
            await engine._handle_market_data(sample_kline_data)

            # 验证没有创建新任务（因为已有任务在运行）
            mock_create_task.assert_not_called()

        # 测试3：任务完成后应该创建新任务
        running_task.done.return_value = True

        with patch("asyncio.create_task") as mock_create_task:
            mock_new_task = AsyncMock()
            mock_create_task.return_value = mock_new_task

            await engine._handle_market_data(sample_kline_data)

            # 验证创建了新任务
            mock_create_task.assert_called_once()
