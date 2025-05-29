"""
数据转换器模块 (Data Transformers Module)

提供数据转换和预处理功能，包括：
- 数据归一化和标准化
- 时间序列预处理
- 数据分割
- 缺失值处理
"""

from typing import List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# 可选导入sklearn
try:
    from sklearn.preprocessing import MinMaxScaler, StandardScaler

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


class DataNormalizer:
    """数据归一化器类"""

    def __init__(self, method: str = "minmax", feature_range: Tuple[float, float] = (0, 1)):
        """
        初始化数据归一化器

        参数:
            method: 归一化方法 ('minmax', 'standard', 'robust')
            feature_range: MinMax归一化的范围
        """
        self.method = method.lower()
        self.feature_range = feature_range
        self.scaler = None
        self._initialize_scaler()

    def _initialize_scaler(self):
        """初始化归一化器"""
        if not HAS_SKLEARN:
            print("⚠️ 警告: sklearn未安装，使用简化实现")
            self.scaler = None
            return

        if self.method == "minmax":
            self.scaler = MinMaxScaler(feature_range=self.feature_range)
        elif self.method == "standard":
            self.scaler = StandardScaler()
        elif self.method == "robust":
            from sklearn.preprocessing import RobustScaler

            self.scaler = RobustScaler()
        else:
            raise ValueError(f"不支持的归一化方法: {self.method}")

    def fit_transform(self, data: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """
        训练并转换数据

        参数:
            data: 要归一化的数据

        返回:
            归一化后的数据
        """
        if not HAS_SKLEARN:
            return self._simple_normalize(data)

        if isinstance(data, pd.DataFrame):
            normalized_data = pd.DataFrame(
                self.scaler.fit_transform(data), columns=data.columns, index=data.index
            )
        else:  # pd.Series
            normalized_data = pd.Series(
                self.scaler.fit_transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name,
            )

        return normalized_data

    def _simple_normalize(
        self, data: Union[pd.DataFrame, pd.Series]
    ) -> Union[pd.DataFrame, pd.Series]:
        """简化的归一化实现（不使用sklearn）"""
        if self.method == "minmax":
            min_val = data.min()
            max_val = data.max()
            normalized = (data - min_val) / (max_val - min_val)
            # 缩放到指定范围
            return (
                normalized * (self.feature_range[1] - self.feature_range[0]) + self.feature_range[0]
            )
        elif self.method == "standard":
            return (data - data.mean()) / data.std()
        else:
            raise ValueError(f"简化实现不支持方法: {self.method}")

    def transform(self, data: Union[pd.DataFrame, pd.Series]) -> Union[pd.DataFrame, pd.Series]:
        """
        使用已训练的归一化器转换数据

        参数:
            data: 要转换的数据

        返回:
            转换后的数据
        """
        if not HAS_SKLEARN:
            return self._simple_normalize(data)

        if self.scaler is None:
            raise ValueError("归一化器未训练，请先调用fit_transform方法")

        if isinstance(data, pd.DataFrame):
            normalized_data = pd.DataFrame(
                self.scaler.transform(data), columns=data.columns, index=data.index
            )
        else:  # pd.Series
            normalized_data = pd.Series(
                self.scaler.transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name,
            )

        return normalized_data

    def inverse_transform(
        self, data: Union[pd.DataFrame, pd.Series]
    ) -> Union[pd.DataFrame, pd.Series]:
        """
        反向转换数据

        参数:
            data: 已归一化的数据

        返回:
            原始尺度的数据
        """
        if not HAS_SKLEARN:
            print("⚠️ 警告: 简化实现不支持inverse_transform")
            return data

        if self.scaler is None:
            raise ValueError("归一化器未训练")

        if isinstance(data, pd.DataFrame):
            original_data = pd.DataFrame(
                self.scaler.inverse_transform(data), columns=data.columns, index=data.index
            )
        else:  # pd.Series
            original_data = pd.Series(
                self.scaler.inverse_transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name,
            )

        return original_data


class TimeSeriesProcessor:
    """时间序列处理器类"""

    @staticmethod
    def create_sequences(
        data: np.ndarray, seq_length: int, pred_length: int = 1, step: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        为时间序列预测创建序列数据

        参数:
            data: 输入数据数组
            seq_length: 每个序列的长度（滑动窗口大小）
            pred_length: 预测长度
            step: 滑动步长

        返回:
            (X序列, Y目标值)
        """
        X, y = [], []

        for i in range(0, len(data) - seq_length - pred_length + 1, step):
            X.append(data[i : (i + seq_length)])
            y.append(data[i + seq_length : (i + seq_length + pred_length)])

        return np.array(X), np.array(y)

    @staticmethod
    def create_lagged_features(
        df: pd.DataFrame, columns: List[str], lags: List[int]
    ) -> pd.DataFrame:
        """
        创建滞后特征

        参数:
            df: 原始DataFrame
            columns: 要创建滞后特征的列名
            lags: 滞后期数列表

        返回:
            包含滞后特征的DataFrame
        """
        df_lagged = df.copy()

        for col in columns:
            if col not in df.columns:
                print(f"⚠️ 警告: 列 '{col}' 不存在，跳过")
                continue

            for lag in lags:
                df_lagged[f"{col}_lag_{lag}"] = df[col].shift(lag)

        return df_lagged

    @staticmethod
    def create_rolling_features(
        df: pd.DataFrame,
        columns: List[str],
        windows: List[int],
        functions: List[str] = ["mean", "std", "min", "max"],
    ) -> pd.DataFrame:
        """
        创建滚动统计特征

        参数:
            df: 原始DataFrame
            columns: 要创建滚动特征的列名
            windows: 滚动窗口大小列表
            functions: 统计函数列表

        返回:
            包含滚动特征的DataFrame
        """
        df_rolling = df.copy()

        for col in columns:
            if col not in df.columns:
                print(f"⚠️ 警告: 列 '{col}' 不存在，跳过")
                continue

            for window in windows:
                rolling_obj = df[col].rolling(window=window)

                for func in functions:
                    if hasattr(rolling_obj, func):
                        df_rolling[f"{col}_rolling_{func}_{window}"] = getattr(rolling_obj, func)()

        return df_rolling

    @staticmethod
    def resample_data(
        df: pd.DataFrame, period: str, agg_methods: Optional[dict] = None
    ) -> pd.DataFrame:
        """
        重采样时间序列数据

        参数:
            df: 时间序列DataFrame (需要DatetimeIndex)
            period: 重采样周期 ('1D', '1H', '1W', etc.)
            agg_methods: 聚合方法字典

        返回:
            重采样后的DataFrame
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame必须有DatetimeIndex")

        if agg_methods is None:
            # 默认聚合方法
            agg_methods = {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }

        # 只使用存在的列
        available_methods = {
            col: method for col, method in agg_methods.items() if col in df.columns
        }

        # 对于其他数值列，使用mean
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in available_methods:
                available_methods[col] = "mean"

        return df.resample(period).agg(available_methods)


class DataSplitter:
    """数据分割器类"""

    @staticmethod
    def train_test_split(
        df: pd.DataFrame,
        test_size: float = 0.2,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        创建训练集和测试集

        参数:
            df: 要分割的DataFrame
            test_size: 测试集大小比例
            shuffle: 是否打乱数据
            random_state: 随机种子

        返回:
            (训练集DataFrame, 测试集DataFrame)
        """
        if shuffle:
            if random_state is not None:
                np.random.seed(random_state)
            shuffled_df = df.sample(frac=1).reset_index(drop=True)
        else:
            shuffled_df = df.copy()

        # 计算分割点
        split_idx = int(len(shuffled_df) * (1 - test_size))

        # 分割数据
        train_df = shuffled_df.iloc[:split_idx]
        test_df = shuffled_df.iloc[split_idx:]

        return train_df, test_df

    @staticmethod
    def train_val_test_split(
        df: pd.DataFrame,
        train_size: float = 0.7,
        val_size: float = 0.15,
        test_size: float = 0.15,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        创建训练集、验证集和测试集

        参数:
            df: 要分割的DataFrame
            train_size: 训练集比例
            val_size: 验证集比例
            test_size: 测试集比例
            shuffle: 是否打乱数据
            random_state: 随机种子

        返回:
            (训练集, 验证集, 测试集)
        """
        # 验证比例总和
        if abs(train_size + val_size + test_size - 1.0) > 1e-6:
            raise ValueError("训练集、验证集和测试集比例之和必须等于1.0")

        if shuffle:
            if random_state is not None:
                np.random.seed(random_state)
            shuffled_df = df.sample(frac=1).reset_index(drop=True)
        else:
            shuffled_df = df.copy()

        # 计算分割点
        train_end = int(len(shuffled_df) * train_size)
        val_end = int(len(shuffled_df) * (train_size + val_size))

        # 分割数据
        train_df = shuffled_df.iloc[:train_end]
        val_df = shuffled_df.iloc[train_end:val_end]
        test_df = shuffled_df.iloc[val_end:]

        return train_df, val_df, test_df

    @staticmethod
    def time_series_split(
        df: pd.DataFrame, n_splits: int = 5, test_size: Optional[int] = None
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        时间序列交叉验证分割

        参数:
            df: 时间序列DataFrame
            n_splits: 分割数量
            test_size: 测试集大小

        返回:
            分割结果列表
        """
        # 简单实现时间序列分割（不依赖sklearn）
        if test_size is None:
            test_size = len(df) // n_splits

        splits = []
        total_size = len(df)

        for i in range(n_splits):
            # 计算训练集结束位置
            train_end = total_size - (n_splits - i) * test_size
            test_start = train_end
            test_end = test_start + test_size

            if test_end > total_size:
                test_end = total_size

            train_df = df.iloc[:train_end]
            test_df = df.iloc[test_start:test_end]

            if len(test_df) > 0:
                splits.append((train_df, test_df))

        return splits


class MissingValueHandler:
    """缺失值处理器类"""

    @staticmethod
    def fill_missing_values(
        df: pd.DataFrame, method: str = "forward", columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        填充缺失值

        参数:
            df: 包含缺失值的DataFrame
            method: 填充方法 ('forward', 'backward', 'mean', 'median', 'zero')
            columns: 要处理的列名列表

        返回:
            填充后的DataFrame
        """
        df_filled = df.copy()
        target_columns = MissingValueHandler._get_target_columns(df, columns)

        for col in target_columns:
            df_filled = MissingValueHandler._fill_column_missing_values(df_filled, col, method)

        return df_filled

    @staticmethod
    def _get_target_columns(df: pd.DataFrame, columns: Optional[List[str]]) -> List[str]:
        """获取要处理的目标列"""
        if columns is None:
            return list(df.columns)

        return [col for col in columns if col in df.columns]

    @staticmethod
    def _fill_column_missing_values(df: pd.DataFrame, col: str, method: str) -> pd.DataFrame:
        """填充单个列的缺失值"""
        if method == "forward":
            df[col] = df[col].fillna(method="ffill")
        elif method == "backward":
            df[col] = df[col].fillna(method="bfill")
        elif method == "mean":
            df[col] = df[col].fillna(df[col].mean())
        elif method == "median":
            df[col] = df[col].fillna(df[col].median())
        elif method == "zero":
            df[col] = df[col].fillna(0)
        else:
            raise ValueError(f"不支持的填充方法: {method}")

        return df

    @staticmethod
    def interpolate_missing_values(
        df: pd.DataFrame, method: str = "linear", columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        插值填充缺失值

        参数:
            df: 包含缺失值的DataFrame
            method: 插值方法 ('linear', 'time', 'cubic', 'spline')
            columns: 要处理的列名列表

        返回:
            插值后的DataFrame
        """
        df_interpolated = df.copy()

        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns

        for col in columns:
            if col not in df.columns:
                continue

            df_interpolated[col] = df_interpolated[col].interpolate(method=method)

        return df_interpolated


# 便捷函数
def normalize_data(
    data: Union[pd.DataFrame, pd.Series],
    method: str = "minmax",
    feature_range: Tuple[float, float] = (0, 1),
) -> Union[pd.DataFrame, pd.Series]:
    """
    便捷函数：数据归一化

    参数:
        data: 要归一化的数据
        method: 归一化方法
        feature_range: 归一化范围

    返回:
        归一化后的数据
    """
    normalizer = DataNormalizer(method, feature_range)
    return normalizer.fit_transform(data)


def create_train_test_split(
    df: pd.DataFrame, test_size: float = 0.2, shuffle: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    便捷函数：创建训练测试集

    参数:
        df: 要分割的DataFrame
        test_size: 测试集比例
        shuffle: 是否打乱

    返回:
        (训练集, 测试集)
    """
    return DataSplitter.train_test_split(df, test_size, shuffle)


def create_sequences(
    data: np.ndarray, seq_length: int, pred_length: int = 1
) -> Tuple[np.ndarray, np.ndarray]:
    """
    便捷函数：创建时间序列

    参数:
        data: 输入数据
        seq_length: 序列长度
        pred_length: 预测长度

    返回:
        (X序列, Y目标)
    """
    return TimeSeriesProcessor.create_sequences(data, seq_length, pred_length)
