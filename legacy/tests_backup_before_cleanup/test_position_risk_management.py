#!/usr/bin/env python3
"""
持仓管理和风险管理模块综合测试 - 提高覆盖率
Position and Risk Management Tests - Coverage Boost

重点关注:
- src/core/position_management.py (当前29.1%覆盖率)
- src/core/risk_management.py (当前21.7%覆盖率)
"""

import os
import tempfile

import pandas as pd
import pytest

from src.core.position_management import PositionManager
from src.core.risk_management import (
    compute_atr,
    compute_position_size,
    compute_stop_price,
    compute_trailing_stop,
    trailing_stop,
    update_trailing_stop_atr,
)


class TestPositionManager:
    """测试仓位管理器"""

    def setup_method(self):
        """测试前设置"""
        # 使用临时文件进行测试
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.close()
        self.position_manager = PositionManager(positions_file=self.temp_file.name)

    def teardown_method(self):
        """测试后清理"""
        # 清理临时文件
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_position_manager_initialization(self):
        """测试仓位管理器初始化"""
        # 测试默认初始化
        pm_default = PositionManager()
        assert pm_default.positions_file == "position_state.json"
        assert isinstance(pm_default.positions, dict)

        # 测试自定义文件路径初始化
        assert self.position_manager.positions_file == self.temp_file.name

    def test_add_position(self):
        """测试添加仓位"""
        symbol = "BTCUSDT"
        quantity = 1.0
        entry_price = 50000.0
        stop_price = 49000.0
        side = "LONG"

        # 添加仓位
        self.position_manager.add_position(symbol, quantity, entry_price, stop_price, side)

        # 验证仓位被添加
        assert symbol in self.position_manager.positions
        position = self.position_manager.positions[symbol]
        assert position["quantity"] == quantity
        assert position["entry_price"] == entry_price
        assert position["stop_price"] == stop_price
        assert position["side"] == side

    def test_remove_position(self):
        """测试移除仓位"""
        symbol = "BTCUSDT"
        self.position_manager.add_position(symbol, 1.0, 50000.0, 49000.0)

        # 移除仓位
        removed_position = self.position_manager.remove_position(symbol)

        # 验证仓位被移除
        assert symbol not in self.position_manager.positions
        assert removed_position is not None

        # 尝试移除不存在的仓位
        non_existent = self.position_manager.remove_position("NONEXISTENT")
        assert non_existent is None

    def test_update_stop_price(self):
        """测试更新止损价格"""
        symbol = "BTCUSDT"
        self.position_manager.add_position(symbol, 1.0, 50000.0, 49000.0)

        # 更新止损价格
        new_stop_price = 49500.0
        result = self.position_manager.update_stop_price(symbol, new_stop_price)

        # 验证更新成功
        assert result is True
        position = self.position_manager.positions[symbol]
        assert position["stop_price"] == new_stop_price

        # 尝试更新不存在的仓位
        result = self.position_manager.update_stop_price("NONEXISTENT", 1000.0)
        assert result is False

    def test_get_position(self):
        """测试获取仓位信息"""
        symbol = "BTCUSDT"
        self.position_manager.add_position(symbol, 1.0, 50000.0, 49000.0)

        # 获取存在的仓位
        position = self.position_manager.get_position(symbol)
        assert position is not None

        # 获取不存在的仓位
        non_existent = self.position_manager.get_position("NONEXISTENT")
        assert non_existent is None

    def test_has_position(self):
        """测试检查是否有仓位"""
        symbol = "BTCUSDT"

        # 初始状态没有仓位
        assert self.position_manager.has_position(symbol) is False

        # 添加仓位后
        self.position_manager.add_position(symbol, 1.0, 50000.0, 49000.0)
        assert self.position_manager.has_position(symbol) is True

    def test_check_stop_loss(self):
        """测试检查止损"""
        symbol = "BTCUSDT"
        self.position_manager.add_position(symbol, 1.0, 50000.0, 49000.0, "LONG")

        # 测试不同价格下的止损检查
        assert self.position_manager.check_stop_loss(symbol, 49500.0) is False
        assert self.position_manager.check_stop_loss(symbol, 49000.0) is True
        assert self.position_manager.check_stop_loss(symbol, 48500.0) is True

        # 测试不存在的仓位
        assert self.position_manager.check_stop_loss("NONEXISTENT", 50000.0) is False

    def test_calculate_unrealized_pnl(self):
        """测试计算未实现盈亏"""
        symbol = "BTCUSDT"
        entry_price = 50000.0
        quantity = 2.0
        self.position_manager.add_position(symbol, quantity, entry_price, 49000.0, "LONG")

        # 测试价格上涨情况
        pnl = self.position_manager.calculate_unrealized_pnl(symbol, 52000.0)
        expected_pnl = (52000.0 - entry_price) * quantity
        assert pnl == expected_pnl

        # 测试不存在的仓位
        pnl = self.position_manager.calculate_unrealized_pnl("NONEXISTENT", 50000.0)
        assert pnl == 0.0


class TestRiskManagement:
    """测试风险管理功能"""

    def test_compute_atr(self):
        """测试ATR计算"""
        # 创建测试价格序列
        prices = pd.Series([100, 102, 98, 105, 103, 107, 104, 109, 106, 112])

        # 计算ATR
        atr = compute_atr(prices, window=5)

        assert isinstance(atr, float)
        assert atr >= 0

        # 测试空序列
        empty_series = pd.Series([])
        atr_empty = compute_atr(empty_series)
        assert atr_empty == 0.0

    def test_compute_position_size(self):
        """测试仓位大小计算"""
        equity = 10000.0
        atr = 100.0
        risk_frac = 0.02

        # 正常计算
        position_size = compute_position_size(equity, atr, risk_frac)
        expected_size = max(1, int((equity * risk_frac) / atr))
        assert position_size == expected_size

        # ATR为零的情况
        position_size_zero_atr = compute_position_size(equity, 0.0, risk_frac)
        assert position_size_zero_atr == 1

    def test_compute_stop_price(self):
        """测试止损价格计算"""
        entry_price = 50000.0
        atr = 500.0
        multiplier = 2.0

        # 正常计算
        stop_price = compute_stop_price(entry_price, atr, multiplier)
        expected_stop = entry_price - multiplier * atr
        assert stop_price == expected_stop

    def test_trailing_stop(self):
        """测试跟踪止损计算"""
        entry_price = 50000.0
        atr = 500.0
        factor = 2.0

        # 正常计算
        trail_stop = trailing_stop(entry_price, atr, factor)
        expected_stop = entry_price - (factor * atr)
        assert trail_stop == expected_stop

    def test_compute_trailing_stop(self):
        """测试移动止损计算"""
        entry_price = 50000.0
        initial_stop = 49000.0
        atr = 300.0

        # 测试价格低于入场价的情况
        below_entry_stop = compute_trailing_stop(entry_price, 49500.0, initial_stop, atr=atr)
        assert below_entry_stop == initial_stop

    def test_update_trailing_stop_atr(self):
        """测试基于ATR的跟踪止损更新"""
        position = {"entry_price": 50000.0, "stop_price": 49000.0, "quantity": 1.0, "side": "LONG"}

        current_price = 52000.0
        atr = 300.0

        # 测试正常更新
        new_stop, updated = update_trailing_stop_atr(position, current_price, atr)
        assert isinstance(new_stop, float)
        assert isinstance(updated, bool)

        # 测试空仓位
        empty_stop, empty_updated = update_trailing_stop_atr({}, current_price, atr)
        assert empty_stop == 0.0
        assert empty_updated is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
