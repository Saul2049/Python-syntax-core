#!/usr/bin/env python
"""
网络重试和状态恢复示例
Network retry and state recovery example

演示如何使用网络重试装饰器和状态恢复功能来处理网络中断和应用重启
Demonstrates how to use network retry decorator and state recovery to handle
network interruptions and application restarts
"""

import os
import sys
import time
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径 (Add project root to path)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.exchange_client import ExchangeClient
from src.utils import get_trades_dir

# 配置日志 (Configure logging)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def simulate_network_failure():
    """模拟网络故障 (Simulate network failure)"""
    if random.random() < 0.3:  # 30% 概率出错 (30% chance of failure)
        logger.warning("模拟网络故障... (Simulating network failure...)")
        raise ConnectionError("Simulated network error")
    return True


def run_balance_check(client):
    """运行余额检查示例 (Run balance check example)"""
    logger.info("==== 运行余额检查 (Running balance check) ====")
    try:
        # 获取余额会自动重试，状态保存在指定的状态文件中
        # Get balance with automatic retries, state saved in specified state file
        balance = client.get_account_balance()
        logger.info(f"余额 (Balance): {balance}")
        return balance
    except Exception as e:
        logger.error(f"余额检查失败 (Balance check failed): {e}")
        return None


def run_order_example(client):
    """运行订单示例 (Run order example)"""
    logger.info("==== 运行订单示例 (Running order example) ====")
    try:
        # 下单接口会自动重试，状态保存在指定的状态文件中
        # Place order with automatic retries, state saved in specified state file
        order = client.place_order(
            symbol="BTCUSDT", side="BUY", quantity=0.001, price=50000.0
        )
        logger.info(f"订单已提交 (Order submitted): {order}")
        return order
    except Exception as e:
        logger.error(f"下单失败 (Order failed): {e}")
        return None


def run_sync_example(client):
    """运行数据同步示例 (Run data sync example)"""
    logger.info("==== 运行数据同步示例 (Running data sync example) ====")
    try:
        # 同步市场数据，会自动恢复已完成的部分
        # Sync market data with automatic resumption of completed parts
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        result = client.sync_market_data(symbols, days=2)
        logger.info(f"同步结果 (Sync result): {result}")
        return result
    except Exception as e:
        logger.error(f"同步失败 (Sync failed): {e}")
        return None


def run_historical_trades_example(client):
    """运行历史交易查询示例 (Run historical trades example)"""
    logger.info("==== 运行历史交易查询示例 (Running historical trades example) ====")
    try:
        # 查询历史交易，会自动恢复已获取的数据
        # Query historical trades with automatic resumption of fetched data
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        trades = client.get_historical_trades(
            symbol="BTCUSDT", start_time=start_time, end_time=end_time
        )
        logger.info(
            f"获取到 {len(trades)} 条交易记录 (Got {len(trades)} trade records)"
        )
        return trades
    except Exception as e:
        logger.error(f"查询历史交易失败 (Historical trades query failed): {e}")
        return None


def main():
    """主函数 (Main function)"""
    logger.info(
        "====== 开始网络重试和状态恢复演示 (Starting network retry and state recovery demo) ======"
    )

    # 创建交易所客户端 (Create exchange client)
    client = ExchangeClient(
        api_key="demo_key",  # 示例密钥 (Example key)
        api_secret="demo_secret",  # 示例密钥 (Example secret)
        state_dir=str(
            get_trades_dir() / "states"
        ),  # 状态文件目录 (State file directory)
    )

    # 运行余额检查 (Run balance check)
    balance = run_balance_check(client)

    # 运行订单示例 (Run order example)
    order = run_order_example(client)

    # 运行历史交易查询示例 (Run historical trades example)
    trades = run_historical_trades_example(client)

    # 运行数据同步示例 (Run data sync example)
    sync_result = run_sync_example(client)

    logger.info("====== 演示完成 (Demo completed) ======")

    # 打印结果摘要 (Print result summary)
    logger.info("\n\n====== 结果摘要 (Result summary) ======")
    logger.info(
        f"余额检查 (Balance check): {'成功 (Success)' if balance else '失败 (Failed)'}"
    )
    logger.info(
        f"订单示例 (Order example): {'成功 (Success)' if order else '失败 (Failed)'}"
    )
    logger.info(
        f"历史交易查询 (Historical trades): {'成功 (Success) - ' + str(len(trades)) + ' 条记录 (records)' if trades else '失败 (Failed)'}"
    )
    logger.info(
        f"数据同步 (Data sync): {'成功 (Success)' if sync_result else '失败 (Failed)'}"
    )


if __name__ == "__main__":
    main()
