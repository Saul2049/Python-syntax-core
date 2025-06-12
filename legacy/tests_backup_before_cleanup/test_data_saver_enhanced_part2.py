#!/usr/bin/env python3
"""
🧪 数据保存器增强测试 - 第二部分 (Data Saver Enhanced Tests - Part 2)

继续覆盖data_saver.py的ProcessedDataExporter类和便捷函数
"""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

import pandas as pd

from src.data.validators.data_saver import DataSaver, ProcessedDataExporter, save_processed_data


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
            },
            index=pd.date_range("2023-01-01", periods=3),
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

    def test_export_ohlcv_data_different_symbols(self):
        """测试不同交易对的OHLCV数据导出"""
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

        for symbol in symbols:
            result = self.exporter.export_ohlcv_data(self.ohlcv_df, symbol, "1d")
            self.assertTrue(result)

        # 检查所有文件都被创建
        ohlcv_dir = self.data_saver.base_output_dir / "ohlcv_data"
        for symbol in symbols:
            files = list(ohlcv_dir.glob(f"{symbol}_1d_ohlcv_*.csv"))
            self.assertEqual(len(files), 1)

    @patch("builtins.print")
    def test_export_ohlcv_data_save_failure(self, mock_print):
        """测试OHLCV数据保存失败"""
        # Mock save_data to return False
        with patch.object(self.data_saver, "save_data", return_value=False):
            result = self.exporter.export_ohlcv_data(self.ohlcv_df, "BTCUSDT", "1h")
            self.assertFalse(result)


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
            },
            index=pd.date_range("2023-01-01", periods=3),
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

    def test_export_signals_data_different_strategies(self):
        """测试不同策略的信号数据导出"""
        strategies = ["rsi_strategy", "macd_strategy", "bollinger_strategy"]

        for strategy in strategies:
            result = self.exporter.export_signals_data(self.signals_df, strategy)
            self.assertTrue(result)

        # 检查所有文件都被创建
        signals_dir = self.data_saver.base_output_dir / "signals"
        for strategy in strategies:
            files = list(signals_dir.glob(f"{strategy}_signals_*.csv"))
            self.assertEqual(len(files), 1)

    def test_export_signals_data_empty_dataframe(self):
        """测试空DataFrame的信号导出"""
        empty_df = pd.DataFrame()
        result = self.exporter.export_signals_data(empty_df, "empty_strategy")
        self.assertTrue(result)  # 应该仍然能够保存空文件


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
            "initial_capital": 10000,
            "final_capital": 11500,
            "trades": [
                {"date": "2023-01-01", "action": "BUY", "price": 100.0},
                {"date": "2023-01-02", "action": "SELL", "price": 105.0},
            ],
            "performance_metrics": {"volatility": 0.18, "sortino_ratio": 1.5},
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

        # 验证文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data["strategy_name"], "test_strategy")
        self.assertEqual(loaded_data["total_return"], 0.15)
        self.assertIn("trades", loaded_data)

    def test_export_backtest_results_with_pandas_data(self):
        """测试包含Pandas对象的回测结果导出"""
        # 添加Pandas对象到结果中
        results_with_pandas = self.backtest_results.copy()
        results_with_pandas["equity_curve"] = pd.Series([10000, 10500, 11000])
        results_with_pandas["drawdown_series"] = pd.DataFrame({"drawdown": [-0.01, -0.03, -0.02]})
        results_with_pandas["timestamp"] = pd.Timestamp("2023-01-01")
        results_with_pandas["datetime_obj"] = datetime(2023, 1, 1)

        result = self.exporter.export_backtest_results(results_with_pandas, "pandas_strategy")
        self.assertTrue(result)

        # 验证序列化后的数据
        backtest_dir = self.data_saver.base_output_dir / "backtest_results"
        file_path = backtest_dir / "pandas_strategy_backtest_results.json"

        with open(file_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        # Pandas对象应该被转换为字典/列表
        self.assertIsInstance(loaded_data["equity_curve"], dict)
        self.assertIsInstance(loaded_data["drawdown_series"], dict)
        self.assertIsInstance(loaded_data["timestamp"], str)
        self.assertIsInstance(loaded_data["datetime_obj"], str)

    @patch("builtins.print")
    def test_export_backtest_results_exception(self, mock_print):
        """测试回测结果导出异常处理"""
        # Mock open to raise exception
        with patch("builtins.open", side_effect=Exception("Permission denied")):
            result = self.exporter.export_backtest_results(
                self.backtest_results, "failing_strategy"
            )
            self.assertFalse(result)
            mock_print.assert_called()

    def test_export_backtest_results_complex_nested_data(self):
        """测试复杂嵌套数据的回测结果导出"""
        complex_results = {
            "nested_dict": {"level1": {"level2": [1, 2, 3], "pandas_series": pd.Series([4, 5, 6])}},
            "list_of_dicts": [
                {"a": 1, "b": pd.Timestamp("2023-01-01")},
                {"a": 2, "b": pd.Timestamp("2023-01-02")},
            ],
            "mixed_types": [1, "string", True, None, 3.14],
        }

        result = self.exporter.export_backtest_results(complex_results, "complex_strategy")
        self.assertTrue(result)


class TestMakeSerializableFunction(unittest.TestCase):
    """测试_make_serializable函数"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.data_saver = DataSaver(self.temp_dir)
        self.exporter = ProcessedDataExporter(self.data_saver)

    def test_make_serializable_basic_types(self):
        """测试基本类型序列化"""
        # 基本类型应该保持不变
        self.assertEqual(self.exporter._make_serializable(42), 42)
        self.assertEqual(self.exporter._make_serializable(3.14), 3.14)
        self.assertEqual(self.exporter._make_serializable("hello"), "hello")
        self.assertEqual(self.exporter._make_serializable(True), True)
        self.assertEqual(self.exporter._make_serializable(None), None)

    def test_make_serializable_dict(self):
        """测试字典序列化"""
        input_dict = {"int": 1, "str": "test", "series": pd.Series([1, 2, 3])}

        result = self.exporter._make_serializable(input_dict)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["int"], 1)
        self.assertEqual(result["str"], "test")
        self.assertIsInstance(result["series"], dict)  # Series转换为dict

    def test_make_serializable_list(self):
        """测试列表序列化"""
        input_list = [1, "test", pd.Series([1, 2, 3]), pd.Timestamp("2023-01-01")]

        result = self.exporter._make_serializable(input_list)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], 1)
        self.assertEqual(result[1], "test")
        self.assertIsInstance(result[2], dict)  # Series转换为dict
        self.assertIsInstance(result[3], str)  # Timestamp转换为str

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
        self.assertEqual(result, timestamp.isoformat())

    def test_make_serializable_datetime(self):
        """测试datetime对象序列化"""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = self.exporter._make_serializable(dt)
        self.assertIsInstance(result, str)
        self.assertEqual(result, dt.isoformat())

    def test_make_serializable_custom_object(self):
        """测试自定义对象序列化"""

        class CustomObject:
            def __init__(self, value):
                self.value = value

            def __str__(self):
                return f"CustomObject({self.value})"

        obj = CustomObject(42)
        result = self.exporter._make_serializable(obj)
        self.assertEqual(result, "CustomObject(42)")

    def test_make_serializable_nested_structure(self):
        """测试嵌套结构序列化"""
        nested_data = {
            "level1": {
                "level2": {
                    "series": pd.Series([1, 2, 3]),
                    "timestamp": pd.Timestamp("2023-01-01"),
                    "list": [pd.DataFrame({"a": [1]}), datetime(2023, 1, 1)],
                }
            }
        }

        result = self.exporter._make_serializable(nested_data)

        # 验证深层嵌套的序列化
        level2 = result["level1"]["level2"]
        self.assertIsInstance(level2["series"], dict)
        self.assertIsInstance(level2["timestamp"], str)
        self.assertIsInstance(level2["list"][0], dict)  # DataFrame -> dict
        self.assertIsInstance(level2["list"][1], str)  # datetime -> str


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

        # 验证数据内容
        loaded_df = pd.read_csv(output_path, index_col=0)
        self.assertEqual(len(loaded_df), 3)

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
        result = save_processed_data(self.test_df, "xyz")

        self.assertFalse(result)

    def test_save_processed_data_with_kwargs(self):
        """测试带额外参数的保存"""
        output_path = os.path.join(self.temp_dir, "test.csv")
        result = save_processed_data(
            self.test_df, output_path, "csv", index=False, encoding="utf-8"
        )

        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_path))

    def test_save_processed_data_directory_creation(self):
        """测试目录自动创建"""
        nested_path = os.path.join(self.temp_dir, "nested", "deep", "test.csv")
        result = save_processed_data(self.test_df, nested_path, "csv")

        self.assertTrue(result)
        self.assertTrue(os.path.exists(nested_path))
        self.assertTrue(os.path.exists(os.path.dirname(nested_path)))

    @patch("builtins.print")
    def test_save_processed_data_exception(self, mock_print):
        """测试异常处理"""
        # 使用无效路径触发异常
        invalid_path = "/invalid/path/test.csv"
        result = save_processed_data(self.test_df, invalid_path, "csv")

        self.assertFalse(result)
        mock_print.assert_called()

    @patch("pandas.DataFrame.to_csv")
    @patch("builtins.print")
    def test_save_processed_data_save_exception(self, mock_print, mock_to_csv):
        """测试保存时的异常处理"""
        mock_to_csv.side_effect = Exception("Save failed")

        output_path = os.path.join(self.temp_dir, "test.csv")
        result = save_processed_data(self.test_df, output_path, "csv")

        self.assertFalse(result)
        mock_print.assert_called()


if __name__ == "__main__":
    unittest.main()
