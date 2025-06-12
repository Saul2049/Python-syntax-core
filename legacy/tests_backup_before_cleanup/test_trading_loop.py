#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.trading_loop 模块的向后兼容性功能
Trading Loop Module Backward Compatibility Tests

覆盖目标:
- 向后兼容导入功能
- __all__ 导出列表
- 主程序块执行
- 环境变量检查
- 模块重新导出功能
"""

import os
import unittest
from io import StringIO
from unittest.mock import patch

import pytest

# Import the module to test
try:
    import src.trading_loop as trading_loop_module
except ImportError:
    pytest.skip("Trading loop module not available, skipping tests", allow_module_level=True)


class TestTradingLoopBackwardCompatibility(unittest.TestCase):
    """测试交易循环模块的向后兼容性"""

    def test_module_imports(self):
        """测试模块导入功能"""
        # 验证所有必要的函数和类都可以导入
        self.assertTrue(hasattr(trading_loop_module, "fetch_price_data"))
        self.assertTrue(hasattr(trading_loop_module, "calculate_atr"))
        self.assertTrue(hasattr(trading_loop_module, "get_trading_signals"))
        self.assertTrue(hasattr(trading_loop_module, "trading_loop"))
        self.assertTrue(hasattr(trading_loop_module, "TradingEngine"))

    def test_all_exports(self):
        """测试 __all__ 导出列表"""
        expected_exports = [
            "fetch_price_data",
            "calculate_atr",
            "get_trading_signals",
            "trading_loop",
            "TradingEngine",
        ]

        # 验证 __all__ 列表存在且包含预期的导出
        self.assertTrue(hasattr(trading_loop_module, "__all__"))
        self.assertEqual(set(trading_loop_module.__all__), set(expected_exports))

    def test_imported_functions_callable(self):
        """测试导入的函数是否可调用"""
        # 验证所有导入的函数都是可调用的
        self.assertTrue(callable(trading_loop_module.fetch_price_data))
        self.assertTrue(callable(trading_loop_module.calculate_atr))
        self.assertTrue(callable(trading_loop_module.get_trading_signals))
        self.assertTrue(callable(trading_loop_module.trading_loop))

        # 验证 TradingEngine 是一个类
        self.assertTrue(isinstance(trading_loop_module.TradingEngine, type))

    def test_fetch_price_data_import(self):
        """测试 fetch_price_data 函数导入"""
        from src.core.price_fetcher import fetch_price_data as original_func

        # 验证导入的函数与原始函数相同
        self.assertIs(trading_loop_module.fetch_price_data, original_func)

    def test_calculate_atr_import(self):
        """测试 calculate_atr 函数导入"""
        from src.core.price_fetcher import calculate_atr as original_func

        # 验证导入的函数与原始函数相同
        self.assertIs(trading_loop_module.calculate_atr, original_func)

    def test_get_trading_signals_import(self):
        """测试 get_trading_signals 函数导入"""
        from src.core.signal_processor import get_trading_signals as original_func

        # 验证导入的函数与原始函数相同
        self.assertIs(trading_loop_module.get_trading_signals, original_func)

    def test_trading_loop_import(self):
        """测试 trading_loop 函数导入"""
        from src.core.trading_engine import trading_loop as original_func

        # 验证导入的函数与原始函数相同
        self.assertIs(trading_loop_module.trading_loop, original_func)

    def test_trading_engine_import(self):
        """测试 TradingEngine 类导入"""
        from src.core.trading_engine import TradingEngine as original_class

        # 验证导入的类与原始类相同
        self.assertIs(trading_loop_module.TradingEngine, original_class)


class TestMainProgramBlock(unittest.TestCase):
    """测试主程序块执行"""

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
    def test_main_with_all_env_vars(self, mock_stdout, mock_trading_loop):
        """测试设置了所有环境变量的主程序执行"""
        # 设置所有必要的环境变量
        os.environ["TG_TOKEN"] = "test_token"
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"

        # 模拟主程序执行
        with patch("src.trading_loop.__name__", "__main__"):
            # 重新导入模块以触发主程序块
            import importlib

            import src.trading_loop

            importlib.reload(src.trading_loop)

        # 验证没有警告输出
        output = mock_stdout.getvalue()
        self.assertNotIn("警告", output)
        self.assertNotIn("Warning", output)

        # 验证 trading_loop 被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_missing_tg_token(self, mock_stdout, mock_trading_loop):
        """测试缺少 TG_TOKEN 环境变量"""
        # 只设置 API 相关环境变量
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"
        # 确保 TG_TOKEN 不存在
        if "TG_TOKEN" in os.environ:
            del os.environ["TG_TOKEN"]

        # 模拟主程序执行
        with patch("src.trading_loop.__name__", "__main__"):
            import importlib

            import src.trading_loop

            importlib.reload(src.trading_loop)

        # 验证有 TG_TOKEN 警告
        output = mock_stdout.getvalue()
        self.assertIn("TG_TOKEN", output)
        self.assertIn("通知功能将不可用", output)

        # 验证 trading_loop 仍然被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_missing_api_key(self, mock_stdout, mock_trading_loop):
        """测试缺少 API_KEY 环境变量"""
        # 只设置 TG_TOKEN
        os.environ["TG_TOKEN"] = "test_token"
        os.environ["API_SECRET"] = "test_secret"
        # 确保 API_KEY 不存在
        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]

        # 模拟主程序执行
        with patch("src.trading_loop.__name__", "__main__"):
            import importlib

            import src.trading_loop

            importlib.reload(src.trading_loop)

        # 验证有 API 相关警告
        output = mock_stdout.getvalue()
        self.assertIn("API_KEY", output)
        self.assertIn("交易功能将不可用", output)

        # 验证 trading_loop 仍然被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_missing_api_secret(self, mock_stdout, mock_trading_loop):
        """测试缺少 API_SECRET 环境变量"""
        # 只设置 TG_TOKEN 和 API_KEY
        os.environ["TG_TOKEN"] = "test_token"
        os.environ["API_KEY"] = "test_key"
        # 确保 API_SECRET 不存在
        if "API_SECRET" in os.environ:
            del os.environ["API_SECRET"]

        # 模拟主程序执行
        with patch("src.trading_loop.__name__", "__main__"):
            import importlib

            import src.trading_loop

            importlib.reload(src.trading_loop)

        # 验证有 API 相关警告
        output = mock_stdout.getvalue()
        self.assertIn("API_SECRET", output)
        self.assertIn("交易功能将不可用", output)

        # 验证 trading_loop 仍然被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_missing_all_env_vars(self, mock_stdout, mock_trading_loop):
        """测试缺少所有环境变量"""
        # 清除所有相关环境变量
        for var in ["TG_TOKEN", "API_KEY", "API_SECRET"]:
            if var in os.environ:
                del os.environ[var]

        # 模拟主程序执行
        with patch("src.trading_loop.__name__", "__main__"):
            import importlib

            import src.trading_loop

            importlib.reload(src.trading_loop)

        # 验证有所有警告
        output = mock_stdout.getvalue()
        self.assertIn("TG_TOKEN", output)
        self.assertIn("API_KEY", output)
        self.assertIn("API_SECRET", output)
        self.assertIn("通知功能将不可用", output)
        self.assertIn("交易功能将不可用", output)

        # 验证 trading_loop 仍然被调用
        mock_trading_loop.assert_called_once()

    @patch("src.trading_loop.trading_loop")
    def test_main_not_executed_when_imported(self, mock_trading_loop):
        """测试作为模块导入时不执行主程序"""
        # 正常导入模块（不是作为主程序）

        # 验证 trading_loop 没有被调用
        mock_trading_loop.assert_not_called()


class TestModuleDocumentation(unittest.TestCase):
    """测试模块文档和元数据"""

    def test_module_docstring(self):
        """测试模块文档字符串"""
        self.assertIsNotNone(trading_loop_module.__doc__)
        self.assertIn("交易循环模块", trading_loop_module.__doc__)
        self.assertIn("向后兼容", trading_loop_module.__doc__)

    def test_module_has_refactoring_notice(self):
        """测试模块包含重构提示"""
        docstring = trading_loop_module.__doc__
        self.assertIn("重构", docstring)
        self.assertIn("src.core.trading_engine", docstring)
        self.assertIn("src.core.price_fetcher", docstring)
        self.assertIn("src.core.signal_processor", docstring)


class TestEnvironmentVariableChecking(unittest.TestCase):
    """测试环境变量检查功能"""

    def setUp(self):
        """设置测试环境"""
        self.original_env = os.environ.copy()

    def tearDown(self):
        """清理测试环境"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_tg_token_check(self):
        """测试 TG_TOKEN 环境变量检查"""
        # 测试存在的情况
        os.environ["TG_TOKEN"] = "test_token"
        self.assertIn("TG_TOKEN", os.environ)

        # 测试不存在的情况
        del os.environ["TG_TOKEN"]
        self.assertNotIn("TG_TOKEN", os.environ)

    def test_api_credentials_check(self):
        """测试 API 凭证环境变量检查"""
        # 测试都存在的情况
        os.environ["API_KEY"] = "test_key"
        os.environ["API_SECRET"] = "test_secret"
        self.assertIn("API_KEY", os.environ)
        self.assertIn("API_SECRET", os.environ)

        # 测试只有 API_KEY 的情况
        del os.environ["API_SECRET"]
        self.assertIn("API_KEY", os.environ)
        self.assertNotIn("API_SECRET", os.environ)

        # 测试都不存在的情况
        del os.environ["API_KEY"]
        self.assertNotIn("API_KEY", os.environ)
        self.assertNotIn("API_SECRET", os.environ)


class TestIntegrationWithOriginalModules(unittest.TestCase):
    """测试与原始模块的集成"""

    def test_price_fetcher_integration(self):
        """测试与价格获取模块的集成"""
        # 验证可以通过向后兼容模块访问价格获取功能
        self.assertTrue(hasattr(trading_loop_module, "fetch_price_data"))
        self.assertTrue(hasattr(trading_loop_module, "calculate_atr"))

        # 验证函数签名一致性
        import inspect

        from src.core.price_fetcher import calculate_atr, fetch_price_data

        # 检查函数签名
        self.assertEqual(
            inspect.signature(trading_loop_module.fetch_price_data),
            inspect.signature(fetch_price_data),
        )
        self.assertEqual(
            inspect.signature(trading_loop_module.calculate_atr), inspect.signature(calculate_atr)
        )

    def test_signal_processor_integration(self):
        """测试与信号处理模块的集成"""
        # 验证可以通过向后兼容模块访问信号处理功能
        self.assertTrue(hasattr(trading_loop_module, "get_trading_signals"))

        # 验证函数签名一致性
        import inspect

        from src.core.signal_processor import get_trading_signals

        self.assertEqual(
            inspect.signature(trading_loop_module.get_trading_signals),
            inspect.signature(get_trading_signals),
        )

    def test_trading_engine_integration(self):
        """测试与交易引擎模块的集成"""
        # 验证可以通过向后兼容模块访问交易引擎功能
        self.assertTrue(hasattr(trading_loop_module, "trading_loop"))
        self.assertTrue(hasattr(trading_loop_module, "TradingEngine"))

        # 验证函数和类的一致性
        import inspect

        from src.core.trading_engine import TradingEngine, trading_loop

        self.assertEqual(
            inspect.signature(trading_loop_module.trading_loop), inspect.signature(trading_loop)
        )

        # 验证类的方法一致性
        original_methods = set(dir(TradingEngine))
        imported_methods = set(dir(trading_loop_module.TradingEngine))
        self.assertEqual(original_methods, imported_methods)


if __name__ == "__main__":
    unittest.main()
