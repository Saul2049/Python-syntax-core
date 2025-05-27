#!/usr/bin/env python3
"""
Git推送前检查流程演示脚本
演示如何使用项目的推送前最佳实践
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """运行命令并显示结果"""
    print(f"\n🔄 {description}")
    print(f"💻 执行: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            cmd, shell=True, check=True, 
            capture_output=True, text=True
        )
        print(f"✅ 成功: {description}")
        if result.stdout:
            print(f"📄 输出:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {description}")
        print(f"🚨 错误: {e.stderr}")
        return False


def check_git_status():
    """检查Git状态"""
    print("\n📋 Git状态检查")
    print("=" * 50)
    
    # 检查是否在Git仓库中
    if not Path(".git").exists():
        print("❌ 当前目录不是Git仓库")
        return False
    
    # 检查是否有未提交的更改
    result = subprocess.run(
        "git status --porcelain", 
        shell=True, capture_output=True, text=True
    )
    
    if result.stdout.strip():
        print("📝 发现未提交的更改:")
        print(result.stdout)
        print("💡 建议: 先提交或暂存更改")
    else:
        print("✅ 工作目录干净")
    
    return True


def demo_push_workflow():
    """演示完整的推送前工作流"""
    print("🛠️ Git推送前最佳实践演示")
    print("=" * 60)
    print("📚 参考文档: docs/guides/GIT_PUSH_BEST_PRACTICES.md")
    print()
    
    # 检查Git状态
    if not check_git_status():
        return False
    
    # 步骤1: 同步远端
    if not run_command("git fetch origin", "1️⃣ 同步远端仓库"):
        return False
    
    # 步骤2: 快速测试
    if not run_command("make test-quick", "2️⃣ 快速单元测试"):
        print("💡 提示: 修复测试失败后再继续")
        return False
    
    # 步骤3: 代码质量检查
    if not run_command("make lint", "3️⃣ 代码质量检查"):
        print("💡 提示: 运行 'make format' 自动修复格式问题")
        return False
    
    # 步骤4: 内存健康检查 (可选)
    print("\n4️⃣ 内存健康检查 (可选)")
    print("💡 对于主分支或重要PR，建议运行:")
    print("   make w2-validate-fast")
    print("   make mem-health")
    
    # 步骤5: Pre-commit检查
    if not run_command("pre-commit run --all-files", "5️⃣ Pre-commit钩子检查"):
        print("💡 提示: 修复pre-commit问题后再继续")
        return False
    
    print("\n🎉 推送前检查全部通过！")
    print("✅ 现在可以安全地推送代码")
    print()
    print("📋 下一步操作:")
    print("   git add .")
    print("   git commit -m 'feat(scope): your description'")
    print("   git push -u origin your-branch")
    
    return True


def quick_demo():
    """快速演示模式"""
    print("⚡ 快速推送检查演示")
    print("=" * 40)
    
    commands = [
        ("make test-quick FAST=1", "快速测试"),
        ("make lint", "代码质量"),
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    
    print("\n✅ 快速检查完成！")
    return True


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        return quick_demo()
    else:
        return demo_push_workflow()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 