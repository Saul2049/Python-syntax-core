#!/usr/bin/env python3
"""
M3阶段信号缓存（简化版）
Simplified Signal Cache for M3 Phase

配合OptimizedSignalProcessor使用
"""


class SignalCache:
    """简化的信号缓存"""

    def __init__(self):
        # 简单的内存缓存
        self.cache = {}

    def get(self, key):
        """获取缓存值"""
        return self.cache.get(key)

    def set(self, key, value):
        """设置缓存值"""
        self.cache[key] = value

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def size(self):
        """缓存大小"""
        return len(self.cache)
