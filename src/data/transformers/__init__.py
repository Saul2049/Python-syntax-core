"""
数据转换器包 (Data Transformers Package)

提供数据转换和预处理功能的统一接口
"""

import warnings

from .missing_values import MissingValueHandler

# 导入新的模块化组件
from .normalizers import DataNormalizer, normalize_data
from .splitters import DataSplitter, create_train_test_split
from .time_series import TimeSeriesProcessor, create_sequences

# 向后兼容性：从原始data_transformers.py导入
try:
    from .data_transformers import create_sequences as _legacy_create_sequences
    from .data_transformers import create_train_test_split as _legacy_create_train_test_split
    from .data_transformers import normalize_data as _legacy_normalize_data

    _HAS_LEGACY = True
except ImportError:
    _HAS_LEGACY = False

# 所有公开的类和函数
__all__ = [
    # 主要类
    "DataNormalizer",
    "TimeSeriesProcessor",
    "DataSplitter",
    "MissingValueHandler",
    # 便捷函数
    "normalize_data",
    "create_sequences",
    "create_train_test_split",
    # 分组访问
    "NORMALIZERS",
    "TIME_SERIES_TOOLS",
    "SPLITTERS",
    "MISSING_VALUE_TOOLS",
    "ALL_TRANSFORMERS",
]

# 分组访问不同类型的转换器
NORMALIZERS = {"DataNormalizer": DataNormalizer, "normalize_data": normalize_data}

TIME_SERIES_TOOLS = {
    "TimeSeriesProcessor": TimeSeriesProcessor,
    "create_sequences": create_sequences,
}

SPLITTERS = {"DataSplitter": DataSplitter, "create_train_test_split": create_train_test_split}

MISSING_VALUE_TOOLS = {"MissingValueHandler": MissingValueHandler}

ALL_TRANSFORMERS = {**NORMALIZERS, **TIME_SERIES_TOOLS, **SPLITTERS, **MISSING_VALUE_TOOLS}


def get_transformer_by_name(name: str):
    """
    根据名称获取转换器类或函数

    参数:
        name: 转换器名称

    返回:
        转换器类或函数
    """
    if name in ALL_TRANSFORMERS:
        return ALL_TRANSFORMERS[name]
    else:
        raise ValueError(f"未知的转换器: {name}")


def list_transformers_by_type(transformer_type: str = None):
    """
    列出指定类型的转换器

    参数:
        transformer_type: 转换器类型 ('normalizers', 'time_series', 'splitters', 'missing_values')

    返回:
        转换器列表
    """
    if transformer_type is None:
        return list(ALL_TRANSFORMERS.keys())
    elif transformer_type.lower() == "normalizers":
        return list(NORMALIZERS.keys())
    elif transformer_type.lower() in ["time_series", "timeseries"]:
        return list(TIME_SERIES_TOOLS.keys())
    elif transformer_type.lower() == "splitters":
        return list(SPLITTERS.keys())
    elif transformer_type.lower() in ["missing_values", "missing"]:
        return list(MISSING_VALUE_TOOLS.keys())
    else:
        raise ValueError(f"未知的转换器类型: {transformer_type}")


def get_transformer_info():
    """
    获取所有转换器的信息

    返回:
        转换器信息字典
    """
    return {
        "total_transformers": len(ALL_TRANSFORMERS),
        "normalizers": len(NORMALIZERS),
        "time_series_tools": len(TIME_SERIES_TOOLS),
        "splitters": len(SPLITTERS),
        "missing_value_tools": len(MISSING_VALUE_TOOLS),
        "available_transformers": list(ALL_TRANSFORMERS.keys()),
    }


# 向后兼容性检查函数
def _check_legacy_usage(func_name: str):
    """检查是否使用了遗留接口并发出警告"""
    if _HAS_LEGACY:
        warnings.warn(
            f"使用了遗留的 {func_name} 接口。建议使用新的模块化接口。",
            DeprecationWarning,
            stacklevel=3,
        )


# 向后兼容性包装器（如果需要）
def _get_legacy_function(name: str):
    """获取遗留函数（带警告）"""
    _check_legacy_usage(name)
    if name == "normalize_data" and _HAS_LEGACY:
        return _legacy_normalize_data
    elif name == "create_train_test_split" and _HAS_LEGACY:
        return _legacy_create_train_test_split
    elif name == "create_sequences" and _HAS_LEGACY:
        return _legacy_create_sequences
    else:
        # 返回新版本
        return ALL_TRANSFORMERS.get(name)
