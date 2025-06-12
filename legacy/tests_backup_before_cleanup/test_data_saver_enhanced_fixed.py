#!/usr/bin/env python3
"""
🧪 数据保存器增强测试 - 修复版本 (Data Saver Enhanced Tests - Fixed)

解决JSON保存和元数据问题，目标从30%提升到75%+覆盖率
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.data.validators.data_saver import DataSaver, ProcessedDataExporter, save_processed_data


class TestDataSaverInitialization(unittest.TestCase):
    """测试DataSaver初始化"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def test_init_with_default_dir(self):
        """测试默认目录初始化"""
        saver = DataSaver()
        self.assertEqual(saver.base_output_dir, Path("output"))
        self.assertTrue(saver.base_output_dir.exists())

    def test_init_with_custom_dir_string(self):
        """测试自定义目录字符串初始化"""
        saver = DataSaver(self.temp_dir)
        self.assertEqual(saver.base_output_dir, Path(self.temp_dir))
        self.assertTrue(saver.base_output_dir.exists())

    def test_init_with_custom_dir_path(self):
        """测试自定义目录Path对象初始化"""
        custom_path = Path(self.temp_dir) / "custom"
        saver = DataSaver(custom_path)
        self.assertEqual(saver.base_output_dir, custom_path)
        self.assertTrue(saver.base_output_dir.exists())


class TestDataSaverBasicSaving(unittest.TestCase):
    """测试DataSaver基本保存功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.saver = DataSaver(self.temp_dir)

        # 创建简单的测试数据（避免复杂类型）
        self.test_df = pd.DataFrame(
            {
                "price": [100.0, 200.0, 300.0],
                "volume": [1000, 2000, 3000],
                "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            }
        )

    def test_save_data_csv_success(self):
        """测试CSV格式保存成功"""
        result = self.saver.save_data(self.test_df, "test.csv", "csv")
        self.assertTrue(result)

        file_path = self.saver.base_output_dir / "test.csv"
        self.assertTrue(file_path.exists())

        # 验证数据内容
        loaded_df = pd.read_csv(file_path, index_col=0)
        self.assertEqual(len(loaded_df), 3)

    def test_save_data_with_subdirectory(self):
        """测试在子目录中保存"""
        result = self.saver.save_data(self.test_df, "test.csv", "csv", "subdir")
        self.assertTrue(result)

        file_path = self.saver.base_output_dir / "subdir" / "test.csv"
        self.assertTrue(file_path.exists())

    def test_save_data_with_timestamp(self):
        """测试带时间戳的保存"""
        result = self.saver.save_data(self.test_df, "test.csv", "csv", add_timestamp=True)
        self.assertTrue(result)

        # 检查是否有带时间戳的文件
        files = list(self.saver.base_output_dir.glob("test_*.csv"))
        self.assertEqual(len(files), 1)

    def test_save_data_without_metadata(self):
        """测试不保存元数据"""
        result = self.saver.save_data(self.test_df, "test.csv", "csv", save_metadata=False)
        self.assertTrue(result)

        # 检查元数据文件不存在
        metadata_path = self.saver.base_output_dir / "test.csv.metadata.json"
        self.assertFalse(metadata_path.exists())

    def test_save_data_parquet_format(self):
        """测试Parquet格式保存"""
        result = self.saver.save_data(self.test_df, "test.parquet", "parquet")
        self.assertTrue(result)

        file_path = self.saver.base_output_dir / "test.parquet"
        self.assertTrue(file_path.exists())

    def test_save_data_pickle_format(self):
        """测试Pickle格式保存"""
        result = self.saver.save_data(self.test_df, "test.pkl", "pickle")
        self.assertTrue(result)

        file_path = self.saver.base_output_dir / "test.pkl"
        self.assertTrue(file_path.exists())

    def test_save_data_json_format(self):
        """测试JSON格式保存（使用简单数据）"""
        simple_df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = self.saver.save_data(simple_df, "test.json", "json")
        self.assertTrue(result)

        file_path = self.saver.base_output_dir / "test.json"
        self.assertTrue(file_path.exists())

    def test_save_data_excel_format(self):
        """测试Excel格式保存"""
        result = self.saver.save_data(self.test_df, "test.xlsx", "excel")
        self.assertTrue(result)

        file_path = self.saver.base_output_dir / "test.xlsx"
        self.assertTrue(file_path.exists())

    def test_save_data_unsupported_format(self):
        """测试不支持的格式"""
        result = self.saver.save_data(self.test_df, "test.xyz", "xyz")
        self.assertFalse(result)

    @patch("builtins.print")
    def test_save_data_exception_handling(self, mock_print):
        """测试异常处理"""
        # 创建无效的DataFrame以触发异常
        invalid_df = None
        result = self.saver.save_data(invalid_df, "test.csv", "csv")
        self.assertFalse(result)

        # 验证错误消息被打印
        mock_print.assert_called()


class TestDataSaverFormatHandling(unittest.TestCase):
    """测试DataSaver格式处理"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.saver = DataSaver(self.temp_dir)
        self.test_df = pd.DataFrame({"col1": [1, 2, 3]})

    def test_is_supported_format_valid(self):
        """测试有效格式检查"""
        self.assertTrue(self.saver._is_supported_format("csv"))
        self.assertTrue(self.saver._is_supported_format("parquet"))
        self.assertTrue(self.saver._is_supported_format("pickle"))
        self.assertTrue(self.saver._is_supported_format("json"))
        self.assertTrue(self.saver._is_supported_format("excel"))
        self.assertTrue(self.saver._is_supported_format("xlsx"))
        self.assertTrue(self.saver._is_supported_format("hdf5"))

    def test_is_supported_format_invalid(self):
        """测试无效格式检查"""
        self.assertFalse(self.saver._is_supported_format("xyz"))
        self.assertFalse(self.saver._is_supported_format(""))

    def test_execute_save_operation_csv(self):
        """测试CSV保存操作"""
        file_path = Path(self.temp_dir) / "test.csv"
        self.saver._execute_save_operation(self.test_df, file_path, "csv")
        self.assertTrue(file_path.exists())

    def test_execute_save_operation_hdf5(self):
        """测试HDF5保存操作"""
        file_path = Path(self.temp_dir) / "test.h5"
        self.saver._execute_save_operation(self.test_df, file_path, "hdf5", key="data")
        self.assertTrue(file_path.exists())

    @patch("builtins.print")
    def test_save_by_format_exception(self, mock_print):
        """测试格式保存异常处理"""
        file_path = Path(self.temp_dir) / "test.csv"

        # 使用无效的DataFrame来触发异常
        with patch.object(self.test_df, "to_csv", side_effect=Exception("Test error")):
            result = self.saver._save_by_format(self.test_df, file_path, "csv")
            self.assertFalse(result)
            mock_print.assert_called()


class TestDataSaverBackupFunctionality(unittest.TestCase):
    """测试DataSaver备份功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.saver = DataSaver(self.temp_dir)
        self.test_df = pd.DataFrame({"col1": [1, 2, 3]})

    def test_create_backup_success(self):
        """测试成功创建备份"""
        # 先创建一个文件
        file_path = Path(self.temp_dir) / "test.csv"
        self.test_df.to_csv(file_path)

        # 创建备份
        self.saver._create_backup(file_path)

        # 检查备份目录和文件
        backup_dir = file_path.parent / "backups"
        self.assertTrue(backup_dir.exists())

        backup_files = list(backup_dir.glob("test_*.csv"))
        self.assertEqual(len(backup_files), 1)

    @patch("builtins.print")
    def test_create_backup_exception(self, mock_print):
        """测试备份创建异常"""
        # 使用不存在的文件
        non_existent_file = Path(self.temp_dir) / "non_existent.csv"
        self.saver._create_backup(non_existent_file)

        # 验证异常处理消息
        mock_print.assert_called()

    def test_save_data_with_backup(self):
        """测试带备份的保存"""
        # 先创建一个文件
        self.saver.save_data(self.test_df, "test.csv", "csv")

        # 修改数据并保存，启用备份
        modified_df = pd.DataFrame({"col1": [4, 5, 6]})
        result = self.saver.save_data(modified_df, "test.csv", "csv", create_backup=True)
        self.assertTrue(result)

        # 检查备份是否创建
        backup_dir = self.saver.base_output_dir / "backups"
        self.assertTrue(backup_dir.exists())


class TestDataSaverMetadata(unittest.TestCase):
    """测试DataSaver元数据功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.saver = DataSaver(self.temp_dir)

        # 创建包含明确数据类型的测试数据
        self.test_df = pd.DataFrame(
            {
                "int_col": pd.Series([1, 2, 3], dtype="int64"),
                "float_col": pd.Series([1.1, 2.2, 3.3], dtype="float64"),
                "str_col": pd.Series(["a", "b", "c"], dtype="string"),
                "bool_col": pd.Series([True, False, True], dtype="bool"),
            }
        )

    def test_save_metadata_success(self):
        """测试成功保存元数据"""
        file_path = self.saver.base_output_dir / "test.csv"
        self.saver._save_metadata(self.test_df, file_path)

        metadata_path = file_path.with_suffix(".csv.metadata.json")
        self.assertTrue(metadata_path.exists())

        # 验证元数据内容
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        self.assertIn("filename", metadata)
        self.assertIn("created_at", metadata)
        self.assertIn("shape", metadata)
        self.assertIn("columns", metadata)
        self.assertIn("dtypes", metadata)
        self.assertIn("memory_usage_mb", metadata)

        self.assertEqual(metadata["shape"], [4, 4])  # 4 rows, 4 columns
        self.assertEqual(len(metadata["columns"]), 4)

    @patch("builtins.print")
    def test_save_metadata_exception(self, mock_print):
        """测试元数据保存异常处理"""
        file_path = Path("/invalid/path/test.csv")
        self.saver._save_metadata(self.test_df, file_path)

        # 验证异常处理消息
        mock_print.assert_called()


class TestDataSaverAdvancedFeatures(unittest.TestCase):
    """测试DataSaver高级功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.saver = DataSaver(self.temp_dir)
        self.test_df = pd.DataFrame({"col1": [1, 2, 3]})

    def test_save_multiple_formats(self):
        """测试多格式保存（避免JSON）"""
        formats = ["csv", "pickle", "parquet"]
        results = self.saver.save_multiple_formats(self.test_df, "test", formats)

        self.assertEqual(len(results), 3)
        for fmt in formats:
            self.assertTrue(results[fmt])

        # 验证文件存在
        self.assertTrue((self.saver.base_output_dir / "test.csv").exists())
        self.assertTrue((self.saver.base_output_dir / "test.pickle").exists())
        self.assertTrue((self.saver.base_output_dir / "test.parquet").exists())

    def test_save_multiple_formats_with_excel(self):
        """测试包含Excel的多格式保存"""
        formats = ["csv", "excel"]
        results = self.saver.save_multiple_formats(self.test_df, "test", formats)

        self.assertTrue(results["excel"])
        self.assertTrue((self.saver.base_output_dir / "test.xlsx").exists())

    def test_batch_save(self):
        """测试批量保存"""
        dataframes = {
            "df1": pd.DataFrame({"a": [1, 2]}),
            "df2": pd.DataFrame({"b": [3, 4]}),
            "df3.csv": pd.DataFrame({"c": [5, 6]}),  # 已有扩展名
        }

        results = self.saver.batch_save(dataframes, "csv")

        self.assertEqual(len(results), 3)
        self.assertTrue(all(results.values()))

        # 验证文件存在
        self.assertTrue((self.saver.base_output_dir / "df1.csv").exists())
        self.assertTrue((self.saver.base_output_dir / "df2.csv").exists())
        self.assertTrue((self.saver.base_output_dir / "df3.csv").exists())

    def test_get_saved_files_info_empty_directory(self):
        """测试空目录的文件信息获取"""
        info = self.saver.get_saved_files_info()
        self.assertEqual(len(info), 0)

    def test_get_saved_files_info_non_existent_directory(self):
        """测试不存在目录的文件信息获取"""
        info = self.saver.get_saved_files_info("non_existent")
        self.assertEqual(len(info), 0)

    def test_get_saved_files_info_with_files(self):
        """测试有文件时的信息获取"""
        # 创建一些文件（只保存到CSV）
        self.saver.save_data(self.test_df, "test1.csv", "csv")
        self.saver.save_data(self.test_df, "test2.csv", "csv")

        info = self.saver.get_saved_files_info()
        self.assertGreaterEqual(len(info), 2)

        # 检查信息字段
        for file_info in info:
            self.assertIn("filename", file_info)
            self.assertIn("path", file_info)
            self.assertIn("size_mb", file_info)
            self.assertIn("created", file_info)
            self.assertIn("modified", file_info)
            self.assertIn("extension", file_info)

    @patch("builtins.print")
    def test_get_saved_files_info_file_stat_exception(self, mock_print):
        """测试文件状态获取异常处理"""
        # 创建文件
        self.saver.save_data(self.test_df, "test.csv", "csv")

        # Mock file iteration to raise exception for specific files
        original_iterdir = Path.iterdir

        def mock_iterdir(self):
            for item in original_iterdir(self):
                if item.name == "test.csv":
                    # Mock stat method for this specific file
                    with patch.object(item, "stat", side_effect=Exception("Permission denied")):
                        yield item
                else:
                    yield item

        with patch.object(Path, "iterdir", mock_iterdir):
            info = self.saver.get_saved_files_info()
            # 应该跳过异常文件但不影响其他文件
            mock_print.assert_called()


class TestDataSaverCleanup(unittest.TestCase):
    """测试DataSaver清理功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.saver = DataSaver(self.temp_dir)
        self.test_df = pd.DataFrame({"col1": [1, 2, 3]})

    def test_cleanup_old_files_no_directory(self):
        """测试清理不存在的目录"""
        count = self.saver.cleanup_old_files("non_existent")
        self.assertEqual(count, 0)

    def test_cleanup_old_files_no_old_files(self):
        """测试清理无旧文件的情况"""
        # 创建新文件
        self.saver.save_data(self.test_df, "test.csv", "csv")

        # 尝试清理1天前的文件（应该没有）
        count = self.saver.cleanup_old_files(days_old=1)
        self.assertEqual(count, 0)

    @patch("time.time")
    def test_cleanup_old_files_with_old_files(self, mock_time):
        """测试清理旧文件"""
        # 设置当前时间
        current_time = 1000000
        mock_time.return_value = current_time

        # 创建文件
        file_path = self.saver.base_output_dir / "old_file.csv"
        self.test_df.to_csv(file_path)

        # 修改文件的修改时间为30天前
        old_time = current_time - (31 * 24 * 60 * 60)  # 31天前
        os.utime(file_path, (old_time, old_time))

        # 清理30天前的文件
        count = self.saver.cleanup_old_files(days_old=30)
        self.assertEqual(count, 1)
        self.assertFalse(file_path.exists())

    def test_get_search_directory(self):
        """测试获取搜索目录"""
        # 无子目录
        search_dir = self.saver._get_search_directory(None)
        self.assertEqual(search_dir, self.saver.base_output_dir)

        # 有子目录
        search_dir = self.saver._get_search_directory("subdir")
        self.assertEqual(search_dir, self.saver.base_output_dir / "subdir")

    def test_calculate_cutoff_time(self):
        """测试计算截止时间"""
        with patch("time.time", return_value=1000000):
            cutoff = self.saver._calculate_cutoff_time(30)
            expected = 1000000 - (30 * 24 * 60 * 60)
            self.assertEqual(cutoff, expected)

    def test_delete_file_and_metadata(self):
        """测试删除文件和元数据"""
        # 创建文件和元数据
        file_path = self.saver.base_output_dir / "test.csv"
        metadata_path = file_path.with_suffix(".csv.metadata.json")

        self.test_df.to_csv(file_path)
        with open(metadata_path, "w") as f:
            json.dump({"test": "data"}, f)

        # 删除
        self.saver._delete_file_and_metadata(file_path)

        # 验证都被删除
        self.assertFalse(file_path.exists())
        self.assertFalse(metadata_path.exists())

    @patch("builtins.print")
    def test_cleanup_old_files_exception(self, mock_print):
        """测试清理文件异常处理"""
        # Mock glob to raise exception
        with patch("pathlib.Path.glob", side_effect=Exception("Permission denied")):
            count = self.saver.cleanup_old_files()
            self.assertEqual(count, 0)
            mock_print.assert_called()


# ProcessedDataExporter测试类
class TestProcessedDataExporterInitialization(unittest.TestCase):
    """测试ProcessedDataExporter初始化"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def test_init_with_default_data_saver(self):
        """测试默认DataSaver初始化"""
        exporter = ProcessedDataExporter()
        self.assertIsInstance(exporter.data_saver, DataSaver)

    def test_init_with_custom_data_saver(self):
        """测试自定义DataSaver初始化"""
        custom_saver = DataSaver(self.temp_dir)
        exporter = ProcessedDataExporter(custom_saver)
        self.assertEqual(exporter.data_saver, custom_saver)


class TestProcessedDataExporterOHLCV(unittest.TestCase):
    """测试ProcessedDataExporter OHLCV导出功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.data_saver = DataSaver(self.temp_dir)
        self.exporter = ProcessedDataExporter(self.data_saver)

        # 创建OHLCV测试数据
        self.ohlcv_df = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [105.0, 106.0, 107.0],
                "low": [99.0, 100.0, 101.0],
                "close": [104.0, 105.0, 106.0],
                "volume": [1000, 1100, 1200],
                "sma_20": [102.0, 103.0, 104.0],  # 技术指标
                "rsi": [50.0, 55.0, 60.0],
            }
        )

    def test_export_ohlcv_data_basic(self):
        """测试基本OHLCV数据导出"""
        result = self.exporter.export_ohlcv_data(
            self.ohlcv_df, "BTCUSDT", "1h", include_indicators=True
        )
        self.assertTrue(result)

        # 检查文件是否存在
        ohlcv_dir = self.data_saver.base_output_dir / "ohlcv_data"
        self.assertTrue(ohlcv_dir.exists())

        # 检查是否有文件（带时间戳）
        files = list(ohlcv_dir.glob("BTCUSDT_1h_ohlcv_with_indicators_*.csv"))
        self.assertEqual(len(files), 1)

    def test_export_ohlcv_data_without_indicators(self):
        """测试不包含技术指标的OHLCV数据导出"""
        result = self.exporter.export_ohlcv_data(
            self.ohlcv_df, "ETHUSDT", "4h", include_indicators=False
        )
        self.assertTrue(result)

        # 检查文件名格式
        ohlcv_dir = self.data_saver.base_output_dir / "ohlcv_data"
        files = list(ohlcv_dir.glob("ETHUSDT_4h_ohlcv_*.csv"))
        self.assertEqual(len(files), 1)

        # 文件名不应包含"with_indicators"
        filename = files[0].name
        self.assertNotIn("with_indicators", filename)


class TestProcessedDataExporterSignals(unittest.TestCase):
    """测试ProcessedDataExporter信号导出功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.data_saver = DataSaver(self.temp_dir)
        self.exporter = ProcessedDataExporter(self.data_saver)

        # 创建信号测试数据
        self.signals_df = pd.DataFrame(
            {
                "signal": ["BUY", "HOLD", "SELL"],
                "strength": [0.8, 0.2, 0.9],
                "confidence": [0.9, 0.5, 0.85],
                "price": [100.0, 101.0, 99.0],
            }
        )

    def test_export_signals_data_success(self):
        """测试成功导出信号数据"""
        result = self.exporter.export_signals_data(self.signals_df, "momentum_strategy")
        self.assertTrue(result)

        # 检查文件是否存在
        signals_dir = self.data_saver.base_output_dir / "signals"
        self.assertTrue(signals_dir.exists())

        # 检查是否有文件（带时间戳）
        files = list(signals_dir.glob("momentum_strategy_signals_*.csv"))
        self.assertEqual(len(files), 1)


class TestProcessedDataExporterBacktest(unittest.TestCase):
    """测试ProcessedDataExporter回测结果导出功能"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.data_saver = DataSaver(self.temp_dir)
        self.exporter = ProcessedDataExporter(self.data_saver)

        # 创建回测结果测试数据
        self.backtest_results = {
            "strategy_name": "test_strategy",
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.05,
            "win_rate": 0.65,
            "total_trades": 100,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
        }

    def test_export_backtest_results_success(self):
        """测试成功导出回测结果"""
        result = self.exporter.export_backtest_results(self.backtest_results, "momentum_strategy")
        self.assertTrue(result)

        # 检查文件是否存在
        backtest_dir = self.data_saver.base_output_dir / "backtest_results"
        self.assertTrue(backtest_dir.exists())

        file_path = backtest_dir / "momentum_strategy_backtest_results.json"
        self.assertTrue(file_path.exists())

    def test_make_serializable_basic_types(self):
        """测试基本类型序列化"""
        # 基本类型应该保持不变
        self.assertEqual(self.exporter._make_serializable(42), 42)
        self.assertEqual(self.exporter._make_serializable(3.14), 3.14)
        self.assertEqual(self.exporter._make_serializable("hello"), "hello")
        self.assertEqual(self.exporter._make_serializable(True), True)
        self.assertEqual(self.exporter._make_serializable(None), None)

    def test_make_serializable_pandas_objects(self):
        """测试Pandas对象序列化"""
        # Series
        series = pd.Series([1, 2, 3], name="test_series")
        result = self.exporter._make_serializable(series)
        self.assertIsInstance(result, dict)

        # DataFrame
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        result = self.exporter._make_serializable(df)
        self.assertIsInstance(result, dict)

        # Timestamp
        timestamp = pd.Timestamp("2023-01-01 12:00:00")
        result = self.exporter._make_serializable(timestamp)
        self.assertIsInstance(result, str)


class TestSaveProcessedDataFunction(unittest.TestCase):
    """测试save_processed_data便捷函数"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

        # 创建测试数据
        self.test_df = pd.DataFrame({"price": [100.0, 200.0, 300.0], "volume": [1000, 2000, 3000]})

    def test_save_processed_data_csv(self):
        """测试CSV格式保存"""
        output_path = os.path.join(self.temp_dir, "test.csv")
        result = save_processed_data(self.test_df, output_path, "csv")

        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    def test_save_processed_data_pickle(self):
        """测试Pickle格式保存"""
        output_path = os.path.join(self.temp_dir, "test.pkl")
        result = save_processed_data(self.test_df, output_path, "pickle")

        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    def test_save_processed_data_parquet(self):
        """测试Parquet格式保存"""
        output_path = os.path.join(self.temp_dir, "test.parquet")
        result = save_processed_data(self.test_df, output_path, "parquet")

        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    def test_save_processed_data_unsupported_format(self):
        """测试不支持的格式"""
        output_path = os.path.join(self.temp_dir, "test.xyz")
        result = save_processed_data(self.test_df, output_path, "xyz")

        self.assertFalse(result)

    @patch("builtins.print")
    def test_save_processed_data_exception(self, mock_print):
        """测试异常处理"""
        # 使用无效路径触发异常
        invalid_path = "/invalid/path/test.csv"
        result = save_processed_data(self.test_df, invalid_path, "csv")

        self.assertFalse(result)
        mock_print.assert_called()


if __name__ == "__main__":
    unittest.main()
