#!/usr/bin/env python3
"""
核心模块综合测试 - 提高覆盖率
Core Modules Comprehensive Tests - Coverage Boost

重点关注:
- src/core/base_strategy.py (当前0%覆盖率)
- src/core/gc_optimizer.py (当前0%覆盖率)
"""

import gc
from datetime import datetime

import pandas as pd
import pytest

# 核心模块导入
from src.core.base_strategy import BaseStrategy
from src.core.gc_optimizer import GCOptimizer


class TestBaseStrategy:
    """测试基础策略类"""

    def setup_method(self):
        """测试前设置"""

        # 创建具体的策略实现用于测试
        class ConcreteStrategy(BaseStrategy):
            def generate_signals(self, data):
                return {
                    "signal": "HOLD",
                    "confidence": 0.5,
                    "timestamp": datetime.now(),
                    "price": data["close"].iloc[-1] if not data.empty else 100.0,
                    "metadata": {"test": True},
                }

        self.ConcreteStrategy = ConcreteStrategy

    def test_base_strategy_initialization(self):
        """测试基础策略初始化"""
        strategy = self.ConcreteStrategy(name="TestStrategy", param1=10, param2="test")

        assert strategy.name == "TestStrategy"
        assert strategy.parameters["param1"] == 10
        assert strategy.parameters["param2"] == "test"
        assert not strategy.is_initialized
        assert strategy.last_signal_time is None
        assert isinstance(strategy.performance_metrics, dict)
        assert strategy._data_cache is None
        assert strategy._last_data_hash is None

    def test_set_and_get_parameter(self):
        """测试参数设置和获取"""
        strategy = self.ConcreteStrategy()

        # 测试设置参数
        strategy.set_parameter("new_param", 42)
        assert strategy.get_parameter("new_param") == 42

        # 测试获取不存在的参数
        assert strategy.get_parameter("nonexistent") is None
        assert strategy.get_parameter("nonexistent", "default") == "default"

        # 验证参数变更会重置初始化状态
        strategy.is_initialized = True
        strategy.set_parameter("existing_param", "new_value")
        assert not strategy.is_initialized

    def test_validate_data_valid(self):
        """测试有效数据验证"""
        strategy = self.ConcreteStrategy()

        # 创建有效数据
        data = pd.DataFrame(
            {
                "close": [100, 101, 102, 103],
                "volume": [1000, 1100, 1200, 1300],
            }
        )

        assert strategy.validate_data(data) is True

    def test_validate_data_invalid(self):
        """测试无效数据验证"""
        strategy = self.ConcreteStrategy()

        # 测试空数据
        assert strategy.validate_data(None) is False
        assert strategy.validate_data(pd.DataFrame()) is False

        # 测试缺少必需列
        data_missing_close = pd.DataFrame({"volume": [1000, 1100]})
        assert strategy.validate_data(data_missing_close) is False

        data_missing_volume = pd.DataFrame({"close": [100, 101]})
        assert strategy.validate_data(data_missing_volume) is False


class TestGCOptimizer:
    """测试垃圾回收优化器"""

    def setup_method(self):
        """测试前设置"""
        self.optimizer = GCOptimizer()

    def test_gc_optimizer_initialization(self):
        """测试GC优化器初始化"""
        assert hasattr(self.optimizer, "original_thresholds")
        assert hasattr(self.optimizer, "gc_profiles")
        assert hasattr(self.optimizer, "monitoring_active")
        assert self.optimizer.monitoring_active is False
        assert isinstance(self.optimizer.gc_profiles, list)
        assert len(self.optimizer.gc_profiles) > 0

    def test_install_and_remove_gc_callbacks(self):
        """测试安装和移除GC回调"""
        # 安装回调
        self.optimizer.install_gc_callbacks()
        assert self.optimizer.monitoring_active is True

        # 移除回调
        self.optimizer.remove_gc_callbacks()
        assert self.optimizer.monitoring_active is False

    def test_apply_profile(self):
        """测试应用GC配置"""
        original_thresholds = gc.get_threshold()

        try:
            # 获取一个可用的配置文件
            test_profile = self.optimizer.gc_profiles[1]  # 使用conservative配置

            # 应用配置
            result = self.optimizer.apply_profile(test_profile)
            assert result is True

            new_thresholds = gc.get_threshold()
            assert new_thresholds != original_thresholds
            assert new_thresholds == test_profile.thresholds

        finally:
            # 恢复默认设置
            self.optimizer.reset_to_default()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
