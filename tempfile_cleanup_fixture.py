"""Tempfile清理Fixture - 添加到tests/conftest.py中"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_directory():
    """提供一个自动清理的临时目录"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass


@pytest.fixture
def temp_file():
    """提供一个自动清理的临时文件"""
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)  # 关闭文件描述符
    try:
        yield temp_path
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


class TempFileManager:
    """临时文件管理器"""

    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []

    def create_temp_file(self, suffix="", prefix="tmp", dir=None):
        """创建临时文件"""
        fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        os.close(fd)
        self.temp_files.append(path)
        return path

    def create_temp_dir(self, suffix="", prefix="tmp", dir=None):
        """创建临时目录"""
        path = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=dir)
        self.temp_dirs.append(path)
        return path

    def cleanup(self):
        """清理所有临时文件和目录"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass

        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass

        self.temp_files.clear()
        self.temp_dirs.clear()


@pytest.fixture
def temp_manager():
    """提供临时文件管理器"""
    manager = TempFileManager()
    try:
        yield manager
    finally:
        manager.cleanup()


# 在conftest.py中添加会话级清理
@pytest.fixture(autouse=True, scope="session")
def cleanup_temp_files():
    """会话结束时清理遗留的临时文件"""
    yield

    # 清理可能遗留的临时文件
    temp_dir = tempfile.gettempdir()

    try:
        # 查找并清理测试相关的临时文件
        for item in Path(temp_dir).glob("tmp*"):
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
            except:
                pass
    except:
        pass
