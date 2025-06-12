#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.strategies.__init__ 模块的功能
Test for src.strategies.__init__ module

覆盖目标:
- get_strategy_by_name 函数
- list_strategies_by_type 函数
- 模块导入和导出
"""

import unittest

import pytest

# Import modules to test
try:
    from src.strategies import (
        ALL_STRATEGIES,
        STRATEGY_GROUPS,
        BaseStrategy,
        RSIStrategy,
        SimpleMAStrategy,
        get_strategy_by_name,
        list_strategies_by_type,
    )
except ImportError:
    pytest.skip("Strategies module not available, skipping tests", allow_module_level=True)


class TestStrategiesInit(unittest.TestCase):
    """测试策略模块初始化功能"""

    def test_get_strategy_by_name_found(self):
        """测试根据名称获取策略类 - 找到策略"""
        # 测试获取存在的策略
        strategy_class = get_strategy_by_name("SimpleMAStrategy")

        # 验证返回正确的策略类
        self.assertIsNotNone(strategy_class)
        self.assertEqual(strategy_class.__name__, "SimpleMAStrategy")
        self.assertEqual(strategy_class, SimpleMAStrategy)

    def test_get_strategy_by_name_not_found(self):
        """测试根据名称获取策略类 - 未找到策略"""
        # 测试获取不存在的策略
        strategy_class = get_strategy_by_name("NonExistentStrategy")

        # 验证返回None（覆盖第134行）
        self.assertIsNone(strategy_class)

    def test_get_strategy_by_name_multiple_strategies(self):
        """测试获取多个不同的策略类"""
        # 测试多个策略类（只使用ALL_STRATEGIES中实际存在的策略）
        test_strategies = ["SimpleMAStrategy", "RSIStrategy", "MACDStrategy"]

        for strategy_name in test_strategies:
            strategy_class = get_strategy_by_name(strategy_name)
            self.assertIsNotNone(strategy_class)
            self.assertEqual(strategy_class.__name__, strategy_name)

    def test_list_strategies_by_type_none(self):
        """测试列出所有策略（type=None）"""
        # 测试返回所有策略（覆盖第148-149行）
        strategies = list_strategies_by_type(None)

        # 验证返回所有策略
        self.assertEqual(strategies, ALL_STRATEGIES)
        self.assertGreater(len(strategies), 0)

    def test_list_strategies_by_type_specific(self):
        """测试列出特定类型的策略"""
        # 测试获取移动平均策略
        ma_strategies = list_strategies_by_type("moving_average")

        # 验证返回正确的策略组
        self.assertEqual(ma_strategies, STRATEGY_GROUPS["moving_average"])
        self.assertIn(SimpleMAStrategy, ma_strategies)

    def test_list_strategies_by_type_invalid(self):
        """测试列出不存在类型的策略"""
        # 测试获取不存在的策略类型（覆盖第150行）
        invalid_strategies = list_strategies_by_type("invalid_type")

        # 验证返回空列表
        self.assertEqual(invalid_strategies, [])

    def test_list_strategies_by_type_all_types(self):
        """测试所有策略类型"""
        # 测试所有已定义的策略类型
        for strategy_type in STRATEGY_GROUPS.keys():
            strategies = list_strategies_by_type(strategy_type)
            self.assertIsInstance(strategies, list)
            self.assertGreater(len(strategies), 0)

    def test_all_strategies_list(self):
        """测试ALL_STRATEGIES列表"""
        # 验证ALL_STRATEGIES不为空
        self.assertIsInstance(ALL_STRATEGIES, list)
        self.assertGreater(len(ALL_STRATEGIES), 0)

        # 验证所有策略都是类
        for strategy in ALL_STRATEGIES:
            self.assertTrue(hasattr(strategy, "__name__"))

    def test_strategy_groups_dict(self):
        """测试STRATEGY_GROUPS字典"""
        # 验证STRATEGY_GROUPS是字典
        self.assertIsInstance(STRATEGY_GROUPS, dict)
        self.assertGreater(len(STRATEGY_GROUPS), 0)

        # 验证所有组都包含策略列表
        for group_name, strategies in STRATEGY_GROUPS.items():
            self.assertIsInstance(strategies, list)
            self.assertGreater(len(strategies), 0)

    def test_module_exports(self):
        """测试模块导出"""
        # 验证主要导出项存在
        self.assertTrue(hasattr(get_strategy_by_name, "__call__"))
        self.assertTrue(hasattr(list_strategies_by_type, "__call__"))

        # 验证策略类可以导入
        self.assertIsNotNone(BaseStrategy)
        self.assertIsNotNone(SimpleMAStrategy)
        self.assertIsNotNone(RSIStrategy)


if __name__ == "__main__":
    unittest.main()
