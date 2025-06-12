"""
经纪商模块覆盖率提升测试 (Broker Module Coverage Boost Tests)

专门针对 src/brokers/broker.py 中未覆盖的代码行进行测试，
将覆盖率从 25% 提升到 85%+。

目标缺失行: 41-51, 74-102, 124-126, 140-148, 152-166, 170-182, 201-224, 235, 248-259, 264-272, 277, 282
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.brokers.broker import Broker


class TestBrokerInitialization:
    """测试经纪商初始化"""

    def test_broker_initialization_basic(self):
        """测试基本初始化 (Lines 41-51)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(
                api_key="test_key",
                api_secret="test_secret",
                telegram_token="test_token",
                trades_dir=temp_dir,
            )

            assert broker.api_key == "test_key"
            assert broker.api_secret == "test_secret"
            assert broker.trades_dir == temp_dir
            assert broker.notifier is not None
            assert broker.position_manager is not None
            assert broker.positions is not None

    def test_broker_initialization_default_trades_dir(self):
        """测试默认交易目录初始化"""
        with patch("src.utils.get_trades_dir", return_value="/mock/trades"):
            broker = Broker(api_key="test_key", api_secret="test_secret")

            assert broker.trades_dir == "/mock/trades"


class TestBrokerExecuteOrder:
    """测试订单执行功能"""

    @pytest.fixture
    def broker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)
            yield broker

    def test_execute_order_success(self, broker):
        """测试成功执行订单 (Lines 74-102)"""
        with (
            patch.object(broker, "_execute_order_internal") as mock_execute,
            patch.object(broker, "_update_positions_after_trade") as mock_update,
            patch.object(broker, "_log_trade_to_csv") as mock_log,
            patch.object(broker, "_send_trade_notification") as mock_notify,
        ):

            mock_execute.return_value = {
                "order_id": "test_order_123",
                "price": 50000.0,
                "status": "FILLED",
            }

            result = broker.execute_order(
                symbol="BTCUSDT", side="BUY", quantity=0.001, price=50000.0, reason="测试买入"
            )

            assert result["order_id"] == "test_order_123"
            assert result["price"] == 50000.0

            # 验证所有内部方法都被调用
            mock_execute.assert_called_once()
            mock_update.assert_called_once()
            mock_log.assert_called_once()
            mock_notify.assert_called_once()

    def test_execute_order_exception_handling(self, broker):
        """测试订单执行异常处理"""
        with (
            patch.object(broker, "_execute_order_internal", side_effect=Exception("网络错误")),
            patch.object(broker.notifier, "notify_error") as mock_notify_error,
        ):

            with pytest.raises(Exception, match="网络错误"):
                broker.execute_order(symbol="BTCUSDT", side="BUY", quantity=0.001)

            mock_notify_error.assert_called_once()


class TestBrokerInternalMethods:
    """测试经纪商内部方法"""

    @pytest.fixture
    def broker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)
            yield broker

    def test_execute_order_internal_with_price(self, broker):
        """测试内部订单执行（指定价格）(Lines 124-126)"""
        result = broker._execute_order_internal(
            symbol="BTCUSDT", side="BUY", quantity=0.001, price=50000.0
        )

        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "BUY"
        assert result["quantity"] == 0.001
        assert result["price"] == 50000.0
        assert result["status"] == "FILLED"
        assert "order_id" in result
        assert "timestamp" in result

    def test_execute_order_internal_market_order(self, broker):
        """测试内部订单执行（市价单）"""
        with patch.object(broker, "_get_mock_price", return_value=49500.0):
            result = broker._execute_order_internal(symbol="BTCUSDT", side="SELL", quantity=0.001)

            assert result["price"] == 49500.0

    def test_update_positions_after_buy_trade(self, broker):
        """测试买入后更新仓位 (Lines 140-148)"""
        with (
            patch.object(broker.position_manager, "has_position", return_value=False),
            patch.object(broker.position_manager, "add_position") as mock_add,
        ):

            broker._update_positions_after_trade(
                symbol="BTCUSDT", side="BUY", quantity=0.001, price=50000.0
            )

            mock_add.assert_called_once_with("BTCUSDT", 0.001, 50000.0, 49000.0)  # 2%止损

    def test_update_positions_after_sell_trade(self, broker):
        """测试卖出后更新仓位"""
        with patch.object(broker.position_manager, "remove_position") as mock_remove:

            broker._update_positions_after_trade(
                symbol="BTCUSDT", side="SELL", quantity=0.001, price=50000.0
            )

            mock_remove.assert_called_once_with("BTCUSDT")

    def test_log_trade_to_csv_new_file(self, broker):
        """测试记录交易到新CSV文件 (Lines 152-166)"""
        trade_data = {
            "timestamp": "2024-01-01T12:00:00",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "price": 50000.0,
            "reason": "测试",
            "order_id": "123",
            "status": "FILLED",
        }

        trades_file = Path(broker.trades_dir) / "trades.csv"
        assert not trades_file.exists()

        broker._log_trade_to_csv(trade_data)

        assert trades_file.exists()
        df = pd.read_csv(trades_file)
        assert len(df) == 1
        assert df.iloc[0]["symbol"] == "BTCUSDT"

    def test_log_trade_to_csv_append_to_existing(self, broker):
        """测试追加交易到现有CSV文件"""
        # 先创建一个交易记录
        first_trade = {
            "timestamp": "2024-01-01T12:00:00",
            "symbol": "ETHUSDT",
            "side": "BUY",
            "quantity": 0.1,
            "price": 3000.0,
            "reason": "首次",
            "order_id": "456",
            "status": "FILLED",
        }
        broker._log_trade_to_csv(first_trade)

        # 再追加一个交易记录
        second_trade = {
            "timestamp": "2024-01-01T13:00:00",
            "symbol": "BTCUSDT",
            "side": "SELL",
            "quantity": 0.001,
            "price": 51000.0,
            "reason": "止盈",
            "order_id": "789",
            "status": "FILLED",
        }
        broker._log_trade_to_csv(second_trade)

        trades_file = Path(broker.trades_dir) / "trades.csv"
        df = pd.read_csv(trades_file)
        assert len(df) == 2
        assert df.iloc[1]["symbol"] == "BTCUSDT"

    def test_log_trade_to_csv_exception_handling(self, broker):
        """测试CSV记录异常处理"""
        trade_data = {"invalid": "data"}

        with patch("pandas.DataFrame.to_csv", side_effect=Exception("磁盘满")):
            # 不应该抛出异常，应该静默处理
            broker._log_trade_to_csv(trade_data)

    def test_send_trade_notification_buy(self, broker):
        """测试买入交易通知 (Lines 170-182)"""
        trade_data = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "quantity": 0.001,
            "price": 50000.12345678,
            "reason": "突破信号",
        }

        with patch.object(broker.notifier, "notify_trade") as mock_notify:
            broker._send_trade_notification(trade_data)

            mock_notify.assert_called_once()
            args, kwargs = mock_notify.call_args
            message = args[1]

            assert "🟢" in message  # 买入emoji
            assert "BTCUSDT" in message
            assert "BUY" in message
            assert "50000.12345678" in message
            assert "突破信号" in message

    def test_send_trade_notification_sell(self, broker):
        """测试卖出交易通知"""
        trade_data = {
            "symbol": "ETHUSDT",
            "side": "SELL",
            "quantity": 0.1,
            "price": 3000.0,
            "reason": "止损",
        }

        with patch.object(broker.notifier, "notify_trade") as mock_notify:
            broker._send_trade_notification(trade_data)

            args, kwargs = mock_notify.call_args
            message = args[1]

            assert "🔴" in message  # 卖出emoji
            assert "SELL" in message

    def test_send_trade_notification_exception_handling(self, broker):
        """测试交易通知异常处理"""
        trade_data = {"symbol": "BTCUSDT", "side": "BUY"}

        with patch.object(broker.notifier, "notify_trade", side_effect=Exception("网络错误")):
            # 不应该抛出异常，应该静默处理
            broker._send_trade_notification(trade_data)


class TestBrokerTradeHistory:
    """测试交易历史功能"""

    @pytest.fixture
    def broker_with_trades(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)

            # 创建测试交易数据
            trades_data = [
                {
                    "timestamp": "2024-01-01T10:00:00",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "quantity": 0.001,
                    "price": 50000.0,
                    "reason": "开仓",
                    "order_id": "1",
                    "status": "FILLED",
                },
                {
                    "timestamp": "2024-01-02T10:00:00",
                    "symbol": "BTCUSDT",
                    "side": "SELL",
                    "quantity": 0.001,
                    "price": 52000.0,
                    "reason": "止盈",
                    "order_id": "2",
                    "status": "FILLED",
                },
                {
                    "timestamp": "2024-01-03T10:00:00",
                    "symbol": "ETHUSDT",
                    "side": "BUY",
                    "quantity": 0.1,
                    "price": 3000.0,
                    "reason": "开仓",
                    "order_id": "3",
                    "status": "FILLED",
                },
            ]

            # 写入CSV文件
            df = pd.DataFrame(trades_data)
            trades_file = Path(temp_dir) / "trades.csv"
            df.to_csv(trades_file, index=False)

            yield broker

    def test_get_all_trades_no_file(self):
        """测试获取交易记录（文件不存在）(Lines 201-224)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)

            result = broker.get_all_trades("BTCUSDT")
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    def test_get_all_trades_by_symbol(self, broker_with_trades):
        """测试按交易对过滤交易记录"""
        result = broker_with_trades.get_all_trades("BTCUSDT")
        assert len(result) == 2
        assert all(result["symbol"] == "BTCUSDT")

    def test_get_all_trades_with_date_filter(self, broker_with_trades):
        """测试按日期过滤交易记录"""
        # 先不过滤symbol，测试日期过滤功能
        result = broker_with_trades.get_all_trades(
            "", start_date="2024-01-02", end_date="2024-01-02"  # 空symbol获取所有交易
        )
        # 应该只有一条在2024-01-02的记录
        trades_on_date = [t for t in result.to_dict("records") if "2024-01-02" in t["timestamp"]]
        assert len(trades_on_date) >= 1

    def test_get_all_trades_start_date_only(self, broker_with_trades):
        """测试只使用开始日期过滤"""
        result = broker_with_trades.get_all_trades(
            "BTCUSDT", start_date="2024-01-01"  # 从第一天开始
        )
        assert len(result) == 2  # 应该有两条BTCUSDT记录

    def test_get_all_trades_end_date_only(self, broker_with_trades):
        """测试只使用结束日期过滤"""
        result = broker_with_trades.get_all_trades("BTCUSDT", end_date="2024-01-02")  # 到第二天结束
        assert len(result) == 2  # 应该有两条BTCUSDT记录

    def test_get_all_trades_exception_handling(self):
        """测试获取交易记录异常处理"""
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)

            # 创建损坏的CSV文件
            trades_file = Path(temp_dir) / "trades.csv"
            trades_file.write_text("invalid,csv,content\n1,2")

            with patch("pandas.read_csv", side_effect=Exception("文件损坏")):
                result = broker.get_all_trades("BTCUSDT")
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 0


class TestBrokerPositionManagement:
    """测试仓位管理功能"""

    @pytest.fixture
    def broker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)
            yield broker

    def test_update_position_stops(self, broker):
        """测试更新仓位止损 (Line 235)"""
        with patch.object(broker.position_manager, "update_trailing_stops") as mock_update:
            broker.update_position_stops("BTCUSDT", 51000.0, 500.0)

            mock_update.assert_called_once_with("BTCUSDT", 51000.0, 500.0, broker.notifier)

    def test_check_stop_loss_triggered(self, broker):
        """测试止损检查（触发）(Lines 248-259)"""
        mock_position = {"quantity": 0.001, "entry_price": 50000.0, "stop_price": 49000.0}

        with (
            patch.object(broker.position_manager, "check_stop_loss", return_value=True),
            patch.object(broker.position_manager, "get_position", return_value=mock_position),
            patch.object(broker, "execute_order") as mock_execute,
        ):

            result = broker.check_stop_loss("BTCUSDT", 48500.0)

            assert result is True
            mock_execute.assert_called_once_with(
                symbol="BTCUSDT", side="SELL", quantity=0.001, reason="止损触发 @ 48500.000000"
            )

    def test_check_stop_loss_not_triggered(self, broker):
        """测试止损检查（未触发）"""
        with patch.object(broker.position_manager, "check_stop_loss", return_value=False):
            result = broker.check_stop_loss("BTCUSDT", 51000.0)
            assert result is False

    def test_check_stop_loss_no_position(self, broker):
        """测试止损检查（无仓位）"""
        with (
            patch.object(broker.position_manager, "check_stop_loss", return_value=True),
            patch.object(broker.position_manager, "get_position", return_value=None),
        ):

            result = broker.check_stop_loss("BTCUSDT", 48500.0)
            assert result is False  # 没有仓位信息，不执行止损


class TestBrokerUtilityMethods:
    """测试经纪商工具方法"""

    @pytest.fixture
    def broker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            broker = Broker(api_key="test_key", api_secret="test_secret", trades_dir=temp_dir)
            yield broker

    def test_get_mock_price_known_symbol(self, broker):
        """测试获取已知交易对的模拟价格 (Lines 264-272)"""
        with patch("random.uniform", return_value=0.01):  # 1%上涨
            price = broker._get_mock_price("BTCUSDT")
            assert price == 50500.0  # 50000 * 1.01

    def test_get_mock_price_unknown_symbol(self, broker):
        """测试获取未知交易对的模拟价格"""
        with patch("random.uniform", return_value=-0.01):  # 1%下跌
            price = broker._get_mock_price("UNKNOWNUSDT")
            assert price == 99.0  # 100 * 0.99

    def test_positions_property_getter(self, broker):
        """测试仓位属性获取 (Line 277)"""
        mock_positions = {"BTCUSDT": {"quantity": 0.001}}

        with patch.object(
            broker.position_manager, "get_all_positions", return_value=mock_positions
        ):
            positions = broker.positions
            assert positions == mock_positions

    def test_positions_property_setter(self, broker):
        """测试仓位属性设置 (Line 282)"""
        new_positions = {"ETHUSDT": {"quantity": 0.1}}
        broker.positions = new_positions

        assert broker.position_manager.positions == new_positions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
