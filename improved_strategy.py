#!/usr/bin/env python3
# improved_strategy.py
# 实现改进的交易策略并与买入持有策略对比

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src import signals, metrics, broker
from math import isfinite

def buy_and_hold(price: pd.Series, init_equity: float = 100_000.0) -> pd.Series:
    """
    简单的买入持有策略
    
    参数:
        price: 价格序列
        init_equity: 初始资金
        
    返回:
        pd.Series: 权益曲线
    """
    position_size = init_equity / price.iloc[0]  # 全仓买入
    equity_curve = init_equity + (price - price.iloc[0]) * position_size
    return equity_curve

def trend_following(price: pd.Series, 
                   long_win: int = 200,
                   atr_win: int = 20, 
                   risk_frac: float = 0.02,
                   init_equity: float = 100_000.0,
                   use_trailing_stop: bool = True) -> pd.Series:
    """
    改进的趋势跟踪策略
    
    使用方向性过滤器，只在价格高于长期移动均线时入场
    
    参数:
        price: 价格序列
        long_win: 长期移动均线窗口
        atr_win: ATR窗口
        risk_frac: 风险系数
        init_equity: 初始资金
        use_trailing_stop: 是否使用移动止损
        
    返回:
        pd.Series: 权益曲线
    """
    # 计算长期移动均线作为方向性过滤器
    long_ma = signals.moving_average(price, long_win)
    
    # 计算ATR用于止损
    tr = pd.concat(
        {
            "hl": price.rolling(2).max() - price.rolling(2).min(),
            "hc": (price - price.shift(1)).abs(),
            "lc": (price - price.shift(1)).abs(),
        }, axis=1
    ).max(axis=1)
    atr = tr.rolling(atr_win).mean()
    
    equity = init_equity
    equity_curve, position, entry, stop = [], 0, None, None
    initial_stop = None
    
    for i, p in enumerate(price):
        # 更新移动止损
        if use_trailing_stop and position and entry is not None and initial_stop is not None:
            current_atr = atr.iloc[i] if i < len(atr) and isfinite(atr.iloc[i]) else None
            new_stop = broker.compute_trailing_stop(
                entry, p, initial_stop, 
                breakeven_r=1.0, 
                trail_r=2.0,
                atr=current_atr
            )
            # 止损只能上移不能下移
            stop = max(stop, new_stop) if stop is not None else new_stop
        
        # 止损平仓
        if position and p < stop:
            equity += (p - entry) * position
            position = 0
            entry = None
            stop = None
            initial_stop = None
        
        # 价格跌破长期均线，考虑卖出
        if position and p < long_ma.iloc[i]:
            equity += (p - entry) * position
            position = 0
            entry = None
            stop = None
            initial_stop = None
            
        # 入场信号: 价格在长期均线上方 + 至少有20天数据 + 之前没有仓位
        if i > long_win and p > long_ma.iloc[i] and position == 0 and isfinite(atr.iloc[i]):
            size = broker.compute_position_size(equity, atr.iloc[i], risk_frac)
            position = size
            entry = p
            stop = broker.compute_stop_price(entry, atr.iloc[i])
            initial_stop = stop
            
        equity_curve.append(equity + (p - entry) * position if position else equity)
        
    return pd.Series(equity_curve, index=price.index[:len(equity_curve)])

def improved_ma_cross(price: pd.Series,
                     fast_win: int = 50,
                     slow_win: int = 200,
                     atr_win: int = 20,
                     risk_frac: float = 0.02,
                     init_equity: float = 100_000.0,
                     use_trailing_stop: bool = True) -> pd.Series:
    """
    改进的MA交叉策略
    
    使用更长期的均线和方向性过滤器
    
    参数:
        price: 价格序列
        fast_win: 快速均线窗口
        slow_win: 慢速均线窗口
        atr_win: ATR窗口
        risk_frac: 风险系数
        init_equity: 初始资金
        use_trailing_stop: 是否使用移动止损
        
    返回:
        pd.Series: 权益曲线
    """
    # 长期均线参数
    return broker.backtest_single(
        price, 
        fast_win=fast_win, 
        slow_win=slow_win, 
        atr_win=atr_win,
        risk_frac=risk_frac,
        init_equity=init_equity,
        use_trailing_stop=use_trailing_stop
    )

if __name__ == "__main__":
    # 加载数据
    df = pd.read_csv('btc_eth.csv', parse_dates=['date'], index_col='date')
    btc = df['btc']
    
    # 运行各种策略
    bnh_equity = buy_and_hold(btc)
    tf_equity = trend_following(btc, long_win=200, atr_win=20)
    improved_ma_equity = improved_ma_cross(btc, fast_win=50, slow_win=200, atr_win=20)
    original_ma_equity = broker.backtest_single(btc, fast_win=7, slow_win=20, atr_win=20)
    
    # 计算和比较绩效指标
    print("\n策略绩效比较:")
    print("-" * 80)
    print(f"简单买入持有:   CAGR: {metrics.cagr(bnh_equity):.2%}, MaxDD: {metrics.max_drawdown(bnh_equity):.2%}, Sharpe: {metrics.sharpe_ratio(bnh_equity):.2f}")
    print(f"趋势跟踪策略:   CAGR: {metrics.cagr(tf_equity):.2%}, MaxDD: {metrics.max_drawdown(tf_equity):.2%}, Sharpe: {metrics.sharpe_ratio(tf_equity):.2f}")
    print(f"改进MA交叉策略: CAGR: {metrics.cagr(improved_ma_equity):.2%}, MaxDD: {metrics.max_drawdown(improved_ma_equity):.2%}, Sharpe: {metrics.sharpe_ratio(improved_ma_equity):.2f}")
    print(f"原始MA交叉策略: CAGR: {metrics.cagr(original_ma_equity):.2%}, MaxDD: {metrics.max_drawdown(original_ma_equity):.2%}, Sharpe: {metrics.sharpe_ratio(original_ma_equity):.2f}")
    print("-" * 80)
    
    # 绘制对比图表
    plt.figure(figsize=(12, 6))
    plt.plot(bnh_equity / bnh_equity.iloc[0], label="买入持有", linewidth=2)
    plt.plot(tf_equity / tf_equity.iloc[0], label="趋势跟踪", linewidth=2)
    plt.plot(improved_ma_equity / improved_ma_equity.iloc[0], label="改进MA交叉(50/200)", linewidth=2)
    plt.plot(original_ma_equity / original_ma_equity.iloc[0], label="原始MA交叉(7/20)", linewidth=2)
    plt.title("BTC不同策略表现对比 (归一化)")
    plt.xlabel("日期")
    plt.ylabel("归一化权益")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("strategy_improvement.png")
    
    # 输出交易统计数据
    # 原始MA策略
    fast_orig = signals.moving_average(btc, 7)
    slow_orig = signals.moving_average(btc, 20)
    buy_orig = signals.bullish_cross_indices(fast_orig, slow_orig)
    sell_orig = signals.bearish_cross_indices(fast_orig, slow_orig)
    
    # 改进MA策略
    fast_improved = signals.moving_average(btc, 50)
    slow_improved = signals.moving_average(btc, 200)
    buy_improved = signals.bullish_cross_indices(fast_improved, slow_improved)
    sell_improved = signals.bearish_cross_indices(fast_improved, slow_improved)
    
    print("\n交易统计:")
    print("-" * 80)
    print(f"原始MA策略 (7/20):  买入信号 {len(buy_orig)} 次, 卖出信号 {len(sell_orig)} 次")
    print(f"改进MA策略 (50/200): 买入信号 {len(buy_improved)} 次, 卖出信号 {len(sell_improved)} 次")
    print("-" * 80)
    
    # 计算各策略CAGR
    cagr_bnh = metrics.cagr(bnh_equity)
    cagr_tf = metrics.cagr(tf_equity)
    cagr_improved_ma = metrics.cagr(improved_ma_equity)
    
    # 确定最优策略
    best_cagr = max(cagr_bnh, cagr_tf, cagr_improved_ma)
    if best_cagr == cagr_bnh:
        best_equity = bnh_equity
        best_name = "买入持有"
    elif best_cagr == cagr_tf:
        best_equity = tf_equity
        best_name = "趋势跟踪"
    else:
        best_equity = improved_ma_equity
        best_name = "改进MA交叉"
    
    print(f"\n最优策略 ({best_name}) 详细指标:")
    print("-" * 80)
    print(f"起始资金: {best_equity.iloc[0]:.2f}")
    print(f"最终资金: {best_equity.iloc[-1]:.2f}")
    print(f"净收益: {best_equity.iloc[-1] - best_equity.iloc[0]:.2f}")
    print(f"收益率: {(best_equity.iloc[-1]/best_equity.iloc[0]-1):.2%}")
    print(f"年化收益率: {metrics.cagr(best_equity):.2%}")
    print(f"最大回撤: {metrics.max_drawdown(best_equity):.2%}")
    print(f"夏普比率: {metrics.sharpe_ratio(best_equity):.2f}")
    print("-" * 80)
    
    print("\n策略改进建议已成功实施并评估完成!") 