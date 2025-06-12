#!/usr/bin/env python3
"""临时文件清理检查器 - 检查和修复tempfile使用问题"""

import glob
import re
import tempfile
from pathlib import Path


def analyze_tempfile_usage():
    """分析tempfile使用情况"""
    print("🔍 分析tempfile使用模式...")

    test_files = glob.glob("tests/test_*.py")
    issues = []

    for test_file in test_files:
        if "BROKEN" in test_file:
            continue

        try:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            file_issues = []

            for i, line in enumerate(lines, 1):
                # 检查问题模式
                if "tempfile.mkdtemp()" in line:
                    # 检查是否有对应的清理代码
                    var_match = re.search(r"(\w+)\s*=\s*tempfile\.mkdtemp\(\)", line)
                    if var_match:
                        var_name = var_match.group(1)
                        has_cleanup = f"shutil.rmtree({var_name})" in content
                        file_issues.append(
                            {
                                "line": i,
                                "issue": f"mkdtemp() 使用变量 {var_name}",
                                "has_cleanup": has_cleanup,
                                "code": line.strip(),
                            }
                        )

                if "delete=False" in line and "tempfile" in line:
                    file_issues.append(
                        {
                            "line": i,
                            "issue": "NamedTemporaryFile with delete=False",
                            "has_cleanup": False,  # 需要进一步检查
                            "code": line.strip(),
                        }
                    )

            if file_issues:
                issues.append({"file": test_file, "issues": file_issues})

        except Exception as e:
            print(f"❌ 读取文件 {test_file} 失败: {e}")

    return issues


def print_analysis_results(issues):
    """打印分析结果"""
    print("\n📊 tempfile使用分析结果:")

    if not issues:
        print("✅ 未发现明显的tempfile清理问题")
        return

    total_issues = sum(len(item["issues"]) for item in issues)
    print(f"⚠️ 发现 {total_issues} 个潜在问题，涉及 {len(issues)} 个文件")

    for file_info in issues:
        print(f"\n📄 {file_info['file']}:")
        for issue in file_info["issues"]:
            status = "✅ 有清理" if issue["has_cleanup"] else "❌ 无清理"
            print(f"   行 {issue['line']}: {issue['issue']} - {status}")
            print(f"   代码: {issue['code']}")


def create_tempfile_cleanup_fixture():
    """创建tempfile清理的fixture"""
    fixture_content = '''"""Tempfile清理Fixture - 添加到tests/conftest.py中"""

import pytest
import tempfile
import shutil
import os
from pathlib import Path

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
'''

    with open("tempfile_cleanup_fixture.py", "w", encoding="utf-8") as f:
        f.write(fixture_content)

    print("📝 已创建临时文件清理fixture: tempfile_cleanup_fixture.py")


def check_current_temp_files():
    """检查当前系统中的临时文件情况"""
    print("\n🔍 检查当前临时文件情况...")

    temp_dir = tempfile.gettempdir()
    print(f"📂 临时目录: {temp_dir}")

    try:
        temp_items = list(Path(temp_dir).glob("tmp*"))
        if temp_items:
            print(f"⚠️ 发现 {len(temp_items)} 个可能的测试临时文件:")
            for item in temp_items[:10]:  # 只显示前10个
                size = "目录" if item.is_dir() else f"{item.stat().st_size} bytes"
                print(f"   {item.name} ({size})")
            if len(temp_items) > 10:
                print(f"   ... 还有 {len(temp_items) - 10} 个")
        else:
            print("✅ 未发现测试相关的临时文件")

        return len(temp_items)
    except Exception as e:
        print(f"❌ 检查临时文件失败: {e}")
        return 0


def create_cleanup_recommendations():
    """创建清理建议"""
    recommendations = """
# 🧹 Tempfile 清理优化建议

## 📊 问题分析
你的测试中有两种tempfile使用模式存在清理问题：

### ❌ 有问题的模式
```python
# 1. mkdtemp() 需要手动清理
self.temp_dir = tempfile.mkdtemp()
# 需要: shutil.rmtree(self.temp_dir)

# 2. delete=False 需要手动清理
with tempfile.NamedTemporaryFile(delete=False) as f:
    pass
# 需要: os.unlink(f.name)
```

### ✅ 推荐的安全模式
```python
# 1. 使用上下文管理器 (自动清理)
with tempfile.TemporaryDirectory() as temp_dir:
    # 使用temp_dir
    pass  # 自动清理

# 2. 使用fixture
def test_something(temp_directory):
    # 使用temp_directory
    pass  # 自动清理
```

## 🔧 具体修复建议

### 1. 立即使用fixture
将 `tempfile_cleanup_fixture.py` 中的内容添加到 `tests/conftest.py`

### 2. 修改测试代码
```python
# 旧代码
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()

def tearDown(self):
    shutil.rmtree(self.temp_dir)  # 经常被忘记!

# 新代码
def test_something(self, temp_directory):
    # 直接使用temp_directory，自动清理
```

### 3. 使用管理器模式
```python
def test_something(self, temp_manager):
    temp_file = temp_manager.create_temp_file(suffix=".csv")
    temp_dir = temp_manager.create_temp_dir()
    # 测试结束时自动清理
```

## 💡 最佳实践
1. **优先使用**: `with tempfile.TemporaryDirectory():`
2. **测试fixture**: 使用提供的 `temp_directory` 和 `temp_manager`
3. **避免**: `mkdtemp()` 和 `delete=False`
4. **清理检查**: 定期运行 `python tempfile_cleanup_checker.py`

## 🎯 性能影响
- 减少文件系统泄漏
- 避免文件描述符耗尽
- 提升测试稳定性
- 减少资源竞争
"""

    with open("TEMPFILE_CLEANUP_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(recommendations)

    print("📝 已创建清理指南: TEMPFILE_CLEANUP_GUIDE.md")


def main():
    print("🧹 Tempfile清理检查器")
    print("🎯 检查和修复临时文件清理问题")

    # 1. 分析代码中的tempfile使用
    issues = analyze_tempfile_usage()
    print_analysis_results(issues)

    # 2. 检查当前临时文件
    temp_count = check_current_temp_files()

    # 3. 创建清理工具
    print(f"\n{'='*60}")
    create_tempfile_cleanup_fixture()
    create_cleanup_recommendations()

    # 4. 总结建议
    print(f"\n{'='*60}")
    print("💡 总结:")

    if issues:
        total_issues = sum(len(item["issues"]) for item in issues)
        print(f"⚠️ 发现 {total_issues} 个潜在的tempfile清理问题")
        print("🔧 建议立即修复，特别是mkdtemp()的使用")
    else:
        print("✅ 代码中的tempfile使用看起来还不错")

    if temp_count > 0:
        print(f"🧹 系统中有 {temp_count} 个临时文件，建议清理")

    print("\n🚀 下一步行动:")
    print("1. 📖 阅读 TEMPFILE_CLEANUP_GUIDE.md")
    print("2. 🔧 将fixture添加到 tests/conftest.py")
    print("3. 🧪 修改使用mkdtemp()的测试")
    print("4. ✅ 运行测试验证改进效果")


if __name__ == "__main__":
    main()
