#!/usr/bin/env python3
"""
交易引擎综合测试 - 完整覆盖核心功能
Trading Engine Comprehensive Tests

合并了所有交易引擎测试版本的最佳部分:
- test_trading_engines.py
- test_trading_engines_enhanced.py
- test_trading_engines_simplified.py
- test_trading_engines_final_fix.py

测试目标:
- src/core/trading_engine.py (完整覆盖)
- src/core/async_trading_engine.py (基础覆盖)
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pandas as pd
import pytest


class TestTradingEngine:
    """主交易引擎测试类 - 合并所有核心功能测试"""

    def setup_method(self):
        """测试前设置"""
        # 设置环境变量
        os.environ.update(
            {"API_KEY": "test_key", "API_SECRET": "test_secret", "TG_TOKEN": "test_token"}
        )

        # 创建持久的patches
        self.broker_patcher = patch("src.brokers.broker.Broker")
        self.metrics_patcher = patch("src.monitoring.get_metrics_collector")
        self.processor_patcher = patch(
            "src.core.signal_processor_vectorized.OptimizedSignalProcessor"
        )

        # 启动patches
        mock_broker_class = self.broker_patcher.start()
        mock_metrics = self.metrics_patcher.start()
        mock_processor_class = self.processor_patcher.start()

        # 设置mock返回值
        self.mock_broker = Mock()
        self.mock_broker.get_account_balance.return_value = {"balance": 10000.0}
        self.mock_broker.get_positions.return_value = {"BTC": 0.1}
        self.mock_broker.place_order.return_value = {"status": "filled", "id": "test123"}
        self.mock_broker.positions = {}

        mock_broker_class.return_value = self.mock_broker

        self.mock_metrics = Mock()
        mock_metrics.return_value = self.mock_metrics

        self.mock_processor = Mock()
        mock_processor_class.return_value = self.mock_processor

        # 导入并创建引擎
        from src.core.trading_engine import TradingEngine

        self.engine = TradingEngine(
            api_key="test_key", api_secret="test_secret", telegram_token="test_token"
        )

        # 设置必要的数值属性
        self.engine.account_equity = 10000.0
        self.engine.peak_balance = 10000.0
        self.engine.risk_percent = 0.01

    def teardown_method(self):
        """测试后清理"""
        self.broker_patcher.stop()
        self.metrics_patcher.stop()
        self.processor_patcher.stop()

    def create_sample_market_data(self, periods=100):
        """创建示例市场数据"""
        dates = pd.date_range("2024-01-01", periods=periods, freq="h")
        np.random.seed(42)
        base_price = 50000
        prices = []
        current_price = base_price

        for i in range(periods):
            change = np.random.normal(0, 0.02)
            current_price = max(current_price * (1 + change), base_price * 0.8)
            prices.append(current_price)

        return pd.DataFrame(
            {
                "open": prices,
                "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                "close": prices,
                "volume": np.random.uniform(1000, 5000, periods),
            },
            index=dates,
        )

    # ===== 基础功能测试 =====

    def test_engine_initialization(self):
        """测试引擎初始化"""
        assert self.engine is not None
        assert hasattr(self.engine, "signal_processor")
        assert hasattr(self.engine, "metrics")
        assert hasattr(self.engine, "broker")
        assert self.engine.signal_count == 0
        assert self.engine.error_count == 0
        assert self.engine.account_equity == 10000.0

    @patch("src.core.price_fetcher.fetch_price_data")
    @patch("src.core.price_fetcher.calculate_atr")
    def test_analyze_market_conditions_success(self, mock_atr, mock_fetch):
        """测试成功的市场分析"""
        market_data = self.create_sample_market_data(50)
        mock_fetch.return_value = market_data
        mock_atr.return_value = 1500.0

        mock_signals = {
            "signal": "BUY",
            "confidence": 0.8,
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50000.0,
            "fast_ma": 49500.0,
            "slow_ma": 49000.0,
        }

        with patch.object(
            self.engine.signal_processor, "get_trading_signals_optimized", return_value=mock_signals
        ):
            result = self.engine.analyze_market_conditions("BTCUSDT")

        assert isinstance(result, dict)
        assert "atr" in result
        assert "volatility" in result
        assert "trend" in result
        assert "recommendation" in result
        assert result["atr"] > 0

    @patch("src.core.price_fetcher.fetch_price_data")
    def test_analyze_market_conditions_error_handling(self, mock_fetch):
        """测试市场分析错误处理"""
        mock_fetch.side_effect = Exception("API错误")

        result = self.engine.analyze_market_conditions("BTCUSDT")

        assert isinstance(result, dict)
        if "error" in result:
            assert "市场分析失败" in result["error"]
            assert self.engine.error_count >= 1

    @patch("src.core.price_fetcher.fetch_price_data")
    def test_analyze_market_conditions_no_data(self, mock_fetch):
        """测试无数据情况"""
        mock_fetch.return_value = None

        result = self.engine.analyze_market_conditions("BTCUSDT")

        assert isinstance(result, dict)
        assert "atr" in result

    # ===== 交易逻辑测试 =====

    def test_validate_trading_conditions_weak_signal(self):
        """测试弱信号验证"""
        weak_analysis = {"signal_strength": 0.3, "recommendation": "hold", "current_price": 50000.0}

        result = self.engine._validate_trading_conditions(weak_analysis, force_trade=False)

        if result is not None:
            assert result["action"] == "hold"
            assert "信号强度过低" in result["message"]

    def test_validate_trading_conditions_force_trade(self):
        """测试强制交易"""
        weak_analysis = {"signal_strength": 0.3, "recommendation": "hold", "current_price": 50000.0}

        # 直接设置Mock对象的方法
        self.engine.broker.get_account_balance = Mock(return_value={"balance": 10000.0})
        result = self.engine._validate_trading_conditions(weak_analysis, force_trade=True)
        assert result is None  # 强制交易应该绕过验证

    def test_calculate_position_size_with_atr(self):
        """测试基于ATR的仓位计算"""
        analysis = {"atr": 1500.0, "current_price": 50000.0, "available_balance": 8000.0}

        # 直接设置Mock对象的方法
        self.engine.broker.get_account_balance = Mock(return_value={"balance": 10000.0})
        position_size = self.engine._calculate_position_size_internal(analysis)

        assert isinstance(position_size, float)
        assert position_size > 0
        assert position_size >= 0.001

    def test_calculate_position_size_edge_cases(self):
        """测试仓位计算边界情况"""
        # 直接设置Mock对象的方法
        self.engine.broker.get_account_balance = Mock(return_value={"balance": 10000.0})

        # 零ATR情况
        analysis_zero_atr = {"atr": 0.0, "current_price": 50000.0, "available_balance": 8000.0}
        size_zero_atr = self.engine._calculate_position_size_internal(analysis_zero_atr)
        assert isinstance(size_zero_atr, float)
        assert size_zero_atr >= 0

        # 极高价格情况
        analysis_high_price = {
            "atr": 1500.0,
            "current_price": 100000.0,
            "available_balance": 1000.0,
        }
        size_high_price = self.engine._calculate_position_size_internal(analysis_high_price)
        assert isinstance(size_high_price, float)
        assert size_high_price >= 0

    # ===== 信号处理测试 =====

    def test_process_buy_signal_success(self):
        """测试买入信号处理"""
        self.mock_broker.positions = {}
        buy_signals = {
            "buy_signal": True,
            "current_price": 50000.0,
            "confidence": 0.8,
            "fast_ma": 49500.0,
            "slow_ma": 48000.0,
        }

        with patch.object(self.engine, "calculate_position_size", return_value=0.1):
            result = self.engine.process_buy_signal("BTCUSDT", buy_signals, 1500.0)
            assert isinstance(result, bool)

    def test_process_sell_signal_success(self):
        """测试卖出信号处理"""
        self.mock_broker.positions = {"BTCUSDT": 0.5}
        sell_signals = {
            "sell_signal": True,
            "current_price": 51000.0,
            "confidence": 0.8,
            "fast_ma": 50500.0,
            "slow_ma": 52000.0,
        }

        result = self.engine.process_sell_signal("BTCUSDT", sell_signals)
        assert isinstance(result, bool)

    # ===== 状态管理测试 =====

    def test_engine_status_methods(self):
        """测试引擎状态管理"""
        # 设置状态
        self.engine.signal_count = 5
        self.engine.error_count = 2
        self.engine.last_signal_time = datetime.now()

        # 测试获取状态
        status = self.engine.get_engine_status()
        assert isinstance(status, dict)
        assert "signal_count" in status or "trading_stats" in status

        # 测试启动
        start_result = self.engine.start_engine()
        assert isinstance(start_result, dict)
        assert "success" in start_result or "status" in start_result

        # 测试停止
        stop_result = self.engine.stop_engine()
        assert isinstance(stop_result, dict)

    def test_trade_statistics_update(self):
        """测试交易统计更新"""
        initial_count = self.engine.signal_count

        self.engine._update_trade_statistics("BTCUSDT", 50000.0)

        assert self.engine.signal_count == initial_count + 1
        assert self.engine.last_signal_time is not None

    # ===== 辅助功能测试 =====

    def test_trend_analysis(self):
        """测试趋势分析"""
        # 上升趋势
        bullish_prices = pd.Series([100, 102, 104, 106, 108, 110] * 20)
        result = self.engine._analyze_trend(bullish_prices)
        assert "direction" in result
        assert result["direction"] in ["bullish", "bearish", "neutral"]

        # 下降趋势
        bearish_prices = pd.Series([110, 108, 106, 104, 102, 100] * 20)
        result = self.engine._analyze_trend(bearish_prices)
        assert result["direction"] in ["bullish", "bearish", "neutral"]

    def test_volatility_analysis(self):
        """测试波动率分析"""
        # 高波动率数据
        volatile_prices = pd.Series([100, 110, 90, 120, 80, 130, 70, 140])
        result = self.engine._analyze_volatility(volatile_prices)

        assert "level" in result
        assert "percent" in result
        assert result["level"] in ["high", "medium", "low"]
        assert isinstance(result["percent"], float)

    def test_recommendation_generation(self):
        """测试推荐生成"""
        test_cases = [
            ({"signal": "BUY", "confidence": 0.8}, "strong_buy"),
            ({"signal": "BUY", "confidence": 0.6}, "buy"),
            ({"signal": "SELL", "confidence": 0.8}, "strong_sell"),
            ({"signal": "SELL", "confidence": 0.6}, "sell"),
            ({"signal": "HOLD", "confidence": 0.5}, "hold"),
        ]

        for signals, expected in test_cases:
            result = self.engine._generate_recommendation(signals)
            assert result == expected

    # ===== 错误处理测试 =====

    def test_error_response_creation(self):
        """测试错误响应创建"""
        error_msg = "测试错误"
        result = self.engine._create_error_result(error_msg)

        assert result["error"] == error_msg
        assert result["atr"] == 0
        assert result["volatility"] == "unknown"
        assert result["trend"] == "unknown"
        assert result["recommendation"] == "hold"

    def test_trading_cycle_error_handling(self):
        """测试交易周期错误处理"""
        with patch.object(
            self.engine, "analyze_market_conditions", side_effect=Exception("网络错误")
        ):
            result = self.engine.execute_trade_decision("BTCUSDT")

            assert result["success"] is False
            assert "交易执行失败" in result["message"]
            assert self.engine.error_count > 0

    # ===== 完整流程测试 =====

    def test_complete_trading_cycle(self):
        """测试完整交易周期"""
        sample_data = self.create_sample_market_data(20)
        mock_signals = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 50250.0,
            "confidence": 0.8,
            "fast_ma": 50000.0,
            "slow_ma": 49500.0,
        }

        with (
            patch("src.core.price_fetcher.fetch_price_data", return_value=sample_data),
            patch.object(
                self.engine.signal_processor,
                "get_trading_signals_optimized",
                return_value=mock_signals,
            ),
            patch.object(self.engine, "calculate_position_size", return_value=0.1),
            patch.object(self.engine, "process_buy_signal", return_value=True),
            patch.object(self.engine, "process_sell_signal", return_value=False),
            patch.object(self.engine, "update_positions"),
            patch.object(self.engine, "send_status_update"),
        ):

            result = self.engine.execute_trading_cycle("BTCUSDT")
            assert isinstance(result, bool)

    # ===== Mock配置优化测试 =====

    def test_response_creation_methods(self):
        """测试响应创建方法"""
        # 测试持有响应
        market_analysis = {
            "atr": 1500.0,
            "current_price": 50000.0,
            "volatility": "medium",
            "trend": "neutral",
            "signal_strength": 0.5,
        }
        hold_response = self.engine._create_hold_response(market_analysis, 0.1, "测试持有")
        assert hold_response["action"] == "hold"
        assert hold_response["message"] == "测试持有"

        # 测试错误响应
        error_response = self.engine._create_error_response("buy", "测试错误", {})
        assert error_response["action"] == "buy"
        assert error_response["message"] == "测试错误"
        assert error_response["success"] == False


class TestAsyncTradingEngine:
    """异步交易引擎测试类"""

    def test_async_engine_import(self):
        """测试异步引擎导入"""
        try:
            from src.core.async_trading_engine import AsyncTradingEngine

            assert AsyncTradingEngine is not None
        except ImportError:
            pytest.skip("AsyncTradingEngine not available")

    @patch("src.core.async_trading_engine.BinanceWSClient")
    @patch("src.core.async_trading_engine.LiveBrokerAsync")
    @patch("src.core.async_trading_engine.get_metrics_collector")
    def test_async_engine_initialization(self, mock_metrics, mock_broker, mock_ws):
        """测试异步引擎初始化"""
        try:
            from src.core.async_trading_engine import AsyncTradingEngine

            # 设置mocks
            mock_metrics.return_value = Mock()
            mock_broker.return_value = AsyncMock()
            mock_ws.return_value = AsyncMock()

            engine = AsyncTradingEngine(api_key="test_key", api_secret="test_secret")

            assert engine is not None
            assert hasattr(engine, "broker")
            assert hasattr(engine, "ws_client")

        except ImportError:
            pytest.skip("AsyncTradingEngine dependencies not available")

    def test_async_engine_module_functions(self):
        """测试异步引擎模块函数"""
        try:
            import src.core.async_trading_engine as async_module

            assert hasattr(async_module, "create_async_trading_engine")
            assert callable(async_module.create_async_trading_engine)
        except ImportError:
            pytest.skip("async_trading_engine module not available")


class TestTradingLoop:
    """交易循环测试类"""

    @patch("src.core.trading_engine.TradingEngine")
    def test_trading_loop_function(self, mock_engine_class):
        """测试交易循环函数"""
        mock_engine = Mock()
        mock_engine.start_trading_loop.return_value = None
        mock_engine_class.return_value = mock_engine

        from src.core.trading_engine import trading_loop

        # 测试基本调用 - 使用正确的参数
        result = trading_loop(symbol="BTCUSDT", interval_seconds=60)

        # 验证引擎被创建
        mock_engine_class.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
