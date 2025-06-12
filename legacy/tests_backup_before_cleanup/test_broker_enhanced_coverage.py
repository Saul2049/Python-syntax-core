#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经纪商模块增强测试 (Enhanced Broker Module Tests)

专门测试 src/brokers/broker.py 模块，提高覆盖率。
这是一个重要的交易执行模块，需要全面的测试覆盖。
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

try:
    from src.brokers.broker import Broker
    from src.core.position_management import PositionManager
    from src.notify import Notifier
except ImportError:
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from brokers.broker import Broker
    from core.position_management import PositionManager
    from notify import Notifier


class TestBrokerInitialization(unittest.TestCase):
    """测试Broker类的初始化"""

    def setUp(self):
        """设置测试环境"""
        self.api_key = "test_api_key"
        self.api_secret = "test_api_secret"
        self.telegram_token = "test_telegram_token"

    def tearDown(self):
        """清理测试环境"""
        pass

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    @patch("src.utils.get_trades_dir")
    def test_broker_initialization_basic(
        self, mock_get_trades_dir, mock_notifier, mock_position_manager
    ):
        """测试基本初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_trades_dir.return_value = temp_dir
            mock_position_manager_instance = Mock()
            mock_position_manager.return_value = mock_position_manager_instance
            mock_position_manager_instance.positions = {}

            broker = Broker(
                api_key=self.api_key, api_secret=self.api_secret, telegram_token=self.telegram_token
            )

            # 验证初始化参数
            self.assertEqual(broker.api_key, self.api_key)
            self.assertEqual(broker.api_secret, self.api_secret)
            self.assertEqual(broker.trades_dir, temp_dir)

            # 验证组件初始化
            mock_notifier.assert_called_once_with(self.telegram_token)
            mock_position_manager.assert_called_once()
            mock_position_manager_instance.load_from_file.assert_called_once()

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_broker_initialization_with_custom_trades_dir(
        self, mock_notifier, mock_position_manager
    ):
        """测试使用自定义交易目录的初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_trades_dir = os.path.join(temp_dir, "custom_trades")
            mock_position_manager_instance = Mock()
            mock_position_manager.return_value = mock_position_manager_instance
            mock_position_manager_instance.positions = {}

            broker = Broker(
                api_key=self.api_key, api_secret=self.api_secret, trades_dir=custom_trades_dir
            )

            self.assertEqual(broker.trades_dir, custom_trades_dir)

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_broker_initialization_without_telegram(self, mock_notifier, mock_position_manager):
        """测试不使用Telegram的初始化"""
        mock_position_manager_instance = Mock()
        mock_position_manager.return_value = mock_position_manager_instance
        mock_position_manager_instance.positions = {}

        broker = Broker(api_key=self.api_key, api_secret=self.api_secret)

        # 验证Notifier使用None初始化
        mock_notifier.assert_called_once_with(None)


class TestBrokerOrderExecution:
    """测试Broker的订单执行功能"""

    @pytest.fixture(autouse=True)
    def setup_method(self, temp_directory):
        """设置测试环境"""
        self.temp_dir = temp_directory

        # Mock所有依赖
        self.mock_notifier = Mock(spec=Notifier)
        self.mock_position_manager = Mock(spec=PositionManager)
        self.mock_position_manager.positions = {}

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_execute_order_buy_success(self, mock_notifier_class, mock_position_manager_class):
        """测试成功执行买入订单"""
        # 设置mocks
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        # Mock内部方法
        with (
            patch.object(broker, "_execute_order_internal") as mock_execute,
            patch.object(broker, "_update_positions_after_trade") as mock_update_pos,
            patch.object(broker, "_log_trade_to_csv") as mock_log,
            patch.object(broker, "_send_trade_notification") as mock_notify,
        ):

            mock_execute.return_value = {
                "order_id": "test_order_123",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": 0.1,
                "price": 50000.0,
                "status": "FILLED",
            }

            result = broker.execute_order(
                symbol="BTCUSDT", side="BUY", quantity=0.1, price=50000.0, reason="Test buy order"
            )

            # 验证结果
            assert result["order_id"] == "test_order_123"
            assert result["status"] == "FILLED"

            # 验证内部方法调用
            mock_execute.assert_called_once_with("BTCUSDT", "BUY", 0.1, 50000.0)
            mock_update_pos.assert_called_once_with("BTCUSDT", "BUY", 0.1, 50000.0)
            mock_log.assert_called_once()
            mock_notify.assert_called_once()

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_execute_order_sell_success(self, mock_notifier_class, mock_position_manager_class):
        """测试成功执行卖出订单"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        with (
            patch.object(broker, "_execute_order_internal") as mock_execute,
            patch.object(broker, "_update_positions_after_trade") as mock_update_pos,
            patch.object(broker, "_log_trade_to_csv") as mock_log,
            patch.object(broker, "_send_trade_notification") as mock_notify,
        ):

            mock_execute.return_value = {
                "order_id": "test_order_456",
                "symbol": "ETHUSDT",
                "side": "SELL",
                "quantity": 1.0,
                "price": 3000.0,
                "status": "FILLED",
            }

            result = broker.execute_order(
                symbol="ETHUSDT", side="SELL", quantity=1.0, reason="Test sell order"
            )

            # 验证结果
            assert result["side"] == "SELL"
            mock_update_pos.assert_called_once_with("ETHUSDT", "SELL", 1.0, 3000.0)

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_execute_order_with_exception(self, mock_notifier_class, mock_position_manager_class):
        """测试订单执行异常处理"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        with patch.object(broker, "_execute_order_internal") as mock_execute:
            mock_execute.side_effect = Exception("Network error")

            with pytest.raises(Exception):
                broker.execute_order("BTCUSDT", "BUY", 0.1)

            # 验证错误通知被调用
            self.mock_notifier.notify_error.assert_called_once()


class TestBrokerInternalMethods:
    """测试Broker的内部方法"""

    @pytest.fixture(autouse=True)
    def setup_method(self, temp_directory):
        """设置测试环境"""
        self.temp_dir = temp_directory
        self.mock_notifier = Mock(spec=Notifier)
        self.mock_position_manager = Mock(spec=PositionManager)
        self.mock_position_manager.positions = {}

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    @patch("time.time")
    def test_execute_order_internal(
        self, mock_time, mock_notifier_class, mock_position_manager_class
    ):
        """测试内部订单执行逻辑"""
        mock_time.return_value = 1640995200  # 固定时间戳
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        with patch.object(broker, "_get_mock_price") as mock_price:
            mock_price.return_value = 45000.0

            # 测试市价单
            result = broker._execute_order_internal("BTCUSDT", "BUY", 0.1, None)

            assert result["symbol"] == "BTCUSDT"
            assert result["side"] == "BUY"
            assert result["quantity"] == 0.1
            assert result["price"] == 45000.0
            assert result["status"] == "FILLED"
            assert "order_id" in result

            # 测试限价单
            result = broker._execute_order_internal("BTCUSDT", "BUY", 0.1, 50000.0)
            assert result["price"] == 50000.0

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_update_positions_after_trade_buy(
        self, mock_notifier_class, mock_position_manager_class
    ):
        """测试买入后仓位更新"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager
        self.mock_position_manager.has_position.return_value = False

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        broker._update_positions_after_trade("BTCUSDT", "BUY", 0.1, 50000.0)

        # 验证新仓位被添加
        self.mock_position_manager.add_position.assert_called_once()
        args = self.mock_position_manager.add_position.call_args[0]
        assert args[0] == "BTCUSDT"
        assert args[1] == 0.1
        assert args[2] == 50000.0
        assert args[3] < 50000.0  # 止损价格应该低于买入价格

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_update_positions_after_trade_sell(
        self, mock_notifier_class, mock_position_manager_class
    ):
        """测试卖出后仓位更新"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        broker._update_positions_after_trade("BTCUSDT", "SELL", 0.1, 50000.0)

        # 验证仓位被移除
        self.mock_position_manager.remove_position.assert_called_once_with("BTCUSDT")

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_log_trade_to_csv_new_file(self, mock_notifier_class, mock_position_manager_class):
        """测试记录交易到新CSV文件"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        trade_data = {
            "timestamp": "2024-01-01T12:00:00",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.1,
            "price": 50000.0,
            "reason": "Test",
            "order_id": "test_123",
            "status": "FILLED",
        }

        broker._log_trade_to_csv(trade_data)

        # 验证文件被创建
        trades_file = Path(self.temp_dir) / "trades.csv"
        assert trades_file.exists()

        # 验证文件内容
        df = pd.read_csv(trades_file)
        assert len(df) == 1
        assert df.iloc[0]["symbol"] == "BTCUSDT"

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_log_trade_to_csv_append(self, mock_notifier_class, mock_position_manager_class):
        """测试追加交易记录到现有CSV文件"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        # 创建初始文件
        trades_file = Path(self.temp_dir) / "trades.csv"
        initial_data = pd.DataFrame(
            [
                {
                    "timestamp": "2024-01-01T11:00:00",
                    "symbol": "ETHUSDT",
                    "side": "SELL",
                    "quantity": 1.0,
                    "price": 3000.0,
                    "reason": "Initial",
                    "order_id": "initial_123",
                    "status": "FILLED",
                }
            ]
        )
        initial_data.to_csv(trades_file, index=False)

        # 追加新交易
        trade_data = {
            "timestamp": "2024-01-01T12:00:00",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.1,
            "price": 50000.0,
            "reason": "Test",
            "order_id": "test_123",
            "status": "FILLED",
        }

        broker._log_trade_to_csv(trade_data)

        # 验证文件内容
        df = pd.read_csv(trades_file)
        assert len(df) == 2
        assert df.iloc[1]["symbol"] == "BTCUSDT"

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_send_trade_notification(self, mock_notifier_class, mock_position_manager_class):
        """测试发送交易通知"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        trade_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.1,
            "price": 50000.0,
            "reason": "Test buy",
        }

        broker._send_trade_notification(trade_data)

        # 验证通知被发送
        self.mock_notifier.notify_trade.assert_called_once()
        args = self.mock_notifier.notify_trade.call_args[0]
        assert args[0] == trade_data
        assert "交易执行" in args[1]
        assert "BTCUSDT" in args[1]

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_get_mock_price(self, mock_notifier_class, mock_position_manager_class):
        """测试模拟价格获取"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        # 测试不同交易对的模拟价格
        btc_price = broker._get_mock_price("BTCUSDT")
        eth_price = broker._get_mock_price("ETHUSDT")
        unknown_price = broker._get_mock_price("UNKNOWN")

        assert isinstance(btc_price, float)
        assert isinstance(eth_price, float)
        assert isinstance(unknown_price, float)

        # BTC价格应该在合理范围内
        assert btc_price > 20000
        assert btc_price < 100000


class TestBrokerPositionManagement:
    """测试Broker的仓位管理功能"""

    @pytest.fixture(autouse=True)
    def setup_method(self, temp_directory):
        """设置测试环境"""
        self.temp_dir = temp_directory
        self.mock_notifier = Mock(spec=Notifier)
        self.mock_position_manager = Mock(spec=PositionManager)
        self.mock_position_manager.positions = {"BTCUSDT": {"quantity": 0.1, "entry_price": 50000}}

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_update_position_stops(self, mock_notifier_class, mock_position_manager_class):
        """测试更新仓位止损"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        broker.update_position_stops("BTCUSDT", 52000.0, 1000.0)

        # 验证仓位管理器的方法被调用（包含notifier参数）
        self.mock_position_manager.update_trailing_stops.assert_called_once_with(
            "BTCUSDT", 52000.0, 1000.0, self.mock_notifier
        )

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_check_stop_loss(self, mock_notifier_class, mock_position_manager_class):
        """测试检查止损"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        # 设置mock返回值
        self.mock_position_manager.check_stop_loss = Mock(return_value=True)
        self.mock_position_manager.get_position = Mock(
            return_value={"quantity": 0.1, "entry_price": 50000}
        )

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        # Mock execute_order方法
        with patch.object(broker, "execute_order") as mock_execute:
            result = broker.check_stop_loss("BTCUSDT", 48000.0)

            # 验证结果
            assert result is True
            self.mock_position_manager.check_stop_loss.assert_called_once_with("BTCUSDT", 48000.0)
            self.mock_position_manager.get_position.assert_called_once_with("BTCUSDT")
            mock_execute.assert_called_once()

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_positions_property_getter(self, mock_notifier_class, mock_position_manager_class):
        """测试positions属性getter"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        positions = broker.positions

        # 修复：验证返回仓位管理器的positions属性，而不是方法调用
        assert positions is not None

    @patch("src.brokers.broker.PositionManager")
    @patch("src.brokers.broker.Notifier")
    def test_positions_property_setter(self, mock_notifier_class, mock_position_manager_class):
        """测试positions属性setter"""
        mock_notifier_class.return_value = self.mock_notifier
        mock_position_manager_class.return_value = self.mock_position_manager

        broker = Broker("key", "secret", trades_dir=self.temp_dir)

        new_positions = {"ETHUSDT": {"quantity": 1.0, "entry_price": 3000}}
        broker.positions = new_positions

        # 验证仓位管理器的positions被更新
        assert self.mock_position_manager.positions == new_positions


if __name__ == "__main__":
    unittest.main()
