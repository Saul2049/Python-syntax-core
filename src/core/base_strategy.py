"""
基础策略抽象类
Base Strategy Abstract Class

为所有交易策略提供统一的接口和基础功能
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


class BaseStrategy(ABC):
    """
    基础策略抽象类

    所有具体策略都应该继承此类并实现必要的方法
    """

    def __init__(self, name: str = "BaseStrategy", **kwargs: Any) -> None:
        """
        初始化基础策略

        Args:
            name: 策略名称 (Strategy name)
            **kwargs: 额外的策略参数 (Additional strategy parameters)
        """
        self.name: str = name  # 策略名称
        self.parameters: Dict[str, Any] = kwargs  # 策略参数字典
        self.logger: logging.Logger = logging.getLogger(f"{__name__}.{name}")  # 日志记录器

        # 策略状态
        self.is_initialized: bool = False  # 是否已初始化
        self.last_signal_time: Optional[datetime] = None  # 最后信号时间
        self.performance_metrics: Dict[str, float] = {}  # 性能指标字典

        # 数据缓存
        self._data_cache: Optional[pd.DataFrame] = None  # 数据缓存
        self._last_data_hash: Optional[str] = None  # 最后数据哈希值

        self.logger.info(f"Strategy {name} initialized with parameters: {kwargs}")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号 (抽象方法)

        Args:
            data: 市场数据 DataFrame (Market data DataFrame)

        Returns:
            包含信号和相关信息的字典 (Dictionary containing signal and related information)
            - signal: 交易信号类型 ("BUY", "SELL", "HOLD")
            - confidence: 信号置信度 (0.0-1.0)
            - timestamp: 信号生成时间
            - price: 当前价格
            - metadata: 额外的信号元数据
        """

    def set_parameter(self, key: str, value: Any) -> None:
        """
        设置策略参数

        Args:
            key: 参数名 (Parameter name)
            value: 参数值 (Parameter value)
        """
        old_value: Any = self.parameters.get(key)
        self.parameters[key] = value

        self.logger.info(f"Parameter {key} changed: {old_value} -> {value}")

        # 参数变更后可能需要重新初始化
        self.is_initialized = False

    def get_parameter(self, key: str, default: Any = None) -> Any:
        """
        获取策略参数

        Args:
            key: 参数名 (Parameter name)
            default: 默认值 (Default value)

        Returns:
            参数值 (Parameter value)
        """
        return self.parameters.get(key, default)

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        验证输入数据的有效性

        Args:
            data: 市场数据 DataFrame (Market data DataFrame)

        Returns:
            数据是否有效 (Whether data is valid)
        """
        if data is None or data.empty:
            self.logger.error("Data is None or empty")
            return False

        # 检查必需的列
        required_columns: list[str] = ["close", "volume"]
        missing_columns: list[str] = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return False

        # 检查数据类型
        if not pd.api.types.is_numeric_dtype(data["close"]):
            self.logger.error("'close' column must be numeric")
            return False

        # 检查空值
        if data["close"].isna().any():
            self.logger.warning("'close' column contains NaN values")

        return True

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        预处理数据

        Args:
            data: 原始市场数据 (Raw market data)

        Returns:
            处理后的数据 (Processed data)
        """
        # 复制数据避免修改原始数据
        processed_data: pd.DataFrame = data.copy()

        # 确保索引是时间序列
        if not isinstance(processed_data.index, pd.DatetimeIndex):
            if "timestamp" in processed_data.columns:
                processed_data["timestamp"] = pd.to_datetime(processed_data["timestamp"])
                processed_data.set_index("timestamp", inplace=True)
            elif "date" in processed_data.columns:
                processed_data["date"] = pd.to_datetime(processed_data["date"])
                processed_data.set_index("date", inplace=True)

        # 排序数据
        processed_data.sort_index(inplace=True)

        # 删除重复行
        processed_data = processed_data[~processed_data.index.duplicated(keep="last")]

        # 填充缺失值
        processed_data = processed_data.ffill().bfill()

        return processed_data

    def calculate_returns(self, data: pd.DataFrame, price_column: str = "close") -> pd.Series:
        """
        计算收益率

        Args:
            data: 包含价格数据的DataFrame (DataFrame containing price data)
            price_column: 价格列名 (Price column name)

        Returns:
            收益率序列 (Returns series)
        """
        if price_column not in data.columns:
            raise ValueError(f"Column '{price_column}' not found in data")

        returns: pd.Series = data[price_column].pct_change()
        return returns.fillna(0)

    def calculate_performance_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        计算策略性能指标

        Args:
            returns: 收益率序列 (Returns series)

        Returns:
            性能指标字典 (Performance metrics dictionary)
            - total_return: 总收益率
            - annual_return: 年化收益率
            - volatility: 波动率
            - sharpe_ratio: 夏普比率
            - max_drawdown: 最大回撤
            - win_rate: 胜率
            - num_trades: 交易次数
        """
        if returns.empty:
            return {}

        # 基础统计
        total_return: float = (1 + returns).prod() - 1
        annual_return: float = (1 + returns.mean()) ** 252 - 1
        volatility: float = returns.std() * np.sqrt(252)

        # 夏普比率
        risk_free_rate: float = 0.02  # 假设无风险利率2%
        excess_returns: float = annual_return - risk_free_rate
        sharpe_ratio: float = excess_returns / volatility if volatility > 0 else 0

        # 最大回撤
        cumulative_returns: pd.Series = (1 + returns).cumprod()
        rolling_max: pd.Series = cumulative_returns.expanding().max()
        drawdown: pd.Series = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown: float = drawdown.min()

        # 胜率
        win_rate: float = (returns > 0).mean()

        metrics: Dict[str, float] = {
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "num_trades": len(returns[returns != 0]),
        }

        self.performance_metrics.update(metrics)
        return metrics

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息

        Returns:
            策略信息字典 (Strategy information dictionary)
            - name: 策略名称
            - parameters: 策略参数
            - is_initialized: 是否已初始化
            - last_signal_time: 最后信号时间
            - performance_metrics: 性能指标
        """
        return {
            "name": self.name,
            "parameters": self.parameters.copy(),
            "is_initialized": self.is_initialized,
            "last_signal_time": self.last_signal_time,
            "performance_metrics": self.performance_metrics.copy(),
        }

    def reset(self) -> None:
        """
        重置策略状态
        """
        self.is_initialized = False
        self.last_signal_time = None
        self.performance_metrics.clear()
        self._data_cache = None
        self._last_data_hash = None

        self.logger.info(f"Strategy {self.name} reset")

    def __str__(self) -> str:
        return f"{self.name}({self.parameters})"

    def __repr__(self) -> str:
        return f"BaseStrategy(name='{self.name}', parameters={self.parameters})"
