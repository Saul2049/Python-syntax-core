from datetime import datetime, timedelta
from math import isfinite
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from src import utils
from src.notify import Notifier

# 由于循环导入问题，延迟导入下面的模块
from . import signals


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


def backtest_single(
    price: pd.Series,
    fast_win: int = 7,
    slow_win: int = 20,
    atr_win: int = 20,
    risk_frac: float = 0.02,
    init_equity: float = 100_000.0,
    use_trailing_stop: bool = True,
    breakeven_r: float = 1.0,
    trail_r: float = 2.0,
    verbose: bool = False,
) -> pd.Series:
    """
    对单一 price 序列执行 MA+ATR 回测，返回 equity 曲线。

    该函数实现了基于移动平均交叉和ATR的回测策略，包含移动止损风险管理功能。
    具体交易逻辑如下:
    1. 入场信号: 快速MA上穿慢速MA (bullish cross)
    2. 出场信号: 快速MA下穿慢速MA (bearish cross) 或 触发止损
    3. 止损策略: 初始止损基于ATR设置，可选择启用移动止损
    4. 仓位管理: 基于账户风险比例和ATR计算头寸大小

    移动止损系统基于盈亏比(R-multiple)工作:
    - 当利润达到初始风险的breakeven_r倍时，止损移至保本位置
    - 当利润达到初始风险的trail_r倍时，止损开始跟踪价格移动
    - 止损只能向有利方向移动，不会回撤

    参数:
        price: 价格序列 (Price Series)
        fast_win: 快速移动平均线窗口 (Fast MA Window)
        slow_win: 慢速移动平均线窗口 (Slow MA Window)
        atr_win: ATR窗口 (ATR Window)
        risk_frac: 风险系数，每笔交易风险比例 (Risk Fraction per Trade, 默认: 2%)
        init_equity: 初始资金 (Initial Equity)
        use_trailing_stop: 是否使用移动止损 (Whether to Use Trailing Stop)
        breakeven_r: 将止损移至保本位的盈亏比阈值 (Breakeven R-multiple Threshold)
                    1.0意味着当利润等于风险时移至保本
        trail_r: 开始跟踪止损的盈亏比阈值 (Trailing R-multiple Threshold)
                2.0意味着当利润达到风险的2倍时开始跟踪
        verbose: 是否打印交易和止损变动信息 (默认: False)

    返回:
        pd.Series: 回测的权益曲线 (Equity Curve)
    """
    fast = signals.moving_average(price, fast_win)
    slow = signals.moving_average(price, slow_win)

    # ATR
    tr = pd.concat(
        {
            "hl": price.rolling(2).max() - price.rolling(2).min(),
            "hc": (price - price.shift(1)).abs(),
            "lc": (price - price.shift(1)).abs(),
        },
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(atr_win).mean()

    equity = init_equity
    equity_curve, position, entry, stop = [], 0, None, None
    initial_stop = None  # 记录初始止损位置，用于计算盈亏比
    stop_history = []  # 记录止损变动历史

    buy_i = set(signals.bullish_cross_indices(fast, slow))
    sell_i = set(signals.bearish_cross_indices(fast, slow))

    for i, p in enumerate(price):
        # 更新移动止损
        if use_trailing_stop and position and entry is not None and initial_stop is not None:
            current_atr = atr.iloc[i] if i < len(atr) and isfinite(atr.iloc[i]) else None
            new_stop = compute_trailing_stop(
                entry,
                p,
                initial_stop,
                breakeven_r=breakeven_r,
                trail_r=trail_r,
                atr=current_atr,
            )
            # 止损只能上移不能下移
            old_stop = stop
            stop = max(stop, new_stop) if stop is not None else new_stop

            # 记录止损变动
            if stop != old_stop and verbose:
                stop_history.append(
                    {
                        "date": price.index[i],
                        "price": p,
                        "old_stop": old_stop,
                        "new_stop": stop,
                        "type": "update",
                        "atr": current_atr,
                    }
                )
                print(f"[{price.index[i]}] 止损更新: {old_stop:.2f} -> {stop:.2f} (价格: {p:.2f})")

        # 止损
        if position and p < stop:
            equity += (p - entry) * position

            # 记录止损触发
            if verbose:
                stop_history.append(
                    {
                        "date": price.index[i],
                        "price": p,
                        "stop": stop,
                        "entry": entry,
                        "position": position,
                        "profit": (p - entry) * position,
                        "type": "stop_loss",
                    }
                )
                print(
                    f"[{price.index[i]}] 止损触发: 价格 {p:.2f} < 止损 {stop:.2f}, 盈亏: {(p - entry) * position:.2f}"
                )

            position = 0
            entry = None
            stop = None
            initial_stop = None

        # 卖出信号
        if i in sell_i and position:
            equity += (p - entry) * position

            # 记录卖出
            if verbose:
                stop_history.append(
                    {
                        "date": price.index[i],
                        "price": p,
                        "stop": stop,
                        "entry": entry,
                        "position": position,
                        "profit": (p - entry) * position,
                        "type": "sell_signal",
                    }
                )
                print(f"[{price.index[i]}] 卖出信号: 价格 {p:.2f}, 盈亏: {(p - entry) * position:.2f}")

            position = 0
            entry = None
            stop = None
            initial_stop = None

        # 买入信号
        if i in buy_i and position == 0 and isfinite(atr.iloc[i]):
            size = compute_position_size(equity, atr.iloc[i], risk_frac)
            # 将仓位舍入到小数点后3位，与Binance最小交易单位(0.001)对齐
            position = round(size, 3)
            entry = p
            stop = compute_stop_price(entry, atr.iloc[i])
            initial_stop = stop  # 记录初始止损以便后续计算盈亏比

            # 记录买入
            if verbose:
                stop_history.append(
                    {
                        "date": price.index[i],
                        "price": p,
                        "stop": stop,
                        "entry": entry,
                        "position": position,
                        "risk": (entry - stop) * position,
                        "type": "buy_signal",
                    }
                )
                print(f"[{price.index[i]}] 买入信号: 价格 {p:.2f}, 仓位 {position:.3f}, 止损 {stop:.2f}")

        equity_curve.append(equity + (p - entry) * position if position else equity)

    return pd.Series(equity_curve, index=price.index[: len(equity_curve)])


# 相对强度计算已集成到backtest_portfolio函数内
# def compute_relative_strength(prices_dict, lookback=20):
#     """
#     计算多个资产的相对强度得分。
#
#     基于近期回报计算资产间的相对强度，用于动态调整权重。
#
#     参数:
#         prices_dict: 包含多个资产价格序列的字典 {资产名: 价格序列}
#         lookback: 计算相对强度的回看周期 (默认: 20)
#
#     返回:
#         pd.DataFrame: 相对强度得分，每行表示一个时间点的资产间强度比
#     """
#     # 函数逻辑已集成到backtest_portfolio中


def backtest_portfolio(
    prices_dict,
    fast_win=7,
    slow_win=20,
    atr_win=20,
    base_risk_frac=0.02,
    init_equity=100_000.0,
    use_trailing_stop=True,
    breakeven_r=1.0,
    trail_r=2.0,
    use_dynamic_weights=True,
    max_weight_factor=1.5,  # 最大权重倍数
    min_weight_factor=0.5,  # 最小权重倍数
    lookback=20,  # 相对强度计算期
    prefer_better_asset=True,  # 是否更积极地偏好表现较好的资产
    weight_power=2.0,
):  # 权重幂次，增大会放大好资产权重
    """
    对多资产组合执行动态权重回测。

    使用相对强度调整不同资产的仓位权重，表现更好的资产获得更高权重。

    参数:
        prices_dict: 包含多个资产价格序列的字典 {资产名: 价格序列}
        fast_win, slow_win, atr_win: 交易信号参数
        base_risk_frac: 基础风险比例
        init_equity: 初始资金
        use_trailing_stop, breakeven_r, trail_r: 止损相关参数
        use_dynamic_weights: 是否使用动态权重 (否则等权重)
        max_weight_factor: 最大权重调整倍数 (默认1.5x)
        min_weight_factor: 最小权重调整倍数 (默认0.5x)
        lookback: 相对强度计算期
        prefer_better_asset: 是否更强烈地偏好表现好的资产
        weight_power: 权重放大因子，大于1时增加强者权重

    返回:
        pd.DataFrame: 包含总权益曲线和各资产子权益曲线
    """
    # 确保所有价格序列长度相同并且索引一致
    # 在这里简化处理，假设已对齐

    asset_count = len(prices_dict)
    if asset_count == 0:
        return pd.Series()

    # 计算每个资产的基础回测曲线
    base_equity = init_equity / asset_count if asset_count > 1 else init_equity
    asset_equity_curves = {}

    for asset, prices in prices_dict.items():
        equity_curve = backtest_single(
            prices,
            fast_win,
            slow_win,
            atr_win,
            risk_frac=base_risk_frac,
            init_equity=base_equity,
            use_trailing_stop=use_trailing_stop,
            breakeven_r=breakeven_r,
            trail_r=trail_r,
        )
        asset_equity_curves[asset] = equity_curve

    # 创建基础权益矩阵
    equity_df = pd.DataFrame(asset_equity_curves)

    # 如果不使用动态权重，直接返回等权重结果
    if not use_dynamic_weights or asset_count <= 1:
        equity_df["Portfolio"] = equity_df.sum(axis=1)
        return equity_df

    # 计算相对强度 - 使用回报率+波动率
    returns_dict = {asset: equity_df[asset].pct_change() for asset in prices_dict.keys()}

    # 计算历史表现分数
    performance_df = pd.DataFrame()
    volatility_df = pd.DataFrame()
    sharpe_df = pd.DataFrame()

    for asset, returns in returns_dict.items():
        # 计算平均回报
        performance_df[asset] = returns.rolling(lookback).mean().fillna(0)

        # 计算波动率
        volatility_df[asset] = returns.rolling(lookback).std().fillna(0.001)  # 防止除零

        # 计算夏普比率
        sharpe_df[asset] = performance_df[asset] / volatility_df[asset]

    # 使用更综合的绩效指标
    composite_df = pd.DataFrame()
    if prefer_better_asset:
        # 使用夏普比率作为更综合的评价指标
        # 在负回报环境中，波动率低但回报高的资产更优
        composite_df = sharpe_df.copy()
    else:
        # 仅使用平均回报作为评价指标
        composite_df = performance_df.copy()

    # 初始化权重矩阵
    weights_df = pd.DataFrame(1.0 / asset_count, index=equity_df.index, columns=equity_df.columns)

    # 滚动调整权重
    for i in range(lookback + 1, len(equity_df)):
        # 获取当前绩效指标
        performance = composite_df.iloc[i - 1]  # 使用前一天的指标

        # 避免所有资产都是负收益的极端情况
        if all(performance <= 0):
            min_performance = performance.min()
            if min_performance < 0:
                # 在所有为负时，选择最不差的
                adjusted_performance = performance - min_performance + 0.0001
            else:
                # 所有为0时，保持等权
                weights_df.iloc[i] = 1.0 / asset_count
                continue
        else:
            # 将负指标调整为0
            adjusted_performance = performance.copy()
            adjusted_performance[adjusted_performance < 0] = 0

        # 如果所有调整后表现都是0，使用等权
        if adjusted_performance.sum() == 0:
            weights_df.iloc[i] = 1.0 / asset_count
            continue

        # 使用幂函数放大表现差异 - 增强表现好的资产权重
        if weight_power != 1.0:
            for asset in adjusted_performance.index:
                if adjusted_performance[asset] > 0:
                    adjusted_performance[asset] = adjusted_performance[asset] ** weight_power

        # 计算原始权重
        raw_weights = adjusted_performance / adjusted_performance.sum()

        # 应用权重限制
        constrained_weights = raw_weights.copy()

        # 限制权重在最小和最大范围内
        base_weight = 1.0 / asset_count
        for asset in prices_dict.keys():
            min_allowed = base_weight * min_weight_factor
            max_allowed = base_weight * max_weight_factor

            if constrained_weights[asset] < min_allowed:
                constrained_weights[asset] = min_allowed
            elif constrained_weights[asset] > max_allowed:
                constrained_weights[asset] = max_allowed

        # 重新归一化确保权重之和=1
        weights_df.iloc[i] = constrained_weights / constrained_weights.sum()

    # 初始化调整后的权益曲线
    adjusted_equity_df = equity_df.copy()

    # 从第lookback天起，应用动态权重策略调整仓位
    for i in range(lookback + 1, len(equity_df)):
        # 上一天的总权益
        prev_total_equity = adjusted_equity_df.iloc[i - 1].sum()

        # 根据新权重重新分配资金
        for asset in equity_df.columns:
            # 获取此资产的原始单日回报率
            day_return = (
                equity_df.iloc[i][asset] / equity_df.iloc[i - 1][asset] if equity_df.iloc[i - 1][asset] > 0 else 1.0
            )

            # 应用加权后的资金计算新权益
            target_allocation = prev_total_equity * weights_df.iloc[i][asset]
            adjusted_equity_df.iloc[i, adjusted_equity_df.columns.get_loc(asset)] = target_allocation * day_return

    # 计算总投资组合价值
    adjusted_equity_df["Portfolio"] = adjusted_equity_df.sum(axis=1)

    return adjusted_equity_df


# 在回测或实盘中使用单一BTC的配置
portfolio_config = {
    "assets": ["btc"],  # 只包含BTC
    "weights": [1.0],  # 100%权重
    "risk_frac": 0.02,  # 维持2%的风险系数
}


def update_trailing_stop_atr(
    position: Dict[str, Any],
    current_price: float,
    atr: float,
    multiplier: float = 1.0,
    notifier: Optional[Notifier] = None,
) -> Tuple[float, bool]:
    """
    使用ATR更新移动止损价格。
    Update trailing stop price using ATR.

    参数 (Parameters):
        position: 持仓信息字典 (Position information dictionary)
                 包含 'entry_price', 'stop_price' 等字段
        current_price: 当前价格 (Current price)
        atr: 当前ATR值 (Current ATR value)
        multiplier: ATR乘数 (ATR multiplier)
        notifier: 可选的通知处理器 (Optional notifier)

    返回 (Returns):
        Tuple[float, bool]: (新止损价, 是否更新)
    """
    if not position or "stop_price" not in position:
        return 0.0, False

    old_stop = position["stop_price"]

    # 使用ATR计算新的止损位置
    new_stop_candidate = current_price - (atr * multiplier)

    # 止损只能上移不能下移
    should_update = new_stop_candidate > old_stop
    new_stop = max(old_stop, new_stop_candidate) if should_update else old_stop

    # 发送止损更新通知
    if should_update and notifier:
        update_msg = (
            f"📊 止损更新 (Stop Updated)\n"
            f"品种 (Symbol): {position.get('symbol', 'Unknown')}\n"
            f"当前价 (Price): {current_price:.8f}\n"
            f"ATR: {atr:.8f}\n"
            f"旧止损 (Old): {old_stop:.8f}\n"
            f"新止损 (New): {new_stop:.8f}\n"
            f"止损距离 (Distance): {(current_price - new_stop):.8f} "
            f"({((current_price - new_stop)/current_price)*100:.2f}%)"
        )
        notifier.notify(update_msg, "INFO")

    return new_stop, should_update


class Broker:
    """Trading broker with Telegram notifications."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        telegram_token: Optional[str] = None,
        trades_dir: Optional[str] = None,
    ):
        """
        初始化交易经纪商。
        Initialize trading broker.

        参数 (Parameters):
            api_key: API密钥 (API key)
            api_secret: API密钥 (API secret)
            telegram_token: Telegram机器人令牌 (Telegram bot token)
            trades_dir: 交易数据存储目录 (Trades data directory)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.notifier = Notifier(telegram_token)
        self.positions = {}  # 当前持仓 (Current positions)
        self.last_stop_update = {}  # 上次止损更新时间 (Last stop update time)
        self.trades_dir = trades_dir  # 交易数据目录 (Trades data directory)

    def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行订单并发送通知。
        Execute order and send notification.

        参数 (Parameters):
            symbol: 交易对 (Trading pair)
            side: 交易方向 (Trade side) - BUY/SELL
            quantity: 交易数量 (Trade quantity)
            price: 限价单价格 (Limit price)
            reason: 交易原因 (Trade reason)

        返回 (Returns):
            Dict[str, Any]: 订单执行结果 (Order execution result)
        """
        try:
            # 执行订单逻辑 (Order execution logic)
            order_result = self._execute_order_internal(symbol, side, quantity, price)

            # 记录交易到CSV (Log trade to CSV)
            trade_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": symbol,
                "side": side,
                "price": order_result["price"],
                "quantity": order_result["quantity"],
                "amount": order_result["price"] * order_result["quantity"],
                "fee": order_result.get("fee", 0.0),
                "order_id": order_result.get("order_id", ""),
                "reason": reason or "",
            }
            self._log_trade_to_csv(trade_data)

            # 更新持仓信息 (Update position information)
            if side.upper() == "BUY":
                self.positions[symbol] = {
                    "symbol": symbol,
                    "entry_price": order_result["price"],
                    "quantity": order_result["quantity"],
                    "side": "LONG",
                    "entry_time": datetime.now(),
                    "stop_price": 0.0,  # 将在首次ATR更新时设置
                }
                self.last_stop_update[symbol] = datetime.now()
            else:
                # 清除持仓信息 (Clear position)
                if symbol in self.positions:
                    del self.positions[symbol]
                if symbol in self.last_stop_update:
                    del self.last_stop_update[symbol]

            # 发送交易通知 (Send trade notification)
            self.notifier.notify_trade(
                action=side,
                symbol=symbol,
                price=order_result["price"],
                quantity=order_result["quantity"],
                reason=reason,
            )

            return order_result

        except Exception as e:
            # 发送错误通知 (Send error notification)
            self.notifier.notify_error(e, f"Order execution for {symbol}")
            raise

    def _log_trade_to_csv(self, trade_data: Dict[str, Any]) -> None:
        """
        记录交易到CSV文件。
        Log trade to CSV file.

        参数 (Parameters):
            trade_data: 交易数据 (Trade data)
        """
        try:
            # 获取交易文件路径 (Get trade file path)
            symbol = trade_data["symbol"].lower()
            trades_file = utils.get_trades_file(symbol, self.trades_dir)

            # 准备数据帧 (Prepare dataframe)
            trade_df = pd.DataFrame([trade_data])

            # 检查文件是否已存在 (Check if file exists)
            file_exists = trades_file.exists()

            # 写入CSV，如果文件已存在则追加 (Write to CSV, append if file exists)
            if file_exists:
                trade_df.to_csv(trades_file, mode="a", header=False, index=False)
            else:
                # 确保目录存在 (Ensure directory exists)
                trades_file.parent.mkdir(parents=True, exist_ok=True)
                trade_df.to_csv(trades_file, index=False)

            print(f"Trade logged to {trades_file}")

        except Exception as e:
            print(f"Error logging trade to CSV: {e}")
            # 通知但不中断程序 (Notify but don't interrupt program)
            self.notifier.notify_error(e, "Trade logging")

    def get_all_trades(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取指定交易对的所有交易记录。
        Get all trades for specified symbol.

        参数 (Parameters):
            symbol: 交易对 (Trading pair)
            start_date: 开始日期 (Start date) 'YYYY-MM-DD'
            end_date: 结束日期 (End date) 'YYYY-MM-DD'

        返回 (Returns):
            pd.DataFrame: 交易记录 (Trade records)
        """
        try:
            # 获取交易文件路径 (Get trade file path)
            trades_file = utils.get_trades_file(symbol.lower(), self.trades_dir)

            # 检查文件是否存在 (Check if file exists)
            if not trades_file.exists():
                print(f"No trades found for {symbol}")
                return pd.DataFrame()

            # 读取CSV (Read CSV)
            trades_df = pd.read_csv(trades_file)

            # 确保时间戳列是日期时间类型 (Ensure timestamp column is datetime)
            trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])

            # 过滤日期范围 (Filter date range)
            if start_date:
                start_dt = pd.to_datetime(start_date)
                trades_df = trades_df[trades_df["timestamp"] >= start_dt]

            if end_date:
                end_dt = pd.to_datetime(end_date)
                trades_df = trades_df[trades_df["timestamp"] <= end_dt]

            return trades_df

        except Exception as e:
            print(f"Error getting trades: {e}")
            return pd.DataFrame()

    def update_position_stops(self, symbol: str, current_price: float, atr: float) -> None:
        """
        更新指定交易对的移动止损。
        Update trailing stop for specified symbol.

        参数 (Parameters):
            symbol: 交易对 (Trading pair)
            current_price: 当前价格 (Current price)
            atr: 当前ATR值 (Current ATR value)
        """
        try:
            # 检查是否持有该交易对头寸
            if symbol not in self.positions:
                return

            # 检查是否需要更新止损 (每小时一次)
            now = datetime.now()
            last_update = self.last_stop_update.get(symbol, datetime.min)
            time_since_update = now - last_update

            # 初始止损设置或每小时更新一次
            if self.positions[symbol]["stop_price"] == 0.0 or time_since_update >= timedelta(hours=1):
                # 使用ATR更新止损
                position = self.positions[symbol]

                # 初始止损设置 (如果尚未设置)
                if position["stop_price"] == 0.0:
                    initial_stop = position["entry_price"] - (atr * 2.0)  # 使用2倍ATR作为初始止损
                    position["stop_price"] = initial_stop

                    # 发送初始止损通知
                    stop_msg = (
                        f"🔒 初始止损设置 (Initial Stop Set)\n"
                        f"品种 (Symbol): {symbol}\n"
                        f"入场价 (Entry): {position['entry_price']:.8f}\n"
                        f"止损价 (Stop): {initial_stop:.8f}\n"
                        f"ATR: {atr:.8f}\n"
                        f"止损距离 (Distance): {(position['entry_price'] - initial_stop):.8f} "
                        f"({((position['entry_price'] - initial_stop)/position['entry_price'])*100:.2f}%)"
                    )
                    self.notifier.notify(stop_msg, "INFO")
                else:
                    # 更新移动止损
                    new_stop, updated = update_trailing_stop_atr(
                        position,
                        current_price,
                        atr,
                        multiplier=1.0,  # 使用1倍ATR作为跟踪距离
                        notifier=self.notifier,
                    )

                    if updated:
                        # 更新止损价格
                        self.positions[symbol]["stop_price"] = new_stop

                # 更新最后更新时间
                self.last_stop_update[symbol] = now

        except Exception as e:
            # 发送错误通知
            self.notifier.notify_error(e, f"Stop update for {symbol}")

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发止损。
        Check if stop loss is triggered.

        参数 (Parameters):
            symbol: 交易对 (Trading pair)
            current_price: 当前价格 (Current price)

        返回 (Returns):
            bool: 是否触发止损 (Whether stop loss is triggered)
        """
        try:
            # 检查是否持有该交易对头寸
            if symbol not in self.positions:
                return False

            position = self.positions[symbol]

            # 检查是否触发止损
            if position["stop_price"] > 0 and current_price <= position["stop_price"]:
                # 发送止损触发通知
                stop_msg = (
                    f"⚠️ 止损触发 (Stop Loss Triggered)\n"
                    f"品种 (Symbol): {symbol}\n"
                    f"当前价 (Price): {current_price:.8f}\n"
                    f"止损价 (Stop): {position['stop_price']:.8f}\n"
                    f"入场价 (Entry): {position['entry_price']:.8f}\n"
                    f"盈亏 (P/L): {(current_price - position['entry_price']) * position['quantity']:.8f} USDT\n"
                    f"盈亏% (P/L%): {((current_price - position['entry_price'])/position['entry_price'])*100:.2f}%"
                )
                self.notifier.notify(stop_msg, "WARN")

                # 执行止损订单
                self.execute_order(
                    symbol=symbol,
                    side="SELL",
                    quantity=position["quantity"],
                    reason="Stop loss triggered",
                )

                return True

            return False

        except Exception as e:
            # 发送错误通知
            self.notifier.notify_error(e, f"Stop check for {symbol}")
            return False

    def _execute_order_internal(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        内部订单执行逻辑。
        Internal order execution logic.
        """
        # 实际的订单执行代码 (Actual order execution code)
        # 这里应该调用交易所API (Should call exchange API here)
