#!/usr/bin/env python3
"""
交易引擎深度测试 - 专注核心逻辑覆盖率
Trading Engine Deep Tests - Focus on Core Logic Coverage

重点关注:
- src/core/trading_engine.py 核心交易执行逻辑
- 提高覆盖率从38%到80%+
"""

import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest


class TestTradingEngineDeepLogic:
    """深度测试交易引擎的核心逻辑"""

    def setup_method(self):
        """测试前设置"""
        # 清理导入缓存
        modules_to_clear = [
            "src.core.trading_engine",
            "src.brokers",
            "src.monitoring.metrics_collector",
            "src.core.signal_processor_vectorized",
            "src.core.price_fetcher",
            "src.core.signal_processor",
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
            "src.core.signal_processor": Mock(),
            "src.core.price_fetcher": Mock(),
        },
    )
    def create_engine_with_mocks(self):
        """创建带有完整Mock的交易引擎"""
        # Mock所有外部依赖
        mock_broker = Mock()
        mock_metrics = Mock()
        mock_processor = Mock()

        # Mock broker返回值
        mock_broker.get_account_balance.return_value = {"balance": 10000.0}
        mock_broker.get_positions.return_value = {"BTC": 0.5}
        mock_broker.place_order.return_value = {
            "orderId": "12345",
            "status": "FILLED",
            "executedQty": "0.1",
        }

        with (
            patch("src.brokers.Broker", return_value=mock_broker),
            patch(
                "src.monitoring.metrics_collector.get_metrics_collector", return_value=mock_metrics
            ),
            patch(
                "src.core.signal_processor_vectorized.OptimizedSignalProcessor",
                return_value=mock_processor,
            ),
        ):

            from src.core.trading_engine import TradingEngine

            engine = TradingEngine(
                api_key="test_key", api_secret="test_secret", telegram_token="test_token"
            )

            return engine, mock_broker, mock_metrics, mock_processor

    def test_validate_trading_conditions_weak_signal(self):
        """测试弱信号的交易条件验证"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # 弱信号的市场分析
        weak_market_analysis = {
            "signal_strength": 0.3,  # 低于0.6阈值
            "recommendation": "hold",
            "current_price": 50000.0,
        }

        result = engine._validate_trading_conditions(weak_market_analysis, force_trade=False)

        assert result is not None
        assert result["action"] == "hold"
        assert "信号强度过低" in result["message"]
        assert result["success"] is True

    def test_validate_trading_conditions_strong_signal(self):
        """测试强信号的交易条件验证"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # 强信号的市场分析
        strong_market_analysis = {
            "signal_strength": 0.8,  # 高于0.6阈值
            "recommendation": "strong_buy",
            "current_price": 50000.0,
        }

        result = engine._validate_trading_conditions(strong_market_analysis, force_trade=False)

        # 强信号且余额充足应该返回None（通过验证）
        assert result is None

    def test_validate_trading_conditions_insufficient_balance(self):
        """测试余额不足的情况"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock余额不足
        mock_broker.get_account_balance.return_value = {"balance": 50.0}  # 少于100

        market_analysis = {
            "signal_strength": 0.8,
            "recommendation": "strong_buy",
            "current_price": 50000.0,
        }

        result = engine._validate_trading_conditions(market_analysis, force_trade=False)

        assert result is not None
        assert result["action"] == "none"
        assert "余额不足" in result["error"]

    def test_validate_trading_conditions_force_trade(self):
        """测试强制交易模式"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # 即使是弱信号，强制交易也应该通过
        weak_market_analysis = {
            "signal_strength": 0.3,
            "recommendation": "hold",
            "current_price": 50000.0,
        }

        result = engine._validate_trading_conditions(weak_market_analysis, force_trade=True)

        # 强制交易应该绕过信号强度检查
        assert result is None

    def test_execute_trading_logic_buy_recommendation(self):
        """测试买入推荐的交易逻辑"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        market_analysis = {
            "recommendation": "strong_buy",
            "current_price": 50000.0,
            "atr": 1500.0,
            "signal_strength": 0.8,
        }

        with (
            patch.object(
                engine, "_calculate_position_size_internal", return_value=0.1
            ) as mock_calc,
            patch.object(engine, "_execute_buy_trade") as mock_buy,
        ):

            mock_buy.return_value = {"action": "buy", "success": True}

            result = engine._execute_trading_logic("BTCUSDT", market_analysis)

            # 验证调用了买入逻辑
            mock_calc.assert_called_once_with(market_analysis)
            mock_buy.assert_called_once()

    def test_execute_trading_logic_sell_recommendation(self):
        """测试卖出推荐的交易逻辑"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        market_analysis = {
            "recommendation": "strong_sell",
            "current_price": 50000.0,
            "atr": 1500.0,
            "signal_strength": 0.8,
        }

        with (
            patch.object(
                engine, "_calculate_position_size_internal", return_value=0.1
            ) as mock_calc,
            patch.object(engine, "_execute_sell_trade") as mock_sell,
        ):

            mock_sell.return_value = {"action": "sell", "success": True}

            result = engine._execute_trading_logic("BTCUSDT", market_analysis)

            # 验证调用了卖出逻辑
            mock_calc.assert_called_once_with(market_analysis)
            mock_sell.assert_called_once()

    def test_execute_trading_logic_hold_recommendation(self):
        """测试持有推荐的交易逻辑"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        market_analysis = {
            "recommendation": "hold",
            "current_price": 50000.0,
            "atr": 1500.0,
            "signal_strength": 0.5,
        }

        with (
            patch.object(
                engine, "_calculate_position_size_internal", return_value=0.1
            ) as mock_calc,
            patch.object(engine, "_create_hold_response") as mock_hold,
        ):

            mock_hold.return_value = {"action": "hold", "success": True}

            result = engine._execute_trading_logic("BTCUSDT", market_analysis)

            # 验证调用了持有逻辑
            mock_calc.assert_called_once_with(market_analysis)
            mock_hold.assert_called_once()

    def test_calculate_position_size_internal_with_atr(self):
        """测试基于ATR的仓位计算"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock账户余额
        mock_broker.get_account_balance.return_value = {"balance": 10000.0}

        market_analysis = {"atr": 1500.0, "current_price": 50000.0}

        position_size = engine._calculate_position_size_internal(market_analysis)

        # 验证计算逻辑
        assert isinstance(position_size, float)
        assert position_size > 0
        assert position_size >= 0.001  # 最小交易量

    def test_calculate_position_size_internal_zero_atr(self):
        """测试ATR为0时的仓位计算"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        mock_broker.get_account_balance.return_value = {"balance": 10000.0}

        market_analysis = {"atr": 0.0, "current_price": 50000.0}  # ATR为0

        position_size = engine._calculate_position_size_internal(market_analysis)

        # 当ATR为0时应该使用备用计算方法
        expected_size = 10000.0 * 0.02 / 50000.0  # balance * 0.02 / price
        assert abs(position_size - expected_size) < 0.001

    def test_execute_buy_trade_success(self):
        """测试成功的买入交易"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock订单执行成功
        mock_order_result = {"orderId": "12345", "status": "FILLED", "executedQty": "0.1"}
        mock_broker.place_order.return_value = mock_order_result

        market_analysis = {"signal_strength": 0.8, "atr": 1500.0}

        with patch.object(engine, "_update_trade_statistics") as mock_update:
            result = engine._execute_buy_trade("BTCUSDT", 0.1, 50000.0, market_analysis)

            # 验证买入结果
            assert result["action"] == "buy"
            assert result["success"] is True
            assert "执行买入订单" in result["message"]
            assert result["position_size"] == 0.1
            assert result["order_info"] == mock_order_result

            # 验证统计更新被调用
            mock_update.assert_called_once_with("BTCUSDT", 50000.0)

    def test_execute_sell_trade_sufficient_position(self):
        """测试有足够持仓的卖出交易"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock足够的BTC持仓
        mock_broker.get_positions.return_value = {"BTC": 0.5}
        mock_order_result = {"orderId": "54321", "status": "FILLED", "executedQty": "0.1"}
        mock_broker.place_order.return_value = mock_order_result

        market_analysis = {"signal_strength": 0.8, "atr": 1500.0}

        with patch.object(engine, "_update_trade_statistics") as mock_update:
            result = engine._execute_sell_trade("BTCUSDT", 0.1, 50000.0, market_analysis)

            # 验证卖出结果
            assert result["action"] == "sell"
            assert result["success"] is True
            assert "执行卖出订单" in result["message"]
            assert result["position_size"] == 0.1

            # 验证统计更新被调用
            mock_update.assert_called_once_with("BTCUSDT", 50000.0)

    def test_execute_sell_trade_insufficient_position(self):
        """测试持仓不足的卖出交易"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock持仓不足
        mock_broker.get_positions.return_value = {"BTC": 0.0001}  # 少于最小交易量

        market_analysis = {"signal_strength": 0.8, "atr": 1500.0}

        with patch.object(engine, "_create_hold_response") as mock_hold:
            mock_hold.return_value = {"action": "hold", "message": "无可卖持仓"}

            result = engine._execute_sell_trade("BTCUSDT", 0.1, 50000.0, market_analysis)

            # 持仓不足应该返回持有响应
            mock_hold.assert_called_once()

    def test_execute_trade_decision_complete_flow(self):
        """测试完整的交易决策流程"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock市场分析
        with (
            patch.object(engine, "analyze_market_conditions") as mock_analyze,
            patch.object(engine, "_validate_trading_conditions", return_value=None),
            patch.object(engine, "_execute_trading_logic") as mock_execute,
        ):

            mock_analyze.return_value = {
                "signal_strength": 0.8,
                "recommendation": "strong_buy",
                "current_price": 50000.0,
                "atr": 1500.0,
            }

            mock_execute.return_value = {
                "action": "buy",
                "success": True,
                "message": "交易执行成功",
            }

            result = engine.execute_trade_decision("BTCUSDT", force_trade=False)

            # 验证完整流程被执行
            mock_analyze.assert_called_once_with("BTCUSDT")
            mock_execute.assert_called_once()
            assert result["action"] == "buy"
            assert result["success"] is True

    def test_get_engine_status_detailed(self):
        """测试详细的引擎状态获取"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # 设置一些状态
        engine.signal_count = 5
        engine.error_count = 2
        engine.last_signal_time = datetime.now()
        engine._start_time = datetime.now() - timedelta(hours=2)  # 运行2小时
        engine.peak_balance = 12000.0

        # Mock账户余额
        mock_broker.get_account_balance.return_value = {"balance": 11000.0}

        status = engine.get_engine_status()

        # 验证状态信息
        assert isinstance(status, dict)
        assert "engine_info" in status
        assert "trading_stats" in status
        assert "performance_metrics" in status

        # 验证具体数值
        assert status["trading_stats"]["signal_count"] == 5
        assert status["trading_stats"]["error_count"] == 2

    def test_start_engine_functionality(self):
        """测试引擎启动功能"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        result = engine.start_engine()

        assert isinstance(result, dict)
        assert result["status"] == "started"
        assert "start_time" in result
        assert hasattr(engine, "_start_time")

    def test_stop_engine_functionality(self):
        """测试引擎停止功能"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # 先启动引擎
        engine.start_engine()

        result = engine.stop_engine()

        assert isinstance(result, dict)
        assert result["status"] == "stopped"
        assert "stop_time" in result

    def test_process_buy_signal_valid(self):
        """测试有效买入信号处理"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        signals = {"buy_signal": True, "current_price": 50000.0, "confidence": 0.8}

        with patch("src.core.signal_processor.validate_signal", return_value=True):
            result = engine.process_buy_signal("BTCUSDT", signals, 1500.0)

            assert isinstance(result, bool)
            # 由于有Mock的broker，应该会尝试执行交易

    def test_process_sell_signal_valid(self):
        """测试有效卖出信号处理"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        signals = {"sell_signal": True, "current_price": 50000.0, "confidence": 0.8}

        with patch("src.core.signal_processor.validate_signal", return_value=True):
            result = engine.process_sell_signal("BTCUSDT", signals)

            assert isinstance(result, bool)

    def test_execute_trading_cycle_complete(self):
        """测试完整的交易周期"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock价格数据获取
        sample_data = pd.DataFrame(
            {
                "open": [50000, 50100, 50200],
                "high": [50100, 50200, 50300],
                "low": [49900, 50000, 50100],
                "close": [50050, 50150, 50250],
                "volume": [1000, 1100, 1200],
            }
        )

        # Mock信号处理器返回
        mock_signals = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50250.0,
            "confidence": 0.8,
        }
        engine.signal_processor.get_trading_signals_optimized.return_value = mock_signals

        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch.object(engine, "calculate_position_size", return_value=0.1),
            patch.object(engine, "process_buy_signal", return_value=True),
            patch.object(engine, "process_sell_signal", return_value=False),
            patch.object(engine, "update_positions"),
            patch.object(engine, "send_status_update"),
        ):

            result = engine.execute_trading_cycle("BTCUSDT", fast_win=7, slow_win=25)

            assert isinstance(result, bool)

    def test_start_trading_loop_with_mock(self):
        """测试交易循环启动（Mock版本）"""
        engine, mock_broker, _, _ = self.create_engine_with_mocks()

        # Mock execute_trading_cycle返回False来停止循环
        with (
            patch.object(engine, "execute_trading_cycle", return_value=False),
            patch("time.sleep"),
        ):  # Mock sleep避免实际等待

            # 测试方法不抛出异常
            try:
                engine.start_trading_loop("BTCUSDT", interval_seconds=1)
                assert True
            except Exception as e:
                pytest.fail(f"start_trading_loop failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
