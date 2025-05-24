"""
风险管理模块 (Risk Management Module)

提供交易风险控制和仓位管理功能，包括：
- ATR计算
- 止损价格计算
- 仓位大小计算
- 跟踪止损逻辑
"""

from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src.notify import Notifier


def compute_atr(series: pd.Series, window: int = 14) -> float:
    """
    计算平均真实波幅(ATR)。

    参数:
        series: 价格序列，可以是收盘价、最高价或最低价
        window: 计算窗口大小，默认为14

    返回:
        float: 计算得到的ATR值
    """
    # 计算价格变化
    price_diff = series.diff().abs()

    # 计算ATR
    atr = price_diff.rolling(window=window).mean()

    # 返回最新的ATR值
    return atr.iloc[-1] if not atr.empty else 0.0


def compute_position_size(equity: float, atr: float, risk_frac: float = 0.02) -> int:
    """
    计算基于风险的仓位大小。

    根据账户权益、波动率(ATR)和风险系数计算适当的仓位大小，至少返回1手。

    参数:
        equity: 当前账户权益
        atr: 平均真实波幅，用于衡量价格波动
        risk_frac: 风险系数，每笔交易愿意损失的资金比例(默认: 2%)

    返回:
        int: 仓位大小，至少为1手
    """
    # 如果ATR为零或无效，返回最小单位1
    if atr <= 0:
        return 1

    # 计算理论上的仓位大小
    position = (equity * risk_frac) / atr

    # 确保至少为1手
    return max(1, int(position))


def compute_stop_price(entry: float, atr: float, multiplier: float = 1.0) -> float:
    """
    计算止损价格。

    基于入场价格、ATR和乘数计算止损价格，通常用于为交易设置风险控制点。

    参数:
        entry: 入场价格
        atr: 平均真实波幅，用于度量价格波动
        multiplier: ATR乘数，控制止损距离(默认: 1.0)

    返回:
        float: 计算得到的止损价格
    """
    # 确保ATR为非负值
    atr_value = max(0, atr)

    # 计算止损价格 (做多的情况下)
    return entry - multiplier * atr_value


def trailing_stop(entry: float, atr: float, factor: float = 2.0) -> float:
    """
    计算基于ATR的跟踪止损价格。

    参数:
        entry: 入场价格
        atr: 平均真实波幅
        factor: ATR乘数，控制止损距离(默认: 2.0)

    返回:
        float: 计算得到的跟踪止损价格
    """
    # 确保ATR为非负值
    atr_value = max(0, atr)

    # 计算跟踪止损价格
    return entry - (factor * atr_value)


def compute_trailing_stop(
    entry: float,
    current_price: float,
    initial_stop: float,
    breakeven_r: float = 1.0,
    trail_r: float = 2.0,
    atr: float = None,
) -> float:
    """
    计算移动止损价格 (Trailing Stop Price).

    根据入场价格、当前价格、初始止损价格和盈亏比阈值计算移动止损价格。
    此函数实现了基于盈亏比(R-multiple)的三段式移动止损策略:
    1. 当利润小于breakeven_r时，保持初始止损不变
    2. 当利润介于breakeven_r和trail_r之间时，将止损移至保本位置
    3. 当利润大于trail_r时，启用跟踪止损，随价格移动而调整

    参数:
        entry: 入场价格 (Entry Price)
        current_price: 当前价格 (Current Price)
        initial_stop: 初始止损价格 (Initial Stop Price)
        breakeven_r: 将止损移至保本位的盈亏比阈值 (默认: 1.0R, 即利润等于初始风险时)
        trail_r: 开始跟踪止损的盈亏比阈值 (默认: 2.0R, 即利润为初始风险两倍时)
        atr: 可选的ATR值，用于计算跟踪距离 (Average True Range)

    返回:
        float: 计算得到的移动止损价格
    """
    # 计算初始风险(R)和当前盈利(以R计)
    initial_risk = entry - initial_stop
    if initial_risk <= 0:  # 防御性检查
        return initial_stop

    current_gain = current_price - entry
    current_r = current_gain / initial_risk

    # 如果价格低于入场价，保持初始止损
    if current_r <= 0:
        return initial_stop

    # 1. 移动至保本位(Breakeven) - 当盈利达到breakeven_r时
    if current_r >= breakeven_r and current_r <= trail_r:
        return entry  # 移至保本位（入场价格）

    # 2. 跟踪止损(Trailing Stop) - 当盈利超过trail_r时
    if current_r > trail_r:
        if atr is not None and atr > 0:
            # 基于ATR的跟踪距离 - 跟随价格但保持一定距离
            return current_price - atr
        else:
            # 基于百分比的跟踪 - 例如保持初始风险距离的50%
            trail_distance = initial_risk * 0.5
            return current_price - trail_distance

    # 默认返回初始止损
    return initial_stop


def update_trailing_stop_atr(
    position: Dict[str, Any],
    current_price: float,
    atr: float,
    multiplier: float = 1.0,
    notifier: Optional[Notifier] = None,
) -> Tuple[float, bool]:
    """
    更新基于ATR的跟踪止损价格。

    参数:
        position: 仓位信息字典
        current_price: 当前价格
        atr: 平均真实波幅
        multiplier: ATR乘数
        notifier: 通知器实例

    返回:
        Tuple[float, bool]: (新止损价, 是否更新了止损)
    """
    if not position:
        return 0.0, False

    entry_price = position.get("entry_price", 0)
    current_stop = position.get("stop_price", 0)

    # 计算新的跟踪止损价格
    new_stop = compute_trailing_stop(
        entry=entry_price, current_price=current_price, initial_stop=current_stop, atr=atr
    )

    # 止损只能向有利方向移动
    if new_stop > current_stop:
        if notifier:
            notifier.notify(f"🔄 止损更新: {current_stop:.6f} → {new_stop:.6f}", "INFO")
        return new_stop, True

    return current_stop, False
