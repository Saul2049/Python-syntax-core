#!/usr/bin/env python3
# market_simulator.py - 市场模拟器模块

import os
from datetime import datetime
from typing import Callable, Dict, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class MarketSimulator:
    """
    市场模拟器类，用于回测交易策略
    """

    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
    ):
        """
        初始化市场模拟器

        参数:
            data: 包含价格数据的DataFrame
            initial_capital: 初始资金
            commission: 交易佣金百分比
            slippage: 滑点百分比
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        # 确保数据有日期索引
        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise ValueError("数据必须具有DatetimeIndex索引")

        # 确保数据按日期排序
        self.data = self.data.sort_index()

        # 交易结果
        self.positions = pd.DataFrame(index=self.data.index)
        self.holdings = pd.DataFrame(index=self.data.index)
        self.performance = pd.DataFrame(index=self.data.index)

        # 交易记录
        self.trades = []

    def run_backtest(self, strategy_func: Callable, *args, **kwargs) -> pd.DataFrame:
        """
        运行回测

        参数:
            strategy_func: 策略函数，接受市场数据并返回信号
            *args, **kwargs: 传递给策略函数的其他参数

        返回:
            回测结果DataFrame
        """
        # 运行策略函数获取信号
        signals = strategy_func(self.data, *args, **kwargs)

        # 确保信号DataFrame有正确的索引
        if not isinstance(signals, pd.DataFrame):
            signals = pd.DataFrame(signals, index=self.data.index)

        # 确保有"signal"列
        if "signal" not in signals.columns:
            raise ValueError("策略函数必须返回包含'signal'列的DataFrame")

        # 生成仓位和权益
        self._generate_positions(signals)
        self._calculate_holdings()
        self._calculate_performance()

        return self.performance

    def _generate_positions(self, signals: pd.DataFrame) -> None:
        """
        根据信号生成仓位

        参数:
            signals: 包含交易信号的DataFrame
        """
        # 创建仓位DataFrame
        self.positions = signals.copy()

        # 添加价格列
        self.positions["price"] = self.data["close"]

        # 计算实际执行价格（考虑滑点）
        self.positions["exec_price"] = self.positions.apply(
            lambda x: (
                x["price"] * (1 + self.slippage)
                if x["signal"] > 0
                else x["price"] * (1 - self.slippage) if x["signal"] < 0 else x["price"]
            ),
            axis=1,
        )

        # 计算佣金
        self.positions["commission"] = (
            abs(self.positions["signal"]) * self.positions["exec_price"] * self.commission
        )

        # 记录交易
        self._record_trades()

    def _record_trades(self) -> None:
        """记录交易详情"""
        prev_signal = 0

        for date, row in self.positions.iterrows():
            if row["signal"] != prev_signal:
                # 如果信号改变，记录交易
                trade = {
                    "date": date,
                    "signal": row["signal"],
                    "price": row["exec_price"],
                    "commission": row["commission"],
                }
                self.trades.append(trade)

                prev_signal = row["signal"]

    def _calculate_holdings(self) -> None:
        """计算仓位价值和现金持有量"""
        # 初始化持仓DataFrame
        self.holdings = pd.DataFrame(index=self.positions.index)

        # 初始现金
        self.holdings["cash"] = self.initial_capital

        # 持有的资产数量
        self.holdings["units"] = 0

        # 资产价值
        self.holdings["asset_value"] = 0

        # 计算每个时间点的持仓
        prev_signal = 0
        for i, (date, row) in enumerate(self.positions.iterrows()):
            if i > 0:
                # 继承前一时间点的现金和资产数量
                self.holdings.loc[date, "cash"] = self.holdings.iloc[i - 1]["cash"]
                self.holdings.loc[date, "units"] = self.holdings.iloc[i - 1]["units"]

            # 如果信号改变，更新仓位
            if row["signal"] != prev_signal:
                if row["signal"] > 0 and prev_signal <= 0:
                    # 买入信号
                    units_to_buy = (
                        self.holdings.loc[date, "cash"]
                        * 0.99
                        / (row["exec_price"] * (1 + self.commission))
                    )
                    cost = units_to_buy * row["exec_price"] * (1 + self.commission)

                    self.holdings.loc[date, "units"] += units_to_buy
                    self.holdings.loc[date, "cash"] -= cost

                elif row["signal"] <= 0 and prev_signal > 0:
                    # 卖出信号
                    units_to_sell = self.holdings.loc[date, "units"]
                    proceeds = units_to_sell * row["exec_price"] * (1 - self.commission)

                    self.holdings.loc[date, "units"] = 0
                    self.holdings.loc[date, "cash"] += proceeds

            # 更新资产价值
            self.holdings.loc[date, "asset_value"] = self.holdings.loc[date, "units"] * row["price"]

            prev_signal = row["signal"]

    def _calculate_performance(self) -> None:
        """计算回测性能指标"""
        # 计算总资产价值
        self.performance = pd.DataFrame(index=self.holdings.index)
        self.performance["total_value"] = self.holdings["cash"] + self.holdings["asset_value"]

        # 计算日收益率
        self.performance["daily_returns"] = self.performance["total_value"].pct_change()

        # 计算累计收益率
        self.performance["cumulative_returns"] = (
            self.performance["total_value"] / self.initial_capital - 1
        )

        # 计算其他指标
        self._calculate_risk_metrics()

    def _calculate_risk_metrics(self) -> None:
        """计算风险指标"""
        # 年化收益率
        days = (self.performance.index[-1] - self.performance.index[0]).days
        years = days / 365.0

        total_return = self.performance["cumulative_returns"].iloc[-1]
        self.performance["annualized_return"] = (
            (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return
        )

        # 波动率
        self.performance["volatility"] = self.performance["daily_returns"].std() * np.sqrt(252)

        # 夏普比率
        risk_free_rate = 0.0  # 可以根据需要调整
        self.performance["sharpe_ratio"] = (
            (self.performance["annualized_return"] - risk_free_rate)
            / self.performance["volatility"]
            if self.performance["volatility"].iloc[-1] > 0
            else 0
        )

        # 最大回撤
        cum_returns = self.performance["total_value"]
        running_max = cum_returns.cummax()
        drawdown = (cum_returns / running_max) - 1
        self.performance["max_drawdown"] = drawdown.min()

    def get_trade_statistics(self) -> Dict[str, Union[float, int]]:
        """
        获取交易统计数据

        返回:
            包含交易统计数据的字典
        """
        if not self.trades:
            return {"total_trades": 0}

        # 初始化统计数据
        stats = {
            "total_trades": len(self.trades) // 2,  # 买入+卖出算作一次交易
            "initial_capital": self.initial_capital,
            "final_capital": self.performance["total_value"].iloc[-1],
            "total_return": self.performance["cumulative_returns"].iloc[-1],
            "annualized_return": self.performance["annualized_return"].iloc[-1],
            "volatility": self.performance["volatility"].iloc[-1],
            "sharpe_ratio": self.performance["sharpe_ratio"].iloc[-1],
            "max_drawdown": self.performance["max_drawdown"].iloc[-1],
        }

        return stats

    def plot_results(self, save_path: Optional[str] = None, show_plot: bool = True) -> None:
        """
        绘制回测结果

        参数:
            save_path: 保存图表的路径（可选）
            show_plot: 是否显示图表
        """
        # 创建图表
        fig, axes = plt.subplots(3, 1, figsize=(12, 16), sharex=True)

        # 设置标题
        fig.suptitle("策略回测结果", fontsize=16)

        # 绘制价格和信号
        axes[0].set_title("价格和交易信号")
        axes[0].plot(self.data.index, self.data["close"], label="价格")

        # 添加买入和卖出点
        buy_signals = [t for t in self.trades if t["signal"] > 0]
        sell_signals = [t for t in self.trades if t["signal"] <= 0]

        if buy_signals:
            buy_dates = [t["date"] for t in buy_signals]
            buy_prices = [t["price"] for t in buy_signals]
            axes[0].scatter(buy_dates, buy_prices, marker="^", color="g", label="买入信号", s=100)

        if sell_signals:
            sell_dates = [t["date"] for t in sell_signals]
            sell_prices = [t["price"] for t in sell_signals]
            axes[0].scatter(
                sell_dates,
                sell_prices,
                marker="v",
                color="r",
                label="卖出信号",
                s=100,
            )

        axes[0].set_ylabel("价格")
        axes[0].legend()
        axes[0].grid(True)

        # 绘制资产价值
        axes[1].set_title("账户价值")
        axes[1].plot(self.performance.index, self.performance["total_value"], label="总资产")
        axes[1].plot(self.holdings.index, self.holdings["cash"], label="现金", alpha=0.7)
        axes[1].plot(
            self.holdings.index,
            self.holdings["asset_value"],
            label="资产价值",
            alpha=0.7,
        )
        axes[1].set_ylabel("价值")
        axes[1].legend()
        axes[1].grid(True)

        # 绘制累计收益率
        axes[2].set_title("累计收益率")
        axes[2].plot(
            self.performance.index,
            self.performance["cumulative_returns"] * 100,
            label="策略收益率",
        )

        # 计算买入持有收益率
        buy_hold_returns = (self.data["close"] / self.data["close"].iloc[0] - 1) * 100
        axes[2].plot(self.data.index, buy_hold_returns, label="买入持有收益率", alpha=0.7)

        axes[2].set_ylabel("收益率 (%)")
        axes[2].legend()
        axes[2].grid(True)

        # 添加统计信息
        stats = self.get_trade_statistics()
        stats_text = "\n".join(
            [
                f"总交易次数: {stats['total_trades']}",
                f"总收益率: {stats['total_return']:.2%}",
                f"年化收益率: {stats['annualized_return']:.2%}",
                f"波动率: {stats['volatility']:.2%}",
                f"夏普比率: {stats['sharpe_ratio']:.2f}",
                f"最大回撤: {stats['max_drawdown']:.2%}",
            ]
        )

        # 在图表边上添加文本框
        plt.figtext(
            0.01,
            0.01,
            stats_text,
            horizontalalignment="left",
            bbox={"facecolor": "white", "alpha": 0.8, "pad": 5},
        )

        plt.tight_layout()
        plt.subplots_adjust(top=0.95)

        # 保存图表
        if save_path:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")

        # 显示图表
        if show_plot:
            plt.show()
        else:
            plt.close()

    def get_performance_df(self) -> pd.DataFrame:
        """
        获取性能指标DataFrame

        返回:
            包含性能指标的DataFrame
        """
        return self.performance

    def get_trades_df(self) -> pd.DataFrame:
        """
        获取交易记录DataFrame

        返回:
            包含交易记录的DataFrame
        """
        return pd.DataFrame(self.trades)


def run_simple_backtest(
    data: pd.DataFrame,
    strategy_func: Callable,
    initial_capital: float = 10000.0,
    commission: float = 0.001,
    slippage: float = 0.0005,
    save_plot: bool = False,
    plot_filename: Optional[str] = None,
    **strategy_params,
) -> Dict[str, Union[float, int]]:
    """
    运行简单的回测并返回统计数据

    参数:
        data: 价格数据DataFrame
        strategy_func: 策略函数
        initial_capital: 初始资金
        commission: 交易佣金率
        slippage: 滑点率
        save_plot: 是否保存图表
        plot_filename: 图表文件名
        **strategy_params: 传递给策略函数的参数

    返回:
        包含回测统计数据的字典
    """
    # 创建模拟器实例
    simulator = MarketSimulator(
        data, initial_capital=initial_capital, commission=commission, slippage=slippage
    )

    # 运行回测
    simulator.run_backtest(strategy_func, **strategy_params)

    # 绘制结果
    if save_plot:
        if plot_filename is None:
            plot_filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        if not os.path.isabs(plot_filename):
            plot_filename = os.path.join("output", plot_filename)

        simulator.plot_results(save_path=plot_filename, show_plot=False)

    # 返回统计数据
    return simulator.get_trade_statistics()


if __name__ == "__main__":
    # 示例用法
    from src.data_processor import load_data, process_ohlcv_data
    from src.improved_strategy import improved_ma_cross

    # 加载数据
    df = load_data("btc_eth.csv")

    if not df.empty:
        # 处理数据
        processed_data = process_ohlcv_data(df)

        # 定义策略参数
        strategy_params = {"short_window": 10, "long_window": 50}

        # 运行回测
        stats = run_simple_backtest(
            processed_data,
            improved_ma_cross,
            initial_capital=10000.0,
            save_plot=True,
            plot_filename="improved_ma_cross_backtest.png",
            **strategy_params,
        )

        # 打印结果
        print("\n==== 回测结果 ====")
        for key, value in stats.items():
            if isinstance(value, float):
                if "return" in key or "drawdown" in key or "volatility" in key:
                    print(f"{key}: {value:.2%}")
                else:
                    print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
    else:
        print("无法加载数据，请检查输入文件.")
