#!/usr/bin/env python3
"""
异步交易引擎深度测试 - 专注核心逻辑覆盖率
Async Trading Engine Deep Tests - Focus on Core Logic Coverage

重点关注:
- src/core/async_trading_engine.py 异步交易系统
- 提高覆盖率从22%到80%+
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest


class TestAsyncTradingEngineDeepLogic:
    """深度测试异步交易引擎的核心逻辑"""

    def setup_method(self):
        """测试前设置"""
        # 清理导入缓存
        modules_to_clear = [
            "src.core.async_trading_engine",
            "src.brokers",
            "src.monitoring.metrics_collector",
            "src.core.signal_processor_vectorized",
            "src.core.price_fetcher",
            "src.database.position_manager",
            "src.utils.notifier",
        ]

        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

    @patch.dict(
        "sys.modules",
        {
            "src.brokers": Mock(),
            "src.monitoring.metrics_collector": Mock(),
            "src.core.signal_processor_vectorized": Mock(),
            "src.core.price_fetcher": Mock(),
            "src.database.position_manager": Mock(),
            "src.utils.notifier": Mock(),
            "websockets": Mock(),
            "asyncio": Mock(),
        },
    )
    def create_async_engine_with_mocks(self):
        """创建带有完整Mock的异步交易引擎"""
        # Mock所有外部依赖
        mock_broker = Mock()
        mock_metrics = Mock()
        mock_position_manager = Mock()
        mock_notifier = Mock()

        # Mock异步方法
        mock_broker.get_account_balance = AsyncMock(return_value={"balance": 10000.0})
        mock_broker.get_positions = AsyncMock(return_value={"BTC": 0.5})
        mock_broker.place_order = AsyncMock(
            return_value={"orderId": "12345", "status": "FILLED", "executedQty": "0.1"}
        )

        with (
            patch("src.brokers.AsyncBroker", return_value=mock_broker),
            patch(
                "src.monitoring.metrics_collector.get_metrics_collector", return_value=mock_metrics
            ),
            patch(
                "src.database.position_manager.PositionManager", return_value=mock_position_manager
            ),
            patch("src.utils.notifier.TelegramNotifier", return_value=mock_notifier),
        ):

            from src.core.async_trading_engine import AsyncTradingEngine

            engine = AsyncTradingEngine(
                api_key="test_key", api_secret="test_secret", telegram_token="test_token"
            )

            return engine, mock_broker, mock_metrics, mock_position_manager, mock_notifier

    @pytest.mark.asyncio
    async def test_init_async_engine(self):
        """测试异步引擎初始化"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        assert hasattr(engine, "broker")
        assert hasattr(engine, "metrics")
        assert hasattr(engine, "position_manager")
        assert hasattr(engine, "notifier")
        assert engine.is_running is False

    @pytest.mark.asyncio
    async def test_start_async_engine(self):
        """测试异步引擎启动"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        with (
            patch.object(engine, "_initialize_connections") as mock_init,
            patch.object(engine, "_start_background_tasks") as mock_start,
        ):

            mock_init.return_value = asyncio.Future()
            mock_init.return_value.set_result(True)
            mock_start.return_value = asyncio.Future()
            mock_start.return_value.set_result(True)

            result = await engine.start()

            assert engine.is_running is True
            mock_init.assert_called_once()
            mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_async_engine(self):
        """测试异步引擎停止"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        # 先启动引擎
        engine.is_running = True

        with patch.object(engine, "_cleanup_connections") as mock_cleanup:
            mock_cleanup.return_value = asyncio.Future()
            mock_cleanup.return_value.set_result(True)

            result = await engine.stop()

            assert engine.is_running is False
            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_market_conditions_async(self):
        """测试异步市场条件分析"""
        engine, mock_broker, _, _, _ = self.create_async_engine_with_mocks()

        # Mock价格数据
        sample_data = pd.DataFrame(
            {
                "open": [50000, 50100, 50200],
                "high": [50100, 50200, 50300],
                "low": [49900, 50000, 50100],
                "close": [50050, 50150, 50250],
                "volume": [1000, 1100, 1200],
            }
        )

        with patch(
            "src.core.price_fetcher.fetch_price_data_async", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = sample_data

            result = await engine.analyze_market_conditions("BTCUSDT")

            assert isinstance(result, dict)
            assert "current_price" in result
            assert "signal_strength" in result
            assert "recommendation" in result
            mock_fetch.assert_called_once_with("BTCUSDT")

    @pytest.mark.asyncio
    async def test_execute_trade_decision_async(self):
        """测试异步交易决策执行"""
        engine, mock_broker, _, _, _ = self.create_async_engine_with_mocks()

        market_analysis = {
            "signal_strength": 0.8,
            "recommendation": "strong_buy",
            "current_price": 50000.0,
            "atr": 1500.0,
        }

        with (
            patch.object(
                engine, "analyze_market_conditions", new_callable=AsyncMock
            ) as mock_analyze,
            patch.object(
                engine, "_validate_trading_conditions_async", new_callable=AsyncMock
            ) as mock_validate,
            patch.object(
                engine, "_execute_trading_logic_async", new_callable=AsyncMock
            ) as mock_execute,
        ):

            mock_analyze.return_value = market_analysis
            mock_validate.return_value = None  # 通过验证
            mock_execute.return_value = {
                "action": "buy",
                "success": True,
                "message": "异步交易执行成功",
            }

            result = await engine.execute_trade_decision("BTCUSDT")

            assert result["action"] == "buy"
            assert result["success"] is True
            mock_analyze.assert_called_once()
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_trading_conditions_async_insufficient_balance(self):
        """测试异步交易条件验证 - 余额不足"""
        engine, mock_broker, _, _, _ = self.create_async_engine_with_mocks()

        # Mock余额不足
        mock_broker.get_account_balance.return_value = {"balance": 50.0}

        market_analysis = {
            "signal_strength": 0.8,
            "recommendation": "strong_buy",
            "current_price": 50000.0,
        }

        result = await engine._validate_trading_conditions_async(market_analysis, force_trade=False)

        assert result is not None
        assert result["success"] is False
        assert "余额不足" in result["message"]

    @pytest.mark.asyncio
    async def test_execute_buy_trade_async(self):
        """测试异步买入交易执行"""
        engine, mock_broker, _, mock_position_manager, _ = self.create_async_engine_with_mocks()

        market_analysis = {"signal_strength": 0.8, "atr": 1500.0}

        # Mock订单执行成功
        mock_order_result = {"orderId": "12345", "status": "FILLED", "executedQty": "0.1"}
        mock_broker.place_order.return_value = mock_order_result

        with (
            patch.object(
                engine, "_calculate_position_size_async", new_callable=AsyncMock
            ) as mock_calc,
            patch.object(
                engine, "_update_trade_statistics_async", new_callable=AsyncMock
            ) as mock_update,
        ):

            mock_calc.return_value = 0.1

            result = await engine._execute_buy_trade_async("BTCUSDT", 50000.0, market_analysis)

            assert result["action"] == "buy"
            assert result["success"] is True
            assert "执行买入订单" in result["message"]
            mock_broker.place_order.assert_called_once()
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sell_trade_async(self):
        """测试异步卖出交易执行"""
        engine, mock_broker, _, mock_position_manager, _ = self.create_async_engine_with_mocks()

        # Mock足够的持仓
        mock_broker.get_positions.return_value = {"BTC": 0.5}

        market_analysis = {"signal_strength": 0.8, "atr": 1500.0}

        mock_order_result = {"orderId": "54321", "status": "FILLED", "executedQty": "0.1"}
        mock_broker.place_order.return_value = mock_order_result

        with (
            patch.object(
                engine, "_calculate_position_size_async", new_callable=AsyncMock
            ) as mock_calc,
            patch.object(
                engine, "_update_trade_statistics_async", new_callable=AsyncMock
            ) as mock_update,
        ):

            mock_calc.return_value = 0.1

            result = await engine._execute_sell_trade_async("BTCUSDT", 50000.0, market_analysis)

            assert result["action"] == "sell"
            assert result["success"] is True
            assert "执行卖出订单" in result["message"]
            mock_broker.place_order.assert_called_once()
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_position_size_async(self):
        """测试异步仓位大小计算"""
        engine, mock_broker, _, _, _ = self.create_async_engine_with_mocks()

        # Mock账户余额
        mock_broker.get_account_balance.return_value = {"balance": 10000.0}

        market_analysis = {"atr": 1500.0, "current_price": 50000.0}

        position_size = await engine._calculate_position_size_async(market_analysis)

        assert isinstance(position_size, float)
        assert position_size > 0
        assert position_size >= 0.001  # 最小交易量

    @pytest.mark.asyncio
    async def test_websocket_price_stream_handler(self):
        """测试WebSocket价格流处理"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        # Mock WebSocket消息
        price_message = {
            "symbol": "BTCUSDT",
            "price": "50000.0",
            "timestamp": datetime.now().isoformat(),
        }

        with patch.object(engine, "_process_price_update", new_callable=AsyncMock) as mock_process:
            await engine._handle_price_stream(json.dumps(price_message))

            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_price_update(self):
        """测试价格更新处理"""
        engine, _, mock_metrics, _, _ = self.create_async_engine_with_mocks()

        price_data = {"symbol": "BTCUSDT", "price": 50000.0, "timestamp": datetime.now()}

        with patch.object(engine, "_check_trading_signals", new_callable=AsyncMock) as mock_check:
            await engine._process_price_update(price_data)

            # 验证价格被记录到metrics
            mock_metrics.record_price_update.assert_called_once()
            mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_trading_signals(self):
        """测试交易信号检查"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        price_data = {"symbol": "BTCUSDT", "price": 50000.0, "timestamp": datetime.now()}

        with (
            patch.object(
                engine, "analyze_market_conditions", new_callable=AsyncMock
            ) as mock_analyze,
            patch.object(engine, "_should_execute_trade", return_value=True) as mock_should,
            patch.object(engine, "execute_trade_decision", new_callable=AsyncMock) as mock_execute,
        ):

            mock_analyze.return_value = {"signal_strength": 0.8, "recommendation": "strong_buy"}

            mock_execute.return_value = {"action": "buy", "success": True}

            await engine._check_trading_signals(price_data)

            mock_analyze.assert_called_once()
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_risk_management_check(self):
        """测试风险管理检查"""
        engine, mock_broker, _, mock_position_manager, _ = self.create_async_engine_with_mocks()

        # Mock账户信息
        mock_broker.get_account_balance.return_value = {"balance": 8000.0}  # 损失了2000

        # 设置初始余额
        engine.initial_balance = 10000.0

        risk_result = await engine._perform_risk_check()

        assert isinstance(risk_result, dict)
        assert "drawdown_percent" in risk_result
        assert "risk_level" in risk_result

        # 20%的损失应该触发风险警告
        assert risk_result["drawdown_percent"] == 20.0

    @pytest.mark.asyncio
    async def test_portfolio_rebalance(self):
        """测试投资组合再平衡"""
        engine, mock_broker, _, mock_position_manager, _ = self.create_async_engine_with_mocks()

        # Mock当前持仓
        current_positions = {"BTC": 0.5, "ETH": 2.0, "ADA": 1000.0}
        mock_broker.get_positions.return_value = current_positions

        with patch.object(
            engine,
            "_calculate_target_allocations",
            return_value={
                "BTC": 0.4,  # 需要减少
                "ETH": 2.2,  # 需要增加
                "ADA": 1000.0,  # 保持不变
            },
        ) as mock_calc:

            rebalance_orders = await engine._rebalance_portfolio()

            assert isinstance(rebalance_orders, list)
            mock_calc.assert_called_once()

    @pytest.mark.asyncio
    async def test_emergency_stop_mechanism(self):
        """测试紧急停止机制"""
        engine, mock_broker, _, _, mock_notifier = self.create_async_engine_with_mocks()

        # 模拟严重损失
        mock_broker.get_account_balance.return_value = {"balance": 3000.0}  # 70%损失
        engine.initial_balance = 10000.0

        with patch.object(engine, "stop", new_callable=AsyncMock) as mock_stop:
            await engine._check_emergency_stop()

            # 损失超过50%应该触发紧急停止
            mock_stop.assert_called_once()
            mock_notifier.send_alert.assert_called()

    @pytest.mark.asyncio
    async def test_performance_analytics(self):
        """测试性能分析"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        # Mock交易历史
        engine.trade_history = [
            {"profit": 100, "timestamp": datetime.now() - timedelta(days=1)},
            {"profit": -50, "timestamp": datetime.now() - timedelta(hours=12)},
            {"profit": 200, "timestamp": datetime.now() - timedelta(hours=6)},
        ]

        analytics = await engine._calculate_performance_metrics()

        assert isinstance(analytics, dict)
        assert "total_profit" in analytics
        assert "win_rate" in analytics
        assert "sharpe_ratio" in analytics
        assert analytics["total_profit"] == 250
        assert analytics["win_rate"] == 2 / 3  # 2胜1负

    @pytest.mark.asyncio
    async def test_concurrent_order_execution(self):
        """测试并发订单执行"""
        engine, mock_broker, _, _, _ = self.create_async_engine_with_mocks()

        # 模拟多个同时的交易信号
        trade_orders = [
            {"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1},
            {"symbol": "ETHUSDT", "side": "BUY", "quantity": 1.0},
            {"symbol": "ADAUSDT", "side": "SELL", "quantity": 100.0},
        ]

        # Mock订单执行
        mock_broker.place_order.side_effect = [
            {"orderId": "1", "status": "FILLED"},
            {"orderId": "2", "status": "FILLED"},
            {"orderId": "3", "status": "FILLED"},
        ]

        results = await engine._execute_concurrent_orders(trade_orders)

        assert len(results) == 3
        assert all(result["status"] == "FILLED" for result in results)
        assert mock_broker.place_order.call_count == 3

    @pytest.mark.asyncio
    async def test_market_data_aggregation(self):
        """测试市场数据聚合"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        # Mock多个市场的价格数据
        market_data = {
            "BTCUSDT": {"price": 50000, "volume": 1000},
            "ETHUSDT": {"price": 3000, "volume": 2000},
            "ADAUSDT": {"price": 1.5, "volume": 5000},
        }

        with patch.object(engine, "_fetch_multi_market_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = market_data

            aggregated_data = await engine._aggregate_market_data(["BTCUSDT", "ETHUSDT", "ADAUSDT"])

            assert isinstance(aggregated_data, dict)
            assert len(aggregated_data) == 3
            mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """测试错误处理和恢复"""
        engine, mock_broker, _, _, _ = self.create_async_engine_with_mocks()

        # Mock broker异常
        mock_broker.place_order.side_effect = Exception("网络连接失败")

        market_analysis = {
            "signal_strength": 0.8,
            "recommendation": "strong_buy",
            "current_price": 50000.0,
            "atr": 1500.0,
        }

        result = await engine._execute_buy_trade_async("BTCUSDT", 50000.0, market_analysis)

        # 应该优雅地处理错误并返回错误响应
        assert result["success"] is False
        assert "error" in result["message"].lower()

        # 错误计数应该增加
        assert engine.error_count > 0

    def test_should_execute_trade_conditions(self):
        """测试交易执行条件判断"""
        engine, _, _, _, _ = self.create_async_engine_with_mocks()

        # 测试强信号
        strong_analysis = {"signal_strength": 0.9, "recommendation": "strong_buy"}
        assert engine._should_execute_trade(strong_analysis) is True

        # 测试弱信号
        weak_analysis = {"signal_strength": 0.3, "recommendation": "hold"}
        assert engine._should_execute_trade(weak_analysis) is False

        # 测试中等信号
        medium_analysis = {"signal_strength": 0.65, "recommendation": "buy"}
        assert engine._should_execute_trade(medium_analysis) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
