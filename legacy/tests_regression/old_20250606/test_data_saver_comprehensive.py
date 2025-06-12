#!/usr/bin/env python3
"""
数据保存器完整测试套件 (Data Saver Comprehensive Tests)

专门提升src/data/validators/data_saver.py覆盖率
目标：从30%覆盖率提升到80%+
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.data.validators.data_saver import DataSaver, ProcessedDataExporter, save_processed_data


class TestDataSaverCore:
    """数据保存器核心功能测试"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_dataframe(self):
        """示例DataFrame"""
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2023-01-01", periods=100, freq="h"),
                "price": np.random.rand(100) * 100 + 50,
                "volume": np.random.randint(1000, 10000, 100),
                "signal": np.random.choice(["buy", "sell", "hold"], 100),
                "value": np.random.randn(100),
            }
        )

    def test_init_default_dir(self):
        """测试默认目录初始化"""
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            saver = DataSaver()
            assert saver.base_output_dir == Path("output")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_init_custom_dir(self, temp_dir):
        """测试自定义目录初始化"""
        custom_dir = Path(temp_dir) / "custom"
        saver = DataSaver(base_output_dir=custom_dir)
        assert saver.base_output_dir == custom_dir
        assert custom_dir.exists()

    def test_init_string_path(self, temp_dir):
        """测试字符串路径初始化"""
        saver = DataSaver(base_output_dir=temp_dir)
        assert saver.base_output_dir == Path(temp_dir)

    def test_save_data_csv_success(self, temp_dir, sample_dataframe):
        """测试CSV格式保存成功"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.csv", file_format="csv")

        assert result is True
        file_path = Path(temp_dir) / "test.csv"
        assert file_path.exists()

        # 验证文件可以加载，但不进行严格的类型比较
        # 因为CSV格式会改变某些数据类型（如datetime变为object）
        loaded_df = pd.read_csv(file_path, index_col=0)
        assert len(loaded_df) == len(sample_dataframe)
        assert list(loaded_df.columns) == list(sample_dataframe.columns)

    def test_save_data_with_subdirectory(self, temp_dir, sample_dataframe):
        """测试在子目录中保存数据"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.csv", subdirectory="data/raw")

        assert result is True
        file_path = Path(temp_dir) / "data" / "raw" / "test.csv"
        assert file_path.exists()

    def test_save_data_with_timestamp(self, temp_dir, sample_dataframe):
        """测试添加时间戳的保存"""
        saver = DataSaver(base_output_dir=temp_dir)

        with patch("src.data.validators.data_saver.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231201_143022"
            result = saver.save_data(sample_dataframe, "test.csv", add_timestamp=True)

        assert result is True
        file_path = Path(temp_dir) / "test_20231201_143022.csv"
        assert file_path.exists()

    def test_save_data_parquet_format(self, temp_dir, sample_dataframe):
        """测试Parquet格式保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.parquet", file_format="parquet")

        assert result is True
        file_path = Path(temp_dir) / "test.parquet"
        assert file_path.exists()

    def test_save_data_json_format(self, temp_dir, sample_dataframe):
        """测试JSON格式保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.json", file_format="json")

        assert result is True
        file_path = Path(temp_dir) / "test.json"
        assert file_path.exists()

    def test_save_data_excel_format(self, temp_dir, sample_dataframe):
        """测试Excel格式保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.xlsx", file_format="excel")

        assert result is True
        file_path = Path(temp_dir) / "test.xlsx"
        assert file_path.exists()

    def test_save_data_pickle_format(self, temp_dir, sample_dataframe):
        """测试Pickle格式保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.pkl", file_format="pickle")

        assert result is True
        file_path = Path(temp_dir) / "test.pkl"
        assert file_path.exists()

    def test_save_data_hdf5_format(self, temp_dir, sample_dataframe):
        """测试HDF5格式保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.h5", file_format="hdf5", key="test_data")

        assert result is True
        file_path = Path(temp_dir) / "test.h5"
        assert file_path.exists()

    def test_save_data_unsupported_format(self, temp_dir, sample_dataframe):
        """测试不支持的格式"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.xyz", file_format="xyz")

        assert result is False

    def test_save_data_exception_handling(self, temp_dir, sample_dataframe):
        """测试异常处理"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 模拟保存异常
        with patch.object(pd.DataFrame, "to_csv", side_effect=Exception("Test error")):
            result = saver.save_data(sample_dataframe, "test.csv")
            assert result is False

    def test_save_metadata_enabled(self, temp_dir, sample_dataframe):
        """测试元数据保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.csv", save_metadata=True)

        assert result is True
        metadata_path = Path(temp_dir) / "test.metadata.json"
        assert metadata_path.exists()

        # 验证元数据内容
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        assert "filename" in metadata
        assert "created_at" in metadata
        assert "shape" in metadata
        assert "columns" in metadata
        assert metadata["shape"] == list(sample_dataframe.shape)

    def test_save_metadata_disabled(self, temp_dir, sample_dataframe):
        """测试禁用元数据保存"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.csv", save_metadata=False)

        assert result is True
        metadata_path = Path(temp_dir) / "test.metadata.json"
        assert not metadata_path.exists()

    def test_create_backup_functionality(self, temp_dir, sample_dataframe):
        """测试备份功能"""
        saver = DataSaver(base_output_dir=temp_dir)
        file_path = Path(temp_dir) / "test.csv"

        # 先保存一个文件
        sample_dataframe.to_csv(file_path)

        # 再次保存并创建备份
        with patch("src.data.validators.data_saver.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20231201_143022"
            result = saver.save_data(sample_dataframe, "test.csv", create_backup=True)

        assert result is True
        backup_dir = Path(temp_dir) / "backups"
        assert backup_dir.exists()
        backup_file = backup_dir / "test_20231201_143022.csv"
        assert backup_file.exists()

    def test_create_backup_no_original_file(self, temp_dir, sample_dataframe):
        """测试原文件不存在时的备份"""
        saver = DataSaver(base_output_dir=temp_dir)
        result = saver.save_data(sample_dataframe, "test.csv", create_backup=True)

        assert result is True
        # 不应该创建备份目录，因为原文件不存在
        backup_dir = Path(temp_dir) / "backups"
        assert not backup_dir.exists()

    def test_create_backup_exception(self, temp_dir, sample_dataframe):
        """测试备份创建异常"""
        saver = DataSaver(base_output_dir=temp_dir)
        file_path = Path(temp_dir) / "test.csv"
        sample_dataframe.to_csv(file_path)

        with patch("shutil.copy2", side_effect=Exception("Backup error")):
            # 应该仍然成功保存，只是备份失败
            result = saver.save_data(sample_dataframe, "test.csv", create_backup=True)
            assert result is True

    def test_save_metadata_exception(self, temp_dir, sample_dataframe):
        """测试元数据保存异常"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 使用更精确的patch来只影响元数据文件写入
        original_open = open

        def mock_open_func(*args, **kwargs):
            if len(args) > 0 and "metadata.json" in str(args[0]):
                raise Exception("Metadata error")
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_func):
            # 应该仍然成功保存主文件
            result = saver.save_data(sample_dataframe, "test.csv", save_metadata=True)
            assert result is True

    def test_save_multiple_formats_success(self, temp_dir, sample_dataframe):
        """测试多格式保存成功"""
        saver = DataSaver(base_output_dir=temp_dir)
        formats = ["csv", "json", "pickle"]
        results = saver.save_multiple_formats(sample_dataframe, "test", formats)

        assert isinstance(results, dict)
        assert len(results) == 3
        for fmt in formats:
            assert results[fmt] is True
            if fmt == "excel":
                file_path = Path(temp_dir) / "test.xlsx"
            else:
                file_path = Path(temp_dir) / f"test.{fmt}"
            assert file_path.exists()

    def test_save_multiple_formats_partial_failure(self, temp_dir, sample_dataframe):
        """测试多格式保存部分失败"""
        saver = DataSaver(base_output_dir=temp_dir)
        formats = ["csv", "unsupported", "json"]
        results = saver.save_multiple_formats(sample_dataframe, "test", formats)

        assert results["csv"] is True
        assert results["unsupported"] is False
        assert results["json"] is True

    def test_batch_save_success(self, temp_dir):
        """测试批量保存成功"""
        saver = DataSaver(base_output_dir=temp_dir)

        dataframes = {
            "data1": pd.DataFrame({"A": [1, 2, 3]}),
            "data2": pd.DataFrame({"B": [4, 5, 6]}),
            "data3": pd.DataFrame({"C": [7, 8, 9]}),
        }

        results = saver.batch_save(dataframes, file_format="csv")

        assert len(results) == 3
        # batch_save 返回的key包含扩展名
        for name in dataframes.keys():
            filename_with_ext = f"{name}.csv"
            assert results[filename_with_ext] is True
            file_path = Path(temp_dir) / f"{name}.csv"
            assert file_path.exists()

    def test_batch_save_with_subdirectory(self, temp_dir):
        """测试在子目录中批量保存"""
        saver = DataSaver(base_output_dir=temp_dir)

        dataframes = {"batch1": pd.DataFrame({"X": [1, 2]}), "batch2": pd.DataFrame({"Y": [3, 4]})}

        results = saver.batch_save(dataframes, subdirectory="batch_data")

        for name in dataframes.keys():
            filename_with_ext = f"{name}.csv"
            assert results[filename_with_ext] is True
            file_path = Path(temp_dir) / "batch_data" / f"{name}.csv"
            assert file_path.exists()

    def test_get_saved_files_info_basic(self, temp_dir, sample_dataframe):
        """测试获取保存文件信息"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 保存几个文件
        saver.save_data(sample_dataframe, "file1.csv")
        saver.save_data(sample_dataframe, "file2.json", file_format="json")

        files_info = saver.get_saved_files_info()

        assert isinstance(files_info, list)
        assert len(files_info) >= 2

        # 验证文件信息结构 - 根据实际实现调整
        for info in files_info:
            assert "filename" in info
            assert "size_mb" in info
            assert "created" in info  # 实际API使用'created'而不是'created_at'
            assert "path" in info  # 实际API使用'path'而不是'file_path'

    def test_get_saved_files_info_with_subdirectory(self, temp_dir, sample_dataframe):
        """测试获取子目录文件信息"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 在子目录中保存文件
        saver.save_data(sample_dataframe, "subfile.csv", subdirectory="subdir")

        files_info = saver.get_saved_files_info(subdirectory="subdir")

        assert isinstance(files_info, list)
        assert len(files_info) >= 1

    def test_get_saved_files_info_empty_directory(self, temp_dir):
        """测试空目录的文件信息"""
        saver = DataSaver(base_output_dir=temp_dir)
        files_info = saver.get_saved_files_info()

        assert isinstance(files_info, list)
        assert len(files_info) == 0

    def test_cleanup_old_files_basic(self, temp_dir, sample_dataframe):
        """测试清理旧文件基础功能"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 保存一个文件
        file_path = Path(temp_dir) / "old_file.csv"
        saver.save_data(sample_dataframe, "old_file.csv")

        # 修改文件时间为31天前
        old_time = datetime.now().timestamp() - (31 * 24 * 3600)
        os.utime(file_path, (old_time, old_time))

        # 清理30天前的文件
        deleted_count = saver.cleanup_old_files(days_old=30)

        assert deleted_count >= 1
        assert not file_path.exists()

    def test_cleanup_old_files_pattern(self, temp_dir, sample_dataframe):
        """测试按模式清理文件"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 保存不同类型的文件
        csv_file = Path(temp_dir) / "data.csv"
        json_file = Path(temp_dir) / "data.json"

        saver.save_data(sample_dataframe, "data.csv")
        saver.save_data(sample_dataframe, "data.json", file_format="json")

        # 设置为旧文件
        old_time = datetime.now().timestamp() - (31 * 24 * 3600)
        os.utime(csv_file, (old_time, old_time))
        os.utime(json_file, (old_time, old_time))

        # 只清理CSV文件
        deleted_count = saver.cleanup_old_files(days_old=30, file_pattern="*.csv")

        assert deleted_count >= 1
        assert not csv_file.exists()
        assert json_file.exists()  # JSON文件应该保留

    def test_cleanup_old_files_with_subdirectory(self, temp_dir, sample_dataframe):
        """测试清理子目录中的旧文件"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 在子目录中保存文件
        saver.save_data(sample_dataframe, "subfile.csv", subdirectory="cleanup_test")
        file_path = Path(temp_dir) / "cleanup_test" / "subfile.csv"

        # 设置为旧文件
        old_time = datetime.now().timestamp() - (31 * 24 * 3600)
        os.utime(file_path, (old_time, old_time))

        deleted_count = saver.cleanup_old_files(subdirectory="cleanup_test", days_old=30)

        assert deleted_count >= 1
        assert not file_path.exists()

    def test_cleanup_old_files_no_files(self, temp_dir):
        """测试清理无文件的情况"""
        saver = DataSaver(base_output_dir=temp_dir)
        deleted_count = saver.cleanup_old_files(days_old=30)

        assert deleted_count == 0

    def test_cleanup_with_metadata_files(self, temp_dir, sample_dataframe):
        """测试清理包含元数据的文件"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 保存带元数据的文件
        result = saver.save_data(sample_dataframe, "meta_test.csv", save_metadata=True)

        assert result is True  # 确保保存成功

        csv_file = Path(temp_dir) / "meta_test.csv"
        metadata_file = Path(temp_dir) / "meta_test.metadata.json"

        # 验证文件存在
        assert csv_file.exists()

        # 设置为旧文件
        old_time = datetime.now().timestamp() - (31 * 24 * 3600)
        os.utime(csv_file, (old_time, old_time))
        if metadata_file.exists():
            os.utime(metadata_file, (old_time, old_time))

        deleted_count = saver.cleanup_old_files(days_old=30)

        assert deleted_count >= 1
        assert not csv_file.exists()
        if metadata_file.exists():
            assert not metadata_file.exists()


class TestProcessedDataExporter:
    """处理数据导出器测试"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def ohlcv_data(self):
        """OHLCV数据fixture"""
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2023-01-01", periods=100, freq="h"),
                "open": np.random.rand(100) * 100 + 50,
                "high": np.random.rand(100) * 100 + 55,
                "low": np.random.rand(100) * 100 + 45,
                "close": np.random.rand(100) * 100 + 50,
                "volume": np.random.randint(1000, 10000, 100),
                "sma_20": np.random.rand(100) * 100 + 50,
                "rsi": np.random.rand(100) * 100,
            }
        )

    def test_exporter_init_default(self):
        """测试导出器默认初始化"""
        exporter = ProcessedDataExporter()
        assert isinstance(exporter.data_saver, DataSaver)

    def test_exporter_init_custom_saver(self, temp_dir):
        """测试导出器自定义保存器初始化"""
        custom_saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=custom_saver)
        assert exporter.data_saver is custom_saver

    def test_export_ohlcv_data_basic(self, temp_dir, ohlcv_data):
        """测试OHLCV数据导出基础功能"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        result = exporter.export_ohlcv_data(ohlcv_data, "BTCUSDT", "1h")

        assert result is True
        # 根据实际API，文件保存在ohlcv_data目录中
        expected_dir = Path(temp_dir) / "ohlcv_data"
        assert expected_dir.exists()
        # 文件名会包含时间戳
        files = list(expected_dir.glob("BTCUSDT_1h_ohlcv_with_indicators_*.csv"))
        assert len(files) >= 1

    def test_export_ohlcv_data_without_indicators(self, temp_dir, ohlcv_data):
        """测试不包含指标的OHLCV数据导出"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        result = exporter.export_ohlcv_data(ohlcv_data, "ETHUSDT", "4h", include_indicators=False)

        assert result is True
        expected_dir = Path(temp_dir) / "ohlcv_data"
        assert expected_dir.exists()
        files = list(expected_dir.glob("ETHUSDT_4h_ohlcv_*.csv"))
        assert len(files) >= 1

    def test_export_signals_data(self, temp_dir):
        """测试信号数据导出"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        signals_data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2023-01-01", periods=50, freq="h"),
                "signal": np.random.choice(["buy", "sell", "hold"], 50),
                "confidence": np.random.rand(50),
                "price": np.random.rand(50) * 100 + 50,
            }
        )

        result = exporter.export_signals_data(signals_data, "momentum_strategy")

        assert result is True
        # 根据实际API，文件保存在signals目录中
        expected_dir = Path(temp_dir) / "signals"
        assert expected_dir.exists()
        files = list(expected_dir.glob("momentum_strategy_signals_*.csv"))
        assert len(files) >= 1

    def test_export_backtest_results(self, temp_dir):
        """测试回测结果导出"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        # 创建包含各种数据类型的回测结果
        backtest_results = {
            "strategy_name": "test_strategy",
            "total_return": 0.15,
            "sharpe_ratio": 1.25,
            "max_drawdown": 0.08,
            "win_rate": 0.65,
            "trades": [
                {"entry_time": "2023-01-01", "exit_time": "2023-01-02", "pnl": 100},
                {"entry_time": "2023-01-03", "exit_time": "2023-01-04", "pnl": -50},
            ],
            "equity_curve": pd.Series([100000, 105000, 110000, 108000]),
            "metadata": {
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "parameters": {"fast_ma": 10, "slow_ma": 20},
            },
        }

        result = exporter.export_backtest_results(backtest_results, "test_strategy")

        assert result is True
        # 根据实际API，文件保存在backtest_results目录中
        expected_file = Path(temp_dir) / "backtest_results" / "test_strategy_backtest_results.json"
        assert expected_file.exists()

        # 验证JSON内容
        with open(expected_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["strategy_name"] == "test_strategy"
        assert saved_data["total_return"] == 0.15

    def test_make_serializable_pandas_series(self, temp_dir):
        """测试pandas Series序列化"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        series = pd.Series([1, 2, 3, 4, 5], name="test_series")
        result = exporter._make_serializable(series)

        # 根据实际实现，Series被转换为dict而不是list
        assert isinstance(result, dict)

    def test_make_serializable_pandas_dataframe(self, temp_dir):
        """测试pandas DataFrame序列化"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        result = exporter._make_serializable(df)

        assert isinstance(result, dict)
        assert "A" in result
        assert "B" in result

    def test_make_serializable_numpy_scalar(self, temp_dir):
        """测试numpy标量序列化"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        scalar = np.float64(3.14)
        result = exporter._make_serializable(scalar)

        # numpy.float64实际上被认为是基本类型(float)，所以返回原值
        assert isinstance(result, (float, np.float64))
        assert result == scalar

    def test_make_serializable_dict(self, temp_dir):
        """测试字典递归序列化"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        data = {"series": pd.Series([1, 2, 3]), "nested": {"scalar": np.int32(42)}}

        result = exporter._make_serializable(data)

        assert isinstance(result, dict)
        assert isinstance(result["series"], dict)  # Series转为dict
        assert isinstance(result["nested"]["scalar"], str)  # numpy标量转为str

    def test_make_serializable_list(self, temp_dir):
        """测试列表递归序列化"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        data = [pd.Series([1, 2]), np.float32(5.5)]

        result = exporter._make_serializable(data)

        assert isinstance(result, list)
        assert isinstance(result[0], dict)  # Series转为dict
        assert isinstance(result[1], str)  # numpy标量转为str

    def test_make_serializable_primitive_types(self, temp_dir):
        """测试基本类型序列化"""
        saver = DataSaver(base_output_dir=temp_dir)
        exporter = ProcessedDataExporter(data_saver=saver)

        # 测试已经可序列化的类型
        assert exporter._make_serializable(42) == 42
        assert exporter._make_serializable(3.14) == 3.14
        assert exporter._make_serializable("hello") == "hello"
        assert exporter._make_serializable(True) is True
        assert exporter._make_serializable(None) is None


class TestSaveProcessedDataFunction:
    """save_processed_data函数测试"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_data(self):
        """示例数据"""
        return pd.DataFrame({"value1": [1, 2, 3, 4, 5], "value2": [10, 20, 30, 40, 50]})

    def test_save_processed_data_csv(self, temp_dir, sample_data):
        """测试CSV格式保存"""
        output_path = os.path.join(temp_dir, "processed_data.csv")
        result = save_processed_data(sample_data, output_path, file_format="csv")

        assert result is True
        assert os.path.exists(output_path)

    def test_save_processed_data_pickle(self, temp_dir, sample_data):
        """测试Pickle格式保存"""
        output_path = os.path.join(temp_dir, "processed_data.pkl")
        result = save_processed_data(sample_data, output_path, file_format="pickle")

        assert result is True
        assert os.path.exists(output_path)

    def test_save_processed_data_with_kwargs(self, temp_dir, sample_data):
        """测试带额外参数的保存"""
        output_path = os.path.join(temp_dir, "processed_data.csv")
        result = save_processed_data(
            sample_data, output_path, file_format="csv", index=False, sep=";"
        )

        assert result is True
        assert os.path.exists(output_path)

        # 验证参数生效
        loaded_data = pd.read_csv(output_path, sep=";")
        assert len(loaded_data) == len(sample_data)

    def test_save_processed_data_exception(self, temp_dir, sample_data):
        """测试保存异常处理"""
        # 使用无效路径
        invalid_path = "/invalid/path/data.csv"
        result = save_processed_data(sample_data, invalid_path)

        assert result is False

    def test_save_processed_data_unsupported_format(self, temp_dir, sample_data):
        """测试不支持的格式"""
        output_path = os.path.join(temp_dir, "data.xyz")
        result = save_processed_data(sample_data, output_path, file_format="xyz")

        assert result is False


class TestEdgeCasesAndErrorHandling:
    """边缘情况和错误处理测试"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_save_empty_dataframe(self, temp_dir):
        """测试保存空DataFrame"""
        saver = DataSaver(base_output_dir=temp_dir)
        empty_df = pd.DataFrame()

        result = saver.save_data(empty_df, "empty.csv")
        assert result is True

        file_path = Path(temp_dir) / "empty.csv"
        assert file_path.exists()

    def test_save_large_dataframe(self, temp_dir):
        """测试保存大DataFrame"""
        saver = DataSaver(base_output_dir=temp_dir)

        # 创建较大的DataFrame
        large_df = pd.DataFrame({f"col_{i}": np.random.randn(1000) for i in range(50)})

        result = saver.save_data(large_df, "large.csv")
        assert result is True

    def test_unicode_in_data(self, temp_dir):
        """测试数据中的Unicode字符"""
        saver = DataSaver(base_output_dir=temp_dir)

        unicode_df = pd.DataFrame(
            {
                "chinese": ["你好", "世界", "测试"],
                "emoji": ["😀", "🚀", "💰"],
                "arabic": ["مرحبا", "العالم", "اختبار"],
            }
        )

        result = saver.save_data(unicode_df, "unicode_test.csv")
        assert result is True

        # 验证Unicode数据保存正确
        file_path = Path(temp_dir) / "unicode_test.csv"
        loaded_df = pd.read_csv(file_path, index_col=0)
        assert "你好" in loaded_df["chinese"].values

    def test_dataframe_with_complex_dtypes(self, temp_dir):
        """测试复杂数据类型的DataFrame"""
        saver = DataSaver(base_output_dir=temp_dir)

        complex_df = pd.DataFrame(
            {
                "integers": pd.array([1, 2, 3], dtype="Int64"),
                "floats": pd.array([1.1, 2.2, None], dtype="Float64"),
                "strings": pd.array(["a", "b", None], dtype="string"),
                "booleans": pd.array([True, False, None], dtype="boolean"),
                "categories": pd.Categorical(["X", "Y", "X"]),
                "datetime": pd.date_range("2023-01-01", periods=3),
            }
        )

        result = saver.save_data(complex_df, "complex_types.csv")
        assert result is True

    def test_concurrent_save_operations(self, temp_dir):
        """测试并发保存操作"""
        import threading

        saver = DataSaver(base_output_dir=temp_dir)
        results = []

        def save_operation(i):
            df = pd.DataFrame({"data": [i, i + 1, i + 2]})
            result = saver.save_data(df, f"concurrent_{i}.csv")
            results.append(result)

        # 创建多个线程并发保存
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有操作都成功
        assert all(results)
        assert len(results) == 5
