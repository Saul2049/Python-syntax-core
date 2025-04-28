import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from src.broker import Broker
from src.signals import moving_average
from src import utils


def fetch_price_data(symbol: str) -> pd.DataFrame:
    """
    获取价格数据。
    Fetch price data.
    
    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        
    返回 (Returns):
        pd.DataFrame: 价格数据 (Price data)
    """
    # 这里应实际调用交易所API获取数据
    # This should call exchange API to get data
    # 示例数据结构 (Example data structure)
    return pd.DataFrame({
        'timestamp': pd.date_range(start='2023-01-01', periods=100, freq='1h'),
        'open': np.random.normal(50000, 1000, 100),
        'high': np.random.normal(50500, 1000, 100),
        'low': np.random.normal(49500, 1000, 100),
        'close': np.random.normal(50000, 1000, 100),
        'volume': np.random.normal(100, 20, 100)
    }).set_index('timestamp')


def calculate_atr(df: pd.DataFrame, window: int = 14) -> float:
    """
    计算ATR值。
    Calculate ATR value.
    
    参数 (Parameters):
        df: 价格数据 (Price data)
        window: 计算窗口 (Calculation window)
        
    返回 (Returns):
        float: ATR值 (ATR value)
    """
    # 计算真实波幅 (Calculate true range)
    df = df.copy()
    df['tr0'] = abs(df['high'] - df['low'])
    df['tr1'] = abs(df['high'] - df['close'].shift())
    df['tr2'] = abs(df['low'] - df['close'].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
    
    # 计算ATR (Calculate ATR)
    df['atr'] = df['tr'].rolling(window).mean()
    
    # 返回最新的ATR值 (Return latest ATR value)
    return df['atr'].iloc[-1]


def get_trading_signals(df: pd.DataFrame, fast_win: int = 7, slow_win: int = 25) -> Dict[str, Any]:
    """
    获取交易信号。
    Get trading signals.
    
    参数 (Parameters):
        df: 价格数据 (Price data)
        fast_win: 快线窗口 (Fast MA window)
        slow_win: 慢线窗口 (Slow MA window)
        
    返回 (Returns):
        Dict[str, Any]: 信号字典 (Signal dictionary)
    """
    # 计算移动平均线 (Calculate moving averages)
    df = df.copy()
    df['fast_ma'] = moving_average(df['close'], fast_win, kind="ema")
    df['slow_ma'] = moving_average(df['close'], slow_win, kind="ema")
    
    # 检查交叉 (Check crossover)
    df['prev_fast'] = df['fast_ma'].shift(1)
    df['prev_slow'] = df['slow_ma'].shift(1)
    
    # 金叉信号 (Golden cross signal)
    buy_signal = (df['prev_fast'] <= df['prev_slow']) & (df['fast_ma'] > df['slow_ma'])
    
    # 死叉信号 (Death cross signal)
    sell_signal = (df['prev_fast'] >= df['prev_slow']) & (df['fast_ma'] < df['slow_ma'])
    
    # 当前价格 (Current price)
    current_price = df['close'].iloc[-1]
    
    # 返回信号 (Return signals)
    return {
        "buy_signal": bool(buy_signal.iloc[-1]),
        "sell_signal": bool(sell_signal.iloc[-1]),
        "current_price": current_price,
        "fast_ma": df['fast_ma'].iloc[-1],
        "slow_ma": df['slow_ma'].iloc[-1],
        "last_timestamp": df.index[-1]
    }


def trading_loop(symbol: str = "BTCUSDT", interval_seconds: int = 60):
    """
    交易循环 - 定时执行策略并发送通知。
    Trading loop - Execute strategy periodically and send notifications.
    
    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        interval_seconds: 循环间隔 (Loop interval)
    """
    print(f"启动交易循环，交易对: {symbol}, 循环间隔: {interval_seconds}秒")
    
    # 初始化broker (Initialize broker)
    broker = Broker(
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET"),
        telegram_token=os.getenv("TG_TOKEN")
    )
    
    # 初始化最后更新时间 (Initialize last update time)
    last_check = datetime.now() - timedelta(hours=1)
    
    try:
        # 发送启动通知 (Send startup notification)
        broker.notifier.notify(f"🚀 交易机器人启动 (Trading bot started)\n交易对: {symbol}", "INFO")
        
        while True:
            current_time = datetime.now()
            
            try:
                # 获取市场数据 (Get market data)
                price_data = fetch_price_data(symbol)
                
                # 计算ATR (Calculate ATR)
                atr = calculate_atr(price_data)
                
                # 获取交易信号 (Get trading signals)
                signals = get_trading_signals(price_data)
                current_price = signals["current_price"]
                
                # 更新持仓止损价 (Update position stop price)
                broker.update_position_stops(symbol, current_price, atr)
                
                # 检查止损 (Check stop loss)
                stop_triggered = broker.check_stop_loss(symbol, current_price)
                
                # 如果止损已触发，跳过信号处理 (Skip signal processing if stop loss triggered)
                if stop_triggered:
                    print(f"止损已触发，跳过信号处理 (Stop loss triggered, skipping signal processing)")
                else:
                    # 处理买入信号 (Process buy signals)
                    if signals["buy_signal"] and symbol not in broker.positions:
                        # 计算仓位大小 - 假设 1% 风险 (Calculate position size - assume 1% risk)
                        equity = 10000.0  # 示例权益 (Example equity)
                        risk_amount = equity * 0.01
                        stop_price = current_price - (atr * 2.0)
                        risk_per_unit = current_price - stop_price
                        quantity = risk_amount / risk_per_unit
                        
                        # 限制数量小数位 (Limit decimal places)
                        quantity = round(quantity, 3)  # 假设最小单位是0.001 (Assume minimum unit is 0.001)
                        
                        # 执行买入订单 (Execute buy order)
                        broker.execute_order(
                            symbol=symbol,
                            side="BUY",
                            quantity=quantity,
                            reason=f"MA交叉: 快线 {signals['fast_ma']:.2f} 上穿 慢线 {signals['slow_ma']:.2f}"
                        )
                    
                    # 处理卖出信号 (Process sell signals)
                    elif signals["sell_signal"] and symbol in broker.positions:
                        # 执行卖出订单 (Execute sell order)
                        position = broker.positions[symbol]
                        broker.execute_order(
                            symbol=symbol,
                            side="SELL",
                            quantity=position["quantity"],
                            reason=f"MA交叉: 快线 {signals['fast_ma']:.2f} 下穿 慢线 {signals['slow_ma']:.2f}"
                        )
                
                # 打印状态 (Print status)
                print(f"[{current_time}] 价格: {current_price:.2f}, ATR: {atr:.2f}, 信号: {'BUY' if signals['buy_signal'] else 'SELL' if signals['sell_signal'] else 'HOLD'}")
                
                # 每小时发送状态通知 (Send status notification every hour)
                if (current_time - last_check).total_seconds() >= 3600:  # 3600秒 = 1小时
                    status_msg = (
                        f"📈 状态更新 (Status Update)\n"
                        f"品种 (Symbol): {symbol}\n"
                        f"价格 (Price): {current_price:.8f}\n"
                        f"ATR: {atr:.8f}\n"
                        f"快线 (Fast MA): {signals['fast_ma']:.8f}\n"
                        f"慢线 (Slow MA): {signals['slow_ma']:.8f}\n"
                        f"头寸 (Position): {'有' if symbol in broker.positions else '无'}"
                    )
                    
                    if symbol in broker.positions:
                        position = broker.positions[symbol]
                        status_msg += f"\n入场价 (Entry): {position['entry_price']:.8f}"
                        status_msg += f"\n止损价 (Stop): {position['stop_price']:.8f}"
                        status_msg += f"\n数量 (Quantity): {position['quantity']:.8f}"
                        status_msg += f"\n盈亏 (P/L): {(current_price - position['entry_price']) * position['quantity']:.8f} USDT"
                        status_msg += f"\n盈亏% (P/L%): {((current_price - position['entry_price'])/position['entry_price'])*100:.2f}%"
                    
                    broker.notifier.notify(status_msg, "INFO")
                    last_check = current_time
                
            except Exception as e:
                # 发送错误通知 (Send error notification)
                broker.notifier.notify_error(e, "Trading loop error")
                print(f"错误: {e}")
            
            # 等待下一次循环 (Wait for next loop)
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        # 发送关闭通知 (Send shutdown notification)
        broker.notifier.notify("🛑 交易机器人关闭 (Trading bot stopped)", "INFO")
        print("交易循环已关闭 (Trading loop stopped)")


if __name__ == "__main__":
    # 使用环境变量 (Use environment variables)
    if "TG_TOKEN" not in os.environ:
        print("警告: 未设置TG_TOKEN环境变量，通知功能将不可用")
        
    if "API_KEY" not in os.environ or "API_SECRET" not in os.environ:
        print("警告: 未设置API_KEY或API_SECRET环境变量，交易功能将不可用")
    
    # 启动交易循环 (Start trading loop)
    trading_loop() 