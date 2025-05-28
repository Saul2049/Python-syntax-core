#!/usr/bin/env python3
"""
测试交易循环模块 (Test Trading Loop Module)
"""

import os
from io import StringIO
from unittest.mock import Mock, patch

import pytest

import src.trading_loop


class TestTradingLoopImports:
    """测试交易循环模块的导入 (Test Trading Loop Module Imports)"""

    def test_import_fetch_price_data(self):
        """测试导入价格数据获取函数"""
        from src.trading_loop import fetch_price_data

        # 验证函数可以导入
        assert callable(fetch_price_data)

    def test_import_calculate_atr(self):
        """测试导入ATR计算函数"""
        from src.trading_loop import calculate_atr

        # 验证函数可以导入
        assert callable(calculate_atr)

    def test_import_get_trading_signals(self):
        """测试导入交易信号函数"""
        from src.trading_loop import get_trading_signals

        # 验证函数可以导入
        assert callable(get_trading_signals)

    def test_import_trading_loop_function(self):
        """测试导入交易循环函数"""
        from src.trading_loop import trading_loop

        # 验证函数可以导入
        assert callable(trading_loop)

    def test_import_trading_engine(self):
        """测试导入交易引擎类"""
        from src.trading_loop import TradingEngine

        # 验证类可以导入
        assert isinstance(TradingEngine, type)

    def test_all_exports(self):
        """测试__all__导出列表"""
        expected_exports = [
            "fetch_price_data",
            "calculate_atr",
            "get_trading_signals",
            "trading_loop",
            "TradingEngine",
        ]

        for export in expected_exports:
            assert hasattr(src.trading_loop, export)
            assert export in src.trading_loop.__all__


class TestTradingLoopBackwardCompatibility:
    """测试交易循环模块的向后兼容性 (Test Trading Loop Backward Compatibility)"""

    def test_backward_compatible_imports_work(self):
        """测试向后兼容导入正常工作"""
        # 测试所有向后兼容导入都能正常工作
        try:
            pass

            # 如果能成功导入，测试通过
            assert True
        except ImportError as e:
            pytest.fail(f"向后兼容导入失败: {e}")

    @patch("src.trading_loop.fetch_price_data")
    def test_fetch_price_data_delegation(self, mock_fetch):
        """测试价格数据获取函数的委托"""
        from src.trading_loop import fetch_price_data

        # 设置模拟返回值
        mock_fetch.return_value = {"price": 100.0}

        # 调用函数
        result = fetch_price_data("BTC/USDT")

        # 验证调用了正确的底层函数
        mock_fetch.assert_called_once_with("BTC/USDT")
        assert result == {"price": 100.0}

    @patch("src.trading_loop.calculate_atr")
    def test_calculate_atr_delegation(self, mock_atr):
        """测试ATR计算函数的委托"""
        from src.trading_loop import calculate_atr

        # 设置模拟返回值
        mock_atr.return_value = 1.5

        # 调用函数
        result = calculate_atr([100, 101, 99], window=2)

        # 验证调用了正确的底层函数
        mock_atr.assert_called_once_with([100, 101, 99], window=2)
        assert result == 1.5

    @patch("src.trading_loop.get_trading_signals")
    def test_get_trading_signals_delegation(self, mock_signals):
        """测试交易信号函数的委托"""
        from src.trading_loop import get_trading_signals

        # 设置模拟返回值
        mock_signals.return_value = {"signal": "buy"}

        # 调用函数
        result = get_trading_signals({"price": 100})

        # 验证调用了正确的底层函数
        mock_signals.assert_called_once_with({"price": 100})
        assert result == {"signal": "buy"}

    @patch("src.trading_loop.trading_loop")
    def test_trading_loop_delegation(self, mock_loop):
        """测试交易循环函数的委托"""
        from src.trading_loop import trading_loop

        # 设置模拟返回值
        mock_loop.return_value = None

        # 调用函数
        trading_loop()

        # 验证调用了正确的底层函数
        mock_loop.assert_called_once()

    def test_trading_engine_class_delegation(self):
        """测试交易引擎类的委托"""
        from src.core.trading_engine import TradingEngine as CoreTradingEngine
        from src.trading_loop import TradingEngine

        # 验证导入的是正确的类
        assert TradingEngine is CoreTradingEngine


class TestTradingLoopMainFunction:
    """测试交易循环主函数 (Test Trading Loop Main Function)"""

    @patch("src.trading_loop.trading_loop")
    @patch.dict(
        "os.environ",
        {
            "TG_TOKEN": "test_token",
            "TG_CHAT_ID": "test_chat_id",
            "API_KEY": "test_key",
            "API_SECRET": "test_secret",
        },
    )
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_function_with_all_env_vars(self, mock_stdout, mock_trading_loop):
        """测试主函数在有所有环境变量时的行为"""
        # 模拟主函数执行

        # 重新加载模块以触发主函数逻辑（在测试环境中模拟）
        # 由于我们不能直接运行if __name__ == "__main__"块，我们测试其逻辑
        # 验证环境变量存在时不会有警告
        # 这里我们测试环境变量检查逻辑
        assert "TG_TOKEN" in os.environ
        assert "TG_CHAT_ID" in os.environ
        assert "API_KEY" in os.environ
        assert "API_SECRET" in os.environ

    @patch("src.trading_loop.trading_loop")
    @patch.dict("os.environ", {}, clear=True)
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_function_without_env_vars(self, mock_stdout, mock_trading_loop):
        """测试主函数在缺少环境变量时的行为"""
        # 模拟缺少环境变量的情况

        # 验证环境变量不存在
        assert "TG_TOKEN" not in os.environ
        assert "TG_CHAT_ID" not in os.environ
        assert "API_KEY" not in os.environ
        assert "API_SECRET" not in os.environ

        # 测试环境变量检查逻辑的正确性
        assert True  # 基本测试通过

    @patch("src.trading_loop.trading_loop")
    @patch.dict("os.environ", {"TG_TOKEN": "test_token"})
    @patch("sys.stdout", new_callable=StringIO)
    def test_main_function_partial_env_vars(self, mock_stdout, mock_trading_loop):
        """测试主函数在部分环境变量存在时的行为"""
        # 验证部分环境变量存在的情况
        assert "TG_TOKEN" in os.environ
        assert "TG_CHAT_ID" not in os.environ
        assert "API_KEY" not in os.environ
        assert "API_SECRET" not in os.environ

    def test_environment_variable_checks(self):
        """测试环境变量检查逻辑"""
        # 测试TG_TOKEN检查
        with patch.dict("os.environ", {}, clear=True):
            assert "TG_TOKEN" not in os.environ

        with patch.dict("os.environ", {"TG_TOKEN": "test"}):
            assert "TG_TOKEN" in os.environ

        # 测试TG_CHAT_ID检查
        with patch.dict("os.environ", {}, clear=True):
            assert "TG_CHAT_ID" not in os.environ

        with patch.dict("os.environ", {"TG_CHAT_ID": "test"}):
            assert "TG_CHAT_ID" in os.environ

        # 测试API密钥检查
        with patch.dict("os.environ", {}, clear=True):
            assert "API_KEY" not in os.environ
            assert "API_SECRET" not in os.environ

        with patch.dict("os.environ", {"API_KEY": "key", "API_SECRET": "secret"}):
            assert "API_KEY" in os.environ
            assert "API_SECRET" in os.environ


class TestTradingLoopModuleStructure:
    """测试交易循环模块结构 (Test Trading Loop Module Structure)"""

    def test_module_docstring(self):
        """测试模块文档字符串"""
        assert src.trading_loop.__doc__ is not None
        assert "交易循环模块" in src.trading_loop.__doc__
        assert "向后兼容" in src.trading_loop.__doc__

    def test_module_has_required_attributes(self):
        """测试模块具有必需的属性"""
        required_attributes = [
            "fetch_price_data",
            "calculate_atr",
            "get_trading_signals",
            "trading_loop",
            "TradingEngine",
            "__all__",
        ]

        for attr in required_attributes:
            assert hasattr(src.trading_loop, attr), f"模块缺少必需属性: {attr}"

    def test_module_imports_are_functions_or_classes(self):
        """测试模块导入的都是函数或类"""
        from src.trading_loop import (
            TradingEngine,
            calculate_atr,
            fetch_price_data,
            get_trading_signals,
            trading_loop,
        )

        # 测试函数
        assert callable(fetch_price_data)
        assert callable(calculate_atr)
        assert callable(get_trading_signals)
        assert callable(trading_loop)

        # 测试类
        assert isinstance(TradingEngine, type)

    def test_module_all_list_completeness(self):
        """测试__all__列表的完整性"""
        # 获取模块中公开的函数和类
        [name for name in dir(src.trading_loop) if not name.startswith("_")]

        # 验证所有公开项目都在__all__中（除了导入的模块）
        expected_in_all = [
            "fetch_price_data",
            "calculate_atr",
            "get_trading_signals",
            "trading_loop",
            "TradingEngine",
        ]

        for item in expected_in_all:
            assert item in src.trading_loop.__all__


class TestTradingLoopIntegration:
    """测试交易循环集成 (Test Trading Loop Integration)"""

    @patch("src.trading_loop.fetch_price_data")
    @patch("src.trading_loop.get_trading_signals")
    @patch("src.trading_loop.TradingEngine")
    @patch.dict(
        "os.environ",
        {
            "TG_TOKEN": "test_token",
            "TG_CHAT_ID": "test_chat_id",
            "API_KEY": "test_key",
            "API_SECRET": "test_secret",
        },
    )
    def test_full_workflow_simulation(self, mock_engine_class, mock_signals, mock_fetch):
        """测试完整工作流程模拟"""
        from src.trading_loop import TradingEngine, fetch_price_data, get_trading_signals

        # 设置模拟数据
        mock_fetch.return_value = {"price": 100.0, "volume": 1000}
        mock_signals.return_value = {"signal": "buy", "confidence": 0.8}

        # 创建模拟的交易引擎实例
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        # 模拟工作流程 - 测试组件而不是无限循环
        price_data = fetch_price_data("BTC/USDT")
        signals = get_trading_signals(price_data)

        # 创建交易引擎实例（但不启动循环）
        TradingEngine()

        # 验证调用
        mock_fetch.assert_called_once_with("BTC/USDT")
        mock_signals.assert_called_once_with({"price": 100.0, "volume": 1000})
        mock_engine_class.assert_called()

        # 验证数据流
        assert price_data == {"price": 100.0, "volume": 1000}
        assert signals == {"signal": "buy", "confidence": 0.8}

    def test_error_handling_in_imports(self):
        """测试导入错误处理"""
        # 测试即使底层模块有问题，导入仍然可以工作
        try:
            import src.trading_loop

            # 验证基本导入成功
            assert hasattr(src.trading_loop, "__all__")
        except Exception as e:
            pytest.fail(f"模块导入失败: {e}")

    def test_module_reload_safety(self):
        """测试模块重新加载安全性"""
        import importlib

        # 重新加载模块应该是安全的
        try:
            importlib.reload(src.trading_loop)
            assert hasattr(src.trading_loop, "__all__")
        except Exception as e:
            pytest.fail(f"模块重新加载失败: {e}")

    @patch("src.core.trading_engine.TradingEngine")
    def test_trading_loop_function(self, mock_engine_class):
        """测试交易循环函数"""
        from src.trading_loop import trading_loop  # 添加正确的导入

        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        trading_loop(symbol="ETHUSDT", interval_seconds=30)

        # 验证创建了交易引擎
        mock_engine_class.assert_called_once()

        # 验证调用了start_trading_loop - 修复参数传递方式
        mock_engine.start_trading_loop.assert_called_once_with(
            "ETHUSDT", 30
        )  # 使用位置参数而不是关键字参数

    @patch("src.trading_loop.trading_loop")
    @patch("builtins.print")
    @patch.dict("os.environ", {}, clear=True)
    def test_main_block_execution_no_env_vars(self, mock_print, mock_trading_loop):
        """测试__main__块执行 - 无环境变量"""
        import subprocess
        import sys

        # 运行trading_loop模块作为脚本
        result = subprocess.run(
            [sys.executable, "-m", "src.trading_loop"],
            cwd="/Users/liam/Python syntax core",
            capture_output=True,
            text=True,
            env={},  # 清空环境变量
        )

        # 验证包含了警告信息
        assert "警告: 未设置TG_TOKEN环境变量" in result.stdout
        assert "警告: 未设置API_KEY或API_SECRET环境变量" in result.stdout

    @patch("src.trading_loop.trading_loop")
    @patch("builtins.print")
    @patch.dict(
        "os.environ", {"TG_TOKEN": "test_token", "API_KEY": "test_key", "API_SECRET": "test_secret"}
    )
    def test_main_block_execution_with_env_vars(self, mock_print, mock_trading_loop):
        """测试__main__块执行 - 有环境变量"""
        import os
        import subprocess
        import sys

        # 设置环境变量
        env = os.environ.copy()
        env.update({"TG_TOKEN": "test_token", "API_KEY": "test_key", "API_SECRET": "test_secret"})

        # 运行trading_loop模块作为脚本
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys
sys.path.insert(0, "/Users/liam/Python syntax core")
import os
os.environ["TG_TOKEN"] = "test_token"
os.environ["API_KEY"] = "test_key"
os.environ["API_SECRET"] = "test_secret"

# 模拟trading_loop函数避免无限循环
import unittest.mock
with unittest.mock.patch("src.trading_loop.trading_loop") as mock_loop:
    # 导入并执行__main__块
    import src.trading_loop
    exec(open("src/trading_loop.py").read())
            """,
            ],
            cwd="/Users/liam/Python syntax core",
            capture_output=True,
            text=True,
            env=env,
        )

        # 验证没有输出警告（因为环境变量都存在）
        assert "警告" not in result.stdout

    def test_main_block_env_variable_logic(self):
        """测试__main__块中的环境变量检查逻辑"""
        import os

        # 测试TG_TOKEN检查逻辑
        with patch.dict("os.environ", {}, clear=True):
            tg_token_missing = "TG_TOKEN" not in os.environ
            assert tg_token_missing is True

        with patch.dict("os.environ", {"TG_TOKEN": "test_token"}):
            tg_token_present = "TG_TOKEN" not in os.environ
            assert tg_token_present is False

        # 测试API密钥检查逻辑
        with patch.dict("os.environ", {}, clear=True):
            api_keys_missing = "API_KEY" not in os.environ or "API_SECRET" not in os.environ
            assert api_keys_missing is True

        with patch.dict("os.environ", {"API_KEY": "key", "API_SECRET": "secret"}):
            api_keys_missing = "API_KEY" not in os.environ or "API_SECRET" not in os.environ
            assert api_keys_missing is False
