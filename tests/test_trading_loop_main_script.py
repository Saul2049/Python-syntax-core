#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.trading_loop 模块作为脚本运行时的主程序块
Test src.trading_loop module when run as a script to trigger main block
"""

import os
import subprocess
import sys
import unittest
from unittest.mock import patch



class TestTradingLoopAsScript(unittest.TestCase):
    """测试交易循环模块作为脚本运行"""

    def setUp(self):
        """设置测试环境"""
        # 保存原始环境变量
        self.original_env = os.environ.copy()

    def tearDown(self):
        """清理测试环境"""
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch("src.core.trading_engine.trading_loop")
    def test_script_execution_all_env_vars(self, mock_trading_loop):
        """测试设置了所有环境变量时的脚本执行"""
        # 设置环境变量
        test_env = os.environ.copy()
        test_env["TG_TOKEN"] = "test_token"
        test_env["API_KEY"] = "test_key"
        test_env["API_SECRET"] = "test_secret"

        # 运行模块作为脚本
        result = subprocess.run(
            [sys.executable, "-m", "src.trading_loop"],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # 验证没有警告输出
        self.assertNotIn("警告", result.stdout)
        self.assertNotIn("警告", result.stderr)

    def test_script_execution_missing_tg_token(self):
        """测试缺少 TG_TOKEN 时的脚本执行"""
        # 设置环境变量（不包括 TG_TOKEN）
        test_env = os.environ.copy()
        test_env["API_KEY"] = "test_key"
        test_env["API_SECRET"] = "test_secret"
        if "TG_TOKEN" in test_env:
            del test_env["TG_TOKEN"]

        # 运行模块作为脚本
        result = subprocess.run(
            [sys.executable, "-m", "src.trading_loop"],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # 验证有 TG_TOKEN 警告
        output = result.stdout + result.stderr
        self.assertIn("TG_TOKEN", output)
        self.assertIn("通知功能将不可用", output)

    def test_script_execution_missing_api_credentials(self):
        """测试缺少 API 凭证时的脚本执行"""
        # 设置环境变量（不包括 API 凭证）
        test_env = os.environ.copy()
        test_env["TG_TOKEN"] = "test_token"
        for var in ["API_KEY", "API_SECRET"]:
            if var in test_env:
                del test_env[var]

        # 运行模块作为脚本
        result = subprocess.run(
            [sys.executable, "-m", "src.trading_loop"],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # 验证有 API 相关警告
        output = result.stdout + result.stderr
        self.assertIn("API_KEY", output)
        self.assertIn("交易功能将不可用", output)

    def test_script_execution_missing_all_env_vars(self):
        """测试缺少所有环境变量时的脚本执行"""
        # 清除所有相关环境变量
        test_env = os.environ.copy()
        for var in ["TG_TOKEN", "API_KEY", "API_SECRET"]:
            if var in test_env:
                del test_env[var]

        # 运行模块作为脚本
        result = subprocess.run(
            [sys.executable, "-m", "src.trading_loop"],
            env=test_env,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # 验证有所有警告
        output = result.stdout + result.stderr
        self.assertIn("TG_TOKEN", output)
        self.assertIn("通知功能将不可用", output)
        self.assertIn("API_KEY", output)
        self.assertIn("交易功能将不可用", output)

    def test_module_import_coverage(self):
        """测试模块导入以确保覆盖率跟踪"""
        # 导入模块以确保覆盖率工具能够跟踪
        import src.trading_loop

        # 验证模块属性
        self.assertTrue(hasattr(src.trading_loop, "__all__"))
        self.assertTrue(hasattr(src.trading_loop, "trading_loop"))
        self.assertTrue(hasattr(src.trading_loop, "TradingEngine"))

        # 验证导出列表
        expected_exports = [
            "fetch_price_data",
            "calculate_atr",
            "get_trading_signals",
            "trading_loop",
            "TradingEngine",
        ]
        self.assertEqual(set(src.trading_loop.__all__), set(expected_exports))


if __name__ == "__main__":
    unittest.main()
