#!/usr/bin/env python3
"""Compatibility shim for older imports

This module re-exports PerformanceProfiler from the new
`scripts.performance.performance_profiler` location so that legacy tests
importing `scripts.performance_profiler` continue to work.
"""

from importlib import import_module

# 动态导入新的实现，避免循环依赖
_performance_profiler_mod = import_module("scripts.performance.performance_profiler")

# 将 PerformanceProfiler 暴露到旧路径
PerformanceProfiler = _performance_profiler_mod.PerformanceProfiler

__all__ = ["PerformanceProfiler"]
