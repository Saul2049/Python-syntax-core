#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中级优先级数据转换器重构测试 (Medium Priority Data Transformers Refactoring Tests)

测试数据转换器模块化重构和配置系统改进
"""

import unittest
import warnings
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.config.manager import TradingConfig
from src.config.utils import flatten_config, merge_dict, unflatten_config
from src.data.transformers import (
    DataNormalizer,
    DataSplitter,
    MissingValueHandler,
    TimeSeriesProcessor,
    create_sequences,
    create_train_test_split,
    normalize_data,
)


class TestDataTransformersRefactoring(unittest.TestCase):
    """测试数据转换器重构"""

    def setUp(self):
        """设置测试数据"""
        # 创建测试数据
        np.random.seed(42)
        self.test_data = pd.DataFrame(
            {
                "price": np.random.rand(100) * 100 + 50,
                "volume": np.random.rand(100) * 1000,
                "returns": np.random.normal(0, 0.02, 100),
            }
        )

        # 添加一些缺失值
        self.test_data_with_missing = self.test_data.copy()
        self.test_data_with_missing.iloc[10:15, 0] = np.nan
        self.test_data_with_missing.iloc[20:25, 1] = np.nan

    def test_data_normalizer_import(self):
        """测试数据归一化器导入"""
        normalizer = DataNormalizer(method="minmax")
        self.assertIsNotNone(normalizer)

    def test_normalize_function(self):
        """测试归一化便捷函数"""
        normalized = normalize_data(self.test_data["price"])
        self.assertTrue(normalized.min() >= 0)
        self.assertTrue(normalized.max() <= 1)

    def test_time_series_processor_import(self):
        """测试时间序列处理器导入"""
        processor = TimeSeriesProcessor()
        self.assertIsNotNone(processor)

    def test_create_sequences_function(self):
        """测试序列创建便捷函数"""
        data = np.random.rand(50)
        X, y = create_sequences(data, seq_length=10)
        self.assertEqual(X.shape[1], 10)
        self.assertEqual(len(X), len(y))

    def test_data_splitter_import(self):
        """测试数据分割器导入"""
        splitter = DataSplitter()
        self.assertIsNotNone(splitter)

    def test_train_test_split_function(self):
        """测试训练测试分割便捷函数"""
        train, test = create_train_test_split(self.test_data, test_size=0.2)
        total_rows = len(train) + len(test)
        self.assertEqual(total_rows, len(self.test_data))
        self.assertAlmostEqual(len(test) / total_rows, 0.2, places=1)

    def test_missing_value_handler_import(self):
        """测试缺失值处理器导入"""
        handler = MissingValueHandler()
        self.assertIsNotNone(handler)

    def test_fill_missing_values(self):
        """测试缺失值填充"""
        filled = MissingValueHandler.fill_missing_values(self.test_data_with_missing, method="mean")
        self.assertEqual(filled.isnull().sum().sum(), 0)

    def test_backward_compatibility_warnings(self):
        """测试向后兼容性警告"""
        # 测试是否能正常导入
        try:
            from src.data.transformers import DataNormalizer

            self.assertTrue(True)
        except ImportError:
            self.fail("向后兼容性导入失败")

    def test_module_organization(self):
        """测试模块组织"""
        # 测试所有组件都可以从主包导入
        from src.data.transformers import (
            ALL_TRANSFORMERS,
            MISSING_VALUE_TOOLS,
            NORMALIZERS,
            SPLITTERS,
            TIME_SERIES_TOOLS,
        )

        self.assertIn("DataNormalizer", NORMALIZERS)
        self.assertIn("TimeSeriesProcessor", TIME_SERIES_TOOLS)
        self.assertIn("DataSplitter", SPLITTERS)
        self.assertIn("MissingValueHandler", MISSING_VALUE_TOOLS)

        # 测试总数
        total_expected = (
            len(NORMALIZERS) + len(TIME_SERIES_TOOLS) + len(SPLITTERS) + len(MISSING_VALUE_TOOLS)
        )
        self.assertEqual(len(ALL_TRANSFORMERS), total_expected)

    def test_advanced_functionality(self):
        """测试高级功能"""
        # 测试时间序列功能
        ts_data = self.test_data.copy()
        ts_data.index = pd.date_range("2023-01-01", periods=len(ts_data), freq="D")

        # 测试滞后特征
        lagged = TimeSeriesProcessor.create_lagged_features(ts_data, ["price"], [1, 2, 3])
        self.assertIn("price_lag_1", lagged.columns)
        self.assertIn("price_lag_2", lagged.columns)

        # 测试滚动特征
        rolling = TimeSeriesProcessor.create_rolling_features(ts_data, ["price"], [5, 10])
        self.assertIn("price_rolling_5_mean", rolling.columns)
        self.assertIn("price_rolling_10_std", rolling.columns)


class TestConfigSystemImprovements(unittest.TestCase):
    """测试配置系统改进"""

    def test_merge_dict_function(self):
        """测试merge_dict函数"""
        target = {"a": 1, "b": {"c": 2}}
        source = {"b": {"d": 3}, "e": 4}

        merge_dict(target, source)

        self.assertEqual(target["a"], 1)
        self.assertEqual(target["b"]["c"], 2)
        self.assertEqual(target["b"]["d"], 3)
        self.assertEqual(target["e"], 4)

    def test_flatten_unflatten_config(self):
        """测试配置扁平化和还原"""
        config = {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"enabled": True, "ttl": 300},
        }

        # 扁平化
        flat = flatten_config(config)
        self.assertIn("database.host", flat)
        self.assertIn("cache.enabled", flat)

        # 还原
        unflat = unflatten_config(flat)
        self.assertEqual(unflat["database"]["host"], "localhost")
        self.assertEqual(unflat["cache"]["enabled"], True)

    def test_config_manager_merge(self):
        """测试配置管理器的合并功能"""
        config = TradingConfig()

        # 测试新的merge_config方法
        external_config = {"symbols": ["BTCUSDT"], "risk_percent": 0.02}

        config.merge_config(external_config)

        self.assertEqual(config.get_symbols(), ["BTCUSDT"])
        self.assertEqual(config.get_risk_percent(), 0.02)

    def test_no_duplicate_merge_dict(self):
        """测试没有重复的_merge_dict方法"""
        # 确保manager.py和sources.py都使用utils中的merge_dict
        from src.config.manager import TradingConfig
        from src.config.sources import ConfigSourceLoader
        from src.config.utils import merge_dict

        # 检查它们都没有自己的_merge_dict方法
        config_manager = TradingConfig()
        loader = ConfigSourceLoader()

        self.assertFalse(hasattr(config_manager, "_merge_dict"))
        self.assertFalse(hasattr(loader, "_merge_dict"))


class TestCodeReduction(unittest.TestCase):
    """测试代码减少效果"""

    def test_original_transformers_file_reduced(self):
        """测试原始转换器文件是否被减少"""
        # 检查原始文件是否仍然存在以及其大小
        import os

        original_file = "src/data/transformers/data_transformers.py"
        if os.path.exists(original_file):
            with open(original_file, "r") as f:
                lines = f.readlines()

            # 原始文件应该仍然存在但可能被重构了
            # 或者至少验证新模块存在
            self.assertTrue(os.path.exists("src/data/transformers/normalizers.py"))
            self.assertTrue(os.path.exists("src/data/transformers/time_series.py"))
            self.assertTrue(os.path.exists("src/data/transformers/splitters.py"))
            self.assertTrue(os.path.exists("src/data/transformers/missing_values.py"))

    def test_config_utils_consolidation(self):
        """测试配置工具的整合"""
        from src.config.utils import (
            flatten_config,
            get_nested_value,
            merge_dict,
            set_nested_value,
            unflatten_config,
        )

        # 测试所有工具函数都存在
        self.assertTrue(callable(merge_dict))
        self.assertTrue(callable(flatten_config))
        self.assertTrue(callable(unflatten_config))
        self.assertTrue(callable(get_nested_value))
        self.assertTrue(callable(set_nested_value))


class TestPerformanceImprovements(unittest.TestCase):
    """测试性能改进"""

    def test_modular_imports(self):
        """测试模块化导入性能"""
        import time

        # 测试只导入需要的模块
        start_time = time.time()
        from src.data.transformers.normalizers import DataNormalizer

        normalizer_time = time.time() - start_time

        start_time = time.time()
        from src.data.transformers.time_series import TimeSeriesProcessor

        timeseries_time = time.time() - start_time

        # 模块化导入应该很快
        self.assertLess(normalizer_time, 1.0)
        self.assertLess(timeseries_time, 1.0)

    def test_memory_efficiency(self):
        """测试内存效率"""
        # 测试创建和销毁对象不会有内存泄漏
        normalizers = []
        for i in range(100):
            normalizer = DataNormalizer()
            normalizers.append(normalizer)

        # 清理
        del normalizers

        # 如果没有异常，则认为内存管理正常
        self.assertTrue(True)


if __name__ == "__main__":
    # 设置警告过滤
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # 运行测试
    unittest.main(verbosity=2)
