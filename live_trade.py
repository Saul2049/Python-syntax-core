#!/usr/bin/env python3
"""
使用Binance Testnet执行实时交易
"""
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
import csv
import configparser
import argparse
import sys
import json
from math import isfinite

from src import signals, broker
from src.binance_client import BinanceClient

# 持仓状态文件路径
POSITION_STATE_FILE = 'position_state.json'

def setup_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description='Binance Testnet实时交易')
    
    parser.add_argument('--config', type=str, default='config.ini',
                      help='配置文件路径 (默认: config.ini)')
                      
    parser.add_argument('--interval', type=str, default='1d',
                      help='K线周期，如1m, 5m, 15m, 1h, 4h, 1d (默认: 1d)')
                      
    parser.add_argument('--test', action='store_true',
                      help='仅运行测试模式，不执行实际交易')
    
    return parser

def load_config(config_file):
    """加载配置文件"""
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        sys.exit(1)
        
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # 验证必要的配置项
    required_sections = ['BINANCE', 'TRADING']
    for section in required_sections:
        if section not in config:
            print(f"错误: 配置文件缺少 [{section}] 部分")
            sys.exit(1)
    
    # 验证API凭据
    if 'API_KEY' not in config['BINANCE'] or 'API_SECRET' not in config['BINANCE']:
        print("错误: 配置文件缺少API_KEY或API_SECRET")
        sys.exit(1)
        
    return config

def initialize_client(config):
    """初始化Binance客户端"""
    api_key = config['BINANCE']['API_KEY']
    api_secret = config['BINANCE']['API_SECRET']
    
    return BinanceClient(api_key=api_key, api_secret=api_secret, testnet=True)

def initialize_trade_log(log_path='trades.csv'):
    """初始化交易日志文件"""
    # 如果日志文件不存在，则创建并写入表头
    if not os.path.exists(log_path):
        with open(log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'action', 'symbol', 'price', 
                'quantity', 'stop_price', 'equity', 'atr'
            ])
    return log_path

def log_trade(log_path, action, symbol, price, quantity, stop_price=None, equity=None, atr=None):
    """记录交易到日志文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建日志条目
    log_entry = [
        timestamp,
        action,
        symbol,
        price,
        quantity,
        stop_price or '',
        equity or '',
        atr or ''
    ]
    
    # 写入CSV文件
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(log_entry)
    
    # 格式化控制台输出
    price_str = f"{price:.2f}" if price else "N/A"
    qty_str = f"{quantity:.3f}" if quantity else "N/A"
    stop_str = f"{stop_price:.2f}" if stop_price else "N/A"
    equity_str = f"{equity:.2f}" if equity else "N/A"
    
    # 打印到控制台
    print(f"[{timestamp}] {'='*50}")
    print(f"交易: {action} {symbol}")
    print(f"价格: {price_str} USDT")
    print(f"数量: {qty_str} {symbol.replace('USDT', '')}")
    if stop_price:
        print(f"止损: {stop_str} USDT")
    if equity:
        print(f"资金: {equity_str} USDT")
    if atr:
        print(f"ATR: {atr:.2f}")
    print(f"{'='*50}")

def get_trading_params(config):
    """从配置文件获取交易参数"""
    params = {
        'symbol': config['TRADING'].get('SYMBOL', 'BTCUSDT'),
        'risk_fraction': float(config['TRADING'].get('RISK_FRACTION', '0.02')),
        'fast_window': int(config['TRADING'].get('FAST_WINDOW', '7')),
        'slow_window': int(config['TRADING'].get('SLOW_WINDOW', '20')),
        'atr_window': int(config['TRADING'].get('ATR_WINDOW', '14'))
    }
    return params

def save_position_state(symbol, has_position, position_size=0, entry_price=0, stop_price=None):
    """保存持仓状态到文件"""
    state = {
        'symbol': symbol,
        'has_position': has_position,
        'position_size': position_size,
        'entry_price': entry_price,
        'stop_price': stop_price,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(POSITION_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)
    
    print(f"持仓状态已保存: {'有持仓' if has_position else '无持仓'}")

def load_position_state():
    """从文件加载持仓状态"""
    if not os.path.exists(POSITION_STATE_FILE):
        return None
        
    try:
        with open(POSITION_STATE_FILE, 'r') as f:
            state = json.load(f)
        print(f"已加载持仓状态: {'有持仓' if state.get('has_position') else '无持仓'}")
        return state
    except Exception as e:
        print(f"加载持仓状态失败: {e}")
        return None

def infer_position_state(client, symbol):
    """从账户信息推断持仓状态"""
    try:
        # 获取账户余额
        balances = client.get_balance()
        base_asset = symbol.replace('USDT', '')
        base_balance = balances.get(base_asset, 0.0)
        
        # 获取当前价格
        klines = client.get_klines(symbol, interval='1h', limit=1)
        current_price = klines['close'].iloc[0]
        
        # 获取历史交易记录
        trades = []
        if os.path.exists('trades.csv'):
            trades_df = pd.read_csv('trades.csv')
            if not trades_df.empty:
                trades = trades_df.to_dict('records')
        
        # 检查是否有持仓
        has_position = base_balance > 0.001  # 小于0.001视为无仓位
        
        if has_position:
            # 尝试从交易日志中获取最近的买入记录
            entry_price = None
            position_size = base_balance
            
            # 从交易日志中查找最近的买入记录
            buy_trades = [t for t in trades if t.get('action') == 'BUY' and t.get('symbol') == symbol]
            if buy_trades:
                # 按时间戳排序找到最近的买入
                latest_buy = sorted(buy_trades, key=lambda x: x.get('timestamp', ''), reverse=True)[0]
                entry_price = float(latest_buy.get('price', current_price))
                
                # 如果有止损价记录，也获取它
                stop_price = latest_buy.get('stop_price')
                if stop_price and stop_price != '':
                    stop_price = float(stop_price)
                else:
                    stop_price = None
            else:
                # 如果找不到买入记录，假设以当前价格的95%买入
                entry_price = current_price * 0.95
                stop_price = None
                
            # 获取当前止损单
            open_orders = client.get_open_orders(symbol)
            for order in open_orders:
                if order['type'] == 'STOP_LOSS' and order['side'] == 'SELL':
                    stop_price = float(order['stopPrice'])
                    break
                    
            return {
                'symbol': symbol,
                'has_position': True,
                'position_size': position_size,
                'entry_price': entry_price,
                'stop_price': stop_price,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'inferred': True
            }
        
        return {
            'symbol': symbol,
            'has_position': False,
            'position_size': 0,
            'entry_price': 0,
            'stop_price': None,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'inferred': True
        }
            
    except Exception as e:
        print(f"推断持仓状态失败: {e}")
        return None

def run_strategy(client, params, interval, log_path, test_mode=False, state=None):
    """
    运行交易策略
    
    参数:
        client: Binance客户端实例
        params: 交易参数字典
        interval: K线周期
        log_path: 交易日志路径
        test_mode: 是否为测试模式
        state: 持仓状态（如果有）
    """
    # 获取交易参数
    symbol = params['symbol']
    risk_fraction = params['risk_fraction']
    fast_window = params['fast_window']
    slow_window = params['slow_window']
    atr_window = params['atr_window']
    
    # 使用缓存的持仓状态，如果有的话
    entry_price_from_state = state.get('entry_price', 0) if state else 0
    
    # 获取账户余额和当前仓位
    try:
        # 获取USDT余额作为权益
        balances = client.get_balance()
        equity = balances.get('USDT', 0.0)
        btc_balance = balances.get('BTC', 0.0)
        
        print(f"当前账户余额: USDT={equity}, BTC={btc_balance}")
        
        # 检查是否有仓位
        position = btc_balance
        has_position = position > 0.001  # 小于0.001视为无仓位
        
        # 获取当前持仓订单
        open_orders = client.get_open_orders(symbol)
        stop_order = None
        for order in open_orders:
            if order['type'] == 'STOP_LOSS' and order['side'] == 'SELL':
                stop_order = order
                break
                
        # 获取K线数据
        klines = client.get_klines(symbol, interval=interval, limit=max(slow_window, atr_window) + 10)
        
        # 确保数据类型为float
        price_series = klines['close']
        high_series = klines['high']
        low_series = klines['low']
        
        current_price = price_series.iloc[-1]
        print(f"当前价格: {current_price}")
        
        # 计算指标
        fast_ma = signals.moving_average(price_series, fast_window)
        slow_ma = signals.moving_average(price_series, slow_window)
        
        # 计算ATR - 改用传统OHLC计算方法
        tr = pd.concat(
            {
                "hl": high_series - low_series,  # 当日最高价与最低价差
                "hc": (high_series - price_series.shift(1)).abs(),  # 当日最高价与前日收盘价差
                "lc": (low_series - price_series.shift(1)).abs(),  # 当日最低价与前日收盘价差
            }, axis=1
        ).max(axis=1)
        
        # 计算ATR
        atr = tr.rolling(atr_window).mean().iloc[-1]
        
        # 限制异常值
        if atr > current_price * 0.05:
            atr = current_price * 0.02
        
        # 生成信号
        buy_signal = fast_ma.iloc[-2] <= slow_ma.iloc[-2] and fast_ma.iloc[-1] > slow_ma.iloc[-1]
        sell_signal = fast_ma.iloc[-2] >= slow_ma.iloc[-2] and fast_ma.iloc[-1] < slow_ma.iloc[-1]
        
        print(f"技术指标: Fast MA={fast_ma.iloc[-1]:.2f}, Slow MA={slow_ma.iloc[-1]:.2f}, ATR={atr:.2f}")
        print(f"信号: Buy={buy_signal}, Sell={sell_signal}")
        
        # 执行策略
        if has_position:
            # 如果有仓位，检查卖出信号
            if sell_signal:
                print(f"卖出信号触发: 当前价格={current_price}, 持仓={position}")
                
                if not test_mode:
                    # 执行市价卖出
                    sell_order = client.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="MARKET",
                        quantity=position
                    )
                    
                    # 尝试取消现有止损单
                    if stop_order:
                        client.cancel_order(symbol=symbol, order_id=stop_order['orderId'])
                        
                    # 记录交易
                    log_trade(
                        log_path=log_path,
                        action="SELL",
                        symbol=symbol,
                        price=current_price,
                        quantity=position,
                        equity=equity
                    )
                    
                    # 更新持仓状态
                    save_position_state(symbol, False)
                else:
                    print("[测试模式] 模拟卖出操作")
                    
        else:
            # 如果没有仓位，检查买入信号
            if buy_signal:
                # 计算仓位大小
                size = broker.compute_position_size(equity, atr, risk_fraction)
                # 将仓位舍入到小数点后3位，与Binance最小交易单位对齐
                size = round(size, 3)
                max_size = equity / current_price * 0.95  # 最大可用95%的资金
                size = min(size, max_size)
                
                # 计算止损
                stop = broker.compute_stop_price(current_price, atr)
                
                print(f"买入信号触发: 价格={current_price}, 仓位大小={size}, 止损={stop}")
                
                if not test_mode:
                    # 执行市价买入
                    buy_order = client.place_order(
                        symbol=symbol,
                        side="BUY",
                        order_type="MARKET",
                        quantity=size
                    )
                    
                    # 设置止损单
                    stop_order = client.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="STOP_LOSS",
                        quantity=size,
                        stop_price=stop
                    )
                    
                    # 记录交易
                    log_trade(
                        log_path=log_path,
                        action="BUY",
                        symbol=symbol,
                        price=current_price,
                        quantity=size,
                        stop_price=stop,
                        equity=equity,
                        atr=atr
                    )
                    
                    # 更新持仓状态
                    save_position_state(symbol, True, size, current_price, stop)
                else:
                    print("[测试模式] 模拟买入操作")
        
        # 在每次策略执行完成后，不论是否有信号触发，都更新状态
        if has_position and not test_mode:
            # 如果之前没有保存开仓价但现在有持仓，推断开仓价
            saved_state = load_position_state()
            if not saved_state or not saved_state.get('has_position'):
                # 使用状态中的持仓价或从当前价推断
                entry = entry_price_from_state if entry_price_from_state > 0 else current_price * 0.95
                stop_price = stop_order['stopPrice'] if stop_order else None
                save_position_state(symbol, True, position, entry, stop_price)
            
            # 检查是否需要更新止损
            elif stop_order and saved_state.get('stop_price') != float(stop_order['stopPrice']):
                old_stop = saved_state.get('stop_price')
                new_stop = float(stop_order['stopPrice'])
                
                # 记录止损更新
                log_trade(
                    log_path=log_path,
                    action="更新止损",
                    symbol=symbol,
                    price=current_price,
                    quantity=position,
                    stop_price=new_stop,
                    equity=equity
                )
                
                # 更新状态文件中的止损价格
                save_position_state(
                    symbol, 
                    True, 
                    position, 
                    saved_state.get('entry_price'), 
                    new_stop
                )
        
        return True
        
    except Exception as e:
        print(f"策略执行错误: {e}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = setup_parser()
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 初始化客户端
    client = initialize_client(config)
    
    # 初始化交易日志
    log_path = initialize_trade_log()
    
    # 获取交易参数
    params = get_trading_params(config)
    
    # 尝试加载持仓状态
    state = load_position_state()
    
    # 如果状态文件不存在但账户中有BTC，尝试推断状态
    if not state:
        state = infer_position_state(client, params['symbol'])
        if state and state.get('has_position'):
            # 保存推断的状态
            save_position_state(
                state['symbol'], 
                state['has_position'], 
                state['position_size'], 
                state['entry_price'], 
                state['stop_price']
            )
    
    # 执行模式提示
    mode = "测试模式" if args.test else "实盘模式"
    print(f"启动{mode}...")
    print(f"交易对: {params['symbol']}")
    print(f"K线周期: {args.interval}")
    print(f"风险系数: {params['risk_fraction']}")
    print(f"均线参数: 快线={params['fast_window']}, 慢线={params['slow_window']}")
    print(f"ATR窗口: {params['atr_window']}")
    
    if state:
        status = "有持仓" if state.get('has_position') else "无持仓"
        source = "推断" if state.get('inferred') else "缓存"
        print(f"持仓状态({source}): {status}")
        if state.get('has_position'):
            print(f"持仓量: {state.get('position_size')}")
            print(f"入场价: {state.get('entry_price')}")
            if state.get('stop_price'):
                print(f"止损价: {state.get('stop_price')}")
    
    try:
        # 测试连接
        server_time = client.get_server_time()
        print(f"服务器时间: {datetime.fromtimestamp(server_time['serverTime']/1000)}")
        
        # 检查账户状态
        account = client.get_account_info()
        print(f"账户状态: {'正常' if account.get('canTrade', False) else '异常'}")
        
        # 单次执行或定时执行
        if len(sys.argv) > 1 and sys.argv[1] == 'run_once':
            # 单次执行
            run_strategy(client, params, args.interval, log_path, args.test, state)
        else:
            # 定时执行
            while True:
                print(f"\n[{datetime.now()}] 执行策略检查")
                success = run_strategy(client, params, args.interval, log_path, args.test, state)
                
                # 确定下次执行时间
                if args.interval == '1d':
                    # 日线策略，每天执行一次
                    sleep_time = 86400  # 24小时
                elif args.interval == '1h':
                    # 小时线策略，每小时执行一次
                    sleep_time = 3600  # 1小时
                elif args.interval == '15m':
                    # 15分钟线策略
                    sleep_time = 900  # 15分钟
                else:
                    # 默认10分钟检查一次
                    sleep_time = 600
                
                print(f"等待{sleep_time}秒后再次执行...")
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("用户中断，程序退出")
    except Exception as e:
        print(f"程序错误: {e}")

if __name__ == "__main__":
    main() 