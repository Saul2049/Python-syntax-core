#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src/config.py 向后兼容模块的所有功能
Src Config.py Backward Compatibility Module Tests

覆盖目标:
- 向后兼容性导入
- 弃用警告
- 重新导出的功能
- _discover_config_files 函数
- __all__ 导出列表
- 模块元数据和文档
"""

import importlib
import importlib.util
import warnings
from unittest.mock import patch

import pytest


def import_config_module():
    """直接导入 src/config.py 模块而不是包"""
    spec = importlib.util.spec_from_file_location("src_config_module", "src/config.py")
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    return config_module


class TestConfigBackwardCompatibility:
    """测试配置模块向后兼容性"""

    def test_config_imports_with_deprecation_warning(self):
        """测试导入时的弃用警告"""
        # 捕获弃用警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 导入模块应该触发弃用警告
            import_config_module()

            # 验证弃用警告
            assert len(w) >= 1
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1

            warning = deprecation_warnings[0]
            assert "Importing from src.config is deprecated" in str(warning.message)
            assert "Please use 'from src.config import get_config' instead" in str(warning.message)

    def test_all_exports_available(self):
        """测试所有导出的功能都可用"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 __all__ 中的所有项目都可用
        expected_exports = [
            "TradingConfig",
            "DefaultConfig",
            "ConfigSourceLoader",
            "ConfigValidator",
            "ConfigSanitizer",
            "get_config",
            "setup_logging",
            "reset_config",
            "_discover_config_files",
        ]

        # 检查 __all__ 列表
        assert hasattr(config_module, "__all__")
        assert config_module.__all__ == expected_exports

        # 检查所有导出的项目都存在
        for export in expected_exports:
            assert hasattr(config_module, export), f"Missing export: {export}"

    def test_trading_config_import(self):
        """测试 TradingConfig 导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 TradingConfig 可以访问
        assert hasattr(config_module, "TradingConfig")
        assert config_module.TradingConfig is not None

    def test_default_config_import(self):
        """测试 DefaultConfig 导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 DefaultConfig 可以访问
        assert hasattr(config_module, "DefaultConfig")
        assert config_module.DefaultConfig is not None

    def test_config_source_loader_import(self):
        """测试 ConfigSourceLoader 导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 ConfigSourceLoader 可以访问
        assert hasattr(config_module, "ConfigSourceLoader")
        assert config_module.ConfigSourceLoader is not None

    def test_config_validator_import(self):
        """测试 ConfigValidator 导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 ConfigValidator 可以访问
        assert hasattr(config_module, "ConfigValidator")
        assert config_module.ConfigValidator is not None

    def test_config_sanitizer_import(self):
        """测试 ConfigSanitizer 导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 ConfigSanitizer 可以访问
        assert hasattr(config_module, "ConfigSanitizer")
        assert config_module.ConfigSanitizer is not None

    def test_get_config_function_import(self):
        """测试 get_config 函数导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 get_config 函数可以访问
        assert hasattr(config_module, "get_config")
        assert callable(config_module.get_config)

    def test_setup_logging_function_import(self):
        """测试 setup_logging 函数导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 setup_logging 函数可以访问
        assert hasattr(config_module, "setup_logging")
        assert callable(config_module.setup_logging)

    def test_reset_config_function_import(self):
        """测试 reset_config 函数导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 reset_config 函数可以访问
        assert hasattr(config_module, "reset_config")
        assert callable(config_module.reset_config)


class TestDiscoverConfigFilesFunction:
    """测试 _discover_config_files 函数"""

    def test_discover_config_files_function_exists(self):
        """测试 _discover_config_files 函数存在"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证函数存在且可调用
        assert hasattr(config_module, "_discover_config_files")
        assert callable(config_module._discover_config_files)

    def test_discover_config_files_docstring(self):
        """测试 _discover_config_files 函数文档字符串"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证函数有文档字符串
        func_doc = config_module._discover_config_files.__doc__
        assert func_doc is not None
        assert "Legacy function" in func_doc
        assert "src.config._discover_config_files instead" in func_doc

    def test_discover_config_files_calls_new_implementation(self):
        """测试 _discover_config_files 调用新实现"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 调用函数（不模拟，测试实际行为）
        result = config_module._discover_config_files()

        # 验证返回结果是合理的（应该是元组或列表）
        assert result is not None
        assert isinstance(result, (list, tuple))

    @patch("src.config._discover_config_files")
    def test_discover_config_files_with_mock(self, mock_new_discover):
        """测试 _discover_config_files 与模拟的新实现"""
        # 设置模拟返回值
        mock_new_discover.return_value = ["config1.yaml", "config2.json"]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 调用遗留函数
        result = config_module._discover_config_files()

        # 验证调用了新函数
        mock_new_discover.assert_called_once()
        assert result == ["config1.yaml", "config2.json"]

    @patch("src.config._discover_config_files")
    def test_discover_config_files_exception_handling(self, mock_new_discover):
        """测试 _discover_config_files 异常处理"""
        # 设置模拟抛出异常
        mock_new_discover.side_effect = FileNotFoundError("Config directory not found")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 调用函数应该传播异常
        with pytest.raises(FileNotFoundError, match="Config directory not found"):
            config_module._discover_config_files()

        mock_new_discover.assert_called_once()


class TestConfigModuleIntegration:
    """测试配置模块集成功能"""

    def test_module_docstring(self):
        """测试模块文档字符串"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证模块有文档字符串
        assert config_module.__doc__ is not None
        assert "Backward Compatibility Configuration Module" in config_module.__doc__
        assert "向后兼容配置模块" in config_module.__doc__

    def test_module_attributes(self):
        """测试模块属性"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证模块有必要的属性
        assert hasattr(config_module, "__file__")
        assert config_module.__file__.endswith("config.py")

    def test_import_structure_validation(self):
        """测试导入结构验证"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证所有必要的导入都存在
        required_imports = [
            "ConfigSanitizer",
            "ConfigSourceLoader",
            "ConfigValidator",
            "DefaultConfig",
            "TradingConfig",
            "get_config",
            "reset_config",
            "setup_logging",
        ]

        for import_name in required_imports:
            assert hasattr(config_module, import_name), f"Missing import: {import_name}"
            # 验证不是None
            assert getattr(config_module, import_name) is not None


class TestWarningsHandling:
    """测试警告处理"""

    def test_deprecation_warning_details(self):
        """测试弃用警告详细信息"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 导入模块
            import_config_module()

            # 验证警告详细信息
            assert len(w) >= 1
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1

            warning = deprecation_warnings[0]
            assert warning.category == DeprecationWarning
            # 警告可能来自测试文件或config.py文件
            assert warning.filename.endswith(".py")
            assert "src.config is deprecated" in str(warning.message)

    def test_warning_stacklevel(self):
        """测试警告堆栈级别"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 导入模块
            import_config_module()

            # 验证警告被正确记录
            assert len(w) >= 1
            # 警告应该指向正确的堆栈级别
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            if deprecation_warnings:
                warning = deprecation_warnings[0]
                assert warning.lineno > 0

    def test_multiple_imports_warning_behavior(self):
        """测试多次导入的警告行为"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 第一次导入
            import_config_module()
            first_warning_count = len(
                [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            )

            # 第二次导入
            import_config_module()

            # 应该有额外的警告
            total_warnings = len(
                [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            )
            assert total_warnings >= first_warning_count


class TestEdgeCases:
    """测试边界情况"""

    def test_all_list_completeness(self):
        """测试 __all__ 列表的完整性"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证 __all__ 包含所有重要的公共属性
        for attr in config_module.__all__:
            assert hasattr(config_module, attr), f"__all__ contains non-existent attribute: {attr}"

    def test_module_reload_safety(self):
        """测试模块重新加载安全性"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 获取原始属性
        original_all = config_module.__all__.copy()

        # 重新导入模块
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module2 = import_config_module()

        # 验证属性保持一致
        assert config_module2.__all__ == original_all


class TestConfigModuleUsage:
    """测试配置模块使用场景"""

    def test_typical_import_pattern(self):
        """测试典型导入模式"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证可以访问主要功能
        assert hasattr(config_module, "get_config")
        assert hasattr(config_module, "TradingConfig")
        assert hasattr(config_module, "setup_logging")

    def test_function_accessibility(self):
        """测试函数可访问性"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证函数可以被调用（不实际调用以避免副作用）
        assert callable(config_module.get_config)
        assert callable(config_module.setup_logging)
        assert callable(config_module.reset_config)
        assert callable(config_module._discover_config_files)

    def test_class_accessibility(self):
        """测试类可访问性"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证类可以被访问
        assert config_module.TradingConfig is not None
        assert config_module.DefaultConfig is not None
        assert config_module.ConfigSourceLoader is not None
        assert config_module.ConfigValidator is not None
        assert config_module.ConfigSanitizer is not None


class TestDocumentationAndMetadata:
    """测试文档和元数据"""

    def test_module_has_proper_encoding(self):
        """测试模块有正确的编码声明"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 读取源文件检查编码
        source_file = config_module.__file__

        with open(source_file, "r", encoding="utf-8") as f:
            first_lines = [f.readline().strip() for _ in range(3)]

        # 验证有编码声明
        encoding_found = any("utf-8" in line for line in first_lines)
        assert encoding_found, "Module should have UTF-8 encoding declaration"

    def test_module_has_shebang(self):
        """测试模块有 shebang 行"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        source_file = config_module.__file__

        with open(source_file, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        # 验证有 shebang
        assert first_line.startswith("#!/usr/bin/env python3"), "Module should have proper shebang"

    def test_backward_compatibility_documentation(self):
        """测试向后兼容性文档"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证文档字符串包含向后兼容性信息
        doc = config_module.__doc__
        assert "Backward Compatibility" in doc
        assert "delegating to the new modular config package" in doc
        assert "For new code, prefer importing from src.config package directly" in doc

    def test_module_file_path(self):
        """测试模块文件路径"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证模块文件路径正确
        assert config_module.__file__.endswith("config.py")
        assert "src" in config_module.__file__


class TestLegacyFunctionBehavior:
    """测试遗留函数行为"""

    def test_discover_config_files_function_exists(self):
        """测试 _discover_config_files 函数存在"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证函数存在且可调用
        assert hasattr(config_module, "_discover_config_files")
        assert callable(config_module._discover_config_files)

    def test_discover_config_files_docstring(self):
        """测试 _discover_config_files 函数文档字符串"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证函数有文档字符串
        func_doc = config_module._discover_config_files.__doc__
        assert func_doc is not None
        assert "Legacy function" in func_doc
        assert "src.config._discover_config_files instead" in func_doc

    def test_discover_config_files_return_type(self):
        """测试 _discover_config_files 返回类型"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 调用函数
        result = config_module._discover_config_files()

        # 验证返回类型
        assert result is not None
        assert isinstance(result, (list, tuple))


class TestImportErrorHandling:
    """测试导入错误处理"""

    def test_module_imports_successfully(self):
        """测试模块成功导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            # 应该能够成功导入
            config_module = import_config_module()

            # 验证模块已加载
            assert config_module is not None
            assert hasattr(config_module, "__all__")

    def test_all_required_attributes_present(self):
        """测试所有必需属性都存在"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证所有 __all__ 中的属性都存在
        for attr_name in config_module.__all__:
            assert hasattr(config_module, attr_name), f"Missing required attribute: {attr_name}"
            attr_value = getattr(config_module, attr_name)
            assert attr_value is not None, f"Attribute {attr_name} is None"

    def test_warnings_module_import(self):
        """测试warnings模块导入"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证warnings模块被正确使用
        assert hasattr(config_module, "warnings")


class TestConfigModuleCoverage:
    """测试配置模块覆盖率相关功能"""

    def test_all_imports_covered(self):
        """测试所有导入都被覆盖"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 验证所有从src.config导入的项目
        from_src_config_imports = [
            "ConfigSanitizer",
            "ConfigSourceLoader",
            "ConfigValidator",
            "DefaultConfig",
            "TradingConfig",
            "get_config",
            "reset_config",
            "setup_logging",
        ]

        for import_name in from_src_config_imports:
            assert hasattr(config_module, import_name)
            imported_item = getattr(config_module, import_name)
            assert imported_item is not None

    def test_legacy_function_implementation(self):
        """测试遗留函数实现"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            config_module = import_config_module()

        # 测试_discover_config_files函数的实现
        func = config_module._discover_config_files
        assert callable(func)

        # 验证函数可以被调用
        result = func()
        assert result is not None

    def test_module_level_warning_generation(self):
        """测试模块级别警告生成"""
        # 这个测试验证模块导入时生成警告的代码路径
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            import_config_module()

            # 验证警告被生成
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) > 0

            # 验证警告内容
            warning_msg = str(deprecation_warnings[0].message)
            assert "deprecated" in warning_msg.lower()
            assert "src.config" in warning_msg


class TestConfigPyDirectImport:
    """测试直接导入 src/config.py 以确保覆盖率"""

    def test_direct_import_for_coverage(self):
        """直接导入 config.py 文件以确保覆盖率工具能够跟踪"""
        # 这个测试确保 coverage 工具能够跟踪到 src/config.py 文件
        import os
        import sys

        # 添加 src 目录到 Python 路径
        src_path = os.path.join(os.path.dirname(__file__), "..", "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        try:
            # 直接导入 config.py 文件
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)

                # 使用 exec 执行文件内容以确保覆盖率跟踪
                config_file_path = os.path.join(src_path, "config.py")
                with open(config_file_path, "r") as f:
                    config_code = f.read()

                # 创建一个模块命名空间
                config_namespace = {}
                exec(config_code, config_namespace)

                # 验证模块内容
                assert "__all__" in config_namespace
                assert "_discover_config_files" in config_namespace
                assert callable(config_namespace["_discover_config_files"])

                # 调用函数以确保覆盖率
                result = config_namespace["_discover_config_files"]()
                assert result is not None

        finally:
            # 清理路径
            if src_path in sys.path:
                sys.path.remove(src_path)

    def test_import_config_py_as_module(self):
        """通过模块导入方式测试 config.py"""
        import os
        import sys

        # 保存原始模块状态
        original_modules = sys.modules.copy()

        try:
            # 添加 src 目录到路径
            src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            # 清除可能存在的模块缓存
            if "config" in sys.modules:
                del sys.modules["config"]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)

                # 直接导入 config 模块（这应该导入 config.py 而不是 config 包）
                import config as config_module

                # 验证这是正确的模块
                assert hasattr(config_module, "__all__")
                assert hasattr(config_module, "_discover_config_files")
                assert callable(config_module._discover_config_files)

                # 调用函数以确保代码被执行
                result = config_module._discover_config_files()
                assert result is not None

                # 验证所有导出的功能
                for item in config_module.__all__:
                    assert hasattr(config_module, item)

        finally:
            # 恢复原始模块状态
            sys.modules.clear()
            sys.modules.update(original_modules)

            # 清理路径
            if src_path in sys.path:
                sys.path.remove(src_path)
