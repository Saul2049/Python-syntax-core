import pandas as pd
import numpy as np
from math import isfinite, ceil

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


def compute_trailing_stop(entry: float, current_price: float, initial_stop: float, 
                         breakeven_r: float = 1.0, trail_r: float = 2.0, atr: float = None) -> float:
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
    if current_r >= breakeven_r and current_r < trail_r:
        return max(initial_stop, entry)  # 可以设为完全保本或略低于保本
        
    # 2. 跟踪止损(Trailing Stop) - 当盈利达到trail_r时
    if current_r >= trail_r:
        if atr is not None and atr > 0:
            # 基于ATR的跟踪距离 - 跟随价格但保持一定距离
            return current_price - atr
        else:
            # 基于百分比的跟踪 - 例如保持初始风险距离的50%
            trail_distance = initial_risk * 0.5
            return current_price - trail_distance
            
    # 默认返回初始止损
    return initial_stop


from src import signals   # 避免循环引用

def backtest_single(price: pd.Series,
                    fast_win: int = 7,
                    slow_win: int = 20,
                    atr_win : int = 20,
                    risk_frac: float = 0.02,
                    init_equity: float = 100_000.0,
                    use_trailing_stop: bool = True,
                    breakeven_r: float = 1.0,
                    trail_r: float = 2.0,
                    verbose: bool = False) -> pd.Series:
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
        }, axis=1
    ).max(axis=1)
    atr = tr.rolling(atr_win).mean()

    equity = init_equity
    equity_curve, position, entry, stop = [], 0, None, None
    initial_stop = None  # 记录初始止损位置，用于计算盈亏比
    stop_history = []    # 记录止损变动历史

    buy_i  = set(signals.bullish_cross_indices(fast, slow))
    sell_i = set(signals.bearish_cross_indices(fast, slow))

    for i, p in enumerate(price):
        # 更新移动止损
        if use_trailing_stop and position and entry is not None and initial_stop is not None:
            current_atr = atr.iloc[i] if i < len(atr) and isfinite(atr.iloc[i]) else None
            new_stop = compute_trailing_stop(
                entry, p, initial_stop, 
                breakeven_r=breakeven_r, 
                trail_r=trail_r,
                atr=current_atr
            )
            # 止损只能上移不能下移
            old_stop = stop
            stop = max(stop, new_stop) if stop is not None else new_stop
            
            # 记录止损变动
            if stop != old_stop and verbose:
                stop_history.append({
                    'date': price.index[i],
                    'price': p,
                    'old_stop': old_stop,
                    'new_stop': stop,
                    'type': 'update',
                    'atr': current_atr
                })
                print(f"[{price.index[i]}] 止损更新: {old_stop:.2f} -> {stop:.2f} (价格: {p:.2f})")
        
        # 止损
        if position and p < stop:
            equity += (p - entry) * position
            
            # 记录止损触发
            if verbose:
                stop_history.append({
                    'date': price.index[i],
                    'price': p,
                    'stop': stop,
                    'entry': entry,
                    'position': position,
                    'profit': (p - entry) * position,
                    'type': 'stop_loss'
                })
                print(f"[{price.index[i]}] 止损触发: 价格 {p:.2f} < 止损 {stop:.2f}, 盈亏: {(p - entry) * position:.2f}")
            
            position = 0
            entry = None
            stop = None
            initial_stop = None

        # 卖出信号
        if i in sell_i and position:
            equity += (p - entry) * position
            
            # 记录卖出
            if verbose:
                stop_history.append({
                    'date': price.index[i],
                    'price': p,
                    'stop': stop,
                    'entry': entry,
                    'position': position,
                    'profit': (p - entry) * position,
                    'type': 'sell_signal'
                })
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
                stop_history.append({
                    'date': price.index[i],
                    'price': p,
                    'stop': stop,
                    'entry': entry,
                    'position': position,
                    'risk': (entry - stop) * position,
                    'type': 'buy_signal'
                })
                print(f"[{price.index[i]}] 买入信号: 价格 {p:.2f}, 仓位 {position:.3f}, 止损 {stop:.2f}")

        equity_curve.append(equity + (p - entry) * position if position else equity)

    return pd.Series(equity_curve, index=price.index[:len(equity_curve)])

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

def backtest_portfolio(prices_dict, 
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
                       lookback=20,            # 相对强度计算期
                       prefer_better_asset=True, # 是否更积极地偏好表现较好的资产
                       weight_power=2.0):      # 权重幂次，增大会放大好资产权重
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
            prices, fast_win, slow_win, atr_win,
            risk_frac=base_risk_frac,
            init_equity=base_equity,
            use_trailing_stop=use_trailing_stop,
            breakeven_r=breakeven_r,
            trail_r=trail_r
        )
        asset_equity_curves[asset] = equity_curve
    
    # 创建基础权益矩阵
    equity_df = pd.DataFrame(asset_equity_curves)
    
    # 如果不使用动态权重，直接返回等权重结果
    if not use_dynamic_weights or asset_count <= 1:
        equity_df['Portfolio'] = equity_df.sum(axis=1)
        return equity_df
    
    # 计算相对强度 - 使用回报率+波动率
    returns_dict = {asset: equity_df[asset].pct_change() 
                    for asset in prices_dict.keys()}
    
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
    weights_df = pd.DataFrame(1.0/asset_count, 
                          index=equity_df.index, 
                          columns=equity_df.columns)
    
    # 滚动调整权重
    for i in range(lookback+1, len(equity_df)):
        # 获取当前绩效指标
        performance = composite_df.iloc[i-1]  # 使用前一天的指标
        
        # 避免所有资产都是负收益的极端情况
        if all(performance <= 0):
            min_performance = performance.min()
            if min_performance < 0:
                # 在所有为负时，选择最不差的
                adjusted_performance = performance - min_performance + 0.0001
            else:
                # 所有为0时，保持等权
                weights_df.iloc[i] = 1.0/asset_count
                continue
        else:
            # 将负指标调整为0
            adjusted_performance = performance.copy()
            adjusted_performance[adjusted_performance < 0] = 0
        
        # 如果所有调整后表现都是0，使用等权
        if adjusted_performance.sum() == 0:
            weights_df.iloc[i] = 1.0/asset_count
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
        base_weight = 1.0/asset_count
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
    for i in range(lookback+1, len(equity_df)):
        # 上一天的总权益
        prev_total_equity = adjusted_equity_df.iloc[i-1].sum()
        
        # 根据新权重重新分配资金
        for asset in equity_df.columns:
            # 获取此资产的原始单日回报率
            day_return = equity_df.iloc[i][asset] / equity_df.iloc[i-1][asset] if equity_df.iloc[i-1][asset] > 0 else 1.0
            
            # 应用加权后的资金计算新权益
            target_allocation = prev_total_equity * weights_df.iloc[i][asset]
            adjusted_equity_df.iloc[i, adjusted_equity_df.columns.get_loc(asset)] = target_allocation * day_return
    
    # 计算总投资组合价值
    adjusted_equity_df['Portfolio'] = adjusted_equity_df.sum(axis=1)
    
    return adjusted_equity_df 

# 在回测或实盘中使用单一BTC的配置
portfolio_config = {
    "assets": ["btc"],      # 只包含BTC
    "weights": [1.0],       # 100%权重
    "risk_frac": 0.02       # 维持2%的风险系数
} 