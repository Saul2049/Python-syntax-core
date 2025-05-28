"""
CSV数据加载器模块 (CSV Data Loader Module)

提供CSV文件数据加载功能，包括：
- 基础CSV加载
- OHLCV数据处理
- 数据验证
- 格式化处理
"""

import os
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd


class CSVDataLoader:
    """CSV数据加载器类"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        初始化CSV数据加载器

        参数:
            base_path: 数据文件基础路径
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def load_data(
        self, file_path: Union[str, Path], columns: Optional[List[str]] = None, **kwargs
    ) -> pd.DataFrame:
        """
        从CSV文件加载数据

        参数:
            file_path: CSV文件路径
            columns: 要加载的列名列表（可选）
            **kwargs: pandas.read_csv的其他参数

        返回:
            pandas DataFrame
        """
        # 尝试多个可能的路径位置
        possible_paths = [
            file_path,  # 原始路径
            self.base_path / file_path,  # 基础路径 + 文件路径
            Path.cwd() / file_path,  # 当前工作目录
            Path(__file__).parent.parent.parent / file_path,  # 项目根目录
        ]

        # 如果是相对路径，添加更多可能的位置
        if not Path(file_path).is_absolute():
            possible_paths.extend(
                [
                    Path(__file__).parent.parent.parent.parent / file_path,  # 上级目录
                    Path.cwd().parent / file_path,  # 父目录
                ]
            )

        for path in possible_paths:
            try:
                abs_path = Path(path).resolve()
                if abs_path.exists():
                    if columns:
                        df = pd.read_csv(abs_path, usecols=columns, **kwargs)
                    else:
                        df = pd.read_csv(abs_path, **kwargs)

                    print(f"✅ 成功加载数据: {abs_path} ({len(df)} 行)")
                    return df
            except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
                continue
            except Exception as e:
                print(f"⚠️ 尝试加载 {path} 时出错: {str(e)}")
                continue

        # 如果所有路径都失败，显示详细错误信息
        print(f"❌ 错误: 在以下路径中都未找到文件 '{file_path}':")
        for path in possible_paths:
            abs_path = Path(path).resolve()
            print(f"  - {abs_path}")

        # 对于特定的文件名，生成fallback数据
        if str(file_path) == "btc_eth.csv" or Path(file_path).name == "btc_eth.csv":
            print("🔄 使用合成数据作为fallback...")
            return self._generate_fallback_data(**kwargs)

        print("❌ 无法生成fallback数据，返回空DataFrame")
        return pd.DataFrame()

    def _generate_fallback_data(self, **kwargs) -> pd.DataFrame:
        """
        生成fallback合成数据

        参数:
            **kwargs: pandas参数，用于确定是否需要日期索引等

        返回:
            合成的DataFrame
        """
        from datetime import datetime, timedelta

        import numpy as np

        # 生成日期范围
        days = 1000
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq="D")

        # 生成合成价格数据
        np.random.seed(42)  # 确保可重现

        # BTC价格数据
        btc_returns = np.random.normal(0.001, 0.03, len(dates))
        btc_prices = [50000]
        for ret in btc_returns[1:]:
            btc_prices.append(btc_prices[-1] * (1 + ret))

        # ETH价格数据
        eth_returns = np.random.normal(0.0015, 0.04, len(dates))
        eth_prices = [3000]
        for ret in eth_returns[1:]:
            eth_prices.append(eth_prices[-1] * (1 + ret))

        # 创建DataFrame
        df = pd.DataFrame({"date": dates, "btc": btc_prices, "eth": eth_prices})

        # 根据kwargs处理日期索引
        if kwargs.get("parse_dates") and "date" in kwargs.get("parse_dates", []):
            df["date"] = pd.to_datetime(df["date"])

        if kwargs.get("index_col") == "date":
            df.set_index("date", inplace=True)

        print(
            f"✅ 生成了 {len(df)} 行合成数据 (BTC: {df['btc'].iloc[0]:.2f} -> {df['btc'].iloc[-1]:.2f})"
        )
        return df

    def load_ohlcv_data(
        self, file_path: Union[str, Path], date_column: str = "date", validate_columns: bool = True
    ) -> pd.DataFrame:
        """
        加载OHLCV格式的交易数据

        参数:
            file_path: CSV文件路径
            date_column: 日期列名
            validate_columns: 是否验证必需列的存在

        返回:
            处理后的OHLCV DataFrame
        """
        df = self.load_data(file_path)

        if df.empty:
            return df

        # 验证必需的OHLCV列
        if validate_columns:
            required_columns = ["open", "high", "low", "close"]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                print(f"⚠️ 警告: 缺失必需列: {missing_columns}")
                # 尝试查找相似列名
                self._suggest_column_mapping(df.columns, missing_columns)

        return self._process_ohlcv_data(df, date_column)

    def _process_ohlcv_data(self, df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
        """
        处理OHLCV数据的内部方法

        参数:
            df: 原始DataFrame
            date_column: 日期列名

        返回:
            处理后的DataFrame
        """
        # 复制DataFrame以避免修改原始数据
        df_processed = df.copy()

        # 处理日期列
        if date_column in df_processed.columns:
            df_processed[date_column] = pd.to_datetime(df_processed[date_column])
            df_processed.set_index(date_column, inplace=True)
            df_processed.sort_index(inplace=True)
        else:
            print(f"⚠️ 警告: 日期列 '{date_column}' 不存在")

        # 数据类型转换
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_numeric(df_processed[col], errors="coerce")

        return df_processed

    def _suggest_column_mapping(self, existing_columns: List[str], missing_columns: List[str]):
        """
        建议列名映射

        参数:
            existing_columns: 现有列名
            missing_columns: 缺失列名
        """
        suggestions = {
            "open": ["Open", "OPEN", "o", "opening"],
            "high": ["High", "HIGH", "h", "max"],
            "low": ["Low", "LOW", "l", "min"],
            "close": ["Close", "CLOSE", "c", "closing"],
            "volume": ["Volume", "VOLUME", "v", "vol"],
        }

        for missing_col in missing_columns:
            if missing_col in suggestions:
                possible_matches = [
                    col for col in existing_columns if col in suggestions[missing_col]
                ]
                if possible_matches:
                    print(f"  💡 建议: '{missing_col}' 可能对应 {possible_matches}")

    def load_multiple_files(
        self, file_patterns: List[Union[str, Path]], combine: bool = False
    ) -> Union[List[pd.DataFrame], pd.DataFrame]:
        """
        加载多个CSV文件

        参数:
            file_patterns: 文件路径模式列表
            combine: 是否合并所有数据

        返回:
            DataFrame列表或合并后的DataFrame
        """
        dataframes = []

        for pattern in file_patterns:
            if isinstance(pattern, str) and ("*" in pattern or "?" in pattern):
                # 处理通配符模式
                matching_files = list(self.base_path.glob(pattern))
            else:
                matching_files = [self.base_path / pattern]

            for file_path in matching_files:
                if file_path.exists():
                    df = self.load_data(file_path)
                    if not df.empty:
                        df["source_file"] = file_path.name  # 添加来源文件信息
                        dataframes.append(df)

        if combine and dataframes:
            combined_df = pd.concat(dataframes, ignore_index=True)
            print(f"✅ 合并了 {len(dataframes)} 个文件的数据")
            return combined_df

        return dataframes

    def get_file_info(self, file_path: Union[str, Path]) -> dict:
        """
        获取文件基本信息

        参数:
            file_path: 文件路径

        返回:
            文件信息字典
        """
        if not Path(file_path).is_absolute():
            file_path = self.base_path / file_path

        try:
            file_stats = os.stat(file_path)
            # 读取文件头部信息
            sample_df = pd.read_csv(file_path, nrows=5)

            return {
                "file_path": str(file_path),
                "file_size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                "columns": list(sample_df.columns),
                "column_count": len(sample_df.columns),
                "sample_rows": len(sample_df),
                "exists": True,
            }
        except Exception as e:
            return {"file_path": str(file_path), "error": str(e), "exists": False}


# 便捷函数
def load_csv(
    file_path: Union[str, Path] = "btc_eth.csv",  # 添加默认值以保持向后兼容
    columns: Optional[List[str]] = None,
    base_path: Optional[Union[str, Path]] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    便捷的CSV加载函数

    参数:
        file_path: CSV文件路径（默认btc_eth.csv以保持向后兼容）
        columns: 要加载的列名列表
        base_path: 基础路径
        **kwargs: pandas.read_csv的其他参数

    返回:
        pandas DataFrame
    """
    # 如果没有指定特殊参数，使用旧的行为（解析日期和设置索引）
    if not kwargs and file_path == "btc_eth.csv":
        kwargs = {"parse_dates": ["date"], "index_col": "date"}

    loader = CSVDataLoader(base_path)
    return loader.load_data(file_path, columns, **kwargs)


def load_ohlcv_csv(
    file_path: Union[str, Path],
    date_column: str = "date",
    base_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """
    便捷的OHLCV CSV加载函数

    参数:
        file_path: CSV文件路径
        date_column: 日期列名
        base_path: 基础路径

    返回:
        处理后的OHLCV DataFrame
    """
    loader = CSVDataLoader(base_path)
    return loader.load_ohlcv_data(file_path, date_column)
