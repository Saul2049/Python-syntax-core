#!/usr/bin/env python3
"""
CI快速测试脚本
Quick CI Test Script

用于GitHub Actions中的快速功能验证
"""

import sys
import os
import time
import traceback

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_core_imports():
    """测试核心模块导入"""
    print("🔍 测试核心模块导入...")
    
    try:
        from src.core.signal_processor_vectorized import OptimizedSignalProcessor
        print("✅ OptimizedSignalProcessor 导入成功")
        
        from src.monitoring.metrics_collector import get_metrics_collector
        print("✅ metrics_collector 导入成功")
        
        from src.core.trading_engine import TradingEngine
        print("✅ TradingEngine 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 核心模块导入失败: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("🔍 测试基本功能...")
    
    try:
        # 测试信号处理器
        from src.core.signal_processor_vectorized import OptimizedSignalProcessor
        processor = OptimizedSignalProcessor()
        print("✅ 信号处理器创建成功")
        
        # 测试指标收集器
        from src.monitoring.metrics_collector import get_metrics_collector
        metrics = get_metrics_collector()
        print("✅ 指标收集器创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        traceback.print_exc()
        return False

def test_memory_scripts():
    """测试内存相关脚本"""
    print("🔍 测试内存脚本...")
    
    try:
        from scripts.memory.mem_snapshot import MemorySnapshot
        snapshot = MemorySnapshot()
        print("✅ MemorySnapshot 导入成功")
        
        from scripts.memory.gc_profiler import GCProfiler
        profiler = GCProfiler()
        print("✅ GCProfiler 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 内存脚本测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始CI快速测试")
    print("=" * 50)
    
    tests = [
        ("核心模块导入", test_core_imports),
        ("基本功能", test_basic_functionality),
        ("内存脚本", test_memory_scripts),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        success = test_func()
        elapsed = time.time() - start_time
        
        if success:
            print(f"✅ {test_name} 通过 ({elapsed:.2f}s)")
            passed += 1
        else:
            print(f"❌ {test_name} 失败 ({elapsed:.2f}s)")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 