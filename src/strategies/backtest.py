"""
回测模块 (Backtesting Module)

提供交易策略回测功能，包括：
- 单一资产回测
- 投资组合回测
- 动态权重计算
- 性能指标计算
"""

import pandas as pd

from src import signals
from src.core.risk_management import (
    compute_position_size,
    compute_stop_price,
    compute_trailing_stop,
)


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
        pd.Series: 权益曲线序列 (Equity curve series)
    """
    # 确保价格序列不为空
    if price.empty:
        return pd.Series([init_equity], index=[price.index[0]] if len(price.index) > 0 else [0])

    # 创建回测执行器
    executor = BacktestExecutor(
        price=price,
        fast_win=fast_win,
        slow_win=slow_win,
        atr_win=atr_win,
        risk_frac=risk_frac,
        init_equity=init_equity,
        use_trailing_stop=use_trailing_stop,
        breakeven_r=breakeven_r,
        trail_r=trail_r,
        verbose=verbose,
    )

    return executor.run_backtest()


class BacktestExecutor:
    """回测执行器类，处理回测的复杂逻辑"""

    def __init__(
        self,
        price: pd.Series,
        fast_win: int,
        slow_win: int,
        atr_win: int,
        risk_frac: float,
        init_equity: float,
        use_trailing_stop: bool,
        breakeven_r: float,
        trail_r: float,
        verbose: bool,
    ):
        self.price = price
        self.fast_win = fast_win
        self.slow_win = slow_win
        self.atr_win = atr_win
        self.risk_frac = risk_frac
        self.init_equity = init_equity
        self.use_trailing_stop = use_trailing_stop
        self.breakeven_r = breakeven_r
        self.trail_r = trail_r
        self.verbose = verbose

        # 交易状态
        self.equity = init_equity
        self.position = 0
        self.entry_price = 0
        self.stop_price = 0
        self.initial_stop = 0
        self.equity_curve = []

    def run_backtest(self) -> pd.Series:
        """执行完整的回测流程"""
        # 计算技术指标
        indicators = self._calculate_indicators()

        # 获取交易信号
        signals_data = self._get_trading_signals(indicators)

        # 执行回测循环
        for i in range(len(self.price)):
            self._process_price_point(i, indicators, signals_data)

        return pd.Series(self.equity_curve, index=self.price.index)

    def _calculate_indicators(self) -> dict:
        """计算技术指标"""
        fast_ma = signals.moving_average(self.price, self.fast_win, kind="sma")
        slow_ma = signals.moving_average(self.price, self.slow_win, kind="sma")

        # 计算ATR序列
        tr_series = self.price.diff().abs()  # 简化的TR计算
        atr_series = tr_series.rolling(window=self.atr_win).mean()

        return {"fast_ma": fast_ma, "slow_ma": slow_ma, "atr_series": atr_series}

    def _get_trading_signals(self, indicators: dict) -> dict:
        """获取交易信号"""
        buy_signals = set(
            signals.bullish_cross_indices(indicators["fast_ma"], indicators["slow_ma"])
        )
        sell_signals = set(
            signals.bearish_cross_indices(indicators["fast_ma"], indicators["slow_ma"])
        )

        return {"buy_signals": buy_signals, "sell_signals": sell_signals}

    def _process_price_point(self, i: int, indicators: dict, signals_data: dict):
        """处理单个价格点的逻辑"""
        current_price = self.price.iloc[i]
        current_atr = self._get_current_atr(i, indicators["atr_series"])

        # 更新止损
        self._update_trailing_stop(current_price, current_atr)

        # 检查止损触发
        stop_triggered = self._check_stop_loss(current_price)

        # 处理交易信号
        self._handle_trading_signals(i, current_price, current_atr, signals_data, stop_triggered)

        # 更新权益曲线
        self._update_equity_curve(current_price)

    def _get_current_atr(self, i: int, atr_series: pd.Series) -> float:
        """获取当前ATR值"""
        try:
            if i < len(atr_series):
                value = atr_series.iloc[i]
                if pd.notna(value):
                    return float(value)
        except (IndexError, TypeError, ValueError):
            pass
        return 0.0

    def _update_trailing_stop(self, current_price: float, current_atr: float):
        """更新跟踪止损"""
        if not (
            self.use_trailing_stop
            and self.position > 0
            and self.entry_price > 0
            and self.initial_stop > 0
        ):
            return

        new_stop = compute_trailing_stop(
            entry=self.entry_price,
            current_price=current_price,
            initial_stop=self.initial_stop,
            breakeven_r=self.breakeven_r,
            trail_r=self.trail_r,
            atr=current_atr if current_atr > 0 else None,
        )

        # 止损只能向有利方向移动
        if new_stop > self.stop_price:
            self.stop_price = new_stop
            if self.verbose:
                print(f"止损更新: {self.stop_price:.4f}")

    def _check_stop_loss(self, current_price: float) -> bool:
        """检查止损是否触发"""
        return self.position > 0 and self.stop_price > 0 and current_price <= self.stop_price

    def _handle_trading_signals(
        self,
        i: int,
        current_price: float,
        current_atr: float,
        signals_data: dict,
        stop_triggered: bool,
    ):
        """处理交易信号"""
        buy_signals = signals_data["buy_signals"]
        sell_signals = signals_data["sell_signals"]

        # 买入信号处理
        if i in buy_signals and self.position == 0 and current_atr > 0:
            self._execute_buy(current_price, current_atr)

        # 卖出信号或止损触发处理
        elif (i in sell_signals or stop_triggered) and self.position > 0:
            self._execute_sell(current_price, stop_triggered)

    def _execute_buy(self, current_price: float, current_atr: float):
        """执行买入操作"""
        position_size = compute_position_size(self.equity, current_atr, self.risk_frac)
        self.position = position_size
        self.entry_price = current_price
        self.stop_price = compute_stop_price(self.entry_price, current_atr, multiplier=1.0)
        self.initial_stop = self.stop_price

        if self.verbose:
            print(
                f"买入: 价格={current_price:.4f}, 数量={self.position}, 止损={self.stop_price:.4f}"
            )

    def _execute_sell(self, current_price: float, stop_triggered: bool):
        """执行卖出操作"""
        pnl = (current_price - self.entry_price) * self.position
        self.equity += pnl

        if self.verbose:
            action = "止损" if stop_triggered else "信号"
            print(f"{action}卖出: 价格={current_price:.4f}, 盈亏={pnl:.2f}, 权益={self.equity:.2f}")

        # 重置交易状态
        self.position = 0
        self.entry_price = 0
        self.stop_price = 0
        self.initial_stop = 0

    def _update_equity_curve(self, current_price: float):
        """更新权益曲线"""
        current_equity = self.equity
        if self.position > 0:
            unrealized_pnl = (current_price - self.entry_price) * self.position
            current_equity += unrealized_pnl

        self.equity_curve.append(current_equity)


def _calculate_base_equity_curves(
    prices_dict,
    fast_win,
    slow_win,
    atr_win,
    base_risk_frac,
    base_equity,
    use_trailing_stop,
    breakeven_r,
    trail_r,
):
    """计算基础权益曲线"""
    equity_curves = {}
    for symbol, price_series in prices_dict.items():
        equity_curves[symbol] = backtest_single(
            price=price_series,
            fast_win=fast_win,
            slow_win=slow_win,
            atr_win=atr_win,
            risk_frac=base_risk_frac,
            init_equity=base_equity,
            use_trailing_stop=use_trailing_stop,
            breakeven_r=breakeven_r,
            trail_r=trail_r,
        )
    return equity_curves


def _calculate_performance_metrics(equity_df, lookback, prefer_better_asset):
    """计算性能指标"""
    returns_df = equity_df.pct_change().fillna(0)

    # 计算滚动夏普比率
    rolling_mean = returns_df.rolling(window=lookback).mean()
    rolling_std = returns_df.rolling(window=lookback).std()
    sharpe_ratios = rolling_mean / (rolling_std + 1e-8)

    # 计算滚动收益率
    rolling_returns = equity_df.pct_change(periods=lookback).fillna(0)

    if prefer_better_asset:
        # 使用夏普比率作为权重基础
        performance_scores = sharpe_ratios.fillna(0)
    else:
        # 使用收益率作为权重基础
        performance_scores = rolling_returns.fillna(0)

    return performance_scores


def _calculate_dynamic_weights(
    composite_df,
    equity_df,
    lookback,
    asset_count,
    weight_power,
    min_weight_factor,
    max_weight_factor,
):
    """计算动态权重"""
    performance_scores = _calculate_performance_metrics(equity_df, lookback, True)

    # 确保性能分数为正值
    min_score = performance_scores.min().min()
    if min_score < 0:
        performance_scores = performance_scores - min_score + 0.01

    # 应用权重幂次
    weighted_scores = performance_scores**weight_power

    # 计算原始权重
    weight_sums = weighted_scores.sum(axis=1)
    raw_weights = weighted_scores.div(weight_sums + 1e-8, axis=0)

    # 应用权重约束
    constrained_weights = _apply_weight_constraints(
        raw_weights, asset_count, min_weight_factor, max_weight_factor
    )

    return constrained_weights


def _apply_weight_constraints(raw_weights, asset_count, min_weight_factor, max_weight_factor):
    """应用权重约束"""
    equal_weight = 1.0 / asset_count
    min_weight = equal_weight * min_weight_factor
    max_weight = equal_weight * max_weight_factor

    # 限制权重范围
    constrained_weights = raw_weights.clip(lower=min_weight, upper=max_weight, axis=1)

    # 重新标准化
    weight_sums = constrained_weights.sum(axis=1)
    final_weights = constrained_weights.div(weight_sums, axis=0)

    return final_weights


def _apply_dynamic_rebalancing(equity_df, weights_df, lookback):
    """应用动态再平衡"""
    composite_equity = []

    for i in range(len(equity_df)):
        if i < lookback:
            # 使用等权重
            weight_vector = pd.Series(
                [1.0 / len(equity_df.columns)] * len(equity_df.columns), index=equity_df.columns
            )
        else:
            weight_vector = weights_df.iloc[i]

        # 计算加权权益
        weighted_equity = (equity_df.iloc[i] * weight_vector).sum()
        composite_equity.append(weighted_equity)

    return pd.Series(composite_equity, index=equity_df.index)


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
    max_weight_factor=1.5,
    min_weight_factor=0.5,
    lookback=20,
    prefer_better_asset=True,
    weight_power=2.0,
):
    """
    投资组合回测函数。

    参数:
        prices_dict: 价格数据字典，键为资产符号，值为价格序列
        其他参数: 与backtest_single相同的策略参数
        use_dynamic_weights: 是否使用动态权重
        max_weight_factor: 最大权重系数
        min_weight_factor: 最小权重系数
        lookback: 回望窗口
        prefer_better_asset: 是否偏好表现更好的资产
        weight_power: 权重幂次

    返回:
        Dict: 包含组合权益曲线和其他信息的字典
    """
    # 计算基础权益曲线
    equity_curves = _calculate_base_equity_curves(
        prices_dict,
        fast_win,
        slow_win,
        atr_win,
        base_risk_frac,
        init_equity,
        use_trailing_stop,
        breakeven_r,
        trail_r,
    )

    # 创建权益DataFrame
    equity_df = pd.DataFrame(equity_curves)
    equity_df = equity_df.fillna(method="ffill").fillna(init_equity)

    if use_dynamic_weights:
        # 计算动态权重
        weights_df = _calculate_dynamic_weights(
            equity_df,
            equity_df,
            lookback,
            len(prices_dict),
            weight_power,
            min_weight_factor,
            max_weight_factor,
        )

        # 应用动态再平衡
        composite_equity = _apply_dynamic_rebalancing(equity_df, weights_df, lookback)
    else:
        # 使用等权重
        composite_equity = equity_df.mean(axis=1)

    return {
        "composite_equity": composite_equity,
        "individual_equity": equity_df,
        "weights": weights_df if use_dynamic_weights else None,
    }
