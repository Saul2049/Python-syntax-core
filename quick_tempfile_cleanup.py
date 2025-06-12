#!/usr/bin/env python3
"""快速临时文件清理脚本"""

import shutil
import tempfile
from pathlib import Path


def cleanup_temp_files():
    """清理遗留的临时文件"""
    temp_dir = Path(tempfile.gettempdir())

    print("🧹 开始清理临时文件...")
    print(f"📂 临时目录: {temp_dir}")

    cleaned_files = 0
    cleaned_dirs = 0
    errors = 0

    try:
        # 查找所有tmp开头的文件和目录
        for item in temp_dir.glob("tmp*"):
            try:
                if item.is_file():
                    item.unlink()
                    cleaned_files += 1
                elif item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                    cleaned_dirs += 1
            except Exception as e:
                errors += 1
                print(f"⚠️ 清理失败: {item.name} - {e}")

    except Exception as e:
        print(f"❌ 清理过程出错: {e}")
        return False

    print("✅ 清理完成!")
    print("📋 清理统计:")
    print(f"   🗃️ 文件: {cleaned_files}个")
    print(f"   📁 目录: {cleaned_dirs}个")
    print(f"   ❌ 错误: {errors}个")

    return True


if __name__ == "__main__":
    cleanup_temp_files()
