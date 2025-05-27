#!/usr/bin/env python3
"""
优化版信号处理器 (Optimized Signal Processor)
提供缓存机制和并行计算优化的信号计算
"""

import hashlib
import logging
import time
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.monitoring.metrics_collector import get_metrics_collector


class SignalCache:
    """信号计算缓存器"""

    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}

    def _generate_key(self, data: pd.DataFrame, fast_win: int, slow_win: int) -> str:
        """生成缓存键"""
        # 使用数据的最后几行和参数生成唯一键
        data_hash = hashlib.md5(
            str(data.tail(max(fast_win, slow_win) + 10).values).encode()
        ).hexdigest()[:16]
        return f"{data_hash}_{fast_win}_{slow_win}"

    def get(self, data: pd.DataFrame, fast_win: int, slow_win: int) -> Optional[Dict]:
        """获取缓存值"""
        key = self._generate_key(data, fast_win, slow_win)
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None

    def set(self, data: pd.DataFrame, fast_win: int, slow_win: int, value: Dict):
        """设置缓存值"""
        key = self._generate_key(data, fast_win, slow_win)

        # 如果缓存已满，删除最老的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[key] = value
        self.access_times[key] = time.time()


class OptimizedSignalProcessor:
    """优化版信号处理器"""

    def __init__(self, enable_cache: bool = True, cache_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.metrics = get_metrics_collector()
        self.enable_cache = enable_cache
        self.cache = SignalCache(cache_size) if enable_cache else None

        # 预计算常用移动平均参数
        self._ma_cache = {}

    @lru_cache(maxsize=512)
    def _calculate_ma_cached(
        self, data_hash: str, window: int, data_len: int
    ) -> Tuple[float, float]:
        """缓存版移动平均计算"""
        # 这里应该重新计算，但由于lru_cache的限制，我们需要另一种方法
        # 实际实现中，我们会在主函数中处理缓存

    def calculate_moving_averages(
        self, data: pd.DataFrame, fast_win: int, slow_win: int
    ) -> Tuple[pd.Series, pd.Series]:
        """优化的移动平均计算"""
        close_prices = data["close"]

        # 使用pandas的向量化操作
        fast_ma = close_prices.rolling(window=fast_win, min_periods=1).mean()
        slow_ma = close_prices.rolling(window=slow_win, min_periods=1).mean()

        return fast_ma, slow_ma

    def calculate_atr_optimized(self, data: pd.DataFrame, period: int = 14) -> float:
        """优化的ATR计算"""
        try:
            # 使用向量化操作计算ATR
            high = data["high"]
            low = data["low"]
            close = data["close"]
            prev_close = close.shift(1)

            # 计算真实范围
            tr1 = high - low
            tr2 = np.abs(high - prev_close)
            tr3 = np.abs(low - prev_close)

            # 使用numpy的maximum函数进行向量化
            true_range = np.maximum(tr1, np.maximum(tr2, tr3))

            # 计算ATR (使用指数移动平均)
            atr = true_range.ewm(span=period, adjust=False).mean().iloc[-1]

            return float(atr) if not pd.isna(atr) else 0.0

        except Exception as e:
            self.logger.error(f"ATR计算失败: {e}")
            return 0.0

    def detect_crossover(self, fast_ma: pd.Series, slow_ma: pd.Series) -> Dict[str, bool]:
        """优化的交叉检测"""
        if len(fast_ma) < 2 or len(slow_ma) < 2:
            return {"buy_signal": False, "sell_signal": False}

        # 使用向量化比较
        current_fast = fast_ma.iloc[-1]
        current_slow = slow_ma.iloc[-1]
        prev_fast = fast_ma.iloc[-2]
        prev_slow = slow_ma.iloc[-2]

        # 金叉：快线上穿慢线
        buy_signal = (prev_fast <= prev_slow) and (current_fast > current_slow)

        # 死叉：快线下穿慢线
        sell_signal = (prev_fast >= prev_slow) and (current_fast < current_slow)

        return {"buy_signal": bool(buy_signal), "sell_signal": bool(sell_signal)}

    def get_trading_signals_optimized(
        self, data: pd.DataFrame, fast_win: int = 7, slow_win: int = 25
    ) -> Dict[str, Any]:
        """
        优化版交易信号计算

        参数:
            data: 价格数据DataFrame
            fast_win: 快速移动平均窗口
            slow_win: 慢速移动平均窗口

        返回:
            包含交易信号的字典
        """
        # 检查缓存
        if self.cache:
            cached_result = self.cache.get(data, fast_win, slow_win)
            if cached_result:
                return cached_result

        try:
            with self.metrics.measure_signal_latency():
                # 数据验证
                if data is None or len(data) < max(fast_win, slow_win):
                    return self._get_empty_signals()

                # 计算移动平均
                fast_ma, slow_ma = self.calculate_moving_averages(data, fast_win, slow_win)

                # 检测交叉信号
                crossover = self.detect_crossover(fast_ma, slow_ma)

                # 计算ATR
                atr = self.calculate_atr_optimized(data)

                # 构建结果
                current_price = float(data["close"].iloc[-1])
                result = {
                    "current_price": current_price,
                    "fast_ma": float(fast_ma.iloc[-1]),
                    "slow_ma": float(slow_ma.iloc[-1]),
                    "buy_signal": crossover["buy_signal"],
                    "sell_signal": crossover["sell_signal"],
                    "atr": atr,
                    "timestamp": pd.Timestamp.now().isoformat(),
                    "data_points": len(data),
                }

                # 缓存结果
                if self.cache:
                    self.cache.set(data, fast_win, slow_win, result)

                return result

        except Exception as e:
            self.metrics.record_exception("signal_processor", e)
            self.logger.error(f"信号计算失败: {e}")
            return self._get_empty_signals()

    def _get_empty_signals(self) -> Dict[str, Any]:
        """返回空信号"""
        return {
            "current_price": 0.0,
            "fast_ma": 0.0,
            "slow_ma": 0.0,
            "buy_signal": False,
            "sell_signal": False,
            "atr": 0.0,
            "timestamp": pd.Timestamp.now().isoformat(),
            "data_points": 0,
            "error": "Insufficient data or calculation error",
        }

    def validate_signal_optimized(self, signals: Dict[str, Any], data: pd.DataFrame) -> bool:
        """优化版信号验证"""
        try:
            # 基础验证
            if not signals or "error" in signals:
                return False

            # 价格有效性验证
            if signals["current_price"] <= 0:
                return False

            # 移动平均有效性验证
            if signals["fast_ma"] <= 0 or signals["slow_ma"] <= 0:
                return False

            # ATR有效性验证
            if signals["atr"] < 0:
                return False

            # 数据量验证
            if signals["data_points"] < 2:
                return False

            # 信号逻辑验证（同时出现买卖信号是无效的）
            if signals["buy_signal"] and signals["sell_signal"]:
                return False

            return True

        except Exception as e:
            self.logger.error(f"信号验证失败: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if not self.cache:
            return {"enabled": False}

        return {
            "enabled": True,
            "size": len(self.cache.cache),
            "max_size": self.cache.max_size,
            "hit_rate": "需要实现命中率统计",
        }


# 全局优化实例
_optimized_processor: Optional[OptimizedSignalProcessor] = None


def get_optimized_processor() -> OptimizedSignalProcessor:
    """获取全局优化处理器实例"""
    global _optimized_processor
    if _optimized_processor is None:
        _optimized_processor = OptimizedSignalProcessor()
    return _optimized_processor


# 兼容性函数
def get_trading_signals_optimized(
    data: pd.DataFrame, fast_win: int = 7, slow_win: int = 25
) -> Dict[str, Any]:
    """优化版交易信号计算函数"""
    processor = get_optimized_processor()
    return processor.get_trading_signals_optimized(data, fast_win, slow_win)


def validate_signal_optimized(signals: Dict[str, Any], data: pd.DataFrame) -> bool:
    """优化版信号验证函数"""
    processor = get_optimized_processor()
    return processor.validate_signal_optimized(signals, data)
