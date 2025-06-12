"""
核心交易引擎模块综合测试 (Core Trading Engine Comprehensive Tests)

覆盖所有主要功能：
- 交易引擎初始化
- 仓位大小计算
- 买入/卖出信号处理
- 仓位更新和状态管理
- 交易循环执行
- 错误处理和边缘情况
"""

import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd

from src.core.trading_engine import TradingEngine, trading_loop


class TestTradingEngineInitialization:
    """测试交易引擎初始化"""

    def test_trading_engine_init_with_params(self):
        """测试使用参数初始化交易引擎"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            engine = TradingEngine(
                api_key="test_key", api_secret="test_secret", telegram_token="test_token"
            )

            assert engine.account_equity == 10000.0  # 默认值
            assert engine.risk_percent == 0.01
            assert engine.atr_multiplier == 2.0
            mock_broker.assert_called_once()

    def test_trading_engine_init_with_env_vars(self):
        """测试使用环境变量初始化"""
        with patch.dict(
            os.environ,
            {
                "API_KEY": "env_key",
                "API_SECRET": "env_secret",
                "TG_TOKEN": "env_token",
                "ACCOUNT_EQUITY": "20000.0",
                "RISK_PERCENT": "0.02",
                "ATR_MULTIPLIER": "3.0",
            },
        ):
            with patch("src.core.trading_engine.Broker") as mock_broker:
                engine = TradingEngine()

                assert engine.account_equity == 20000.0
                assert engine.risk_percent == 0.02
                assert engine.atr_multiplier == 3.0

    def test_trading_engine_init_default_values(self):
        """测试默认值初始化"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            with patch.dict(os.environ, {}, clear=True):
                engine = TradingEngine()

                assert engine.account_equity == 10000.0
                assert engine.risk_percent == 0.01
                assert engine.atr_multiplier == 2.0
                assert isinstance(engine.last_status_update, datetime)


class TestPositionSizeCalculation:
    """测试仓位大小计算"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker"):
            self.engine = TradingEngine()

    def test_calculate_position_size_normal(self):
        """测试正常情况下的仓位大小计算"""
        current_price = 100.0
        atr = 2.0
        symbol = "BTCUSDT"

        # 风险金额 = 10000 * 0.01 = 100
        # 止损价 = 100 - (2 * 2) = 96
        # 每单位风险 = 100 - 96 = 4
        # 数量 = 100 / 4 = 25

        result = self.engine.calculate_position_size(current_price, atr, symbol)
        assert result == 25.0

    def test_calculate_position_size_zero_risk(self):
        """测试零风险情况"""
        current_price = 100.0
        atr = 0.0  # ATR为0
        symbol = "BTCUSDT"

        result = self.engine.calculate_position_size(current_price, atr, symbol)
        assert result == 0.0

    def test_calculate_position_size_negative_risk(self):
        """测试负风险情况（止损价高于当前价）"""
        current_price = 100.0
        atr = 60.0  # 很大的ATR，导致止损价 = 100 - (60 * 2) = -20
        symbol = "BTCUSDT"

        result = self.engine.calculate_position_size(current_price, atr, symbol)
        # 实际上这种情况下 risk_per_unit = 100 - (-20) = 120 > 0
        # 所以会计算出一个正数，约为 100/120 = 0.833
        assert result > 0
        assert abs(result - 0.833) < 0.01  # 允许小的浮点误差

    def test_calculate_position_size_small_atr(self):
        """测试小ATR值"""
        current_price = 50000.0
        atr = 0.1
        symbol = "BTCUSDT"

        result = self.engine.calculate_position_size(current_price, atr, symbol)
        assert result > 0
        assert isinstance(result, float)

    def test_calculate_position_size_rounding(self):
        """测试结果四舍五入"""
        current_price = 100.0
        atr = 1.7  # 导致非整数结果
        symbol = "BTCUSDT"

        result = self.engine.calculate_position_size(current_price, atr, symbol)
        # 检查结果是否正确四舍五入到3位小数
        assert len(str(result).split(".")[-1]) <= 3


class TestBuySignalProcessing:
    """测试买入信号处理"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            self.engine = TradingEngine()
            self.mock_broker = mock_broker.return_value
            self.engine.broker = self.mock_broker

    def test_process_buy_signal_success(self):
        """测试成功处理买入信号"""
        symbol = "BTCUSDT"
        signals = {"buy_signal": True, "current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}
        atr = 2.0

        # 模拟没有现有仓位
        self.mock_broker.positions = {}
        self.mock_broker.execute_order.return_value = True

        result = self.engine.process_buy_signal(symbol, signals, atr)

        assert result is True
        self.mock_broker.execute_order.assert_called_once()
        call_args = self.mock_broker.execute_order.call_args
        assert call_args[1]["symbol"] == symbol
        assert call_args[1]["side"] == "BUY"
        assert call_args[1]["quantity"] > 0

    def test_process_buy_signal_no_signal(self):
        """测试没有买入信号的情况"""
        symbol = "BTCUSDT"
        signals = {"buy_signal": False, "current_price": 100.0, "fast_ma": 98.0, "slow_ma": 102.0}
        atr = 2.0

        result = self.engine.process_buy_signal(symbol, signals, atr)

        assert result is False
        self.mock_broker.execute_order.assert_not_called()

    def test_process_buy_signal_existing_position(self):
        """测试已有仓位时的买入信号"""
        symbol = "BTCUSDT"
        signals = {"buy_signal": True, "current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}
        atr = 2.0

        # 模拟已有仓位
        self.mock_broker.positions = {symbol: {"quantity": 10}}

        result = self.engine.process_buy_signal(symbol, signals, atr)

        assert result is False
        self.mock_broker.execute_order.assert_not_called()

    def test_process_buy_signal_zero_quantity(self):
        """测试计算出零数量的情况"""
        symbol = "BTCUSDT"
        signals = {"buy_signal": True, "current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}
        atr = 0.0  # 导致零数量

        self.mock_broker.positions = {}

        result = self.engine.process_buy_signal(symbol, signals, atr)

        assert result is False
        self.mock_broker.execute_order.assert_not_called()

    def test_process_buy_signal_execution_error(self):
        """测试订单执行错误"""
        symbol = "BTCUSDT"
        signals = {"buy_signal": True, "current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}
        atr = 2.0

        self.mock_broker.positions = {}
        self.mock_broker.execute_order.side_effect = Exception("订单执行失败")
        self.mock_broker.notifier = Mock()

        result = self.engine.process_buy_signal(symbol, signals, atr)

        assert result is False
        self.mock_broker.notifier.notify_error.assert_called_once()


class TestSellSignalProcessing:
    """测试卖出信号处理"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            self.engine = TradingEngine()
            self.mock_broker = mock_broker.return_value
            self.engine.broker = self.mock_broker

    def test_process_sell_signal_success(self):
        """测试成功处理卖出信号"""
        symbol = "BTCUSDT"
        signals = {"sell_signal": True, "current_price": 100.0, "fast_ma": 98.0, "slow_ma": 102.0}

        # 模拟有现有仓位
        position = {"quantity": 10.0, "entry_price": 95.0}
        self.mock_broker.positions = {symbol: position}
        self.mock_broker.execute_order.return_value = True

        result = self.engine.process_sell_signal(symbol, signals)

        assert result is True
        self.mock_broker.execute_order.assert_called_once()
        call_args = self.mock_broker.execute_order.call_args
        assert call_args[1]["symbol"] == symbol
        assert call_args[1]["side"] == "SELL"
        assert call_args[1]["quantity"] == 10.0

    def test_process_sell_signal_no_signal(self):
        """测试没有卖出信号的情况"""
        symbol = "BTCUSDT"
        signals = {"sell_signal": False, "current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}

        result = self.engine.process_sell_signal(symbol, signals)

        assert result is False
        self.mock_broker.execute_order.assert_not_called()

    def test_process_sell_signal_no_position(self):
        """测试没有仓位时的卖出信号"""
        symbol = "BTCUSDT"
        signals = {"sell_signal": True, "current_price": 100.0, "fast_ma": 98.0, "slow_ma": 102.0}

        # 模拟没有仓位
        self.mock_broker.positions = {}

        result = self.engine.process_sell_signal(symbol, signals)

        assert result is False
        self.mock_broker.execute_order.assert_not_called()

    def test_process_sell_signal_execution_error(self):
        """测试卖出订单执行错误"""
        symbol = "BTCUSDT"
        signals = {"sell_signal": True, "current_price": 100.0, "fast_ma": 98.0, "slow_ma": 102.0}

        position = {"quantity": 10.0, "entry_price": 95.0}
        self.mock_broker.positions = {symbol: position}
        self.mock_broker.execute_order.side_effect = Exception("卖出失败")
        self.mock_broker.notifier = Mock()

        result = self.engine.process_sell_signal(symbol, signals)

        assert result is False
        self.mock_broker.notifier.notify_error.assert_called_once()


class TestPositionUpdates:
    """测试仓位更新"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            self.engine = TradingEngine()
            self.mock_broker = mock_broker.return_value
            self.engine.broker = self.mock_broker

    def test_update_positions(self):
        """测试仓位更新"""
        symbol = "BTCUSDT"
        current_price = 100.0
        atr = 2.0

        self.engine.update_positions(symbol, current_price, atr)

        self.mock_broker.update_position_stops.assert_called_once_with(symbol, current_price, atr)
        self.mock_broker.check_stop_loss.assert_called_once_with(symbol, current_price)


class TestStatusUpdates:
    """测试状态更新"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            self.engine = TradingEngine()
            self.mock_broker = mock_broker.return_value
            self.engine.broker = self.mock_broker
            self.mock_broker.notifier = Mock()

    def test_send_status_update_no_position(self):
        """测试没有仓位时的状态更新"""
        symbol = "BTCUSDT"
        signals = {"current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}
        atr = 2.0

        # 设置上次更新时间为2小时前，确保会发送更新
        self.engine.last_status_update = datetime.now() - timedelta(hours=2)
        self.mock_broker.positions = {}

        self.engine.send_status_update(symbol, signals, atr)

        self.mock_broker.notifier.notify.assert_called_once()
        call_args = self.mock_broker.notifier.notify.call_args[0]
        status_msg = call_args[0]

        assert "BTCUSDT" in status_msg
        assert "100.00000000" in status_msg
        assert "无" in status_msg  # 没有仓位

    def test_send_status_update_with_position(self):
        """测试有仓位时的状态更新"""
        symbol = "BTCUSDT"
        signals = {"current_price": 105.0, "fast_ma": 107.0, "slow_ma": 103.0}
        atr = 2.0

        # 设置上次更新时间为2小时前
        self.engine.last_status_update = datetime.now() - timedelta(hours=2)

        # 模拟有仓位
        position = {"entry_price": 100.0, "stop_price": 96.0, "quantity": 10.0}
        self.mock_broker.positions = {symbol: position}

        self.engine.send_status_update(symbol, signals, atr)

        self.mock_broker.notifier.notify.assert_called_once()
        call_args = self.mock_broker.notifier.notify.call_args[0]
        status_msg = call_args[0]

        assert "BTCUSDT" in status_msg
        assert "105.00000000" in status_msg
        assert "有" in status_msg  # 有仓位
        assert "100.00000000" in status_msg  # 入场价
        assert "96.00000000" in status_msg  # 止损价
        assert "50.00000000" in status_msg  # 盈亏 (105-100)*10 = 50
        assert "5.00%" in status_msg  # 盈亏百分比

    def test_send_status_update_too_recent(self):
        """测试距离上次更新时间太短的情况"""
        symbol = "BTCUSDT"
        signals = {"current_price": 100.0, "fast_ma": 102.0, "slow_ma": 98.0}
        atr = 2.0

        # 设置上次更新时间为30分钟前（小于1小时）
        self.engine.last_status_update = datetime.now() - timedelta(minutes=30)

        self.engine.send_status_update(symbol, signals, atr)

        # 不应该发送通知
        self.mock_broker.notifier.notify.assert_not_called()


class TestTradingCycleExecution:
    """测试交易周期执行"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            self.engine = TradingEngine()
            self.mock_broker = mock_broker.return_value
            self.engine.broker = self.mock_broker

    @patch("src.core.trading_engine.fetch_price_data")
    @patch("src.core.trading_engine.calculate_atr")
    @patch("src.core.trading_engine.get_trading_signals")
    @patch("src.core.trading_engine.validate_signal")
    def test_execute_trading_cycle_success(self, mock_validate, mock_signals, mock_atr, mock_price):
        """测试成功执行交易周期"""
        symbol = "BTCUSDT"

        # 模拟数据
        mock_price.return_value = pd.DataFrame({"close": [100, 101, 102]})
        mock_atr.return_value = 2.0
        mock_signals.return_value = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 102.0,
            "fast_ma": 103.0,
            "slow_ma": 101.0,
        }
        mock_validate.return_value = True

        self.mock_broker.positions = {}
        self.mock_broker.check_stop_loss.return_value = False

        with patch.object(self.engine, "process_buy_signal", return_value=True) as mock_buy:
            with patch.object(self.engine, "process_sell_signal", return_value=False) as mock_sell:
                with patch.object(self.engine, "send_status_update") as mock_status:
                    result = self.engine.execute_trading_cycle(symbol)

        assert result is True
        mock_buy.assert_called_once()
        mock_sell.assert_called_once()
        mock_status.assert_called_once()

    @patch("src.core.trading_engine.fetch_price_data")
    @patch("src.core.trading_engine.calculate_atr")
    @patch("src.core.trading_engine.get_trading_signals")
    @patch("src.core.trading_engine.validate_signal")
    def test_execute_trading_cycle_invalid_signal(
        self, mock_validate, mock_signals, mock_atr, mock_price
    ):
        """测试信号验证失败的情况"""
        symbol = "BTCUSDT"

        mock_price.return_value = pd.DataFrame({"close": [100, 101, 102]})
        mock_atr.return_value = 2.0
        mock_signals.return_value = {"buy_signal": True}
        mock_validate.return_value = False  # 信号验证失败

        result = self.engine.execute_trading_cycle(symbol)

        assert result is False

    @patch("src.core.trading_engine.fetch_price_data")
    def test_execute_trading_cycle_exception(self, mock_price):
        """测试交易周期执行异常"""
        symbol = "BTCUSDT"

        mock_price.side_effect = Exception("数据获取失败")
        self.mock_broker.notifier = Mock()

        result = self.engine.execute_trading_cycle(symbol)

        assert result is False
        self.mock_broker.notifier.notify_error.assert_called_once()

    @patch("src.core.trading_engine.fetch_price_data")
    @patch("src.core.trading_engine.calculate_atr")
    @patch("src.core.trading_engine.get_trading_signals")
    @patch("src.core.trading_engine.validate_signal")
    def test_execute_trading_cycle_stop_triggered(
        self, mock_validate, mock_signals, mock_atr, mock_price
    ):
        """测试止损触发的情况"""
        symbol = "BTCUSDT"

        mock_price.return_value = pd.DataFrame({"close": [100, 101, 102]})
        mock_atr.return_value = 2.0
        mock_signals.return_value = {
            "buy_signal": True,
            "sell_signal": False,
            "current_price": 102.0,
            "fast_ma": 103.0,
            "slow_ma": 101.0,
        }
        mock_validate.return_value = True

        self.mock_broker.check_stop_loss.return_value = True  # 止损触发

        with patch.object(self.engine, "process_buy_signal") as mock_buy:
            with patch.object(self.engine, "process_sell_signal") as mock_sell:
                result = self.engine.execute_trading_cycle(symbol)

        assert result is True
        # 止损触发时不应该处理买卖信号
        mock_buy.assert_not_called()
        mock_sell.assert_not_called()


class TestTradingLoop:
    """测试交易循环"""

    @patch("src.core.trading_engine.TradingEngine")
    def test_trading_loop_function(self, mock_engine_class):
        """测试向后兼容的trading_loop函数"""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        # 模拟start_trading_loop方法，避免无限循环
        mock_engine.start_trading_loop = Mock()

        trading_loop("ETHUSDT", 30)

        mock_engine_class.assert_called_once()
        mock_engine.start_trading_loop.assert_called_once_with("ETHUSDT", 30)

    def test_start_trading_loop_keyboard_interrupt(self):
        """测试交易循环的键盘中断处理"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            engine = TradingEngine()
            mock_notifier = Mock()
            engine.broker.notifier = mock_notifier

            with patch.object(engine, "execute_trading_cycle", side_effect=KeyboardInterrupt):
                with patch("time.sleep"):
                    engine.start_trading_loop("BTCUSDT", 1)

            # 应该发送关闭通知
            mock_notifier.notify.assert_called()
            call_args = mock_notifier.notify.call_args[0]
            assert "关闭" in call_args[0] or "stopped" in call_args[0]


class TestTradingEngineEdgeCases:
    """测试交易引擎边缘情况"""

    def setup_method(self):
        """设置测试环境"""
        with patch("src.core.trading_engine.Broker") as mock_broker:
            self.engine = TradingEngine()
            self.mock_broker = mock_broker.return_value
            self.engine.broker = self.mock_broker

    def test_calculate_position_size_extreme_values(self):
        """测试极端值的仓位计算"""
        # 极小价格
        result1 = self.engine.calculate_position_size(0.001, 0.0001, "SHIB")
        assert result1 >= 0

        # 极大价格
        result2 = self.engine.calculate_position_size(100000.0, 1000.0, "BTC")
        assert result2 >= 0

        # 极小ATR
        result3 = self.engine.calculate_position_size(100.0, 0.00001, "ETH")
        assert result3 >= 0

    def test_signal_processing_with_missing_fields(self):
        """测试信号字典缺少字段的情况"""
        symbol = "BTCUSDT"
        incomplete_signals = {
            "buy_signal": True,
            "current_price": 100.0,
            # 缺少 fast_ma 和 slow_ma
        }
        atr = 2.0

        self.mock_broker.positions = {}

        # 应该能处理缺少字段的情况
        try:
            result = self.engine.process_buy_signal(symbol, incomplete_signals, atr)
            # 可能成功也可能失败，取决于具体实现
            assert isinstance(result, bool)
        except KeyError:
            # 如果抛出KeyError也是可以接受的
            pass

    def test_multiple_symbols_handling(self):
        """测试多交易对处理"""
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

        for symbol in symbols:
            signals = {
                "buy_signal": False,
                "sell_signal": False,
                "current_price": 100.0,
                "fast_ma": 100.0,
                "slow_ma": 100.0,
            }

            # 测试每个交易对都能正常处理
            buy_result = self.engine.process_buy_signal(symbol, signals, 2.0)
            sell_result = self.engine.process_sell_signal(symbol, signals)

            assert isinstance(buy_result, bool)
            assert isinstance(sell_result, bool)
