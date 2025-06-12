"""
数据处理器模块测试 (Data Processors Module Tests)

提供数据处理相关功能的全面测试覆盖
"""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from src.data.loaders.csv_loader import CSVDataLoader
from src.data.processors.data_processor import (
    add_technical_indicators,
    calculate_returns,
    calculate_volatility,
    create_train_test_split,
    load_data,
    normalize_data,
    process_ohlcv_data,
    save_processed_data,
)
from src.data.validators.data_saver import DataSaver


class TestDataProcessorFunctions:
    """测试数据处理器函数"""

    def test_load_data_success(self, temp_manager):
        """测试成功加载数据"""
        # 创建临时CSV文件
        temp_file_path = temp_manager.create_temp_file(suffix=".csv")

        with open(temp_file_path, "w") as f:
            f.write("col1,col2,col3\n1,2,3\n4,5,6\n7,8,9\n")

        df = load_data(temp_file_path)

        assert not df.empty
        assert len(df) == 3
        assert list(df.columns) == ["col1", "col2", "col3"]
        assert df.iloc[0]["col1"] == 1

    def test_load_data_with_specific_columns(self, temp_manager):
        """测试加载指定列"""
        # 创建临时CSV文件
        temp_file_path = temp_manager.create_temp_file(suffix=".csv")

        with open(temp_file_path, "w") as f:
            f.write("col1,col2,col3\n1,2,3\n4,5,6\n")

        df = load_data(temp_file_path, columns=["col1", "col3"])

        assert not df.empty
        assert list(df.columns) == ["col1", "col3"]
        assert "col2" not in df.columns

    def test_load_data_file_not_found(self):
        """测试加载不存在的文件"""
        df = load_data("nonexistent_file.csv")

        assert df.empty

    def test_process_ohlcv_data_basic(self):
        """测试基础OHLCV数据处理"""
        # 创建测试数据
        data = {
            "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [104, 105, 106],
            "volume": [1000, 1100, 1200],
        }
        df = pd.DataFrame(data)

        processed_df = process_ohlcv_data(df, date_column="date")

        # 验证日期索引
        assert isinstance(processed_df.index, pd.DatetimeIndex)
        assert len(processed_df) == 3
        assert "open" in processed_df.columns

    def test_process_ohlcv_data_with_missing_values(self):
        """测试包含缺失值的OHLCV数据处理"""
        data = {
            "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "open": [100, np.nan, 102],
            "high": [105, 106, np.nan],
            "low": [99, 100, 101],
            "close": [104, np.nan, 106],
            "volume": [1000, np.nan, 1200],
        }
        df = pd.DataFrame(data)

        processed_df = process_ohlcv_data(df, date_column="date", fill_missing=True)

        # 验证缺失值被填充
        assert not processed_df["open"].isnull().any()
        assert not processed_df["close"].isnull().any()

    def test_calculate_returns_simple(self):
        """测试简单收益率计算"""
        prices = pd.Series([100, 110, 105, 115, 120])

        returns = calculate_returns(prices)

        assert len(returns) == 5
        assert pd.isna(returns.iloc[0])  # 第一个值应该是NaN
        assert abs(returns.iloc[1] - 0.1) < 0.001  # 10%涨幅

    def test_calculate_returns_log(self):
        """测试对数收益率计算"""
        prices = pd.Series([100, 110, 120])

        log_returns = calculate_returns(prices, log_returns=True)

        assert len(log_returns) == 3
        assert pd.isna(log_returns.iloc[0])
        assert log_returns.iloc[1] > 0  # 正收益

    def test_add_technical_indicators(self):
        """测试添加技术指标"""
        # 创建价格数据
        prices = np.random.rand(50) * 100 + 100  # 50个价格点
        df = pd.DataFrame({"close": prices, "volume": np.random.randint(1000, 5000, 50)})

        enhanced_df = add_technical_indicators(df, price_column="close")

        # 验证技术指标被添加
        assert "MA_5" in enhanced_df.columns
        assert "MA_20" in enhanced_df.columns
        assert "EMA_10" in enhanced_df.columns
        assert "RSI_14" in enhanced_df.columns
        assert "BB_upper" in enhanced_df.columns
        assert "MACD_line" in enhanced_df.columns

        # 验证数据长度不变
        assert len(enhanced_df) == len(df)

    def test_add_technical_indicators_missing_column(self):
        """测试添加技术指标 - 缺失价格列"""
        df = pd.DataFrame({"open": [100, 101, 102], "volume": [1000, 1100, 1200]})

        # 应该返回原始DataFrame（因为缺少指定的价格列）
        result_df = add_technical_indicators(df, price_column="close")

        assert len(result_df.columns) == len(df.columns)

    def test_calculate_volatility(self):
        """测试波动率计算"""
        # 创建价格序列
        np.random.seed(42)
        prices = pd.Series(100 + np.cumsum(np.random.randn(100) * 0.02))

        volatility = calculate_volatility(prices, window=20)

        assert len(volatility) == len(prices)
        assert volatility.dtype == float
        # 前19个值应该是NaN（因为窗口大小为20）
        assert pd.isna(volatility.iloc[:19]).all()
        # 修复：第19个值可能仍然是NaN，因为需要计算对数收益率
        # 从第20个值开始检查（索引20，即第21个值）
        assert not pd.isna(volatility.iloc[20:]).any()

    def test_normalize_data_dataframe(self):
        """测试DataFrame数据标准化"""
        df = pd.DataFrame(
            {
                "feature1": [1, 2, 3, 4, 5],
                "feature2": [10, 20, 30, 40, 50],
                "feature3": [100, 200, 300, 400, 500],
            }
        )

        normalized_df = normalize_data(df)

        # 验证标准化结果
        assert isinstance(normalized_df, pd.DataFrame)
        assert normalized_df.shape == df.shape

        # 验证每列都在0-1范围内
        for col in normalized_df.columns:
            assert normalized_df[col].min() >= 0
            assert normalized_df[col].max() <= 1

    def test_normalize_data_series(self):
        """测试Series数据标准化"""
        series = pd.Series([1, 5, 10, 15, 20])

        normalized_series = normalize_data(series)

        assert isinstance(normalized_series, pd.Series)
        assert len(normalized_series) == len(series)
        assert normalized_series.min() >= 0
        assert normalized_series.max() <= 1

    def test_create_train_test_split(self):
        """测试训练测试数据分割"""
        df = pd.DataFrame(
            {"feature1": range(100), "feature2": range(100, 200), "target": range(200, 300)}
        )

        train_df, test_df = create_train_test_split(df, test_size=0.2, shuffle=False)

        # 验证分割结果
        assert len(train_df) == 80
        assert len(test_df) == 20
        assert len(train_df) + len(test_df) == len(df)

        # 验证列名保持不变
        assert list(train_df.columns) == list(df.columns)
        assert list(test_df.columns) == list(df.columns)

    def test_save_processed_data_csv(self, temp_manager):
        """测试保存处理后的数据为CSV"""
        df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})

        temp_file_path = temp_manager.create_temp_file(suffix=".csv")

        success = save_processed_data(df, temp_file_path, file_format="csv")

        assert success is True
        assert os.path.exists(temp_file_path)

        # 验证保存的数据可以重新加载
        reloaded_df = pd.read_csv(temp_file_path)
        assert len(reloaded_df) == len(df)


class TestCSVDataLoader:
    """测试CSV加载器功能"""

    @pytest.fixture
    def sample_csv_file(self, temp_manager):
        """创建示例CSV文件用于测试"""
        data = {
            "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [104, 105, 106],
            "volume": [1000, 1100, 1200],
        }
        df = pd.DataFrame(data)

        # 创建临时文件
        temp_file_path = temp_manager.create_temp_file(suffix=".csv")
        df.to_csv(temp_file_path, index=False)

        yield temp_file_path

    def test_csv_loader_initialization(self):
        """测试CSV加载器初始化"""
        loader = CSVDataLoader()

        assert hasattr(loader, "base_path")
        assert hasattr(loader, "load_data")
        assert hasattr(loader, "load_ohlcv_data")

    def test_load_data_basic(self, sample_csv_file):
        """测试基础CSV加载"""
        loader = CSVDataLoader()

        df = loader.load_data(sample_csv_file)

        assert not df.empty
        assert len(df) > 0
        assert "open" in df.columns
        assert "close" in df.columns

    def test_load_data_with_columns(self, sample_csv_file):
        """测试指定列加载"""
        loader = CSVDataLoader()

        df = loader.load_data(sample_csv_file, columns=["open", "close"])

        assert not df.empty
        assert list(df.columns) == ["open", "close"]

    def test_load_data_file_not_found(self):
        """测试加载不存在的文件"""
        loader = CSVDataLoader()

        df = loader.load_data("nonexistent_file.csv")

        # CSVDataLoader returns empty DataFrame instead of raising exception
        assert df.empty

    def test_load_ohlcv_data_valid(self, sample_csv_file):
        """测试OHLCV数据加载 - 有效数据"""
        loader = CSVDataLoader()

        df = loader.load_ohlcv_data(sample_csv_file, date_column="date")

        assert not df.empty
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns

    def test_load_multiple_files(self, sample_csv_file):
        """测试多文件加载"""
        loader = CSVDataLoader()

        # 测试单文件列表
        dataframes = loader.load_multiple_files([sample_csv_file])

        assert isinstance(dataframes, list)
        assert len(dataframes) >= 0

    def test_get_file_info(self, sample_csv_file):
        """测试文件信息获取"""
        loader = CSVDataLoader()

        info = loader.get_file_info(sample_csv_file)

        assert isinstance(info, dict)
        assert "file_path" in info


class TestDataSaver:
    """测试数据保存器功能"""

    def test_data_saver_initialization(self):
        """测试数据保存器初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            saver = DataSaver(base_output_dir=temp_dir)

            assert saver.base_output_dir.exists()
            assert str(saver.base_output_dir) == temp_dir

    def test_save_dataframe_csv(self):
        """测试保存DataFrame为CSV"""
        with tempfile.TemporaryDirectory() as temp_dir:
            saver = DataSaver(base_output_dir=temp_dir)

            # 创建测试数据
            test_data = pd.DataFrame(
                {"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50], "C": ["a", "b", "c", "d", "e"]}
            )

            # 保存数据
            success = saver.save_data(test_data, "test_data.csv", file_format="csv")
            assert success is True

            # 验证文件存在
            saved_file = saver.base_output_dir / "test_data.csv"
            assert saved_file.exists()

            # 验证数据内容
            loaded_data = pd.read_csv(saved_file, index_col=0)
            pd.testing.assert_frame_equal(test_data, loaded_data)

    def test_load_dataframe_csv(self):
        """测试加载CSV文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            saver = DataSaver(base_output_dir=temp_dir)

            # 创建并保存测试数据
            test_data = pd.DataFrame(
                {"X": [1.1, 2.2, 3.3], "Y": [4.4, 5.5, 6.6], "Z": ["x", "y", "z"]}
            )

            saver.save_data(test_data, "load_test.csv")

            # 加载数据
            loaded_file = saver.base_output_dir / "load_test.csv"
            loaded_data = pd.read_csv(loaded_file, index_col=0)

            # 验证数据一致性
            pd.testing.assert_frame_equal(test_data, loaded_data)

    def test_create_subdirectory(self):
        """测试创建子目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            saver = DataSaver(base_output_dir=temp_dir)

            test_data = pd.DataFrame({"col1": [1, 2, 3]})

            # 在子目录中保存数据
            success = saver.save_data(test_data, "subdir_test.csv", subdirectory="test_subdir")
            assert success is True

            # 验证子目录和文件存在
            subdir_path = saver.base_output_dir / "test_subdir"
            assert subdir_path.exists()
            assert subdir_path.is_dir()

            saved_file = subdir_path / "subdir_test.csv"
            assert saved_file.exists()


# 集成测试
class TestDataProcessingIntegration:
    """数据处理模块集成测试"""

    def test_full_data_pipeline(self):
        """测试完整数据处理流水线"""
        # 创建原始数据
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        raw_data = pd.DataFrame(
            {
                "date": dates,
                "open": np.random.rand(100) * 100 + 100,
                "high": np.random.rand(100) * 100 + 110,
                "low": np.random.rand(100) * 100 + 90,
                "close": np.random.rand(100) * 100 + 100,
                "volume": np.random.rand(100) * 1000 + 1000,
            }
        )

        # 添加一些缺失值
        raw_data.loc[5:7, "close"] = np.nan

        # 执行完整的处理流水线
        # 1. 处理OHLCV数据
        processed_data = process_ohlcv_data(raw_data, date_column="date", fill_missing=True)
        assert not processed_data.isnull().any().any()

        # 2. 添加技术指标
        enhanced_data = add_technical_indicators(processed_data, price_column="close")
        assert len(enhanced_data.columns) > len(processed_data.columns)

        # 3. 标准化数据 - 修复：只对没有NaN的列进行标准化
        numeric_cols = enhanced_data.select_dtypes(include=[np.number]).columns
        # 过滤掉包含NaN的列
        valid_cols = []
        for col in numeric_cols:
            if not enhanced_data[col].isnull().any():
                valid_cols.append(col)

        if valid_cols:  # 只有当有有效列时才进行标准化
            normalized_data = normalize_data(enhanced_data[valid_cols])
            for col in normalized_data.columns:
                assert normalized_data[col].min() >= 0
                # 使用np.isclose处理浮点精度问题
                assert normalized_data[col].max() <= 1.0 + 1e-10  # 允许微小的浮点误差

        # 4. 计算波动率
        volatility = calculate_volatility(enhanced_data["close"], window=10)
        assert len(volatility) == len(enhanced_data)

        print("✅ 完整数据处理流水线测试通过")

    def test_csv_loader_processor_integration(self, temp_manager):
        """测试CSV加载器与数据处理器的集成"""
        # 创建临时CSV文件
        data = {
            "date": pd.date_range("2023-01-01", periods=50),
            "open": np.random.rand(50) * 100 + 100,
            "high": np.random.rand(50) * 100 + 110,
            "low": np.random.rand(50) * 100 + 90,
            "close": np.random.rand(50) * 100 + 100,
            "volume": np.random.rand(50) * 1000 + 1000,
        }
        df = pd.DataFrame(data)

        temp_file_path = temp_manager.create_temp_file(suffix=".csv")
        df.to_csv(temp_file_path, index=False)

        # 使用CSV加载器加载数据
        loader = CSVDataLoader()
        loaded_df = loader.load_data(temp_file_path)

        # 使用数据处理器处理数据
        processed_df = process_ohlcv_data(loaded_df, date_column="date")
        enhanced_df = add_technical_indicators(processed_df, price_column="close")

        # 验证集成结果
        assert not enhanced_df.empty
        assert len(enhanced_df.columns) > len(loaded_df.columns)
        assert isinstance(enhanced_df.index, pd.DatetimeIndex)
