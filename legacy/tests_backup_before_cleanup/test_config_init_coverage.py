#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.config.__init__ 模块的未覆盖行
Test for uncovered lines in src.config.__init__ module

专门针对第106, 115, 124行的覆盖率测试
"""

import tempfile
import unittest
from pathlib import Path

import pytest

# Import modules to test
try:
    from src.config import _find_env_file, _find_ini_file, _find_yaml_file

    print("Successfully imported config functions")
except ImportError as e:
    print(f"Import error: {e}")
    pytest.skip("Config module not available, skipping tests", allow_module_level=True)


class TestConfigInitCoverage(unittest.TestCase):
    """测试配置模块初始化的未覆盖行"""

    def setUp(self):
        """设置测试环境"""
        # 🧹 使用pytest fixture替代手动创建临时目录
        # 这个将在test runner中通过fixture提供
        pass

    def tearDown(self):
        """清理测试环境"""
        # 🧹 不再需要手动清理，fixture会自动处理
        pass

    def test_find_ini_file_not_found(self):
        """测试 _find_ini_file 函数找不到文件时返回 None (第106行)"""
        print("Testing _find_ini_file with empty directory")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建一个空目录，不包含任何INI文件
            empty_dir = temp_path / "empty"
            empty_dir.mkdir()

            # 调用函数，应该返回None
            result = _find_ini_file(empty_dir)
            print(f"Result: {result}")

            # 验证返回None（覆盖第106行）
            self.assertIsNone(result)

    def test_find_yaml_file_not_found(self):
        """测试 _find_yaml_file 函数找不到文件时返回 None (第115行)"""
        print("Testing _find_yaml_file with empty directory")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建一个空目录，不包含任何YAML文件
            empty_dir = temp_path / "empty_yaml"
            empty_dir.mkdir()

            # 调用函数，应该返回None
            result = _find_yaml_file(empty_dir)
            print(f"Result: {result}")

            # 验证返回None（覆盖第115行）
            self.assertIsNone(result)

    def test_find_env_file_not_found(self):
        """测试 _find_env_file 函数找不到文件时返回 None (第124行)"""
        print("Testing _find_env_file with empty directory")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建一个空目录，不包含任何环境变量文件
            empty_dir = temp_path / "empty_env"
            empty_dir.mkdir()

            # 调用函数，应该返回None
            result = _find_env_file(empty_dir)
            print(f"Result: {result}")

            # 验证返回None（覆盖第124行）
            self.assertIsNone(result)

    def test_find_ini_file_found(self):
        """测试 _find_ini_file 函数找到文件时的行为"""
        print("Testing _find_ini_file with existing file")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建一个包含INI文件的目录
            test_dir = temp_path / "with_ini"
            test_dir.mkdir()

            # 创建一个config.ini文件
            ini_file = test_dir / "config.ini"
            ini_file.write_text("[section]\nkey=value\n")

            # 调用函数，应该返回文件路径
            result = _find_ini_file(test_dir)
            print(f"Result: {result}")

            # 验证返回正确的路径
            self.assertEqual(result, str(ini_file))

    def test_find_yaml_file_found(self):
        """测试 _find_yaml_file 函数找到文件时的行为"""
        print("Testing _find_yaml_file with existing file")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建一个包含YAML文件的目录
            test_dir = temp_path / "with_yaml"
            test_dir.mkdir()

            # 创建一个config.yaml文件
            yaml_file = test_dir / "config.yaml"
            yaml_file.write_text("key: value\n")

            # 调用函数，应该返回文件路径
            result = _find_yaml_file(test_dir)
            print(f"Result: {result}")

            # 验证返回正确的路径
            self.assertEqual(result, str(yaml_file))

    def test_find_env_file_found(self):
        """测试 _find_env_file 函数找到文件时的行为"""
        print("Testing _find_env_file with existing file")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建一个包含环境变量文件的目录
            test_dir = temp_path / "with_env"
            test_dir.mkdir()

            # 创建一个.env文件
            env_file = test_dir / ".env"
            env_file.write_text("KEY=value\n")

            # 调用函数，应该返回文件路径
            result = _find_env_file(test_dir)
            print(f"Result: {result}")

            # 验证返回正确的路径
            self.assertEqual(result, str(env_file))

    def test_find_files_priority_order(self):
        """测试文件查找的优先级顺序"""
        print("Testing file priority order")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # 创建包含多个文件的目录
            test_dir = temp_path / "priority_test"
            test_dir.mkdir()

            # 创建多个INI文件，测试优先级
            (test_dir / "app.ini").write_text("[app]\n")
            (test_dir / "config.ini").write_text("[config]\n")
            (test_dir / "trading.ini").write_text("[trading]\n")

            # 应该返回第一个找到的文件（config.ini）
            result = _find_ini_file(test_dir)
            print(f"Priority result: {result}")
            self.assertTrue(result.endswith("config.ini"))

    def test_nonexistent_directory(self):
        """测试不存在的目录"""
        print("Testing nonexistent directory")
        # 🧹 使用临时目录上下文管理器
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            nonexistent_dir = temp_path / "nonexistent"

            # 这些函数应该能处理不存在的目录
            ini_result = _find_ini_file(nonexistent_dir)
            yaml_result = _find_yaml_file(nonexistent_dir)
            env_result = _find_env_file(nonexistent_dir)

            print(f"Nonexistent results: ini={ini_result}, yaml={yaml_result}, env={env_result}")

            # 所有结果都应该是None
            self.assertIsNone(ini_result)
            self.assertIsNone(yaml_result)
            self.assertIsNone(env_result)


if __name__ == "__main__":
    print("Running config init coverage tests...")
    unittest.main(verbosity=2)
