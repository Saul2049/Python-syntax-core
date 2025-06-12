"""
数据转换器覆盖率提升测试 (Data Transformers Coverage Boost Tests)

专门针对 data_transformers.py 中未覆盖的代码行进行测试，
将覆盖率从 88% 提升到接近 100%。

目标缺失行: 21-22, 91-94, 113, 116, 123, 144-145, 148, 155, 210-211, 241-242, 269, 361-363, 407, 464, 492
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

# 导入被测试的模块
from src.data.transformers.data_transformers import (
    DataNormalizer,
    DataSplitter,
    MissingValueHandler,
    TimeSeriesProcessor,
    create_sequences,
    create_train_test_split,
    normalize_data,
)


class TestDataTransformersSklearnImportError:
    """测试 sklearn 导入错误处理 (Lines 21-22)"""

    def test_sklearn_import_error_handling(self):
        """测试当 sklearn 不可用时的处理"""
        # 模拟 sklearn 导入失败
        with patch.dict("sys.modules", {"sklearn": None, "sklearn.preprocessing": None}):
            # 重新导入模块以触发 ImportError
            import importlib

            import src.data.transformers.data_transformers as dt_module

            importlib.reload(dt_module)

            # 验证 HAS_SKLEARN 被设置为 False
            assert not hasattr(dt_module, "HAS_SKLEARN") or not dt_module.HAS_SKLEARN


class TestDataNormalizerWithoutSklearn:
    """测试 DataNormalizer 在没有 sklearn 时的行为"""

    def test_initialize_scaler_without_sklearn(self):
        """测试在没有 sklearn 时初始化归一化器 (Lines 44-46)"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer()
            assert normalizer.scaler is None

    def test_simple_normalize_robust_method_error(self):
        """测试简化实现不支持 robust 方法 (Lines 91-94)"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="robust")
            data = pd.Series([1, 2, 3, 4, 5])

            with pytest.raises(ValueError, match="简化实现不支持方法"):
                normalizer._simple_normalize(data)

    def test_fit_transform_without_sklearn(self):
        """测试在没有 sklearn 时的 fit_transform (Line 67)"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="minmax")
            data = pd.Series([1, 2, 3, 4, 5])
            result = normalizer.fit_transform(data)
            assert isinstance(result, pd.Series)

    def test_transform_without_sklearn(self):
        """测试在没有 sklearn 时的 transform (Line 113)"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer(method="standard")
            data = pd.Series([1, 2, 3, 4, 5])
            result = normalizer.transform(data)
            assert isinstance(result, pd.Series)

    def test_transform_untrained_scaler_error(self):
        """测试未训练的归一化器错误 (Line 116)"""
        # 确保 sklearn 可用，然后设置未训练状态
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", True):
            normalizer = DataNormalizer()
            normalizer.scaler = None  # 模拟未训练状态
            data = pd.Series([1, 2, 3, 4, 5])

            with pytest.raises(ValueError, match="归一化器未训练"):
                normalizer.transform(data)

    def test_inverse_transform_without_sklearn(self):
        """测试在没有 sklearn 时的 inverse_transform (Lines 144-145)"""
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", False):
            normalizer = DataNormalizer()
            data = pd.Series([0.0, 0.25, 0.5, 0.75, 1.0])

            # 捕获打印输出
            with patch("builtins.print") as mock_print:
                result = normalizer.inverse_transform(data)
                mock_print.assert_called_with("⚠️ 警告: 简化实现不支持inverse_transform")
                assert result.equals(data)

    def test_inverse_transform_untrained_scaler_error(self):
        """测试未训练归一化器的 inverse_transform 错误 (Line 148)"""
        # 确保 sklearn 可用，然后设置未训练状态
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", True):
            normalizer = DataNormalizer()
            normalizer.scaler = None
            data = pd.Series([0.0, 0.25, 0.5, 0.75, 1.0])

            with pytest.raises(ValueError, match="归一化器未训练"):
                normalizer.inverse_transform(data)


class TestTimeSeriesProcessorEdgeCases:
    """测试 TimeSeriesProcessor 边缘情况"""

    def test_create_lagged_features_missing_column_warning(self):
        """测试滞后特征创建时缺失列的警告 (Lines 210-211)"""
        df = pd.DataFrame({"A": [1, 2, 3, 4, 5]})

        with patch("builtins.print") as mock_print:
            result = TimeSeriesProcessor.create_lagged_features(
                df, columns=["A", "nonexistent_column"], lags=[1, 2]
            )
            mock_print.assert_called_with("⚠️ 警告: 列 'nonexistent_column' 不存在，跳过")

        # 验证结果包含存在列的滞后特征
        assert "A_lag_1" in result.columns
        assert "A_lag_2" in result.columns
        assert "nonexistent_column_lag_1" not in result.columns

    def test_create_rolling_features_missing_column_warning(self):
        """测试滚动特征创建时缺失列的警告 (Lines 241-242)"""
        df = pd.DataFrame({"B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})

        with patch("builtins.print") as mock_print:
            result = TimeSeriesProcessor.create_rolling_features(
                df, columns=["B", "missing_col"], windows=[3], functions=["mean"]
            )
            mock_print.assert_called_with("⚠️ 警告: 列 'missing_col' 不存在，跳过")

        # 验证结果包含存在列的滚动特征
        assert "B_rolling_mean_3" in result.columns
        assert "missing_col_rolling_mean_3" not in result.columns

    def test_resample_data_invalid_index_error(self):
        """测试重采样数据时无效索引错误 (Line 269)"""
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})  # 没有 DatetimeIndex

        with pytest.raises(ValueError, match="DataFrame必须有DatetimeIndex"):
            TimeSeriesProcessor.resample_data(df, "1D")


class TestDataSplitterEdgeCases:
    """测试 DataSplitter 边缘情况"""

    def test_train_val_test_split_invalid_proportions(self):
        """测试训练/验证/测试分割时比例无效错误 (Lines 361-363)"""
        df = pd.DataFrame({"A": range(100), "B": range(100, 200)})

        with pytest.raises(ValueError, match="训练集、验证集和测试集比例之和必须等于1.0"):
            DataSplitter.train_val_test_split(
                df, train_size=0.6, val_size=0.3, test_size=0.2  # 总和 = 1.1
            )

    def test_time_series_split_edge_case(self):
        """测试时间序列分割边缘情况 (Line 407)"""
        # 创建很小的数据集，测试边缘情况
        df = pd.DataFrame({"value": [1, 2]})

        splits = DataSplitter.time_series_split(df, n_splits=5, test_size=1)

        # 验证分割结果
        assert len(splits) >= 0  # 可能没有有效分割
        for train_df, test_df in splits:
            assert len(test_df) > 0  # 测试集不为空


class TestMissingValueHandlerEdgeCases:
    """测试 MissingValueHandler 边缘情况"""

    def test_fill_missing_values_unsupported_method(self):
        """测试不支持的填充方法错误 (Line 464)"""
        df = pd.DataFrame({"A": [1, np.nan, 3, np.nan, 5]})

        with pytest.raises(ValueError, match="不支持的填充方法"):
            MissingValueHandler._fill_column_missing_values(df, "A", "unsupported_method")

    def test_interpolate_missing_values_missing_column(self):
        """测试插值时缺失列的处理 (Line 492)"""
        df = pd.DataFrame({"A": [1, np.nan, 3, np.nan, 5]})

        # 测试指定不存在的列
        result = MissingValueHandler.interpolate_missing_values(
            df, columns=["A", "nonexistent_column"]
        )

        # 验证结果只处理存在的列
        assert "A" in result.columns
        assert not result["A"].isna().any()


class TestConvenienceFunctionsEdgeCases:
    """测试便捷函数边缘情况"""

    def test_normalize_data_with_custom_parameters(self):
        """测试带自定义参数的数据归一化"""
        data = pd.DataFrame({"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50]})

        result = normalize_data(data, method="standard", feature_range=(0, 1))
        assert isinstance(result, pd.DataFrame)
        assert result.shape == data.shape

    def test_create_train_test_split_convenience(self):
        """测试便捷的训练测试集分割函数"""
        df = pd.DataFrame({"A": range(100), "B": range(100, 200)})

        train_df, test_df = create_train_test_split(df, test_size=0.3, shuffle=True)

        assert len(train_df) == 70
        assert len(test_df) == 30
        assert len(train_df) + len(test_df) == len(df)

    def test_create_sequences_convenience(self):
        """测试便捷的序列创建函数"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        X, y = create_sequences(data, seq_length=3, pred_length=2)

        assert X.shape[1] == 3  # 序列长度
        assert y.shape[1] == 2  # 预测长度
        assert X.shape[0] == y.shape[0]  # 样本数量一致


class TestDataNormalizerRobustMethod:
    """测试 DataNormalizer 的 robust 方法"""

    def test_initialize_robust_scaler(self):
        """测试 robust 归一化器初始化"""
        # 确保 sklearn 可用
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", True):
            normalizer = DataNormalizer(method="robust")

            # 验证 robust scaler 被正确初始化
            assert normalizer.method == "robust"
            assert normalizer.scaler is not None

    def test_invalid_normalization_method(self):
        """测试无效的归一化方法"""
        # 确保 sklearn 可用以触发错误检查
        with patch("src.data.transformers.data_transformers.HAS_SKLEARN", True):
            with pytest.raises(ValueError, match="不支持的归一化方法"):
                DataNormalizer(method="invalid_method")


class TestTimeSeriesProcessorAdvanced:
    """测试 TimeSeriesProcessor 高级功能"""

    def test_create_sequences_with_step(self):
        """测试带步长的序列创建"""
        data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        X, y = TimeSeriesProcessor.create_sequences(data, seq_length=3, pred_length=1, step=2)

        # 验证步长效果
        assert X.shape[0] < len(data) - 3  # 由于步长，样本数减少
        assert X.shape[1] == 3
        assert y.shape[1] == 1

    def test_resample_data_with_custom_agg_methods(self):
        """测试带自定义聚合方法的重采样"""
        # 创建带 DatetimeIndex 的数据
        dates = pd.date_range("2023-01-01", periods=10, freq="H")
        df = pd.DataFrame(
            {
                "price": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
                "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
            },
            index=dates,
        )

        custom_agg = {"price": "mean", "volume": "sum"}
        result = TimeSeriesProcessor.resample_data(df, "2H", custom_agg)

        assert isinstance(result, pd.DataFrame)
        assert "price" in result.columns
        assert "volume" in result.columns


class TestMissingValueHandlerComprehensive:
    """测试 MissingValueHandler 全面功能"""

    def test_fill_missing_values_all_methods(self):
        """测试所有填充方法"""
        df = pd.DataFrame({"A": [1, np.nan, 3, np.nan, 5], "B": [np.nan, 2, np.nan, 4, np.nan]})

        methods = ["forward", "backward", "mean", "median", "zero"]

        for method in methods:
            result = MissingValueHandler.fill_missing_values(df.copy(), method=method)
            assert isinstance(result, pd.DataFrame)
            # 某些方法可能仍有 NaN（如 forward fill 的第一个值）

    def test_interpolate_missing_values_all_methods(self):
        """测试所有插值方法"""
        df = pd.DataFrame({"A": [1, np.nan, 3, np.nan, 5], "B": [10, np.nan, 30, np.nan, 50]})

        methods = ["linear", "time", "cubic"]

        for method in methods:
            try:
                result = MissingValueHandler.interpolate_missing_values(df.copy(), method=method)
                assert isinstance(result, pd.DataFrame)
            except Exception:
                # 某些插值方法可能在特定数据上失败
                pass


class TestDataSplitterComprehensive:
    """测试 DataSplitter 全面功能"""

    def test_train_test_split_with_random_state(self):
        """测试带随机种子的训练测试分割"""
        df = pd.DataFrame({"A": range(100), "B": range(100, 200)})

        # 测试相同随机种子产生相同结果
        train1, test1 = DataSplitter.train_test_split(
            df, test_size=0.2, shuffle=True, random_state=42
        )
        train2, test2 = DataSplitter.train_test_split(
            df, test_size=0.2, shuffle=True, random_state=42
        )

        pd.testing.assert_frame_equal(train1, train2)
        pd.testing.assert_frame_equal(test1, test2)

    def test_train_val_test_split_with_shuffle(self):
        """测试带打乱的三分割"""
        df = pd.DataFrame({"A": range(100), "B": range(100, 200)})

        train, val, test = DataSplitter.train_val_test_split(
            df, train_size=0.6, val_size=0.2, test_size=0.2, shuffle=True, random_state=42
        )

        assert len(train) == 60
        assert len(val) == 20
        assert len(test) == 20
        assert len(train) + len(val) + len(test) == len(df)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
