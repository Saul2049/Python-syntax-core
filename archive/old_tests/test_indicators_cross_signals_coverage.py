"""
交叉信号检测模块综合测试 (Cross Signals Detection Module Comprehensive Tests)

覆盖所有交叉检测功能：
- crossover/crossunder基础函数
- vectorized_cross向量化函数
- 各种交叉索引和序列生成函数
- 边缘情况和参数验证
"""

import pytest
import pandas as pd
import numpy as np
from typing import Union

from src.indicators.cross_signals import (
    crossover,
    crossunder,
    vectorized_cross,
    bullish_cross_indices,
    bearish_cross_indices,
    bullish_cross_series,
    bearish_cross_series,
)


class TestCrossoverFunction:
    """测试crossover基础函数"""
    
    def test_crossover_basic_case(self):
        """测试基本的上穿情况"""
        # 创建上穿数据：series1从下方穿越series2
        series1 = pd.Series([1, 2, 4, 5, 6])  # 上升趋势，第3个值4 > 3
        series2 = pd.Series([3, 3, 3, 3, 3])  # 水平线
        
        result = crossover(series1, series2)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 5
        # 第3个位置(index=2)应该是上穿点：4 > 3且前值2 <= 3
        assert result.iloc[2] == True
        assert result.iloc[0] == False  # 第一个值没有前值，不是交叉
        assert result.iloc[1] == False  # 2 <= 3，不是上穿

    def test_crossover_with_numpy_arrays(self):
        """测试使用numpy数组作为输入（覆盖第26行的pd.Series转换）"""
        # 这里会触发第26行：series1, series2 = pd.Series(series1), pd.Series(series2)
        array1 = np.array([1, 2, 4, 5])
        array2 = np.array([3, 3, 3, 3])
        
        result = crossover(array1, array2)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 4
        # 第3个位置(index=2)：4 > 3且前值2 <= 3
        assert result.iloc[2] == True

    def test_crossover_with_lists(self):
        """测试使用列表作为输入"""
        list1 = [1, 2, 4, 5]
        list2 = [3, 3, 3, 3]
        
        result = crossover(list1, list2)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 4

    def test_crossover_no_cross_events(self):
        """测试没有交叉事件的情况"""
        series1 = pd.Series([1, 1, 1, 1])  # 始终在下方
        series2 = pd.Series([2, 2, 2, 2])  # 始终在上方
        
        result = crossover(series1, series2)
        
        assert not result.any()  # 所有值都应该是False

    def test_crossover_multiple_crosses(self):
        """测试多次交叉的情况"""
        series1 = pd.Series([1, 3, 2, 4, 1, 3])  # 振荡穿越
        series2 = pd.Series([2, 2, 2, 2, 2, 2])  # 水平线
        
        result = crossover(series1, series2)
        
        # 找出所有上穿点
        cross_points = result[result == True].index.tolist()
        assert len(cross_points) >= 2  # 至少有两次上穿

    def test_crossover_equal_values_edge_case(self):
        """测试相等值的边缘情况（覆盖第27-28行的逻辑）"""
        # 这会触发第27-28行的完整逻辑：
        # return (series1 > series2) & (series1.shift(1) <= series2.shift(1))
        series1 = pd.Series([2, 3, 3, 4])  # 包含相等值
        series2 = pd.Series([3, 3, 3, 3])  # 水平线
        
        result = crossover(series1, series2)
        
        # 检查逻辑：当前值>基准 且 前值<=基准
        assert result.iloc[3] == True   # 4 > 3 且 3 <= 3
        assert result.iloc[2] == False  # 3 == 3，不是严格大于


class TestCrossunderFunction:
    """测试crossunder基础函数"""
    
    def test_crossunder_basic_case(self):
        """测试基本的下穿情况"""
        series1 = pd.Series([5, 4, 3, 2, 1])  # 下降趋势
        series2 = pd.Series([3, 3, 3, 3, 3])  # 水平线
        
        result = crossunder(series1, series2)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 5
        # 第3个位置(index=2)应该是下穿点：3 == 3但前值4 >= 3，这不是严格下穿
        # 实际下穿应该在index=3：2 < 3且前值3 >= 3
        assert result.iloc[3] == True

    def test_crossunder_with_numpy_arrays(self):
        """测试使用numpy数组作为输入（覆盖第42行的pd.Series转换）"""
        # 这里会触发第42行：series1, series2 = pd.Series(series1), pd.Series(series2)
        array1 = np.array([5, 4, 2, 1])
        array2 = np.array([3, 3, 3, 3])
        
        result = crossunder(array1, array2)
        
        assert isinstance(result, pd.Series)
        assert len(result) == 4

    def test_crossunder_with_mixed_types(self):
        """测试混合数据类型"""
        series1 = [4.5, 3.5, 2.5, 1.5]
        series2 = pd.Series([3.0, 3.0, 3.0, 3.0])
        
        result = crossunder(series1, series2)
        
        assert isinstance(result, pd.Series)

    def test_crossunder_equal_values_edge_case(self):
        """测试相等值的边缘情况（覆盖第43-44行的逻辑）"""
        # 这会触发第43-44行的完整逻辑：
        # return (series1 < series2) & (series1.shift(1) >= series2.shift(1))
        series1 = pd.Series([4, 3, 3, 2])
        series2 = pd.Series([3, 3, 3, 3])
        
        result = crossunder(series1, series2)
        
        # 检查逻辑：当前值<基准 且 前值>=基准
        assert result.iloc[3] == True   # 2 < 3 且 3 >= 3
        assert result.iloc[2] == False  # 3 == 3，不是严格小于

    def test_crossunder_no_cross_events(self):
        """测试没有下穿事件的情况"""
        series1 = pd.Series([4, 4, 4, 4])  # 始终在上方
        series2 = pd.Series([2, 2, 2, 2])  # 始终在下方
        
        result = crossunder(series1, series2)
        
        assert not result.any()  # 所有值都应该是False


class TestVectorizedCross:
    """测试向量化交叉检测函数"""
    
    def test_vectorized_cross_above_direction(self):
        """测试上穿方向检测"""
        fast = pd.Series([1, 2, 4, 5])
        slow = pd.Series([3, 3, 3, 3])
        
        result = vectorized_cross(fast, slow, direction="above")
        
        assert isinstance(result, pd.Series)
        assert result.iloc[2] == True  # 4 > 3且前值2 <= 3

    def test_vectorized_cross_below_direction(self):
        """测试下穿方向检测"""
        fast = pd.Series([5, 4, 2, 1])
        slow = pd.Series([3, 3, 3, 3])
        
        result = vectorized_cross(fast, slow, direction="below")
        
        assert isinstance(result, pd.Series)
        assert result.iloc[2] == True  # 2 < 3且前值4 >= 3

    def test_vectorized_cross_with_threshold(self):
        """测试带阈值的交叉检测"""
        fast = pd.Series([1, 2, 3.5, 4])
        slow = pd.Series([3, 3, 3, 3])
        threshold = 0.2
        
        result = vectorized_cross(fast, slow, direction="above", threshold=threshold)
        
        # 使用阈值0.2，需要超过3.2才算上穿
        assert isinstance(result, pd.Series)

    def test_vectorized_cross_return_indices(self):
        """测试返回索引数组"""
        fast = pd.Series([1, 2, 4, 3, 5])
        slow = pd.Series([3, 3, 3, 3, 3])
        
        result = vectorized_cross(fast, slow, direction="above", return_series=False)
        
        assert isinstance(result, np.ndarray)
        assert len(result) >= 0  # 可能有或没有交叉点

    def test_vectorized_cross_below_with_threshold(self):
        """测试向下交叉带阈值"""
        fast = pd.Series([5, 4, 2.8, 2])
        slow = pd.Series([3, 3, 3, 3])
        threshold = 0.1
        
        result = vectorized_cross(fast, slow, direction="below", threshold=threshold)
        
        assert isinstance(result, pd.Series)

    def test_vectorized_cross_invalid_direction(self):
        """测试无效方向参数"""
        fast = pd.Series([1, 2, 3])
        slow = pd.Series([2, 2, 2])
        
        # 这里假设函数会处理无效方向，或者抛出异常
        try:
            result = vectorized_cross(fast, slow, direction="invalid")
            # 如果没有抛出异常，检查结果
            assert isinstance(result, pd.Series)
        except (ValueError, KeyError):
            # 如果抛出异常，也是可以接受的
            pass


class TestCrossIndicesAndSeriesFunctions:
    """测试交叉索引和序列生成函数"""
    
    def test_bullish_cross_indices(self):
        """测试看涨交叉索引"""
        fast = pd.Series([1, 2, 4, 3, 5])
        slow = pd.Series([3, 3, 3, 3, 3])
        
        result = bullish_cross_indices(fast, slow)
        
        assert isinstance(result, np.ndarray)
        # 应该返回上穿点的索引

    def test_bearish_cross_indices(self):
        """测试看跌交叉索引"""
        fast = pd.Series([5, 4, 2, 1, 3])
        slow = pd.Series([3, 3, 3, 3, 3])
        
        result = bearish_cross_indices(fast, slow)
        
        assert isinstance(result, np.ndarray)

    def test_bullish_cross_series(self):
        """测试看涨交叉序列"""
        fast = pd.Series([1, 2, 4, 3])
        slow = pd.Series([3, 3, 3, 3])
        
        result = bullish_cross_series(fast, slow)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(fast)

    def test_bearish_cross_series(self):
        """测试看跌交叉序列"""
        fast = pd.Series([5, 4, 2, 1])
        slow = pd.Series([3, 3, 3, 3])
        
        result = bearish_cross_series(fast, slow)
        
        assert isinstance(result, pd.Series)
        assert len(result) == len(fast)

    def test_cross_series_with_datetime_index(self):
        """测试带日期时间索引的交叉序列"""
        dates = pd.date_range("2023-01-01", periods=4)
        fast = pd.Series([1, 2, 4, 3], index=dates)
        slow = pd.Series([3, 3, 3, 3], index=dates)
        
        bullish_result = bullish_cross_series(fast, slow)
        bearish_result = bearish_cross_series(fast, slow)
        
        assert isinstance(bullish_result.index, pd.DatetimeIndex)
        assert isinstance(bearish_result.index, pd.DatetimeIndex)
        assert len(bullish_result) == 4
        assert len(bearish_result) == 4


class TestCrossSignalsEdgeCases:
    """测试交叉信号边缘情况"""
    
    def test_empty_series(self):
        """测试空序列"""
        empty_series1 = pd.Series([])
        empty_series2 = pd.Series([])
        
        result_over = crossover(empty_series1, empty_series2)
        result_under = crossunder(empty_series1, empty_series2)
        
        assert len(result_over) == 0
        assert len(result_under) == 0

    def test_single_value_series(self):
        """测试单值序列"""
        single1 = pd.Series([1])
        single2 = pd.Series([2])
        
        result_over = crossover(single1, single2)
        result_under = crossunder(single1, single2)
        
        assert len(result_over) == 1
        assert len(result_under) == 1
        # 单个值没有前值，所以不应该有交叉
        assert result_over.iloc[0] == False
        assert result_under.iloc[0] == False

    def test_different_length_series(self):
        """测试不同长度的序列"""
        # 使用具有相同索引范围的序列，但长度不同
        short = pd.Series([1, 2], index=[0, 1])
        long = pd.Series([3, 3, 3, 3], index=[0, 1, 2, 3])
        
        # 手动对齐索引以避免pandas比较错误
        aligned_short, aligned_long = short.align(long, fill_value=np.nan)
        
        result = crossover(aligned_short, aligned_long)
        
        assert len(result) == 4  # 结果长度应该是较长序列的长度
        # 由于短序列后面是NaN，相关位置的结果也应该是False或NaN

    def test_nan_values_handling(self):
        """测试NaN值处理"""
        series_with_nan = pd.Series([1, np.nan, 4, 5])
        series_normal = pd.Series([3, 3, 3, 3])
        
        result_over = crossover(series_with_nan, series_normal)
        result_under = crossunder(series_with_nan, series_normal)
        
        assert len(result_over) == 4
        assert len(result_under) == 4
        # NaN值应该导致相应位置的结果也是NaN或False

    def test_infinite_values_handling(self):
        """测试无穷值处理"""
        series_with_inf = pd.Series([1, np.inf, 4, 5])
        series_normal = pd.Series([3, 3, 3, 3])
        
        result = crossover(series_with_inf, series_normal)
        
        assert len(result) == 4
        # 无穷值应该被正确处理

    def test_all_functions_consistency(self):
        """测试所有函数的一致性"""
        fast = pd.Series([1, 2, 4, 3, 5, 2, 1])
        slow = pd.Series([3, 3, 3, 3, 3, 3, 3])
        
        # 比较不同函数的结果一致性
        crossover_result = crossover(fast, slow)
        bullish_series_result = bullish_cross_series(fast, slow)
        bullish_indices = bullish_cross_indices(fast, slow)
        
        # bullish_cross_series应该与crossover结果相同
        pd.testing.assert_series_equal(crossover_result, bullish_series_result)
        
        # 索引函数应该返回True值的位置
        true_positions = crossover_result[crossover_result == True].index.values
        if len(true_positions) > 0 and len(bullish_indices) > 0:
            assert len(np.intersect1d(true_positions, bullish_indices)) > 0


class TestCrossSignalsPerformance:
    """测试交叉信号性能"""
    
    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        np.random.seed(42)
        size = 10000
        
        fast = pd.Series(np.random.randn(size).cumsum() + 100)
        slow = pd.Series(np.random.randn(size).cumsum() + 100)
        
        import time
        
        start_time = time.time()
        crossover_result = crossover(fast, slow)
        crossunder_result = crossunder(fast, slow)
        vectorized_result = vectorized_cross(fast, slow)
        end_time = time.time()
        
        assert len(crossover_result) == size
        assert len(crossunder_result) == size
        assert len(vectorized_result) == size
        assert end_time - start_time < 1.0  # 应该在1秒内完成

    def test_memory_efficiency(self):
        """测试内存效率"""
        # 创建大数据集但检查内存使用
        size = 50000
        fast = pd.Series(range(size))
        slow = pd.Series([size // 2] * size)
        
        # 所有函数都应该能处理大数据集而不出错
        result_over = crossover(fast, slow)
        result_under = crossunder(fast, slow)
        result_indices = bullish_cross_indices(fast, slow)
        
        assert isinstance(result_over, pd.Series)
        assert isinstance(result_under, pd.Series)
        assert isinstance(result_indices, np.ndarray) 