#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳定性测试模块测试
Stability Test Module Tests
"""

import datetime
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

# 导入要测试的模块
try:
    # 导入需要模拟的依赖
    from scripts.market_data import MarketDataManager
    from scripts.stability_test import StabilityTest
except ImportError:
    pytest.skip("稳定性测试模块不可用，跳过测试", allow_module_level=True)


class TestStabilityTest(unittest.TestCase):
    """测试稳定性测试类"""

    @patch("scripts.stability_test.get_config")
    @patch("scripts.stability_test.create_market_data_manager")
    @patch("scripts.stability_test.setup_logging")
    def setUp(self, mock_setup_logging, mock_create_mdm, mock_get_config):
        """设置测试环境"""
        # 配置模拟对象
        self.mock_config = MagicMock()
        self.mock_config.get_symbols.return_value = ["BTC/USDT", "ETH/USDT"]
        self.mock_config.get_check_interval.return_value = 10
        self.mock_config.is_test_mode.return_value = True
        self.mock_config.get_risk_percent.return_value = 0.5
        self.mock_config.use_binance_testnet.return_value = True

        # 创建临时目录作为日志目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.mock_config.get_log_dir.return_value = self.temp_dir.name

        mock_get_config.return_value = self.mock_config

        # 模拟市场数据管理器
        self.mock_mdm = MagicMock(spec=MarketDataManager)
        self.mock_mdm.get_current_provider_name.return_value = "MockMarket"
        mock_create_mdm.return_value = self.mock_mdm

        # 初始化被测类
        self.stability_test = StabilityTest(
            symbols=["BTC/USDT", "ETH/USDT"],
            duration_days=0.01,  # 非常短的测试持续时间
            check_interval=0.01,  # 非常短的检查间隔
            test_mode=True,
        )

        # 禁用监控以避免实际的网络服务启动
        self.stability_test.exporter = None

    def tearDown(self):
        """清理测试环境"""
        self.temp_dir.cleanup()

    def test_init(self):
        """测试初始化"""
        # 验证参数传递和配置
        self.assertEqual(self.stability_test.symbols, ["BTC/USDT", "ETH/USDT"])
        self.assertEqual(self.stability_test.duration_seconds, 0.01 * 24 * 60 * 60)
        self.assertEqual(self.stability_test.check_interval, 0.01)
        self.assertTrue(self.stability_test.test_mode)

        # 验证统计数据初始化
        self.assertIsNone(self.stability_test.stats["start_time"])
        self.assertEqual(self.stability_test.stats["total_signals"], 0)
        self.assertEqual(self.stability_test.stats["errors"], 0)
        self.assertEqual(self.stability_test.stats["data_interruptions"], 0)
        self.assertEqual(self.stability_test.stats["reconnections"], 0)
        self.assertEqual(self.stability_test.stats["data_source_switches"], 0)
        self.assertEqual(self.stability_test.stats["memory_usage"], [])

    @patch("scripts.stability_test.MarketSimulator")
    @patch("scripts.stability_test.TradingLoop")
    def test_setup_trading_system(self, mock_trading_loop, mock_market_simulator):
        """测试设置交易系统组件"""
        # 配置模拟对象
        mock_market = MagicMock()
        mock_market_simulator.return_value = mock_market

        mock_loop = MagicMock()
        mock_trading_loop.return_value = mock_loop

        # 调用被测方法
        result = self.stability_test.setup_trading_system()

        # 验证结果
        self.assertTrue(result)

        # 验证市场模拟器创建
        mock_market_simulator.assert_called_once_with(
            symbols=["BTC/USDT", "ETH/USDT"],
            initial_balance=10000.0,
            fee_rate=0.001,
            market_data_manager=self.mock_mdm,
        )

        # 验证交易循环创建
        mock_trading_loop.assert_called_once_with(
            market=mock_market,
            symbols=["BTC/USDT", "ETH/USDT"],
            risk_percent=0.5,
            fast_ma=7,
            slow_ma=25,
            atr_period=14,
            test_mode=True,
        )

        # 验证实例变量设置
        self.assertEqual(self.stability_test.market, mock_market)
        self.assertEqual(self.stability_test.trading_loop, mock_loop)

    @patch("psutil.Process")
    def test_monitor_system_resources(self, mock_process_class):
        """测试监控系统资源"""
        # 配置模拟对象
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_process.cpu_percent.return_value = 5.0

        mock_process_class.return_value = mock_process

        # 调用被测方法
        memory_mb, cpu_percent = self.stability_test.monitor_system_resources()

        # 验证结果
        self.assertEqual(memory_mb, 100.0)
        self.assertEqual(cpu_percent, 5.0)
        self.assertEqual(self.stability_test.stats["memory_usage"], [100.0])

        # 第二次调用
        mock_process.memory_info.return_value.rss = 200 * 1024 * 1024  # 200MB
        memory_mb, cpu_percent = self.stability_test.monitor_system_resources()

        # 验证结果更新
        self.assertEqual(memory_mb, 200.0)
        self.assertEqual(self.stability_test.stats["memory_usage"], [100.0, 200.0])

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_generate_report(self, mock_open, mock_exists):
        """测试生成报告"""
        # 配置模拟对象
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        # 设置一些测试数据
        self.stability_test.stats["start_time"] = datetime.datetime(2023, 1, 1, 12, 0, 0)
        self.stability_test.stats["total_signals"] = 42
        self.stability_test.stats["errors"] = 5
        self.stability_test.stats["data_interruptions"] = 2
        self.stability_test.stats["reconnections"] = 2
        self.stability_test.stats["data_source_switches"] = 1
        self.stability_test.stats["memory_usage"] = [100.0, 200.0, 150.0]

        # 调用被测方法
        report = self.stability_test.generate_report(1.5, is_final=True)

        # 验证结果
        self.assertIn("最终稳定性测试报告", report)
        self.assertIn("2023-01-01 12:00:00", report)
        self.assertIn("运行时长: 1.50 天", report)
        self.assertIn("总信号数: 42", report)
        self.assertIn("错误次数: 5", report)
        self.assertIn("每小时错误率: 0.1389", report)  # 5 / (1.5 * 24)
        self.assertIn("数据中断次数: 2", report)
        self.assertIn("重连次数: 2", report)
        self.assertIn("数据源切换次数: 1", report)
        self.assertIn("平均内存使用: 150.00 MB", report)
        self.assertIn("最大内存使用: 200.00 MB", report)

        # 由于错误率大于0.1，应该显示不稳定
        self.assertIn("系统状态: 不稳定", report)

        # 验证写入文件
        mock_file.write.assert_called_once_with(report)

    @patch.object(StabilityTest, "monitor_system_resources")
    @patch.object(StabilityTest, "generate_report")
    @patch.object(StabilityTest, "setup_trading_system")
    @patch("time.sleep")
    @patch("time.time")
    def test_run_short_duration(
        self, mock_time, mock_sleep, mock_setup, mock_generate_report, mock_monitor
    ):
        """测试运行短时间场景"""
        # 配置模拟对象
        mock_setup.return_value = True

        # 模拟时间流逝，提供足够的时间戳避免StopIteration
        start_time = 1000.0
        end_time = start_time + self.stability_test.duration_seconds + 1

        # 创建一个可调用对象来提供时间戳
        time_values = [start_time, start_time + 0.5, end_time]
        time_counter = [0]  # 使用列表来让闭包可以修改

        def time_side_effect():
            if time_counter[0] < len(time_values):
                result = time_values[time_counter[0]]
                time_counter[0] += 1
                return result
            else:
                # 如果超出预期调用，返回结束时间
                return end_time

        mock_time.side_effect = time_side_effect

        # 模拟交易循环
        self.stability_test.trading_loop = MagicMock()
        self.stability_test.trading_loop.check_and_execute.return_value = []

        # 调用被测方法
        result = self.stability_test.run()

        # 验证结果
        self.assertTrue(result)

        # 验证调用
        mock_setup.assert_called_once()

        # 验证开始时间设置
        self.assertIsNotNone(self.stability_test.stats["start_time"])

        # 验证报告生成
        mock_generate_report.assert_called_once()

        # 验证sleep调用
        mock_sleep.assert_called_once_with(0.01)  # 使用我们配置的检查间隔
