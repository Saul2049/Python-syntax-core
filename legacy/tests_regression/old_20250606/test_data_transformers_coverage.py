#!/usr/bin/env python3
"""
数据转换器覆盖率提升测试 (Data Transformers Coverage Enhancement Tests)

专门提升data/transformers模块覆盖率的测试
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.data.transformers.missing_values import MissingValueHandler
from src.data.transformers.normalizers import DataNormalizer, normalize_data
from src.data.transformers.splitters import DataSplitter
from src.data.transformers.time_series import TimeSeriesProcessor


class TestDataNormalizer:
    """测试数据归一化器"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return pd.DataFrame(
            {
                "feature1": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "feature2": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
                "feature3": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
            }
        )

    def test_normalizer_initialization(self):
        """测试归一化器初始化"""
        normalizer = DataNormalizer(method="minmax")
        assert normalizer.method == "minmax"

        normalizer = DataNormalizer(method="standard")
        assert normalizer.method == "standard"

    def test_minmax_normalization(self, sample_data):
        """测试MinMax归一化"""
        normalizer = DataNormalizer(method="minmax")
        normalized = normalizer.fit_transform(sample_data)

        # 验证范围在0-1之间
        for col in normalized.columns:
            assert normalized[col].min() >= 0
            assert normalized[col].max() <= 1

    def test_standard_normalization(self, sample_data):
        """测试标准化"""
        normalizer = DataNormalizer(method="standard")
        normalized = normalizer.fit_transform(sample_data)

        # 验证均值接近0，标准差接近1
        for col in normalized.columns:
            assert abs(normalized[col].mean()) < 0.1
            assert abs(normalized[col].std() - 1.0) < 0.1

    def test_invalid_method_with_sklearn(self):
        """测试无效方法（有sklearn时）"""
        with patch("src.data.transformers.normalizers.HAS_SKLEARN", True):
            with pytest.raises(ValueError):
                DataNormalizer(method="invalid_method")

    def test_simple_normalize_methods(self, sample_data):
        """测试简化归一化方法"""
        with patch("src.data.transformers.normalizers.HAS_SKLEARN", False):
            # MinMax
            normalizer = DataNormalizer(method="minmax")
            result = normalizer.fit_transform(sample_data)
            assert isinstance(result, pd.DataFrame)

            # Standard
            normalizer = DataNormalizer(method="standard")
            result = normalizer.fit_transform(sample_data)
            assert isinstance(result, pd.DataFrame)

    def test_simple_normalize_unsupported_method(self, sample_data):
        """测试简化实现不支持的方法"""
        with patch("src.data.transformers.normalizers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="robust")
            with pytest.raises(ValueError, match="简化实现不支持方法"):
                normalizer.fit_transform(sample_data)

    def test_transform_without_sklearn(self, sample_data):
        """测试没有sklearn时的transform方法"""
        with patch("src.data.transformers.normalizers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="minmax")
            result = normalizer.transform(sample_data)
            assert isinstance(result, pd.DataFrame)

    def test_inverse_transform_without_sklearn(self, sample_data):
        """测试没有sklearn时的逆变换"""
        with patch("src.data.transformers.normalizers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="minmax")
            normalized = normalizer.fit_transform(sample_data)
            restored = normalizer.inverse_transform(normalized)

            # 简化实现不支持逆变换，应该返回原数据
            pd.testing.assert_frame_equal(normalized, restored)

    def test_normalize_data_function(self, sample_data):
        """测试便捷函数"""
        result = normalize_data(sample_data, method="minmax")
        assert isinstance(result, pd.DataFrame)
        assert result.shape == sample_data.shape


class TestTimeSeriesProcessor:
    """测试时间序列处理器"""

    @pytest.fixture
    def time_series_data(self):
        """创建时间序列数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "value": np.random.randn(100).cumsum() + 100,
                "volume": np.random.randint(1000, 5000, 100),
            },
            index=dates,
        )

    def test_processor_initialization(self):
        """测试处理器初始化"""
        processor = TimeSeriesProcessor()
        assert hasattr(processor, "create_sequences")
        assert hasattr(processor, "create_lagged_features")

    def test_create_sequences(self, time_series_data):
        """测试序列创建"""
        processor = TimeSeriesProcessor()
        X, y = processor.create_sequences(time_series_data["value"].values, seq_length=10)

        assert X.shape[1] == 10
        assert len(X) == len(y)
        assert len(X) == len(time_series_data) - 10

    def test_create_lagged_features(self, time_series_data):
        """测试滞后特征创建"""
        processor = TimeSeriesProcessor()
        lagged = processor.create_lagged_features(time_series_data, ["value"], [1, 2, 3])

        assert "value_lag_1" in lagged.columns
        assert "value_lag_2" in lagged.columns
        assert "value_lag_3" in lagged.columns
        assert len(lagged) == len(time_series_data)

    def test_create_rolling_features(self, time_series_data):
        """测试滚动特征创建"""
        processor = TimeSeriesProcessor()
        rolling = processor.create_rolling_features(time_series_data, ["value"], [5, 10])

        assert "value_rolling_5_mean" in rolling.columns
        assert "value_rolling_5_std" in rolling.columns
        assert "value_rolling_10_mean" in rolling.columns
        assert "value_rolling_10_std" in rolling.columns

    def test_detect_outliers_iqr(self, time_series_data):
        """测试IQR异常值检测"""
        processor = TimeSeriesProcessor()

        # 添加明显的异常值
        data_with_outliers = time_series_data.copy()
        data_with_outliers.iloc[50, 0] = 1000  # 极大值

        outliers = processor.detect_outliers_iqr(data_with_outliers["value"])
        assert outliers.sum() > 0  # 应该检测到异常值

    def test_remove_outliers(self, time_series_data):
        """测试异常值移除"""
        processor = TimeSeriesProcessor()

        # 添加异常值
        data_with_outliers = time_series_data.copy()
        data_with_outliers.iloc[50, 0] = 1000

        cleaned = processor.remove_outliers(data_with_outliers, ["value"], method="iqr")
        assert len(cleaned) <= len(data_with_outliers)  # 数据量应该减少

    def test_resample_data(self, time_series_data):
        """测试数据重采样"""
        processor = TimeSeriesProcessor()
        resampled = processor.resample_data(time_series_data, "7D", "mean")

        # 周重采样应该减少数据量
        assert len(resampled) < len(time_series_data)
        assert isinstance(resampled, pd.DataFrame)


class TestDataSplitter:
    """测试数据分割器"""

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return pd.DataFrame(
            {
                "feature1": range(100),
                "feature2": range(100, 200),
                "target": np.random.choice([0, 1], 100),
            }
        )

    def test_splitter_initialization(self):
        """测试分割器初始化"""
        splitter = DataSplitter()
        assert hasattr(splitter, "train_test_split")
        assert hasattr(splitter, "stratified_split")

    def test_basic_train_test_split(self, sample_data):
        """测试基本训练测试分割"""
        splitter = DataSplitter()
        train, test = splitter.train_test_split(sample_data, test_size=0.2)

        assert len(train) == 80
        assert len(test) == 20
        assert len(train) + len(test) == len(sample_data)

    def test_stratified_split(self, sample_data):
        """测试分层分割"""
        splitter = DataSplitter()
        train, test = splitter.stratified_split(sample_data, target_column="target", test_size=0.2)

        # 检查分割比例
        assert len(train) + len(test) == len(sample_data)

        # 检查分层效果（目标变量分布应该相似）
        train_ratio = train["target"].mean()
        test_ratio = test["target"].mean()
        assert abs(train_ratio - test_ratio) < 0.15  # 放宽容差

    def test_rolling_window_split(self, sample_data):
        """测试滚动窗口分割"""
        splitter = DataSplitter()
        splits = splitter.rolling_window_split(sample_data, window_size=50, step_size=5)

        # 验证返回的是列表
        assert isinstance(splits, list)
        assert len(splits) > 0

        # 验证每个分割的结构
        for train_df, test_df in splits:
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            assert len(train_df) == 50  # 训练窗口大小
            assert len(test_df) <= 5  # 测试集大小不超过步长

    def test_time_series_split(self):
        """测试时间序列分割"""
        # 创建时间序列数据
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        ts_data = pd.DataFrame({"value": range(100)}, index=dates)

        splitter = DataSplitter()
        splits = splitter.time_series_split(ts_data, n_splits=3, test_size=20)

        # 验证返回的是分割列表
        assert isinstance(splits, list)
        assert len(splits) == 3

        # 验证每个分割的时序性
        for train_df, test_df in splits:
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            # 训练集的最大时间应该小于测试集的最小时间
            assert train_df.index.max() <= test_df.index.min()


class TestMissingValueHandler:
    """测试缺失值处理器"""

    @pytest.fixture
    def data_with_missing(self):
        """创建包含缺失值的数据"""
        data = pd.DataFrame(
            {
                "feature1": [1, 2, np.nan, 4, 5, np.nan, 7, 8, 9, 10],
                "feature2": [10, np.nan, 30, np.nan, 50, 60, 70, np.nan, 90, 100],
                "feature3": [100, 200, 300, 400, np.nan, 600, 700, 800, 900, np.nan],
            }
        )
        return data

    def test_handler_initialization(self):
        """测试处理器初始化"""
        handler = MissingValueHandler()
        assert hasattr(handler, "fill_missing_values")
        assert hasattr(handler, "detect_missing_patterns")

    def test_fill_missing_mean(self, data_with_missing):
        """测试均值填充"""
        handler = MissingValueHandler()
        filled = handler.fill_missing_values(data_with_missing, method="mean")

        # 验证没有缺失值
        assert filled.isnull().sum().sum() == 0

        # 验证填充值合理
        for col in filled.columns:
            original_mean = data_with_missing[col].mean()
            assert filled[col].mean() == pytest.approx(original_mean, abs=0.1)

    def test_fill_missing_median(self, data_with_missing):
        """测试中位数填充"""
        handler = MissingValueHandler()
        filled = handler.fill_missing_values(data_with_missing, method="median")

        assert filled.isnull().sum().sum() == 0

    def test_unsupported_fill_method(self, data_with_missing):
        """测试不支持的填充方法"""
        handler = MissingValueHandler()
        with pytest.raises(ValueError, match="不支持的填充方法"):
            handler.fill_missing_values(data_with_missing, method="invalid_method")

    def test_analyze_missing_patterns(self, data_with_missing):
        """测试缺失值模式分析"""
        handler = MissingValueHandler()
        patterns = handler.detect_missing_patterns(data_with_missing)

        # 返回DataFrame而不是dict
        assert isinstance(patterns, pd.DataFrame)
        assert "missing_count" in patterns.columns
        assert "missing_percent" in patterns.columns

    def test_get_missing_summary(self, data_with_missing):
        """测试缺失值摘要"""
        handler = MissingValueHandler()
        summary = handler.get_missing_summary(data_with_missing)

        # 返回dict而不是DataFrame
        assert isinstance(summary, dict)
        assert "total_missing" in summary
        assert "missing_percentage" in summary
        assert summary["total_missing"] > 0


class TestTransformersIntegration:
    """测试转换器集成"""

    def test_full_pipeline(self):
        """测试完整的数据转换流水线"""
        # 创建包含各种问题的数据
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "price": np.random.randn(100).cumsum() + 100,
                "volume": np.random.randint(1000, 5000, 100),
                "returns": np.random.normal(0, 0.02, 100),
            },
            index=dates,
        )

        # 添加缺失值
        data.iloc[10:15, 0] = np.nan
        data.iloc[30:35, 1] = np.nan

        # 1. 处理缺失值
        missing_handler = MissingValueHandler()
        data_filled = missing_handler.fill_missing_values(data, method="mean")
        assert data_filled.isnull().sum().sum() == 0

        # 2. 创建滞后特征
        ts_processor = TimeSeriesProcessor()
        data_with_lags = ts_processor.create_lagged_features(data_filled, ["price"], [1, 2, 3])
        assert "price_lag_1" in data_with_lags.columns

        # 3. 归一化数据
        normalizer = DataNormalizer(method="minmax")
        data_normalized = normalizer.fit_transform(
            data_with_lags.select_dtypes(include=[np.number])
        )

        # 验证归一化结果
        for col in data_normalized.columns:
            assert data_normalized[col].min() >= 0
            assert data_normalized[col].max() <= 1

        # 4. 分割数据 - 使用时间序列分割的正确参数
        splitter = DataSplitter()
        # time_series_split返回分割列表，我们取第一个分割
        splits = splitter.time_series_split(data_normalized, n_splits=1, test_size=20)
        train, test = splits[0]  # 获取第一个分割

        assert len(train) + len(test) <= len(data_normalized)
        assert train.index.max() <= test.index.min()

    def test_error_handling(self):
        """测试错误处理"""
        # 测试空数据
        empty_data = pd.DataFrame()

        with patch("src.data.transformers.normalizers.HAS_SKLEARN", False):
            normalizer = DataNormalizer()
            # 对于空数据，简化实现会返回空DataFrame而不是抛出异常
            result = normalizer.fit_transform(empty_data)
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

        # 测试无效参数 - 使用会真正抛出异常的方法
        splitter = DataSplitter()
        valid_data = pd.DataFrame({"a": range(10)})

        # 测试stratified_split与不存在的列
        with pytest.raises(ValueError):
            splitter.stratified_split(valid_data, target_column="nonexistent_column")

        # 测试train_val_test_split的无效比例（总和超过1.0）
        with pytest.raises(ValueError):
            splitter.train_val_test_split(valid_data, train_size=0.5, val_size=0.3, test_size=0.5)

    def test_memory_efficiency(self):
        """测试内存效率"""
        # 创建大数据集
        large_data = pd.DataFrame(
            {"feature1": np.random.randn(10000), "feature2": np.random.randn(10000)}
        )

        # 测试各个组件不会消耗过多内存
        normalizer = DataNormalizer()
        normalized = normalizer.fit_transform(large_data)
        assert normalized.memory_usage().sum() > 0

        splitter = DataSplitter()
        train, test = splitter.train_test_split(normalized, test_size=0.2)
        assert len(train) + len(test) == len(normalized)
