"""
数据处理模块 (Data Processing Module)

提供完整的数据处理功能套件，包括：
- 数据加载和导入
- 技术指标计算
- 数据转换和预处理
- 数据保存和导出
- 向后兼容接口

使用示例:
    from src.data import load_ohlcv_csv, add_technical_indicators, save_processed_data

    # 加载数据
    df = load_ohlcv_csv("btc_eth.csv")

    # 添加技术指标
    df_with_indicators = add_technical_indicators(df)

    # 保存数据
    save_processed_data(df_with_indicators, "output/processed_data.csv")
"""

# 基础依赖 - 为向后兼容性保留
import pandas as pd

# 技术指标
from .indicators.technical_analysis import (
    ReturnAnalysis,
    TechnicalIndicators,
    VolatilityIndicators,
    add_technical_indicators,
    calculate_returns,
    calculate_volatility,
)

# 数据加载器
from .loaders.csv_loader import (
    CSVDataLoader,
    load_csv,
    load_ohlcv_csv,
)

# 向后兼容 - 从processors导入
from .processors.data_processor import (
    load_data,
    process_ohlcv_data,
    resample_data,
)

# 数据转换器
from .transformers.data_transformers import (
    DataNormalizer,
    DataSplitter,
    MissingValueHandler,
    TimeSeriesProcessor,
    create_sequences,
    create_train_test_split,
    normalize_data,
)

# 数据保存器
from .validators.data_saver import (
    DataSaver,
    ProcessedDataExporter,
    save_processed_data,
)

__all__ = [
    # 基础依赖
    "pd",
    # 数据加载器
    "CSVDataLoader",
    "load_csv",
    "load_ohlcv_csv",
    # 技术指标
    "TechnicalIndicators",
    "VolatilityIndicators",
    "ReturnAnalysis",
    "add_technical_indicators",
    "calculate_volatility",
    "calculate_returns",
    # 数据转换器
    "DataNormalizer",
    "TimeSeriesProcessor",
    "DataSplitter",
    "MissingValueHandler",
    "normalize_data",
    "create_train_test_split",
    "create_sequences",
    # 数据保存器
    "DataSaver",
    "ProcessedDataExporter",
    "save_processed_data",
    # 向后兼容
    "load_data",
    "process_ohlcv_data",
    "resample_data",
]
