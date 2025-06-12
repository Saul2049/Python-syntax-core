#!/usr/bin/env python3
"""
测试核心仓位管理模块 (Test Core Position Management Module)
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.core.position_management import PositionManager


class TestPositionManagerInitialization:
    """测试仓位管理器初始化 (Test Position Manager Initialization)"""

    def test_init_default_file(self):
        """测试默认文件路径初始化"""
        pm = PositionManager()

        assert pm.positions == {}
        assert pm.positions_file == "position_state.json"

    def test_init_custom_file(self):
        """测试自定义文件路径初始化"""
        custom_file = "custom_positions.json"
        pm = PositionManager(positions_file=custom_file)

        assert pm.positions == {}
        assert pm.positions_file == custom_file

    def test_init_none_file(self):
        """测试None文件路径初始化"""
        pm = PositionManager(positions_file=None)

        assert pm.positions == {}
        assert pm.positions_file == "position_state.json"


class TestPositionManagerBasicOperations:
    """测试仓位管理器基本操作 (Test Position Manager Basic Operations)"""

    @pytest.fixture
    def position_manager(self):
        """创建仓位管理器实例"""
        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            temp_file = f.name
            yield PositionManager(positions_file=temp_file)

    @patch("src.core.position_management.datetime")
    def test_add_position_basic(self, mock_datetime, position_manager):
        """测试添加基本仓位"""
        # 设置固定时间
        fixed_time = datetime(2023, 1, 10, 14, 30, 0)
        mock_datetime.now.return_value = fixed_time

        with patch.object(position_manager, "_save_positions") as mock_save:
            position_manager.add_position(
                symbol="BTCUSDT", quantity=0.1, entry_price=50000.0, stop_price=48000.0, side="LONG"
            )

            # 验证仓位被正确添加
            assert "BTCUSDT" in position_manager.positions
            position = position_manager.positions["BTCUSDT"]

            assert position["quantity"] == 0.1
            assert position["entry_price"] == 50000.0
            assert position["stop_price"] == 48000.0
            assert position["side"] == "LONG"
            assert position["entry_time"] == fixed_time.isoformat()
            assert position["last_update"] == fixed_time.isoformat()

            # 验证保存被调用
            mock_save.assert_called_once()

    @patch("src.core.position_management.datetime")
    def test_add_position_default_side(self, mock_datetime, position_manager):
        """测试添加仓位使用默认方向"""
        fixed_time = datetime(2023, 1, 10, 14, 30, 0)
        mock_datetime.now.return_value = fixed_time

        with patch.object(position_manager, "_save_positions"):
            position_manager.add_position(
                symbol="ETHUSDT", quantity=1.0, entry_price=3000.0, stop_price=2800.0
            )

            position = position_manager.positions["ETHUSDT"]
            assert position["side"] == "LONG"  # 默认方向

    def test_remove_position_exists(self, position_manager):
        """测试移除存在的仓位"""
        # 先添加仓位
        position_manager.positions["BTCUSDT"] = {
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 48000.0,
            "side": "LONG",
            "entry_time": "2023-01-10T14:30:00",
            "last_update": "2023-01-10T14:30:00",
        }

        with patch.object(position_manager, "_save_positions") as mock_save:
            removed_position = position_manager.remove_position("BTCUSDT")

            # 验证返回被移除的仓位
            assert removed_position is not None
            assert removed_position["quantity"] == 0.1
            assert removed_position["entry_price"] == 50000.0

            # 验证仓位已被移除
            assert "BTCUSDT" not in position_manager.positions

            # 验证保存被调用
            mock_save.assert_called_once()

    def test_remove_position_not_exists(self, position_manager):
        """测试移除不存在的仓位"""
        with patch.object(position_manager, "_save_positions") as mock_save:
            removed_position = position_manager.remove_position("NONEXISTENT")

            # 验证返回None
            assert removed_position is None

            # 验证保存没有被调用
            mock_save.assert_not_called()

    @patch("src.core.position_management.datetime")
    def test_update_stop_price_exists(self, mock_datetime, position_manager):
        """测试更新存在仓位的止损价格"""
        fixed_time = datetime(2023, 1, 10, 15, 30, 0)
        mock_datetime.now.return_value = fixed_time

        # 先添加仓位
        position_manager.positions["BTCUSDT"] = {
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 48000.0,
            "side": "LONG",
            "entry_time": "2023-01-10T14:30:00",
            "last_update": "2023-01-10T14:30:00",
        }

        with patch.object(position_manager, "_save_positions") as mock_save:
            result = position_manager.update_stop_price("BTCUSDT", 49000.0)

            # 验证更新成功
            assert result is True

            # 验证止损价格被更新
            position = position_manager.positions["BTCUSDT"]
            assert position["stop_price"] == 49000.0
            assert position["last_update"] == fixed_time.isoformat()

            # 验证保存被调用
            mock_save.assert_called_once()

    def test_update_stop_price_not_exists(self, position_manager):
        """测试更新不存在仓位的止损价格"""
        with patch.object(position_manager, "_save_positions") as mock_save:
            result = position_manager.update_stop_price("NONEXISTENT", 49000.0)

            # 验证更新失败
            assert result is False

            # 验证保存没有被调用
            mock_save.assert_not_called()

    def test_get_position_exists(self, position_manager):
        """测试获取存在的仓位"""
        expected_position = {
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 48000.0,
            "side": "LONG",
            "entry_time": "2023-01-10T14:30:00",
            "last_update": "2023-01-10T14:30:00",
        }
        position_manager.positions["BTCUSDT"] = expected_position

        result = position_manager.get_position("BTCUSDT")

        assert result == expected_position

    def test_get_position_not_exists(self, position_manager):
        """测试获取不存在的仓位"""
        result = position_manager.get_position("NONEXISTENT")

        assert result is None

    def test_has_position_exists(self, position_manager):
        """测试检查存在的仓位"""
        position_manager.positions["BTCUSDT"] = {"quantity": 0.1}

        assert position_manager.has_position("BTCUSDT") is True

    def test_has_position_not_exists(self, position_manager):
        """测试检查不存在的仓位"""
        assert position_manager.has_position("NONEXISTENT") is False

    def test_get_all_positions(self, position_manager):
        """测试获取所有仓位"""
        expected_positions = {
            "BTCUSDT": {"quantity": 0.1, "entry_price": 50000.0},
            "ETHUSDT": {"quantity": 1.0, "entry_price": 3000.0},
        }
        position_manager.positions = expected_positions

        result = position_manager.get_all_positions()

        # 验证返回副本
        assert result == expected_positions
        assert result is not position_manager.positions


class TestPositionManagerAdvancedFeatures:
    """测试仓位管理器高级功能 (Test Position Manager Advanced Features)"""

    @pytest.fixture
    def position_manager(self):
        """创建仓位管理器实例"""
        return PositionManager(positions_file="test_positions.json")

    @patch("src.core.position_management.update_trailing_stop_atr")
    def test_update_trailing_stops_exists_updated(self, mock_update_stop, position_manager):
        """测试更新跟踪止损 - 仓位存在且更新"""
        # 设置仓位
        position_manager.positions["BTCUSDT"] = {
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 48000.0,
            "side": "LONG",
        }

        # 设置模拟返回值
        mock_update_stop.return_value = (49500.0, True)

        with patch.object(position_manager, "update_stop_price") as mock_update_price:
            mock_notifier = Mock()
            result = position_manager.update_trailing_stops(
                "BTCUSDT", 52000.0, 1000.0, mock_notifier
            )

            # 验证调用了底层函数
            mock_update_stop.assert_called_once_with(
                position_manager.positions["BTCUSDT"], 52000.0, 1000.0, notifier=mock_notifier
            )

            # 验证更新了止损价格
            mock_update_price.assert_called_once_with("BTCUSDT", 49500.0)

            # 验证返回值
            assert result is True

    @patch("src.core.position_management.update_trailing_stop_atr")
    def test_update_trailing_stops_exists_not_updated(self, mock_update_stop, position_manager):
        """测试更新跟踪止损 - 仓位存在但未更新"""
        position_manager.positions["BTCUSDT"] = {
            "quantity": 0.1,
            "entry_price": 50000.0,
            "stop_price": 48000.0,
            "side": "LONG",
        }

        # 设置模拟返回值 - 未更新
        mock_update_stop.return_value = (48000.0, False)

        with patch.object(position_manager, "update_stop_price") as mock_update_price:
            result = position_manager.update_trailing_stops("BTCUSDT", 51000.0, 1000.0)

            # 验证没有更新止损价格
            mock_update_price.assert_not_called()

            # 验证返回值
            assert result is False

    def test_update_trailing_stops_not_exists(self, position_manager):
        """测试更新跟踪止损 - 仓位不存在"""
        result = position_manager.update_trailing_stops("NONEXISTENT", 52000.0, 1000.0)

        assert result is False

    def test_check_stop_loss_long_triggered(self, position_manager):
        """测试检查止损 - 多头仓位触发"""
        position_manager.positions["BTCUSDT"] = {"stop_price": 48000.0, "side": "LONG"}

        # 当前价格低于或等于止损价格
        assert position_manager.check_stop_loss("BTCUSDT", 48000.0) is True
        assert position_manager.check_stop_loss("BTCUSDT", 47000.0) is True

    def test_check_stop_loss_long_not_triggered(self, position_manager):
        """测试检查止损 - 多头仓位未触发"""
        position_manager.positions["BTCUSDT"] = {"stop_price": 48000.0, "side": "LONG"}

        # 当前价格高于止损价格
        assert position_manager.check_stop_loss("BTCUSDT", 49000.0) is False

    def test_check_stop_loss_short_triggered(self, position_manager):
        """测试检查止损 - 空头仓位触发"""
        position_manager.positions["BTCUSDT"] = {"stop_price": 52000.0, "side": "SHORT"}

        # 当前价格高于或等于止损价格
        assert position_manager.check_stop_loss("BTCUSDT", 52000.0) is True
        assert position_manager.check_stop_loss("BTCUSDT", 53000.0) is True

    def test_check_stop_loss_short_not_triggered(self, position_manager):
        """测试检查止损 - 空头仓位未触发"""
        position_manager.positions["BTCUSDT"] = {"stop_price": 52000.0, "side": "SHORT"}

        # 当前价格低于止损价格
        assert position_manager.check_stop_loss("BTCUSDT", 51000.0) is False

    def test_check_stop_loss_not_exists(self, position_manager):
        """测试检查止损 - 仓位不存在"""
        assert position_manager.check_stop_loss("NONEXISTENT", 50000.0) is False

    def test_calculate_unrealized_pnl_long_profit(self, position_manager):
        """测试计算未实现盈亏 - 多头盈利"""
        position_manager.positions["BTCUSDT"] = {
            "entry_price": 50000.0,
            "quantity": 0.1,
            "side": "LONG",
        }

        # 当前价格高于入场价格
        pnl = position_manager.calculate_unrealized_pnl("BTCUSDT", 52000.0)
        expected_pnl = (52000.0 - 50000.0) * 0.1  # 200.0

        assert pnl == expected_pnl

    def test_calculate_unrealized_pnl_long_loss(self, position_manager):
        """测试计算未实现盈亏 - 多头亏损"""
        position_manager.positions["BTCUSDT"] = {
            "entry_price": 50000.0,
            "quantity": 0.1,
            "side": "LONG",
        }

        # 当前价格低于入场价格
        pnl = position_manager.calculate_unrealized_pnl("BTCUSDT", 48000.0)
        expected_pnl = (48000.0 - 50000.0) * 0.1  # -200.0

        assert pnl == expected_pnl

    def test_calculate_unrealized_pnl_short_profit(self, position_manager):
        """测试计算未实现盈亏 - 空头盈利"""
        position_manager.positions["BTCUSDT"] = {
            "entry_price": 50000.0,
            "quantity": 0.1,
            "side": "SHORT",
        }

        # 当前价格低于入场价格
        pnl = position_manager.calculate_unrealized_pnl("BTCUSDT", 48000.0)
        expected_pnl = (50000.0 - 48000.0) * 0.1  # 200.0

        assert pnl == expected_pnl

    def test_calculate_unrealized_pnl_short_loss(self, position_manager):
        """测试计算未实现盈亏 - 空头亏损"""
        position_manager.positions["BTCUSDT"] = {
            "entry_price": 50000.0,
            "quantity": 0.1,
            "side": "SHORT",
        }

        # 当前价格高于入场价格
        pnl = position_manager.calculate_unrealized_pnl("BTCUSDT", 52000.0)
        expected_pnl = (50000.0 - 52000.0) * 0.1  # -200.0

        assert pnl == expected_pnl

    def test_calculate_unrealized_pnl_not_exists(self, position_manager):
        """测试计算未实现盈亏 - 仓位不存在"""
        pnl = position_manager.calculate_unrealized_pnl("NONEXISTENT", 50000.0)

        assert pnl == 0.0


class TestPositionManagerFileOperations:
    """测试仓位管理器文件操作 (Test Position Manager File Operations)"""

    @pytest.fixture
    def position_manager(self):
        """创建仓位管理器实例"""
        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            temp_file = f.name
            yield PositionManager(positions_file=temp_file)

    def test_save_positions_success(self, position_manager):
        """测试成功保存仓位"""
        position_manager.positions = {
            "BTCUSDT": {
                "quantity": 0.1,
                "entry_price": 50000.0,
                "stop_price": 48000.0,
                "side": "LONG",
            }
        }

        # 调用保存方法
        position_manager._save_positions()

        # 验证文件被创建且内容正确
        assert os.path.exists(position_manager.positions_file)

        with open(position_manager.positions_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data == position_manager.positions

    @patch("builtins.print")
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_save_positions_failure(self, mock_open, mock_print, position_manager):
        """测试保存仓位失败"""
        position_manager.positions = {"BTCUSDT": {"quantity": 0.1}}

        position_manager._save_positions()

        # 验证错误信息被打印
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "保存仓位状态失败" in call_args

    def test_load_positions_success(self, position_manager):
        """测试成功加载仓位"""
        test_data = {
            "BTCUSDT": {
                "quantity": 0.1,
                "entry_price": 50000.0,
                "stop_price": 48000.0,
                "side": "LONG",
            },
            "ETHUSDT": {
                "quantity": 1.0,
                "entry_price": 3000.0,
                "stop_price": 2800.0,
                "side": "LONG",
            },
        }

        # 先保存测试数据到文件
        with open(position_manager.positions_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 加载数据
        position_manager._load_positions()

        # 验证数据被正确加载
        assert position_manager.positions == test_data

    def test_load_positions_file_not_exists(self, position_manager):
        """测试加载不存在的文件"""
        # 确保文件不存在
        if os.path.exists(position_manager.positions_file):
            os.unlink(position_manager.positions_file)

        position_manager._load_positions()

        # 验证初始化为空字典
        assert position_manager.positions == {}

    @patch("builtins.print")
    @patch("builtins.open", side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_positions_invalid_json(
        self, mock_exists, mock_open, mock_print, position_manager
    ):
        """测试加载无效JSON文件"""
        position_manager._load_positions()

        # 验证错误信息被打印
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "加载仓位状态失败" in call_args

        # 验证初始化为空字典
        assert position_manager.positions == {}

    def test_load_from_file_public_method(self, position_manager):
        """测试公共的加载方法"""
        test_data = {"BTCUSDT": {"quantity": 0.1}}

        with open(position_manager.positions_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        position_manager.load_from_file()

        assert position_manager.positions == test_data


class TestPositionManagerSummary:
    """测试仓位管理器汇总功能 (Test Position Manager Summary)"""

    @pytest.fixture
    def position_manager(self):
        """创建仓位管理器实例"""
        return PositionManager()

    def test_get_position_summary_empty(self, position_manager):
        """测试空仓位汇总"""
        summary = position_manager.get_position_summary()

        expected_summary = {
            "total_positions": 0,
            "symbols": [],
            "total_quantity": 0,
            "oldest_position": None,
            "newest_position": None,
        }

        assert summary == expected_summary

    def test_get_position_summary_single_position(self, position_manager):
        """测试单个仓位汇总"""
        entry_time = "2023-01-10T14:30:00"
        position_manager.positions = {
            "BTCUSDT": {
                "quantity": 0.1,
                "entry_price": 50000.0,
                "stop_price": 48000.0,
                "side": "LONG",
                "entry_time": entry_time,
                "last_update": entry_time,
            }
        }

        summary = position_manager.get_position_summary()

        expected_summary = {
            "total_positions": 1,
            "symbols": ["BTCUSDT"],
            "total_quantity": 0.1,
            "oldest_position": entry_time,
            "newest_position": entry_time,
        }

        assert summary == expected_summary

    def test_get_position_summary_multiple_positions(self, position_manager):
        """测试多个仓位汇总"""
        position_manager.positions = {
            "BTCUSDT": {
                "quantity": 0.1,
                "entry_price": 50000.0,
                "stop_price": 48000.0,
                "side": "LONG",
                "entry_time": "2023-01-10T14:30:00",
                "last_update": "2023-01-10T14:30:00",
            },
            "ETHUSDT": {
                "quantity": 1.0,
                "entry_price": 3000.0,
                "stop_price": 2800.0,
                "side": "LONG",
                "entry_time": "2023-01-08T10:15:00",  # 更早
                "last_update": "2023-01-08T10:15:00",
            },
            "ADAUSDT": {
                "quantity": 100.0,
                "entry_price": 0.5,
                "stop_price": 0.45,
                "side": "LONG",
                "entry_time": "2023-01-12T16:45:00",  # 最新
                "last_update": "2023-01-12T16:45:00",
            },
        }

        summary = position_manager.get_position_summary()

        expected_summary = {
            "total_positions": 3,
            "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            "total_quantity": 101.1,  # 0.1 + 1.0 + 100.0
            "oldest_position": "2023-01-08T10:15:00",
            "newest_position": "2023-01-12T16:45:00",
        }

        assert summary == expected_summary


class TestPositionManagerIntegration:
    """测试仓位管理器集成 (Test Position Manager Integration)"""

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 🧹 使用自动清理的临时文件替代delete=False
        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            temp_file = f.name

            pm = PositionManager(positions_file=temp_file)

            # 1. 添加仓位
            pm.add_position("BTCUSDT", 0.1, 50000.0, 48000.0, "LONG")
            pm.add_position("ETHUSDT", 1.0, 3000.0, 2800.0, "SHORT")

            # 2. 验证仓位存在
            assert pm.has_position("BTCUSDT")
            assert pm.has_position("ETHUSDT")

            # 3. 更新止损
            assert pm.update_stop_price("BTCUSDT", 49000.0)

            # 4. 检查止损
            assert not pm.check_stop_loss("BTCUSDT", 50000.0)  # 未触发
            assert pm.check_stop_loss("BTCUSDT", 48500.0)  # 触发

            # 5. 计算盈亏
            pnl_btc = pm.calculate_unrealized_pnl("BTCUSDT", 52000.0)
            pnl_eth = pm.calculate_unrealized_pnl("ETHUSDT", 2800.0)

            assert pnl_btc > 0  # 多头盈利
            assert pnl_eth > 0  # 空头盈利

            # 6. 获取汇总
            summary = pm.get_position_summary()
            assert summary["total_positions"] == 2
            assert "BTCUSDT" in summary["symbols"]
            assert "ETHUSDT" in summary["symbols"]

            # 7. 移除仓位
            removed = pm.remove_position("BTCUSDT")
            assert removed is not None
            assert not pm.has_position("BTCUSDT")

            # 8. 验证文件持久化
            pm2 = PositionManager(positions_file=temp_file)
            pm2.load_from_file()
            assert pm2.has_position("ETHUSDT")
            assert not pm2.has_position("BTCUSDT")
