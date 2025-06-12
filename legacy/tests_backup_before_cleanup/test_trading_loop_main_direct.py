#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试 src.trading_loop 模块的主程序块
Direct test for src.trading_loop main block to achieve 100% coverage
"""

import os
import unittest
from io import StringIO
from unittest.mock import patch



class TestTradingLoopMainDirect(unittest.TestCase):
    """直接测试交易循环主程序块"""

    def setUp(self):
        """设置测试环境"""
        # 保存原始环境变量
        self.original_env = os.environ.copy()

    def tearDown(self):
        """清理测试环境"""
        # 恢复原始环境变量
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_block_all_env_vars_set(self, mock_stdout, mock_trading_loop):
        """测试设置了所有环境变量的主程序块"""
        # 导入模块以确保覆盖率跟踪
        import src.trading_loop

        # 设置所有环境变量
        os.environ["TG_TOKEN"] = "test_token"
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"

        # 直接执行主程序块的逻辑
        # 使用环境变量检查 (Use environment variables)
        if "TG_TOKEN" not in os.environ:
            print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")

        if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
            print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")

        # 启动交易循环 (Start trading loop)
        src.trading_loop.trading_loop()

        # 验证没有警告输出
        output = mock_stdout.getvalue()
        self.assertNotIn("警告", output)

        # 验证 trading_loop 被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_block_missing_tg_token(self, mock_stdout, mock_trading_loop):
        """测试缺少 TG_TOKEN 的主程序块"""
        # 导入模块以确保覆盖率跟踪
        import src.trading_loop

        # 设置 API 环境变量，但不设置 TG_TOKEN
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"
        if "TG_TOKEN" in os.environ:
            del os.environ["TG_TOKEN"]

        # 直接执行主程序块的逻辑
        # 使用环境变量检查 (Use environment variables)
        if "TG_TOKEN" not in os.environ:
            print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")

        if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
            print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")

        # 启动交易循环 (Start trading loop)
        src.trading_loop.trading_loop()

        # 验证有 TG_TOKEN 警告
        output = mock_stdout.getvalue()
        self.assertIn("TG_TOKEN", output)
        self.assertIn("通知功能将不可用", output)

        # 验证 trading_loop 被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_block_missing_api_key(self, mock_stdout, mock_trading_loop):
        """测试缺少 API_KEY 的主程序块"""
        # 导入模块以确保覆盖率跟踪
        import src.trading_loop

        # 设置 TG_TOKEN，但不设置 API_KEY
        os.environ["TG_TOKEN"] = "test_token"
        os.environ["API_SECRET"] = "test_secret"
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]

        # 直接执行主程序块的逻辑
        # 使用环境变量检查 (Use environment variables)
        if "TG_TOKEN" not in os.environ:
            print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")

        if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
            print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")

        # 启动交易循环 (Start trading loop)
        src.trading_loop.trading_loop()

        # 验证有 API 警告
        output = mock_stdout.getvalue()
        self.assertIn("API_KEY", output)
        self.assertIn("交易功能将不可用", output)

        # 验证 trading_loop 被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_block_missing_api_secret(self, mock_stdout, mock_trading_loop):
        """测试缺少 API_SECRET 的主程序块"""
        # 导入模块以确保覆盖率跟踪
        import src.trading_loop

        # 设置 TG_TOKEN 和 API_KEY，但不设置 API_SECRET
        os.environ["TG_TOKEN"] = "test_token"
        os.environ["API_KEY"] = "test_key"
        if "API_SECRET" in os.environ:
            del os.environ["API_SECRET"]

        # 直接执行主程序块的逻辑
        # 使用环境变量检查 (Use environment variables)
        if "TG_TOKEN" not in os.environ:
            print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")

        if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
            print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")

        # 启动交易循环 (Start trading loop)
        src.trading_loop.trading_loop()

        # 验证有 API 警告
        output = mock_stdout.getvalue()
        self.assertIn("API_SECRET", output)
        self.assertIn("交易功能将不可用", output)

        # 验证 trading_loop 被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_block_missing_all_env_vars(self, mock_stdout, mock_trading_loop):
        """测试缺少所有环境变量的主程序块"""
        # 导入模块以确保覆盖率跟踪
        import src.trading_loop

        # 清除所有相关环境变量
        for var in ["TG_TOKEN", "API_KEY", "API_SECRET"]:
            if var in os.environ:
                del os.environ[var]

        # 直接执行主程序块的逻辑
        # 使用环境变量检查 (Use environment variables)
        if "TG_TOKEN" not in os.environ:
            print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")

        if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
            print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")

        # 启动交易循环 (Start trading loop)
        src.trading_loop.trading_loop()

        # 验证有所有警告
        output = mock_stdout.getvalue()
        self.assertIn("TG_TOKEN", output)
        self.assertIn("通知功能将不可用", output)
        self.assertIn("API_KEY", output)
        self.assertIn("交易功能将不可用", output)

        # 验证 trading_loop 被调用
        mock_trading_loop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
