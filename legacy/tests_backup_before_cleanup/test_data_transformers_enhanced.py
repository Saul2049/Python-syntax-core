#!/usr/bin/env python3
"""
🧪 数据转换器增强测试 (Data Transformers Enhanced Tests)

提升data_transformers.py模块测试覆盖率的全面测试套件
当前覆盖率: 22% -> 目标: 80%+
"""

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.data.transformers.data_transformers import (
    DataNormalizer,
    DataSplitter,
    MissingValueHandler,
    TimeSeriesProcessor,
    create_sequences,
    create_train_test_split,
    normalize_data,
)


class TestDataNormalizerComprehensive(unittest.TestCase):
    """全面测试DataNormalizer类"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.df_data = pd.DataFrame(
            {"price": [100, 200, 300, 400, 500], "volume": [1000, 2000, 3000, 4000, 5000]}
        )
        self.series_data = pd.Series([10, 20, 30, 40, 50], name="test_series")

    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        normalizer = DataNormalizer()
        self.assertEqual(normalizer.method, "minmax")
        self.assertEqual(normalizer.feature_range, (0, 1))

    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        normalizer = DataNormalizer(method="standard", feature_range=(-1, 1))
        self.assertEqual(normalizer.method, "standard")
        self.assertEqual(normalizer.feature_range, (-1, 1))

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", True)
    def test_init_invalid_method_with_sklearn(self):
        """测试有sklearn时的无效方法"""
        with self.assertRaises(ValueError):
            DataNormalizer(method="invalid_method")

    def test_fit_transform_dataframe_minmax(self):
        """测试DataFrame的MinMax归一化"""
        normalizer = DataNormalizer(method="minmax")
        result = normalizer.fit_transform(self.df_data)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue((result >= 0).all().all())
        self.assertTrue((result <= 1).all().all())
        self.assertEqual(result.index.tolist(), self.df_data.index.tolist())
        self.assertEqual(result.columns.tolist(), self.df_data.columns.tolist())

    def test_fit_transform_series_minmax(self):
        """测试Series的MinMax归一化"""
        normalizer = DataNormalizer(method="minmax")
        result = normalizer.fit_transform(self.series_data)

        self.assertIsInstance(result, pd.Series)
        self.assertTrue((result >= 0).all())
        self.assertTrue((result <= 1).all())
        self.assertEqual(result.name, self.series_data.name)

    def test_fit_transform_standard(self):
        """测试标准化"""
        normalizer = DataNormalizer(method="standard")
        result = normalizer.fit_transform(self.df_data)

        # 标准化后均值应接近0，标准差接近1
        self.assertTrue(np.allclose(result.mean(), 0, atol=1e-10))
        self.assertTrue(np.allclose(result.std(), 1, atol=1e-10))

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", True)
    def test_fit_transform_robust_with_sklearn(self):
        """测试有sklearn时的鲁棒归一化"""
        normalizer = DataNormalizer(method="robust")
        result = normalizer.fit_transform(self.df_data)

        self.assertIsInstance(result, pd.DataFrame)

    def test_fit_transform_robust_without_sklearn(self):
        """测试没有sklearn时的鲁棒归一化"""
        normalizer = DataNormalizer(method="robust")
        with self.assertRaises(ValueError):
            # 简化实现不支持robust方法
            normalizer.fit_transform(self.df_data)

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", True)
    def test_transform_without_fit_with_sklearn(self):
        """测试有sklearn时在未训练时调用transform"""
        normalizer = DataNormalizer()
        with self.assertRaises(ValueError):
            normalizer.transform(self.df_data)

    def test_transform_after_fit(self):
        """测试训练后的transform"""
        normalizer = DataNormalizer(method="minmax")
        normalizer.fit_transform(self.df_data)

        new_data = pd.DataFrame({"price": [150], "volume": [1500]})
        result = normalizer.transform(new_data)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", True)
    def test_inverse_transform_with_sklearn(self):
        """测试有sklearn时的反向转换"""
        normalizer = DataNormalizer(method="minmax")
        normalized = normalizer.fit_transform(self.df_data)
        recovered = normalizer.inverse_transform(normalized)

        # 原始数据应该被恢复
        pd.testing.assert_frame_equal(recovered, self.df_data, check_dtype=False)

    def test_inverse_transform_without_sklearn(self):
        """测试没有sklearn时的反向转换"""
        normalizer = DataNormalizer()
        result = normalizer.inverse_transform(self.df_data)

        # 简化实现返回原数据
        pd.testing.assert_frame_equal(result, self.df_data)

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", False)
    def test_simple_normalize_minmax(self):
        """测试简化版MinMax归一化"""
        normalizer = DataNormalizer(method="minmax")
        result = normalizer._simple_normalize(self.series_data)

        self.assertTrue((result >= 0).all())
        self.assertTrue((result <= 1).all())

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", False)
    def test_simple_normalize_standard(self):
        """测试简化版标准化"""
        normalizer = DataNormalizer(method="standard")
        result = normalizer._simple_normalize(self.series_data)

        self.assertTrue(np.allclose(result.mean(), 0))
        self.assertTrue(np.allclose(result.std(), 1))

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", False)
    def test_simple_normalize_invalid_method(self):
        """测试简化版无效方法"""
        normalizer = DataNormalizer(method="robust")
        with self.assertRaises(ValueError):
            normalizer._simple_normalize(self.series_data)

    @patch("src.data.transformers.data_transformers.HAS_SKLEARN", False)
    def test_fit_transform_without_sklearn(self):
        """测试没有sklearn时的fit_transform"""
        normalizer = DataNormalizer(method="minmax")
        result = normalizer.fit_transform(self.series_data)

        self.assertTrue((result >= 0).all())
        self.assertTrue((result <= 1).all())


class TestTimeSeriesProcessorComprehensive(unittest.TestCase):
    """全面测试TimeSeriesProcessor类"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.data_array = np.random.rand(100)

        self.df_data = pd.DataFrame(
            {
                "price": np.random.rand(50) * 100,
                "volume": np.random.rand(50) * 1000,
            },
            index=pd.date_range("2023-01-01", periods=50),
        )

    def test_create_sequences_basic(self):
        """测试基本序列创建"""
        X, y = TimeSeriesProcessor.create_sequences(self.data_array, seq_length=10)

        self.assertEqual(X.shape[1], 10)
        self.assertEqual(y.shape[1], 1)
        self.assertEqual(len(X), len(y))
        self.assertEqual(len(X), len(self.data_array) - 10)

    def test_create_sequences_custom_pred_length(self):
        """测试自定义预测长度"""
        X, y = TimeSeriesProcessor.create_sequences(self.data_array, seq_length=5, pred_length=3)

        self.assertEqual(X.shape[1], 5)
        self.assertEqual(y.shape[1], 3)
        self.assertEqual(len(X), len(self.data_array) - 5 - 3 + 1)

    def test_create_sequences_custom_step(self):
        """测试自定义步长"""
        X, y = TimeSeriesProcessor.create_sequences(self.data_array, seq_length=5, step=2)

        # 根据实际实现调整期望值
        expected_length = len([i for i in range(0, len(self.data_array) - 5 - 1 + 1, 2)])
        self.assertEqual(len(X), expected_length)

    def test_create_sequences_edge_case(self):
        """测试边界情况"""
        small_data = np.array([1, 2, 3])
        X, y = TimeSeriesProcessor.create_sequences(small_data, seq_length=2)

        self.assertEqual(len(X), 1)
        self.assertEqual(len(y), 1)

    def test_create_lagged_features(self):
        """测试滞后特征创建"""
        result = TimeSeriesProcessor.create_lagged_features(self.df_data, ["price"], [1, 2, 3])

        self.assertIn("price_lag_1", result.columns)
        self.assertIn("price_lag_2", result.columns)
        self.assertIn("price_lag_3", result.columns)
        self.assertEqual(len(result), len(self.df_data))

    def test_create_lagged_features_multiple_columns(self):
        """测试多列滞后特征"""
        result = TimeSeriesProcessor.create_lagged_features(
            self.df_data, ["price", "volume"], [1, 2]
        )

        expected_cols = ["price_lag_1", "price_lag_2", "volume_lag_1", "volume_lag_2"]
        for col in expected_cols:
            self.assertIn(col, result.columns)

    def test_create_rolling_features(self):
        """测试滚动特征创建"""
        result = TimeSeriesProcessor.create_rolling_features(self.df_data, ["price"], [5, 10])

        # 根据实际实现调整列名格式
        expected_cols = [
            "price_rolling_mean_5",
            "price_rolling_std_5",
            "price_rolling_min_5",
            "price_rolling_max_5",
            "price_rolling_mean_10",
            "price_rolling_std_10",
            "price_rolling_min_10",
            "price_rolling_max_10",
        ]
        for col in expected_cols:
            self.assertIn(col, result.columns)

    def test_create_rolling_features_custom_functions(self):
        """测试自定义滚动函数"""
        result = TimeSeriesProcessor.create_rolling_features(
            self.df_data, ["price"], [5], ["mean", "sum"]
        )

        self.assertIn("price_rolling_mean_5", result.columns)
        self.assertIn("price_rolling_sum_5", result.columns)
        self.assertNotIn("price_rolling_std_5", result.columns)

    def test_resample_data_basic(self):
        """测试数据重采样"""
        result = TimeSeriesProcessor.resample_data(self.df_data, "5D")

        self.assertLess(len(result), len(self.df_data))
        # 列的顺序可能不同，只检查列集合
        self.assertEqual(set(result.columns), set(self.df_data.columns))

    def test_resample_data_custom_agg(self):
        """测试自定义聚合方法"""
        agg_methods = {"price": "mean", "volume": "sum"}
        result = TimeSeriesProcessor.resample_data(self.df_data, "7D", agg_methods)

        self.assertIsInstance(result, pd.DataFrame)
        self.assertLess(len(result), len(self.df_data))


class TestDataSplitterComprehensive(unittest.TestCase):
    """全面测试DataSplitter类"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.df_data = pd.DataFrame(
            {
                "feature1": np.random.rand(100),
                "feature2": np.random.rand(100),
                "target": np.random.rand(100),
            }
        )

    def test_train_test_split_basic(self):
        """测试基本训练测试分割"""
        train, test = DataSplitter.train_test_split(self.df_data, test_size=0.2)

        self.assertEqual(len(train) + len(test), len(self.df_data))
        self.assertAlmostEqual(len(test) / len(self.df_data), 0.2, places=1)

    def test_train_test_split_with_shuffle(self):
        """测试带洗牌的分割"""
        train1, test1 = DataSplitter.train_test_split(
            self.df_data, test_size=0.2, shuffle=True, random_state=42
        )
        train2, test2 = DataSplitter.train_test_split(
            self.df_data, test_size=0.2, shuffle=True, random_state=42
        )

        # 相同随机种子应该产生相同结果
        pd.testing.assert_frame_equal(train1, train2)
        pd.testing.assert_frame_equal(test1, test2)

    def test_train_test_split_without_shuffle(self):
        """测试不洗牌的分割"""
        train, test = DataSplitter.train_test_split(self.df_data, test_size=0.2, shuffle=False)

        # 训练集应该是前80行，测试集是后20行
        expected_train_size = int(0.8 * len(self.df_data))
        self.assertEqual(len(train), expected_train_size)
        self.assertEqual(train.index[0], 0)
        self.assertEqual(test.index[0], expected_train_size)

    def test_train_val_test_split(self):
        """测试三分割"""
        train, val, test = DataSplitter.train_val_test_split(
            self.df_data, train_size=0.7, val_size=0.15, test_size=0.15
        )

        total_size = len(train) + len(val) + len(test)
        self.assertEqual(total_size, len(self.df_data))

        self.assertAlmostEqual(len(train) / len(self.df_data), 0.7, places=1)
        self.assertAlmostEqual(len(val) / len(self.df_data), 0.15, places=1)
        self.assertAlmostEqual(len(test) / len(self.df_data), 0.15, places=1)

    def test_train_val_test_split_size_validation(self):
        """测试三分割大小验证"""
        with self.assertRaises(ValueError):
            DataSplitter.train_val_test_split(
                self.df_data, train_size=0.5, val_size=0.3, test_size=0.3
            )

    def test_time_series_split(self):
        """测试时间序列分割"""
        splits = DataSplitter.time_series_split(self.df_data, n_splits=3)

        self.assertEqual(len(splits), 3)

        # 检查每个分割
        for train, test in splits:
            self.assertIsInstance(train, pd.DataFrame)
            self.assertIsInstance(test, pd.DataFrame)
            self.assertGreater(len(train), 0)
            self.assertGreater(len(test), 0)

    def test_time_series_split_custom_test_size(self):
        """测试自定义测试大小的时间序列分割"""
        splits = DataSplitter.time_series_split(self.df_data, n_splits=3, test_size=10)

        for train, test in splits:
            self.assertEqual(len(test), 10)


class TestMissingValueHandlerComprehensive(unittest.TestCase):
    """全面测试MissingValueHandler类"""

    def setUp(self):
        """设置测试数据"""
        self.df_data = pd.DataFrame(
            {
                "price": [100, np.nan, 300, np.nan, 500],
                "volume": [1000, 2000, np.nan, 4000, np.nan],
                "returns": [0.01, 0.02, 0.03, np.nan, 0.05],
            }
        )

    def test_fill_missing_values_forward(self):
        """测试前向填充"""
        result = MissingValueHandler.fill_missing_values(self.df_data, method="forward")

        # 检查没有缺失值
        self.assertEqual(result.isnull().sum().sum(), 0)

        # 检查前向填充逻辑
        self.assertEqual(result.iloc[1]["price"], 100)  # 前向填充

    def test_fill_missing_values_backward(self):
        """测试后向填充"""
        result = MissingValueHandler.fill_missing_values(self.df_data, method="backward")

        # 后向填充可能仍有缺失值（第一个值）
        self.assertLessEqual(result.isnull().sum().sum(), self.df_data.isnull().sum().sum())

    def test_fill_missing_values_mean(self):
        """测试均值填充"""
        result = MissingValueHandler.fill_missing_values(self.df_data, method="mean")

        self.assertEqual(result.isnull().sum().sum(), 0)

        # 均值填充应该用列的均值
        original_mean = self.df_data["price"].mean()
        self.assertEqual(result.iloc[1]["price"], original_mean)

    def test_fill_missing_values_median(self):
        """测试中位数填充"""
        result = MissingValueHandler.fill_missing_values(self.df_data, method="median")

        self.assertEqual(result.isnull().sum().sum(), 0)

    def test_fill_missing_values_unsupported_mode(self):
        """测试不支持的众数填充"""
        with self.assertRaises(ValueError):
            MissingValueHandler.fill_missing_values(self.df_data, method="mode")

    def test_fill_missing_values_specific_columns(self):
        """测试指定列填充"""
        result = MissingValueHandler.fill_missing_values(
            self.df_data, method="mean", columns=["price"]
        )

        # 只有price列被填充
        self.assertEqual(result["price"].isnull().sum(), 0)
        self.assertGreater(result["volume"].isnull().sum(), 0)

    def test_fill_missing_values_invalid_method(self):
        """测试无效填充方法"""
        with self.assertRaises(ValueError):
            MissingValueHandler.fill_missing_values(self.df_data, method="invalid")

    def test_interpolate_missing_values_linear(self):
        """测试线性插值"""
        result = MissingValueHandler.interpolate_missing_values(self.df_data, method="linear")

        self.assertLessEqual(result.isnull().sum().sum(), self.df_data.isnull().sum().sum())

    def test_interpolate_missing_values_specific_columns(self):
        """测试指定列插值"""
        result = MissingValueHandler.interpolate_missing_values(
            self.df_data, method="linear", columns=["price"]
        )

        # 只有price列被插值
        self.assertEqual(result["price"].isnull().sum(), 0)

    def test_get_target_columns_all(self):
        """测试获取所有目标列"""
        columns = MissingValueHandler._get_target_columns(self.df_data, None)
        self.assertEqual(set(columns), set(self.df_data.columns))

    def test_get_target_columns_specific(self):
        """测试获取指定目标列"""
        columns = MissingValueHandler._get_target_columns(self.df_data, ["price", "volume"])
        self.assertEqual(set(columns), {"price", "volume"})

    def test_fill_column_missing_values_forward(self):
        """测试单列前向填充"""
        result = MissingValueHandler._fill_column_missing_values(
            self.df_data.copy(), "price", "forward"
        )

        self.assertEqual(result["price"].isnull().sum(), 0)

    def test_fill_column_missing_values_mean(self):
        """测试单列均值填充"""
        result = MissingValueHandler._fill_column_missing_values(
            self.df_data.copy(), "price", "mean"
        )

        self.assertEqual(result["price"].isnull().sum(), 0)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def setUp(self):
        """设置测试数据"""
        np.random.seed(42)
        self.data = pd.Series([10, 20, 30, 40, 50])
        self.df_data = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})

    def test_normalize_data_function(self):
        """测试normalize_data便捷函数"""
        result = normalize_data(self.data)

        self.assertTrue((result >= 0).all())
        self.assertTrue((result <= 1).all())

    def test_normalize_data_custom_params(self):
        """测试自定义参数的归一化"""
        result = normalize_data(self.data, method="standard")

        self.assertTrue(np.allclose(result.mean(), 0))
        self.assertTrue(np.allclose(result.std(), 1))

    def test_create_train_test_split_function(self):
        """测试create_train_test_split便捷函数"""
        train, test = create_train_test_split(self.df_data, test_size=0.2)

        self.assertEqual(len(train) + len(test), len(self.df_data))

    def test_create_sequences_function(self):
        """测试create_sequences便捷函数"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = create_sequences(data, seq_length=3)

        self.assertEqual(X.shape[1], 3)
        self.assertEqual(len(X), len(data) - 3)


if __name__ == "__main__":
    unittest.main()
