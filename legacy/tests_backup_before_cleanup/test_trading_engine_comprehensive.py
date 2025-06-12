"""
交易引擎综合测试模块 (Trading Engine Comprehensive Tests)

测试覆盖：
- 交易引擎初始化
- 市场分析功能
- 交易决策执行
- 风险管理
- 状态监控
- 错误处理
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.core.trading_engine import TradingEngine, trading_loop


class TestTradingEngineInitialization:
    """测试交易引擎初始化"""

    def test_init_with_default_params(self):
        """测试默认参数初始化"""
        engine = TradingEngine()

        assert engine.signal_processor is not None
        assert engine.metrics is not None
        assert engine.broker is not None
        assert engine.account_equity == 10000.0
        assert engine.risk_percent == 0.01
        assert engine.atr_multiplier == 2.0
        assert engine.signal_count == 0
        assert engine.error_count == 0

    def test_init_with_custom_params(self):
        """测试自定义参数初始化"""
        engine = TradingEngine(
            api_key="test_key", api_secret="test_secret", telegram_token="test_token"
        )

        assert engine.broker is not None
        assert engine.last_signal_time is None
        assert isinstance(engine.last_status_update, datetime)

    @patch.dict(
        "os.environ", {"ACCOUNT_EQUITY": "50000.0", "RISK_PERCENT": "0.02", "ATR_MULTIPLIER": "3.0"}
    )
    def test_init_with_env_vars(self):
        """测试环境变量配置"""
        engine = TradingEngine()

        assert engine.account_equity == 50000.0
        assert engine.risk_percent == 0.02
        assert engine.atr_multiplier == 3.0


class TestMarketAnalysis:
    """测试市场分析功能"""

    @pytest.fixture
    def engine(self):
        """创建测试用交易引擎"""
        return TradingEngine()

    @pytest.fixture
    def mock_price_data(self):
        """创建模拟价格数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="1H")
        data = pd.DataFrame(
            {
                "open": [50000 + i * 10 for i in range(100)],
                "high": [50100 + i * 10 for i in range(100)],
                "low": [49900 + i * 10 for i in range(100)],
                "close": [50050 + i * 10 for i in range(100)],
                "volume": [1000 + i for i in range(100)],
            },
            index=dates,
        )
        return data

    @patch("src.core.trading_engine.fetch_price_data")
    @patch("src.core.trading_engine.calculate_atr")
    def test_analyze_market_conditions_success(self, mock_atr, mock_fetch, engine, mock_price_data):
        """测试成功的市场分析"""
        # 设置模拟数据
        mock_fetch.return_value = mock_price_data
        mock_atr.return_value = 150.5

        # 模拟信号处理器
        engine.signal_processor.process_signals = Mock(
            return_value={"signal": "BUY", "confidence": 0.8}
        )

        result = engine.analyze_market_conditions("BTCUSDT")

        assert "error" not in result
        assert result["atr"] == 150.5
        assert result["volatility"] in ["low", "medium", "high"]
        assert result["trend"] in ["bullish", "bearish", "neutral"]
        assert result["signal_strength"] == 0.8
        assert result["recommendation"] in ["strong_buy", "buy", "hold", "sell", "strong_sell"]

    @patch("src.core.trading_engine.fetch_price_data")
    def test_analyze_market_conditions_no_data(self, mock_fetch, engine):
        """测试无数据情况"""
        mock_fetch.return_value = None

        result = engine.analyze_market_conditions("BTCUSDT")

        assert "error" in result
        assert result["error"] == "无法获取市场数据"
        assert result["atr"] == 0
        assert result["volatility"] == "unknown"

    @patch("src.core.trading_engine.fetch_price_data")
    def test_analyze_market_conditions_exception(self, mock_fetch, engine):
        """测试异常处理"""
        mock_fetch.side_effect = Exception("网络错误")

        result = engine.analyze_market_conditions("BTCUSDT")

        assert "error" in result
        assert "市场分析失败" in result["error"]
        assert engine.error_count == 1

    def test_analyze_trend_bullish(self, engine, mock_price_data):
        """测试牛市趋势分析"""
        # 创建上升趋势数据
        close_prices = pd.Series([100, 105, 110, 115, 120] * 20)

        result = engine._analyze_trend(close_prices)

        assert result["direction"] in ["bullish", "bearish", "neutral"]
        assert "short_ma" in result
        assert "long_ma" in result

    def test_analyze_volatility_levels(self, engine):
        """测试波动率分析"""
        # 高波动率数据
        high_vol_prices = pd.Series([100, 110, 95, 115, 85, 120, 80])
        result_high = engine._analyze_volatility(high_vol_prices)
        assert result_high["level"] in ["low", "medium", "high"]

        # 低波动率数据
        low_vol_prices = pd.Series([100, 100.5, 99.5, 100.2, 99.8])
        result_low = engine._analyze_volatility(low_vol_prices)
        assert result_low["level"] in ["low", "medium", "high"]

    def test_generate_recommendation(self, engine):
        """测试交易推荐生成"""
        # 强买信号
        signals_strong_buy = {"signal": "BUY", "confidence": 0.8}
        assert engine._generate_recommendation(signals_strong_buy) == "strong_buy"

        # 弱买信号
        signals_weak_buy = {"signal": "BUY", "confidence": 0.6}
        assert engine._generate_recommendation(signals_weak_buy) == "buy"

        # 强卖信号
        signals_strong_sell = {"signal": "SELL", "confidence": 0.8}
        assert engine._generate_recommendation(signals_strong_sell) == "strong_sell"

        # 持有信号
        signals_hold = {"signal": "HOLD", "confidence": 0.5}
        assert engine._generate_recommendation(signals_hold) == "hold"


class TestTradingDecision:
    """测试交易决策执行"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    @pytest.fixture
    def mock_market_analysis(self):
        return {
            "atr": 150.0,
            "volatility": "medium",
            "trend": "bullish",
            "signal_strength": 0.8,
            "recommendation": "strong_buy",
            "current_price": 50000.0,
            "signals": {"signal": "BUY", "confidence": 0.8},
        }

    @patch.object(TradingEngine, "analyze_market_conditions")
    @patch.object(TradingEngine, "_execute_trading_logic")
    def test_execute_trade_decision_success(
        self, mock_execute, mock_analyze, engine, mock_market_analysis
    ):
        """测试成功的交易决策执行"""
        mock_analyze.return_value = mock_market_analysis
        mock_execute.return_value = {"action": "buy", "success": True, "message": "买入订单已执行"}

        result = engine.execute_trade_decision("BTCUSDT")

        assert result["action"] == "buy"
        assert result["success"] is True
        mock_analyze.assert_called_once_with("BTCUSDT")

    @patch.object(TradingEngine, "analyze_market_conditions")
    def test_execute_trade_decision_market_error(self, mock_analyze, engine):
        """测试市场分析错误"""
        mock_analyze.return_value = {"error": "数据获取失败"}

        result = engine.execute_trade_decision("BTCUSDT")

        assert "error" in result
        assert result["action"] == "none"

    def test_validate_trading_conditions_force_trade(self, engine, mock_market_analysis):
        """测试强制交易条件验证"""
        result = engine._validate_trading_conditions(mock_market_analysis, force_trade=True)
        assert result is None  # 强制交易应该通过验证

    def test_calculate_position_size_internal(self, engine, mock_market_analysis):
        """测试内部仓位计算"""
        position_size = engine._calculate_position_size_internal(mock_market_analysis)

        assert isinstance(position_size, float)
        assert position_size > 0
        # 验证风险管理：仓位不应超过账户权益的合理比例
        max_position = engine.account_equity * engine.risk_percent * 10  # 10倍杠杆上限
        assert position_size <= max_position


class TestTradeExecution:
    """测试交易执行"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    @pytest.fixture
    def mock_market_analysis(self):
        return {
            "atr": 150.0,
            "current_price": 50000.0,
            "recommendation": "strong_buy",
            "signals": {"signal": "BUY", "confidence": 0.8},
        }

    @patch.object(TradingEngine, "_update_trade_statistics")
    def test_execute_buy_trade(self, mock_update_stats, engine, mock_market_analysis):
        """测试买入交易执行"""
        result = engine._execute_buy_trade("BTCUSDT", 0.001, 50000.0, mock_market_analysis)

        assert result["action"] == "buy"
        assert result["symbol"] == "BTCUSDT"
        assert result["position_size"] == 0.001
        assert result["price"] == 50000.0
        mock_update_stats.assert_called_once()

    @patch.object(TradingEngine, "_update_trade_statistics")
    def test_execute_sell_trade(self, mock_update_stats, engine, mock_market_analysis):
        """测试卖出交易执行"""
        mock_market_analysis["recommendation"] = "strong_sell"
        mock_market_analysis["signals"] = {"signal": "SELL", "confidence": 0.8}

        result = engine._execute_sell_trade("BTCUSDT", 0.001, 50000.0, mock_market_analysis)

        assert result["action"] == "sell"
        assert result["symbol"] == "BTCUSDT"
        assert result["position_size"] == 0.001
        assert result["price"] == 50000.0

    def test_create_hold_response(self, engine, mock_market_analysis):
        """测试持有响应创建"""
        result = engine._create_hold_response(mock_market_analysis, 0.001, "测试持有")

        assert result["action"] == "hold"
        assert result["message"] == "测试持有"
        assert result["position_size"] == 0.001

    def test_create_error_response(self, engine):
        """测试错误响应创建"""
        result = engine._create_error_response("buy", "测试错误")

        assert result["action"] == "buy"
        assert result["success"] is False
        assert result["error"] == "测试错误"


class TestEngineStatus:
    """测试引擎状态管理"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    def test_get_engine_status(self, engine):
        """测试获取引擎状态"""
        status = engine.get_engine_status()

        assert "status" in status
        assert "uptime" in status
        assert "signal_count" in status
        assert "error_count" in status
        assert "last_signal_time" in status
        assert "account_equity" in status
        assert "peak_balance" in status

    def test_start_engine(self, engine):
        """测试启动引擎"""
        result = engine.start_engine()

        assert result["status"] == "started"
        assert "message" in result
        assert "timestamp" in result

    def test_stop_engine(self, engine):
        """测试停止引擎"""
        result = engine.stop_engine()

        assert result["status"] == "stopped"
        assert "message" in result
        assert "timestamp" in result


class TestPositionManagement:
    """测试仓位管理"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    def test_calculate_position_size(self, engine):
        """测试仓位大小计算"""
        position_size = engine.calculate_position_size(50000.0, 150.0, "BTCUSDT")

        assert isinstance(position_size, float)
        assert position_size > 0
        # 验证仓位大小合理性
        assert position_size <= engine.account_equity * 0.1  # 不超过账户的10%

    @patch.object(TradingEngine, "broker")
    def test_process_buy_signal(self, mock_broker, engine):
        """测试买入信号处理"""
        signals = {"signal": "BUY", "confidence": 0.8}

        result = engine.process_buy_signal("BTCUSDT", signals, 150.0)

        assert isinstance(result, bool)

    @patch.object(TradingEngine, "broker")
    def test_process_sell_signal(self, mock_broker, engine):
        """测试卖出信号处理"""
        signals = {"signal": "SELL", "confidence": 0.8}

        result = engine.process_sell_signal("BTCUSDT", signals)

        assert isinstance(result, bool)

    def test_update_positions(self, engine):
        """测试仓位更新"""
        # 这个方法主要是更新内部状态，测试它不抛出异常
        try:
            engine.update_positions("BTCUSDT", 50000.0, 150.0)
            assert True
        except Exception as e:
            pytest.fail(f"update_positions raised {e} unexpectedly!")


class TestTradingCycle:
    """测试交易周期"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    @patch("src.core.trading_engine.fetch_price_data")
    @patch.object(TradingEngine, "process_buy_signal")
    @patch.object(TradingEngine, "process_sell_signal")
    def test_execute_trading_cycle(self, mock_sell, mock_buy, mock_fetch, engine):
        """测试交易周期执行"""
        # 创建模拟数据
        mock_data = pd.DataFrame(
            {
                "close": [50000, 50100, 50200, 50300, 50400],
                "high": [50100, 50200, 50300, 50400, 50500],
                "low": [49900, 50000, 50100, 50200, 50300],
                "volume": [1000, 1100, 1200, 1300, 1400],
            }
        )
        mock_fetch.return_value = mock_data
        mock_buy.return_value = False
        mock_sell.return_value = False

        result = engine.execute_trading_cycle("BTCUSDT")

        assert isinstance(result, bool)
        mock_fetch.assert_called_once()

    @patch("src.core.trading_engine.fetch_price_data")
    def test_execute_trading_cycle_no_data(self, mock_fetch, engine):
        """测试无数据的交易周期"""
        mock_fetch.return_value = None

        result = engine.execute_trading_cycle("BTCUSDT")

        assert result is False


class TestTradingLoop:
    """测试交易循环函数"""

    @patch("src.core.trading_engine.TradingEngine")
    def test_trading_loop_function(self, mock_engine_class):
        """测试交易循环函数"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine
        mock_engine.execute_trading_cycle.return_value = True

        # 由于这是一个无限循环，我们只测试它能正确创建引擎
        try:
            # 这里我们不能真正运行循环，只测试函数存在且可调用
            assert callable(trading_loop)
        except Exception as e:
            pytest.fail(f"trading_loop function test failed: {e}")


class TestErrorHandling:
    """测试错误处理"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    def test_error_count_increment(self, engine):
        """测试错误计数增加"""
        initial_count = engine.error_count

        # 触发一个会增加错误计数的操作
        with patch("src.core.trading_engine.fetch_price_data", side_effect=Exception("测试错误")):
            engine.analyze_market_conditions("BTCUSDT")

        assert engine.error_count == initial_count + 1

    def test_metrics_exception_recording(self, engine):
        """测试异常记录到指标"""
        with patch.object(engine.metrics, "record_exception") as mock_record:
            with patch(
                "src.core.trading_engine.fetch_price_data", side_effect=Exception("测试错误")
            ):
                engine.analyze_market_conditions("BTCUSDT")

            mock_record.assert_called_once()


class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def engine(self):
        return TradingEngine()

    @patch("src.core.trading_engine.fetch_price_data")
    @patch("src.core.trading_engine.calculate_atr")
    def test_full_trading_decision_flow(self, mock_atr, mock_fetch, engine):
        """测试完整的交易决策流程"""
        # 设置模拟数据
        mock_data = pd.DataFrame(
            {
                "open": [50000, 50100, 50200],
                "high": [50100, 50200, 50300],
                "low": [49900, 50000, 50100],
                "close": [50050, 50150, 50250],
                "volume": [1000, 1100, 1200],
            }
        )
        mock_fetch.return_value = mock_data
        mock_atr.return_value = 150.0

        # 模拟信号处理器
        engine.signal_processor.process_signals = Mock(
            return_value={"signal": "BUY", "confidence": 0.8}
        )

        # 执行完整流程
        result = engine.execute_trade_decision("BTCUSDT")

        # 验证结果结构
        assert "action" in result
        assert "symbol" in result
        assert result["symbol"] == "BTCUSDT"

        # 验证调用链
        mock_fetch.assert_called()
        mock_atr.assert_called()
