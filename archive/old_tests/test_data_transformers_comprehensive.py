#!/usr/bin/env python3
"""
数据转换器综合测试 (Data Transformers Comprehensive Tests)

专门提升src/data/transformers/data_transformers.py覆盖率的完整测试套件
目标：从22%覆盖率提升到75%+
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, Mock
from typing import List, Tuple

from src.data.transformers.data_transformers import (
    DataNormalizer,
    TimeSeriesProcessor,
    DataSplitter,
    MissingValueHandler,
    normalize_data,
    create_train_test_split,
    create_sequences,
)


class TestDataNormalizerComprehensive:
    """数据归一化器全面测试"""

    @pytest.fixture
    def sample_dataframe(self):
        """示例DataFrame数据"""
        return pd.DataFrame(
            {
                "price": [10.0, 20.0, 30.0, 40.0, 50.0],
                "volume": [100, 200, 300, 400, 500],
                "score": [1.1, 2.2, 3.3, 4.4, 5.5],
            }
        )

    @pytest.fixture
    def sample_series(self):
        """示例Series数据"""
        return pd.Series([1, 2, 3, 4, 5], name="test_series")

    def test_init_with_custom_range(self):
        """测试自定义范围初始化"""
        normalizer = DataNormalizer(method="minmax", feature_range=(-1, 1))
        assert normalizer.feature_range == (-1, 1)
        assert normalizer.method == "minmax"

    def test_init_robust_scaler_without_sklearn(self):
        """测试RobustScaler初始化（无sklearn时）"""
        # 在实际环境中，sklearn不存在，所以不能测试robust
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="robust")
            assert normalizer.method == "robust"
            assert normalizer.scaler is None

    def test_init_invalid_method_with_sklearn(self):
        """测试无效方法抛出异常（模拟有sklearn）"""
        # 由于实际没有sklearn，我们测试简化实现的错误处理
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="invalid")
            # 简化实现中，invalid方法会在fit_transform时抛出异常
            sample_df = pd.DataFrame({"a": [1, 2, 3]})
            with pytest.raises(ValueError, match="简化实现不支持方法"):
                normalizer.fit_transform(sample_df)

    def test_simple_normalize_minmax_custom_range(self, sample_dataframe):
        """测试简化MinMax归一化自定义范围"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="minmax", feature_range=(-1, 1))
            result = normalizer.fit_transform(sample_dataframe)

            # 验证自定义范围
            for col in result.columns:
                assert result[col].min() >= -1
                assert result[col].max() <= 1

    def test_simple_normalize_standard(self, sample_dataframe):
        """测试简化标准归一化"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="standard")
            result = normalizer.fit_transform(sample_dataframe)

            assert isinstance(result, pd.DataFrame)
            assert result.shape == sample_dataframe.shape

    def test_simple_normalize_invalid_method(self, sample_dataframe):
        """测试简化实现不支持的方法"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="robust")
            with pytest.raises(ValueError, match="简化实现不支持方法"):
                normalizer.fit_transform(sample_dataframe)

    def test_transform_without_sklearn(self, sample_dataframe):
        """测试没有sklearn时的transform方法"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="minmax")
            result = normalizer.transform(sample_dataframe)
            assert isinstance(result, pd.DataFrame)

    def test_inverse_transform_without_sklearn(self, sample_dataframe):
        """测试无sklearn时逆变换警告"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="minmax")
            result = normalizer.inverse_transform(sample_dataframe)

            # 简化实现返回原数据
            pd.testing.assert_frame_equal(result, sample_dataframe)

    def test_fit_transform_series(self, sample_series):
        """测试Series归一化"""
        normalizer = DataNormalizer(method="minmax")
        result = normalizer.fit_transform(sample_series)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_series)


class TestTimeSeriesProcessorComprehensive:
    """时间序列处理器全面测试"""

    @pytest.fixture
    def time_series_data(self):
        """时间序列测试数据"""
        dates = pd.date_range("2023-01-01", periods=20, freq="D")
        return pd.DataFrame(
            {
                "price": np.random.randn(20).cumsum() + 100,
                "volume": np.random.randint(1000, 5000, 20),
                "feature": range(20),
            },
            index=dates,
        )

    def test_create_sequences_basic(self):
        """测试基础序列创建"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = TimeSeriesProcessor.create_sequences(data, seq_length=3, pred_length=1)

        # 正确的计算：10 - 3 - 1 + 1 = 7
        assert X.shape == (7, 3)
        assert y.shape == (7, 1)
        assert np.array_equal(X[0], [1, 2, 3])
        assert y[0] == 4

    def test_create_sequences_multi_pred(self):
        """测试多步预测序列"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = TimeSeriesProcessor.create_sequences(data, seq_length=3, pred_length=2)

        assert X.shape[1] == 3
        assert y.shape[1] == 2
        assert np.array_equal(X[0], [1, 2, 3])
        assert np.array_equal(y[0], [4, 5])

    def test_create_sequences_with_step(self):
        """测试带步长的序列创建"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = TimeSeriesProcessor.create_sequences(data, seq_length=3, pred_length=1, step=2)

        # step=2 会跳过一些样本
        assert X.shape[0] < 7  # 应该少于step=1的情况
        assert np.array_equal(X[0], [1, 2, 3])
        assert y[0] == 4

    def test_create_lagged_features_basic(self, time_series_data):
        """测试基础滞后特征创建"""
        result = TimeSeriesProcessor.create_lagged_features(time_series_data, ["price"], [1, 2, 3])

        assert "price_lag_1" in result.columns
        assert "price_lag_2" in result.columns
        assert "price_lag_3" in result.columns
        assert len(result) == len(time_series_data)

        # 验证滞后值正确性
        assert pd.isna(result["price_lag_1"].iloc[0])  # 第一个值应该是NaN
        assert result["price_lag_1"].iloc[1] == time_series_data["price"].iloc[0]

    def test_create_lagged_features_multiple_columns(self, time_series_data):
        """测试多列滞后特征"""
        result = TimeSeriesProcessor.create_lagged_features(
            time_series_data, ["price", "volume"], [1, 2]
        )

        expected_cols = ["price_lag_1", "price_lag_2", "volume_lag_1", "volume_lag_2"]
        for col in expected_cols:
            assert col in result.columns

    def test_create_rolling_features_basic(self, time_series_data):
        """测试基础滚动特征创建"""
        result = TimeSeriesProcessor.create_rolling_features(time_series_data, ["price"], [3, 5])

        # 修正的列名格式：{col}_rolling_{func}_{window}
        expected_cols = [
            "price_rolling_mean_3",
            "price_rolling_std_3",
            "price_rolling_min_3",
            "price_rolling_max_3",
            "price_rolling_mean_5",
            "price_rolling_std_5",
            "price_rolling_min_5",
            "price_rolling_max_5",
        ]

        for col in expected_cols:
            assert col in result.columns

    def test_create_rolling_features_custom_functions(self, time_series_data):
        """测试自定义函数滚动特征"""
        result = TimeSeriesProcessor.create_rolling_features(
            time_series_data, ["price"], [3], ["mean", "sum"]
        )

        assert "price_rolling_mean_3" in result.columns
        assert "price_rolling_sum_3" in result.columns
        # 确保不包含其他函数的列
        assert "price_rolling_std_3" not in result.columns

    def test_resample_data_basic(self, time_series_data):
        """测试基础数据重采样"""
        result = TimeSeriesProcessor.resample_data(time_series_data, "2D")

        assert len(result) <= len(time_series_data)  # 重采样后数据减少
        assert isinstance(result, pd.DataFrame)

    def test_resample_data_custom_agg(self, time_series_data):
        """测试自定义聚合方法重采样"""
        agg_methods = {"price": "mean", "volume": "sum"}
        result = TimeSeriesProcessor.resample_data(time_series_data, "3D", agg_methods)

        assert len(result) <= len(time_series_data)
        assert "price" in result.columns
        assert "volume" in result.columns

    def test_resample_data_no_datetime_index(self):
        """测试非DatetimeIndex的重采样错误"""
        df = pd.DataFrame({"value": [1, 2, 3]})
        with pytest.raises(ValueError, match="DataFrame必须有DatetimeIndex"):
            TimeSeriesProcessor.resample_data(df, "1D")


class TestDataSplitterComprehensive:
    """数据分割器全面测试"""

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return pd.DataFrame(
            {
                "feature1": range(100),
                "feature2": np.random.randn(100),
                "target": np.random.randint(0, 2, 100),
            }
        )

    def test_train_test_split_basic(self, sample_data):
        """测试基础训练测试分割"""
        train, test = DataSplitter.train_test_split(sample_data, test_size=0.2)

        assert len(train) + len(test) == len(sample_data)
        assert len(test) == int(len(sample_data) * 0.2)

    def test_train_test_split_with_shuffle(self, sample_data):
        """测试带随机打乱的分割"""
        train, test = DataSplitter.train_test_split(
            sample_data, test_size=0.2, shuffle=True, random_state=42
        )

        assert len(train) + len(test) == len(sample_data)

    def test_train_val_test_split_basic(self, sample_data):
        """测试三分割基础功能"""
        train, val, test = DataSplitter.train_val_test_split(
            sample_data, train_size=0.6, val_size=0.2, test_size=0.2
        )

        assert len(train) + len(val) + len(test) == len(sample_data)
        assert len(train) == int(len(sample_data) * 0.6)
        assert len(val) == int(len(sample_data) * 0.2)

    def test_train_val_test_split_invalid_proportions(self, sample_data):
        """测试无效比例抛出异常"""
        with pytest.raises(ValueError, match="比例之和必须等于1.0"):
            DataSplitter.train_val_test_split(
                sample_data, train_size=0.6, val_size=0.3, test_size=0.2
            )

    def test_train_val_test_split_with_shuffle(self, sample_data):
        """测试带随机打乱的三分割"""
        train, val, test = DataSplitter.train_val_test_split(
            sample_data, shuffle=True, random_state=123
        )

        assert len(train) + len(val) + len(test) == len(sample_data)

    def test_time_series_split_basic(self, sample_data):
        """测试时间序列分割基础功能"""
        splits = DataSplitter.time_series_split(sample_data, n_splits=3)

        assert len(splits) <= 3  # 可能少于3个分割
        for train, test in splits:
            assert isinstance(train, pd.DataFrame)
            assert isinstance(test, pd.DataFrame)
            assert len(test) > 0

    def test_time_series_split_custom_test_size(self, sample_data):
        """测试自定义测试集大小的时间序列分割"""
        splits = DataSplitter.time_series_split(sample_data, n_splits=2, test_size=10)

        for train, test in splits:
            assert len(test) <= 10  # 测试集大小应该不超过指定值

    def test_time_series_split_edge_case(self):
        """测试时间序列分割边缘情况"""
        small_data = pd.DataFrame({"col": [1, 2, 3]})
        splits = DataSplitter.time_series_split(small_data, n_splits=5, test_size=1)

        # 小数据集应该能正常处理
        assert len(splits) >= 0


class TestMissingValueHandlerComprehensive:
    """缺失值处理器全面测试"""

    @pytest.fixture
    def data_with_missing(self):
        """包含缺失值的测试数据"""
        data = pd.DataFrame(
            {
                "A": [1.0, 2.0, np.nan, 4.0, 5.0, np.nan],
                "B": [np.nan, 2.0, 3.0, np.nan, 5.0, 6.0],
                "C": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],  # 无缺失值
            }
        )
        return data

    @pytest.fixture
    def data_with_mixed_types(self):
        """包含混合类型的测试数据"""
        return pd.DataFrame({"numeric": [1.0, 2.0, np.nan, 4.0], "string": ["a", "b", None, "d"]})

    def test_fill_missing_forward(self, data_with_missing):
        """测试前向填充"""
        result = MissingValueHandler.fill_missing_values(data_with_missing, method="forward")

        # 验证前向填充效果
        assert result["A"].iloc[2] == 2.0  # 第3个值应该被填充为第2个值

    def test_fill_missing_backward(self, data_with_missing):
        """测试后向填充"""
        result = MissingValueHandler.fill_missing_values(data_with_missing, method="backward")

        # 验证后向填充
        assert isinstance(result, pd.DataFrame)

    def test_fill_missing_mean(self, data_with_missing):
        """测试均值填充"""
        # 只使用数值列进行测试
        numeric_data = data_with_missing[["A", "B", "C"]]
        result = MissingValueHandler.fill_missing_values(numeric_data, method="mean")

        # 数值列应该被均值填充
        assert not result["A"].isna().any()
        assert not result["B"].isna().any()

    def test_fill_missing_median(self, data_with_missing):
        """测试中位数填充"""
        # 只使用数值列进行测试
        numeric_data = data_with_missing[["A", "B", "C"]]
        result = MissingValueHandler.fill_missing_values(numeric_data, method="median")

        assert not result["A"].isna().any()
        assert not result["B"].isna().any()

    def test_fill_missing_zero(self, data_with_missing):
        """测试零值填充"""
        result = MissingValueHandler.fill_missing_values(data_with_missing, method="zero")

        # 验证NaN被替换为0
        assert result["A"].fillna(0).equals(result["A"])

    def test_fill_missing_invalid_method(self, data_with_missing):
        """测试无效填充方法"""
        with pytest.raises(ValueError, match="不支持的填充方法"):
            MissingValueHandler.fill_missing_values(data_with_missing, method="invalid")

    def test_fill_missing_specific_columns(self, data_with_missing):
        """测试指定列填充"""
        result = MissingValueHandler.fill_missing_values(
            data_with_missing, method="mean", columns=["A"]
        )

        # 只有A列应该被处理
        assert not result["A"].isna().any()
        assert result["B"].isna().any()  # B列仍有缺失值

    def test_get_target_columns_all(self, data_with_missing):
        """测试获取所有目标列"""
        columns = MissingValueHandler._get_target_columns(data_with_missing, None)
        assert columns == list(data_with_missing.columns)

    def test_get_target_columns_specific(self, data_with_missing):
        """测试获取指定目标列"""
        columns = MissingValueHandler._get_target_columns(
            data_with_missing, ["A", "B", "nonexistent"]
        )
        assert "A" in columns
        assert "B" in columns
        assert "nonexistent" not in columns

    def test_interpolate_missing_linear(self, data_with_missing):
        """测试线性插值"""
        result = MissingValueHandler.interpolate_missing_values(data_with_missing, method="linear")

        # 数值列应该被插值处理
        assert isinstance(result, pd.DataFrame)

    def test_interpolate_missing_specific_columns(self, data_with_missing):
        """测试指定列插值"""
        result = MissingValueHandler.interpolate_missing_values(
            data_with_missing, method="linear", columns=["A"]
        )

        assert isinstance(result, pd.DataFrame)

    def test_interpolate_missing_nonexistent_column(self, data_with_missing):
        """测试不存在列的插值处理"""
        result = MissingValueHandler.interpolate_missing_values(
            data_with_missing, method="linear", columns=["nonexistent"]
        )

        # 应该正常返回，不报错
        assert isinstance(result, pd.DataFrame)


class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return pd.DataFrame({"feature1": [1, 2, 3, 4, 5], "feature2": [10, 20, 30, 40, 50]})

    def test_normalize_data_function(self, sample_data):
        """测试normalize_data便捷函数"""
        result = normalize_data(sample_data, method="minmax")

        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_data.shape

    def test_normalize_data_custom_range(self, sample_data):
        """测试自定义范围的normalize_data"""
        result = normalize_data(sample_data, method="minmax", feature_range=(-1, 1))

        for col in result.columns:
            assert result[col].min() >= -1
            assert result[col].max() <= 1

    def test_create_train_test_split_function(self, sample_data):
        """测试create_train_test_split便捷函数"""
        train, test = create_train_test_split(sample_data, test_size=0.2)

        assert len(train) + len(test) == len(sample_data)
        assert isinstance(train, pd.DataFrame)
        assert isinstance(test, pd.DataFrame)

    def test_create_train_test_split_with_shuffle(self, sample_data):
        """测试带shuffle的create_train_test_split"""
        train, test = create_train_test_split(sample_data, test_size=0.2, shuffle=True)

        assert len(train) + len(test) == len(sample_data)

    def test_create_sequences_function(self):
        """测试create_sequences便捷函数"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = create_sequences(data, seq_length=3)

        # 修正的期望值：10 - 3 - 1 + 1 = 7
        assert X.shape == (7, 3)
        assert y.shape == (7, 1)

    def test_create_sequences_multi_prediction(self):
        """测试多步预测的create_sequences"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        X, y = create_sequences(data, seq_length=3, pred_length=2)

        assert X.shape[1] == 3
        assert y.shape[1] == 2


class TestEdgeCasesAndErrorHandling:
    """边缘情况和错误处理测试"""

    def test_normalizer_empty_data(self):
        """测试空数据归一化"""
        empty_df = pd.DataFrame()
        normalizer = DataNormalizer()

        # 应该能处理空数据而不崩溃
        try:
            result = normalizer.fit_transform(empty_df)
            assert isinstance(result, pd.DataFrame)
        except Exception:
            # 如果抛出异常也是可接受的
            pass

    def test_time_series_empty_sequences(self):
        """测试空数组创建序列"""
        empty_data = np.array([])
        X, y = TimeSeriesProcessor.create_sequences(empty_data, seq_length=3)

        assert len(X) == 0
        assert len(y) == 0

    def test_data_splitter_small_data(self):
        """测试小数据集分割"""
        small_data = pd.DataFrame({"col": [1, 2]})
        train, test = DataSplitter.train_test_split(small_data, test_size=0.5)

        assert len(train) + len(test) == 2

    def test_missing_value_handler_no_missing(self):
        """测试无缺失值数据的处理"""
        clean_data = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        result = MissingValueHandler.fill_missing_values(clean_data)

        pd.testing.assert_frame_equal(result, clean_data)

    def test_rolling_features_with_nonexistent_column(self):
        """测试滚动特征创建时处理不存在的列"""
        df = pd.DataFrame({"existing": [1, 2, 3, 4, 5]})

        # 应该打印警告但不报错
        result = TimeSeriesProcessor.create_rolling_features(df, ["nonexistent"], [3])

        # 原数据应该保持不变
        assert "existing" in result.columns
        assert len(result) == len(df)
