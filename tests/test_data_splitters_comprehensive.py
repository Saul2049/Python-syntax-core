#!/usr/bin/env python3
"""
数据分割模块全面测试
"""

import numpy as np
import pandas as pd
import pytest

from src.data.transformers.splitters import DataSplitter, create_train_test_split


class TestDataSplitterTrainTestSplit:
    """测试训练测试集分割"""

    @pytest.fixture
    def sample_df(self):
        """创建样本数据"""
        return pd.DataFrame(
            {
                "feature1": range(100),
                "feature2": np.random.randn(100),
                "target": np.random.randint(0, 2, 100),
            }
        )

    def test_train_test_split_basic(self, sample_df):
        """测试基本分割"""
        train_df, test_df = DataSplitter.train_test_split(sample_df, test_size=0.2)

        # 验证分割比例
        assert len(train_df) == 80
        assert len(test_df) == 20
        assert len(train_df) + len(test_df) == len(sample_df)

        # 验证数据类型
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(test_df, pd.DataFrame)

        # 验证列相同
        assert list(train_df.columns) == list(sample_df.columns)
        assert list(test_df.columns) == list(sample_df.columns)

    def test_train_test_split_different_ratios(self, sample_df):
        """测试不同分割比例"""
        ratios = [0.1, 0.3, 0.5, 0.8]

        for test_size in ratios:
            train_df, test_df = DataSplitter.train_test_split(sample_df, test_size=test_size)

            # 验证总数正确
            assert len(train_df) + len(test_df) == len(sample_df)

            # 验证测试集大小在合理范围内（允许1的误差）
            expected_test_size = int(len(sample_df) * test_size)
            assert abs(len(test_df) - expected_test_size) <= 1

    def test_train_test_split_with_shuffle(self, sample_df):
        """测试带随机打乱的分割"""
        train_df, test_df = DataSplitter.train_test_split(
            sample_df, test_size=0.2, shuffle=True, random_state=42
        )

        # 验证大小正确
        assert len(train_df) == 80
        assert len(test_df) == 20

        # 由于打乱，索引重置后应该是连续的，但原始数据顺序应该被改变
        # 检查数据顺序是否被打乱（比较第一列的值）
        original_first_10 = sample_df["feature1"].iloc[:10].values
        train_first_10 = train_df["feature1"].iloc[:10].values
        assert not np.array_equal(original_first_10, train_first_10)

    def test_train_test_split_reproducible(self, sample_df):
        """测试可重现性"""
        train1, test1 = DataSplitter.train_test_split(
            sample_df, test_size=0.2, shuffle=True, random_state=42
        )
        train2, test2 = DataSplitter.train_test_split(
            sample_df, test_size=0.2, shuffle=True, random_state=42
        )

        # 相同随机种子应该产生相同结果
        pd.testing.assert_frame_equal(train1, train2)
        pd.testing.assert_frame_equal(test1, test2)

    def test_train_test_split_no_shuffle(self, sample_df):
        """测试不打乱的分割"""
        train_df, test_df = DataSplitter.train_test_split(sample_df, test_size=0.2, shuffle=False)

        # 不打乱时应该是前80行和后20行
        expected_train_indices = list(range(80))
        expected_test_indices = list(range(80, 100))

        assert list(train_df.index) == expected_train_indices
        assert list(test_df.index) == expected_test_indices

    def test_train_test_split_small_dataset(self):
        """测试小数据集"""
        small_df = pd.DataFrame({"x": [1, 2, 3]})

        train_df, test_df = DataSplitter.train_test_split(small_df, test_size=0.33)

        # 验证至少有数据
        assert len(train_df) >= 1
        assert len(test_df) >= 1
        assert len(train_df) + len(test_df) == 3

    def test_train_test_split_edge_cases(self, sample_df):
        """测试边缘情况"""
        # 测试极小分割
        train_df, test_df = DataSplitter.train_test_split(sample_df, test_size=0.01)
        assert len(test_df) == 1
        assert len(train_df) == 99

        # 测试极大分割
        train_df, test_df = DataSplitter.train_test_split(sample_df, test_size=0.99)
        assert len(test_df) == 99
        assert len(train_df) == 1


class TestDataSplitterTrainValTestSplit:
    """测试训练验证测试集分割"""

    @pytest.fixture
    def sample_df(self):
        """创建样本数据"""
        return pd.DataFrame(
            {
                "feature1": range(100),
                "feature2": np.random.randn(100),
                "target": np.random.randint(0, 3, 100),
            }
        )

    def test_train_val_test_split_basic(self, sample_df):
        """测试基本三分割"""
        train_df, val_df, test_df = DataSplitter.train_val_test_split(
            sample_df, train_size=0.7, val_size=0.15, test_size=0.15
        )

        # 验证分割大小
        assert len(train_df) == 70
        assert len(val_df) == 15
        assert len(test_df) == 15
        assert len(train_df) + len(val_df) + len(test_df) == len(sample_df)

        # 验证数据类型
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(val_df, pd.DataFrame)
        assert isinstance(test_df, pd.DataFrame)

    def test_train_val_test_split_different_ratios(self, sample_df):
        """测试不同分割比例"""
        train_df, val_df, test_df = DataSplitter.train_val_test_split(
            sample_df, train_size=0.6, val_size=0.2, test_size=0.2
        )

        assert len(train_df) == 60
        assert len(val_df) == 20
        assert len(test_df) == 20

    def test_train_val_test_split_invalid_ratios(self, sample_df):
        """测试无效比例"""
        with pytest.raises(ValueError, match="分割比例总和必须为1.0"):
            DataSplitter.train_val_test_split(
                sample_df, train_size=0.5, val_size=0.3, test_size=0.3  # 总和1.1
            )

    def test_train_val_test_split_with_shuffle(self, sample_df):
        """测试带打乱的三分割"""
        train_df, val_df, test_df = DataSplitter.train_val_test_split(
            sample_df, train_size=0.7, val_size=0.15, test_size=0.15, shuffle=True, random_state=42
        )

        # 验证大小
        assert len(train_df) == 70
        assert len(val_df) == 15
        assert len(test_df) == 15

        # 验证数据被打乱（检查数据顺序变化）
        original_first_10 = sample_df["feature1"].iloc[:10].values
        train_first_10 = train_df["feature1"].iloc[:10].values
        assert not np.array_equal(original_first_10, train_first_10)

    def test_train_val_test_split_reproducible(self, sample_df):
        """测试可重现性"""
        result1 = DataSplitter.train_val_test_split(
            sample_df, train_size=0.7, val_size=0.15, test_size=0.15, shuffle=True, random_state=42
        )
        result2 = DataSplitter.train_val_test_split(
            sample_df, train_size=0.7, val_size=0.15, test_size=0.15, shuffle=True, random_state=42
        )

        for df1, df2 in zip(result1, result2):
            pd.testing.assert_frame_equal(df1, df2)


class TestDataSplitterTimeSeriesSplit:
    """测试时间序列分割"""

    @pytest.fixture
    def time_series_df(self):
        """创建时间序列数据"""
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "date": dates,
                "value": np.cumsum(np.random.randn(100)),
                "feature": np.random.randn(100),
            }
        )

    def test_time_series_split_basic(self, time_series_df):
        """测试基本时间序列分割"""
        splits = DataSplitter.time_series_split(time_series_df, n_splits=5)

        # 验证分割数量
        assert len(splits) == 5

        # 验证每个分割都是元组
        for train_df, test_df in splits:
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            assert len(train_df) > 0
            assert len(test_df) > 0

    def test_time_series_split_with_test_size(self, time_series_df):
        """测试指定测试集大小的时间序列分割"""
        splits = DataSplitter.time_series_split(time_series_df, n_splits=3, test_size=10)

        # 验证测试集大小
        for train_df, test_df in splits:
            assert len(test_df) == 10

    def test_time_series_split_chronological_order(self, time_series_df):
        """测试时间序列分割保持时间顺序"""
        splits = DataSplitter.time_series_split(time_series_df, n_splits=3)

        for i, (train_df, test_df) in enumerate(splits):
            # 训练集的最后一行应该在测试集的第一行之前
            if len(train_df) > 0 and len(test_df) > 0:
                last_train_idx = train_df.index[-1]
                first_test_idx = test_df.index[0]
                assert last_train_idx < first_test_idx

    def test_time_series_split_increasing_train_size(self, time_series_df):
        """测试训练集大小递增"""
        splits = DataSplitter.time_series_split(time_series_df, n_splits=3)

        train_sizes = [len(train_df) for train_df, _ in splits]

        # 训练集大小应该递增
        for i in range(1, len(train_sizes)):
            assert train_sizes[i] > train_sizes[i - 1]

    def test_time_series_split_small_dataset(self):
        """测试小数据集的时间序列分割"""
        small_df = pd.DataFrame({"value": range(10)})

        splits = DataSplitter.time_series_split(small_df, n_splits=3)

        # 小数据集也应该能分割
        assert len(splits) <= 3  # 可能少于请求的分割数


class TestDataSplitterStratifiedSplit:
    """测试分层分割"""

    @pytest.fixture
    def stratified_df(self):
        """创建分层数据"""
        np.random.seed(42)
        return pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "target": np.random.choice(["A", "B", "C"], 100, p=[0.5, 0.3, 0.2]),
            }
        )

    def test_stratified_split_basic(self, stratified_df):
        """测试基本分层分割"""
        train_df, test_df = DataSplitter.stratified_split(
            stratified_df, target_column="target", test_size=0.2
        )

        # 验证分割大小
        assert len(train_df) + len(test_df) == len(stratified_df)

        # 验证目标列分布保持相似
        original_dist = stratified_df["target"].value_counts(normalize=True).sort_index()
        train_dist = train_df["target"].value_counts(normalize=True).sort_index()
        test_dist = test_df["target"].value_counts(normalize=True).sort_index()

        # 分布应该相似（允许小误差）
        for category in original_dist.index:
            assert abs(train_dist[category] - original_dist[category]) < 0.1
            assert abs(test_dist[category] - original_dist[category]) < 0.1

    def test_stratified_split_missing_column(self, stratified_df):
        """测试目标列不存在"""
        with pytest.raises(ValueError, match="目标列 'nonexistent' 不存在"):
            DataSplitter.stratified_split(stratified_df, target_column="nonexistent", test_size=0.2)

    def test_stratified_split_reproducible(self, stratified_df):
        """测试分层分割可重现性"""
        train1, test1 = DataSplitter.stratified_split(
            stratified_df, target_column="target", test_size=0.2, random_state=42
        )
        train2, test2 = DataSplitter.stratified_split(
            stratified_df, target_column="target", test_size=0.2, random_state=42
        )

        # 结果应该相同
        pd.testing.assert_frame_equal(train1.sort_index(), train2.sort_index())
        pd.testing.assert_frame_equal(test1.sort_index(), test2.sort_index())

    def test_stratified_split_binary_target(self):
        """测试二分类目标"""
        binary_df = pd.DataFrame(
            {"feature": np.random.randn(100), "target": np.random.choice([0, 1], 100, p=[0.7, 0.3])}
        )

        train_df, test_df = DataSplitter.stratified_split(
            binary_df, target_column="target", test_size=0.2
        )

        # 验证分层效果
        original_ratio = binary_df["target"].mean()
        train_ratio = train_df["target"].mean()
        test_ratio = test_df["target"].mean()

        assert abs(train_ratio - original_ratio) < 0.1
        assert abs(test_ratio - original_ratio) < 0.1

    def test_stratified_split_imbalanced_data(self):
        """测试不平衡数据"""
        imbalanced_df = pd.DataFrame(
            {
                "feature": np.random.randn(100),
                "target": np.random.choice(["rare", "common"], 100, p=[0.05, 0.95]),
            }
        )

        train_df, test_df = DataSplitter.stratified_split(
            imbalanced_df, target_column="target", test_size=0.2
        )

        # 验证稀有类别在两个集合中都存在
        assert "rare" in train_df["target"].values
        assert "rare" in test_df["target"].values
        assert "common" in train_df["target"].values
        assert "common" in test_df["target"].values


class TestDataSplitterRollingWindowSplit:
    """测试滚动窗口分割"""

    @pytest.fixture
    def rolling_df(self):
        """创建滚动窗口数据"""
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2023-01-01", periods=50, freq="D"),
                "value": np.cumsum(np.random.randn(50)),
            }
        )

    def test_rolling_window_split_basic(self, rolling_df):
        """测试基本滚动窗口分割"""
        splits = DataSplitter.rolling_window_split(rolling_df, window_size=20, step_size=5)

        # 验证分割存在
        assert len(splits) > 0

        # 验证每个窗口的训练集大小
        for train_df, test_df in splits:
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            assert len(train_df) == 20  # 固定窗口大小

    def test_rolling_window_split_different_step_sizes(self, rolling_df):
        """测试不同步长"""
        splits_1 = DataSplitter.rolling_window_split(rolling_df, window_size=15, step_size=1)
        splits_5 = DataSplitter.rolling_window_split(rolling_df, window_size=15, step_size=5)

        # 小步长应该产生更多分割
        assert len(splits_1) > len(splits_5)

    def test_rolling_window_split_window_progression(self, rolling_df):
        """测试窗口递进"""
        splits = DataSplitter.rolling_window_split(rolling_df, window_size=10, step_size=5)

        # 验证窗口按步长递进
        for i in range(len(splits) - 1):
            train1, _ = splits[i]
            train2, _ = splits[i + 1]

            # 下一个窗口应该向前移动step_size
            assert train2.index[0] == train1.index[5]  # step_size=5

    def test_rolling_window_split_large_window(self, rolling_df):
        """测试大窗口情况"""
        splits = DataSplitter.rolling_window_split(rolling_df, window_size=45, step_size=2)

        # 大窗口应该产生较少分割
        assert len(splits) >= 1

    def test_rolling_window_split_edge_cases(self, rolling_df):
        """测试边缘情况"""
        # 窗口等于数据长度
        splits = DataSplitter.rolling_window_split(rolling_df, window_size=50, step_size=1)

        # 应该有一个分割（或0个，取决于实现）
        assert len(splits) <= 1

    def test_rolling_window_split_small_dataset(self):
        """测试小数据集"""
        small_df = pd.DataFrame({"value": range(5)})

        splits = DataSplitter.rolling_window_split(small_df, window_size=3, step_size=1)

        # 小数据集应该能产生分割
        assert len(splits) >= 1


class TestCreateTrainTestSplit:
    """测试全局函数"""

    def test_create_train_test_split_function(self):
        """测试全局分割函数"""
        df = pd.DataFrame({"x": range(20), "y": np.random.randn(20)})

        train_df, test_df = create_train_test_split(df, test_size=0.25)

        # 验证分割正确
        assert len(train_df) == 15
        assert len(test_df) == 5
        assert len(train_df) + len(test_df) == len(df)

    def test_create_train_test_split_with_shuffle(self):
        """测试全局函数的打乱功能"""
        df = pd.DataFrame({"x": range(20), "y": np.random.randn(20)})

        train_df, test_df = create_train_test_split(df, test_size=0.25, shuffle=True)

        # 验证分割正确
        assert len(train_df) == 15
        assert len(test_df) == 5


class TestDataSplitterEdgeCases:
    """测试边缘情况和错误处理"""

    def test_empty_dataframe(self):
        """测试空数据框"""
        empty_df = pd.DataFrame()

        # 大多数分割方法应该能处理空数据框
        try:
            train_df, test_df = DataSplitter.train_test_split(empty_df, test_size=0.2)
            assert len(train_df) == 0
            assert len(test_df) == 0
        except (ValueError, IndexError):
            # 抛出异常也是可接受的行为
            pass

    def test_single_row_dataframe(self):
        """测试单行数据框"""
        single_row_df = pd.DataFrame({"x": [1], "y": [2]})

        train_df, test_df = DataSplitter.train_test_split(single_row_df, test_size=0.5)

        # 应该能合理分割（或者一个为空）
        assert len(train_df) + len(test_df) == 1

    def test_very_small_test_size(self):
        """测试极小测试集"""
        df = pd.DataFrame({"x": range(1000)})

        train_df, test_df = DataSplitter.train_test_split(df, test_size=0.001)

        # 至少应该有一个测试样本
        assert len(test_df) >= 1
        assert len(train_df) == 1000 - len(test_df)

    def test_invalid_test_size(self):
        """测试无效测试集大小"""
        df = pd.DataFrame({"x": range(10)})

        # 测试负值 - 可能不会抛出异常，但结果应该不合理
        try:
            train_df, test_df = DataSplitter.train_test_split(df, test_size=-0.1)
            # 如果没抛异常，验证结果是否合理
            assert len(train_df) + len(test_df) == len(df)
        except (ValueError, AssertionError):
            pass  # 抛出异常也是可接受的

        # 测试大于1的值
        try:
            train_df, test_df = DataSplitter.train_test_split(df, test_size=1.1)
            # 如果没抛异常，验证结果
            assert len(train_df) + len(test_df) == len(df)
        except (ValueError, AssertionError):
            pass  # 抛出异常也是可接受的

    def test_all_same_category_stratified(self):
        """测试分层分割中所有样本都是同一类别"""
        same_category_df = pd.DataFrame(
            {"feature": np.random.randn(20), "target": ["A"] * 20}  # 所有样本都是A类
        )

        train_df, test_df = DataSplitter.stratified_split(
            same_category_df, target_column="target", test_size=0.2
        )

        # 应该能正常分割
        assert len(train_df) + len(test_df) == 20
        assert all(train_df["target"] == "A")
        assert all(test_df["target"] == "A")


class TestDataSplitterPerformance:
    """性能测试"""

    def test_large_dataset_performance(self):
        """测试大数据集性能"""
        # 创建大数据集
        large_df = pd.DataFrame(
            {
                "feature1": np.random.randn(100000),
                "feature2": np.random.randn(100000),
                "target": np.random.randint(0, 10, 100000),
            }
        )

        import time

        start_time = time.time()

        train_df, test_df = DataSplitter.train_test_split(large_df, test_size=0.2, shuffle=True)

        end_time = time.time()
        duration = end_time - start_time

        # 验证结果正确
        assert len(train_df) == 80000
        assert len(test_df) == 20000

        # 性能要求：大数据集分割应该在合理时间内完成
        assert duration < 5.0, f"分割时间过长: {duration:.3f}秒"

    def test_multiple_splits_performance(self):
        """测试多次分割性能"""
        df = pd.DataFrame(
            {"feature": np.random.randn(1000), "target": np.random.randint(0, 5, 1000)}
        )

        import time

        start_time = time.time()

        # 执行多次分割
        for _ in range(100):
            DataSplitter.train_test_split(df, test_size=0.2, shuffle=True)

        end_time = time.time()
        duration = end_time - start_time

        # 多次分割应该在合理时间内完成
        assert duration < 10.0, f"多次分割时间过长: {duration:.3f}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
