"""
技术分析模块 (Technical Analysis Module)

提供各种技术指标计算功能，包括：
- 移动平均线
- 技术指标 (RSI, MACD, 布林带等)
- 波动率计算
- 收益率分析
"""

from typing import Dict

import numpy as np
import pandas as pd


class TechnicalIndicators:
    """技术指标计算器类"""

    @staticmethod
    def moving_average(prices: pd.Series, window: int, ma_type: str = "simple") -> pd.Series:
        """
        计算移动平均线

        参数:
            prices: 价格序列
            window: 窗口大小
            ma_type: 移动平均类型 ('simple', 'exponential')

        返回:
            移动平均序列
        """
        if ma_type.lower() == "simple":
            return prices.rolling(window=window).mean()
        elif ma_type.lower() == "exponential":
            return prices.ewm(span=window).mean()
        else:
            raise ValueError(f"不支持的移动平均类型: {ma_type}")

    @staticmethod
    def add_moving_averages(
        df: pd.DataFrame, price_column: str = "close", windows: list = [5, 10, 20, 50, 200]
    ) -> pd.DataFrame:
        """
        添加多个移动平均线

        参数:
            df: 价格数据DataFrame
            price_column: 价格列名
            windows: 窗口大小列表

        返回:
            添加移动平均线的DataFrame
        """
        if price_column not in df.columns:
            raise ValueError(f"列 '{price_column}' 不存在于DataFrame中")

        df_with_ma = df.copy()
        prices = df_with_ma[price_column]

        # 简单移动平均线
        for window in windows:
            df_with_ma[f"MA_{window}"] = TechnicalIndicators.moving_average(
                prices, window, "simple"
            )

        # 指数移动平均线
        for window in windows:
            df_with_ma[f"EMA_{window}"] = TechnicalIndicators.moving_average(
                prices, window, "exponential"
            )

        return df_with_ma

    @staticmethod
    def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """
        计算相对强弱指数 (RSI)

        参数:
            prices: 价格序列
            window: 计算窗口

        返回:
            RSI序列
        """
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()

        # 避免除以零
        avg_loss = avg_loss.replace(0, 0.000001)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def bollinger_bands(
        prices: pd.Series, window: int = 20, std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        计算布林带

        参数:
            prices: 价格序列
            window: 计算窗口
            std_dev: 标准差倍数

        返回:
            包含上轨、中轨、下轨的字典
        """
        rolling_mean = prices.rolling(window=window).mean()
        rolling_std = prices.rolling(window=window).std()

        return {
            "BB_middle": rolling_mean,
            "BB_upper": rolling_mean + (rolling_std * std_dev),
            "BB_lower": rolling_mean - (rolling_std * std_dev),
        }

    @staticmethod
    def macd(
        prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        计算MACD (移动平均收敛/发散)

        参数:
            prices: 价格序列
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期

        返回:
            包含MACD线、信号线、柱状图的字典
        """
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()
        histogram = macd_line - signal_line

        return {"MACD_line": macd_line, "MACD_signal": signal_line, "MACD_histogram": histogram}

    @staticmethod
    def stochastic_oscillator(
        high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """
        计算随机震荡指标

        参数:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            k_period: %K线周期
            d_period: %D线周期

        返回:
            包含%K和%D的字典
        """
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()

        return {"Stoch_K": k_percent, "Stoch_D": d_percent}

    @staticmethod
    def add_all_indicators(df: pd.DataFrame, price_column: str = "close") -> pd.DataFrame:
        """
        添加所有常用技术指标

        参数:
            df: 价格数据DataFrame (需包含OHLCV列)
            price_column: 主要价格列名

        返回:
            添加所有技术指标的DataFrame
        """
        if price_column not in df.columns:
            raise ValueError(f"列 '{price_column}' 不存在于DataFrame中")

        df_with_indicators = df.copy()
        prices = df_with_indicators[price_column]

        # 添加移动平均线
        df_with_indicators = TechnicalIndicators.add_moving_averages(
            df_with_indicators, price_column
        )

        # 添加RSI
        df_with_indicators["RSI_14"] = TechnicalIndicators.rsi(prices, 14)

        # 添加布林带
        bb_data = TechnicalIndicators.bollinger_bands(prices)
        for key, value in bb_data.items():
            df_with_indicators[key] = value

        # 添加MACD
        macd_data = TechnicalIndicators.macd(prices)
        for key, value in macd_data.items():
            df_with_indicators[key] = value

        # 添加随机震荡指标 (如果有高低价数据)
        if all(col in df.columns for col in ["high", "low", "close"]):
            stoch_data = TechnicalIndicators.stochastic_oscillator(
                df_with_indicators["high"], df_with_indicators["low"], df_with_indicators["close"]
            )
            for key, value in stoch_data.items():
                df_with_indicators[key] = value

        return df_with_indicators


class VolatilityIndicators:
    """波动率指标计算器类"""

    @staticmethod
    def historical_volatility(
        prices: pd.Series, window: int = 20, trading_days: int = 252
    ) -> pd.Series:
        """
        计算历史波动率

        参数:
            prices: 价格序列
            window: 计算窗口
            trading_days: 年交易日数

        返回:
            波动率序列
        """
        # 计算对数收益率
        log_returns = np.log(prices / prices.shift(1))

        # 计算滚动标准差
        rolling_std = log_returns.rolling(window=window).std()

        # 年化波动率
        annualized_vol = rolling_std * np.sqrt(trading_days)

        return annualized_vol

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
        """
        计算平均真实范围 (ATR)

        参数:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            window: 计算窗口

        返回:
            ATR序列
        """
        # 计算真实范围
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # 计算ATR
        atr = true_range.rolling(window=window).mean()

        return atr

    @staticmethod
    def vix_like_indicator(prices: pd.Series, window: int = 30) -> pd.Series:
        """
        计算类似VIX的波动率指标

        参数:
            prices: 价格序列
            window: 计算窗口

        返回:
            波动率指标序列
        """
        returns = prices.pct_change()
        rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100

        return rolling_vol


class ReturnAnalysis:
    """收益率分析类"""

    @staticmethod
    def calculate_returns(prices: pd.Series, periods: int = 1, method: str = "simple") -> pd.Series:
        """
        计算收益率

        参数:
            prices: 价格序列
            periods: 计算周期
            method: 计算方法 ('simple', 'log')

        返回:
            收益率序列
        """
        if method.lower() == "simple":
            return prices.pct_change(periods=periods)
        elif method.lower() == "log":
            return np.log(prices / prices.shift(periods))
        else:
            raise ValueError(f"不支持的收益率计算方法: {method}")

    @staticmethod
    def rolling_returns(prices: pd.Series, window: int, method: str = "simple") -> pd.Series:
        """
        计算滚动收益率

        参数:
            prices: 价格序列
            window: 滚动窗口
            method: 计算方法

        返回:
            滚动收益率序列
        """
        if method.lower() == "simple":
            return (prices / prices.shift(window)) - 1
        elif method.lower() == "log":
            return np.log(prices / prices.shift(window))
        else:
            raise ValueError(f"不支持的收益率计算方法: {method}")

    @staticmethod
    def sharpe_ratio(
        returns: pd.Series, risk_free_rate: float = 0.02, window: int = 252
    ) -> pd.Series:
        """
        计算夏普比率

        参数:
            returns: 收益率序列
            risk_free_rate: 无风险利率 (年化)
            window: 计算窗口

        返回:
            夏普比率序列
        """
        excess_returns = returns - (risk_free_rate / 252)  # 日无风险利率
        rolling_mean = excess_returns.rolling(window=window).mean() * 252
        rolling_std = returns.rolling(window=window).std() * np.sqrt(252)

        return rolling_mean / rolling_std


# 便捷函数
def add_technical_indicators(df: pd.DataFrame, price_column: str = "close") -> pd.DataFrame:
    """
    便捷函数：添加技术指标

    参数:
        df: 价格数据DataFrame
        price_column: 价格列名

    返回:
        添加技术指标的DataFrame
    """
    return TechnicalIndicators.add_all_indicators(df, price_column)


def calculate_volatility(prices: pd.Series, window: int = 20, trading_days: int = 252) -> pd.Series:
    """
    便捷函数：计算历史波动率

    参数:
        prices: 价格序列
        window: 计算窗口
        trading_days: 年交易日数

    返回:
        波动率序列
    """
    return VolatilityIndicators.historical_volatility(prices, window, trading_days)


def calculate_returns(prices: pd.Series, periods: int = 1, log_returns: bool = False) -> pd.Series:
    """
    便捷函数：计算收益率

    参数:
        prices: 价格序列
        periods: 计算周期
        log_returns: 是否计算对数收益率

    返回:
        收益率序列
    """
    method = "log" if log_returns else "simple"
    return ReturnAnalysis.calculate_returns(prices, periods, method)
