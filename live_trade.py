#!/usr/bin/env python3
"""
使用Binance Testnet执行实时交易
"""
import argparse
import configparser
import csv
import json
import os
import sys
import time
from datetime import datetime
from math import isfinite

import numpy as np
import pandas as pd
import requests

from src import broker, signals
from src.binance_client import BinanceClient

# 持仓状态文件路径
POSITION_STATE_FILE = "position_state.json"


def setup_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="Binance Testnet实时交易")

    parser.add_argument(
        "--config",
        type=str,
        default="config.ini",
        help="配置文件路径 (默认: config.ini)",
    )

    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="K线周期，如1m, 5m, 15m, 1h, 4h, 1d (默认: 1d)",
    )

    parser.add_argument(
        "--test", action="store_true", help="仅运行测试模式，不执行实际交易"
    )

    return parser


def load_config(config_file):
    """加载配置文件"""
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)

    # 验证必要的配置项
    required_sections = ["BINANCE", "TRADING"]
    for section in required_sections:
        if section not in config:
            print(f"错误: 配置文件缺少 [{section}] 部分")
            sys.exit(1)

    # 验证API凭据
    if (
        "API_KEY" not in config["BINANCE"]
        or "API_SECRET" not in config["BINANCE"]
    ):
        print("错误: 配置文件缺少API_KEY或API_SECRET")
        sys.exit(1)

    return config


def initialize_client(config):
    """初始化Binance客户端"""
    api_key = config["BINANCE"]["API_KEY"]
    api_secret = config["BINANCE"]["API_SECRET"]

    return BinanceClient(api_key=api_key, api_secret=api_secret, testnet=True)


def initialize_trade_log(log_path="trades.csv"):
    """初始化交易日志文件"""
    # 如果日志文件不存在，则创建并写入表头
    if not os.path.exists(log_path):
        with open(log_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "timestamp",
                    "action",
                    "symbol",
                    "price",
                    "quantity",
                    "stop_price",
                    "equity",
                    "atr",
                    "commission",
                ]
            )
    return log_path


def tg_notify(text: str):
    """发送Telegram通知"""
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT")

    if not token or not chat_id:
        print("警告: 未配置Telegram通知 (TG_TOKEN, TG_CHAT)")
        return

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(
            url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"Telegram通知发送失败: {e}")


def calculate_commission(quantity, price, is_testnet=True):
    """
    计算交易手续费

    参数:
        quantity: 交易数量
        price: 交易价格
        is_testnet: 是否为测试网

    返回:
        float: 手续费金额
    """
    if is_testnet:
        return 0.0  # 测试网不收取手续费
    return quantity * price * 0.001  # 主网手续费率0.1%


def log_trade(
    log_path,
    action,
    symbol,
    price,
    quantity,
    stop_price=None,
    equity=None,
    atr=None,
    commission=0.0,
):
    """
    记录交易日志

    参数:
        log_path: 日志文件路径
        action: 交易动作 (BUY/SELL)
        symbol: 交易对
        price: 交易价格
        quantity: 交易数量
        stop_price: 止损价
        equity: 账户权益
        atr: ATR值
        commission: 手续费
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                timestamp,
                action,
                symbol,
                price,
                quantity,
                stop_price,
                equity,
                atr,
                commission,
            ]
        )


def save_position_state(
    symbol, has_position, position_size=0, entry_price=0, stop_price=None
):
    """
    保存持仓状态到文件

    参数:
        symbol: 交易对
        has_position: 是否有持仓
        position_size: 持仓数量
        entry_price: 入场价格
        stop_price: 止损价格
    """
    state = {
        "symbol": symbol,
        "has_position": has_position,
        "position_size": position_size,
        "entry_price": entry_price,
        "stop_price": stop_price,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        with open(POSITION_STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"保存持仓状态失败: {e}")


def load_position_state():
    """
    从文件加载持仓状态

    返回:
        dict: 持仓状态，如果文件不存在或加载失败则返回None
    """
    if not os.path.exists(POSITION_STATE_FILE):
        return None

    try:
        with open(POSITION_STATE_FILE, "r") as f:
            state = json.load(f)

        # 验证状态数据的完整性
        required_fields = [
            "symbol",
            "has_position",
            "position_size",
            "entry_price",
        ]
        if not all(field in state for field in required_fields):
            print("警告: 持仓状态文件数据不完整")
            return None

        return state
    except Exception as e:
        print(f"加载持仓状态失败: {e}")
        return None


def run_strategy(
    client, params, interval, log_path, test_mode=False, state=None
):
    """
    运行交易策略

    参数:
        client: Binance客户端实例
        params: 交易参数
        interval: K线周期
        log_path: 日志文件路径
        test_mode: 是否为测试模式
        state: 初始持仓状态
    """
    symbol = params["symbol"]
    position = state["position_size"] if state else 0
    entry_price = state["entry_price"] if state else 0
    stop_price = state["stop_price"] if state else None

    while True:
        try:
            # 获取K线数据
            klines = client.get_klines(symbol, interval, limit=100)

            # 计算技术指标
            signals_df = signals.calculate_signals(klines)
            latest_signal = signals_df.iloc[-1]

            # 获取当前价格
            current_price = float(latest_signal["close"])

            # 计算账户权益
            balance = client.get_balance("USDT")
            equity = balance + (position * current_price)

            # 计算手续费
            commission = calculate_commission(
                position, current_price, client.testnet
            )
            equity -= commission

            # 生成交易信号
            if position == 0 and latest_signal["buy_signal"]:
                # 计算交易数量
                quantity = float(params["position_size"])

                if not test_mode:
                    # 执行买入
                    order = client.place_order(
                        symbol=symbol,
                        side="BUY",
                        order_type="MARKET",
                        quantity=quantity,
                    )

                    # 更新持仓状态
                    position = float(order["executedQty"])
                    entry_price = float(order["fills"][0]["price"])
                    stop_price = entry_price * (1 - float(params["stop_loss"]))

                    # 保存状态
                    save_position_state(
                        symbol, True, position, entry_price, stop_price
                    )

                    # 发送通知
                    tg_notify(
                        f"🟢 买入 {symbol}\n"
                        f"价格: {entry_price}\n"
                        f"数量: {position}\n"
                        f"止损: {stop_price}"
                    )

                # 记录交易
                log_trade(
                    log_path,
                    "BUY",
                    symbol,
                    entry_price,
                    position,
                    stop_price,
                    equity,
                    latest_signal["atr"],
                    commission,
                )

            elif position > 0 and (
                latest_signal["sell_signal"] or current_price <= stop_price
            ):
                if not test_mode:
                    # 执行卖出
                    order = client.place_order(
                        symbol=symbol,
                        side="SELL",
                        order_type="MARKET",
                        quantity=position,
                    )

                    # 更新持仓状态
                    position = 0
                    entry_price = 0
                    stop_price = None

                    # 保存状态
                    save_position_state(symbol, False)

                    # 发送通知
                    tg_notify(
                        f"🔴 卖出 {symbol}\n"
                        f"价格: {current_price}\n"
                        f"数量: {position}\n"
                        f"盈亏: {(current_price - entry_price) * position}"
                    )

                # 记录交易
                log_trade(
                    log_path,
                    "SELL",
                    symbol,
                    current_price,
                    position,
                    stop_price,
                    equity,
                    latest_signal["atr"],
                    commission,
                )

            # 等待下一个周期
            time.sleep(60)  # 每分钟检查一次

        except Exception as e:
            print(f"策略执行错误: {e}")
            time.sleep(60)  # 发生错误时等待一分钟后重试


def main():
    """主函数"""
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

    # 加载持仓状态
    state = load_position_state()

    # 运行策略
    run_strategy(client, params, args.interval, log_path, args.test, state)


if __name__ == "__main__":
    main()
