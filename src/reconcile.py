import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import argparse

from src.broker import Broker
from src import utils


def get_exchange_trades(
    symbol: str, start_date: str, end_date: str, api_key: str, api_secret: str
) -> pd.DataFrame:
    """
    从交易所获取交易历史。
    Get trade history from exchange.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        start_date: 开始日期 (Start date) 'YYYY-MM-DD'
        end_date: 结束日期 (End date) 'YYYY-MM-DD'
        api_key: API密钥 (API key)
        api_secret: API密钥 (API secret)

    返回 (Returns):
        pd.DataFrame: 交易所交易记录 (Exchange trade records)
    """
    # 这里应实际调用交易所API获取交易历史
    # This should call exchange API to get trade history
    # 示例返回空数据帧，实际使用时应连接API获取数据
    print(f"从交易所获取{symbol}交易历史 ({start_date} 至 {end_date})")
    return pd.DataFrame(
        columns=[
            "timestamp",
            "symbol",
            "side",
            "price",
            "quantity",
            "amount",
            "fee",
            "order_id",
        ]
    )


def get_local_trades(
    symbol: str, start_date: str, end_date: str, trades_dir: Optional[str] = None
) -> pd.DataFrame:
    """
    从本地CSV获取交易历史。
    Get trade history from local CSV.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        start_date: 开始日期 (Start date) 'YYYY-MM-DD'
        end_date: 结束日期 (End date) 'YYYY-MM-DD'
        trades_dir: 交易数据目录 (Trades data directory)

    返回 (Returns):
        pd.DataFrame: 本地交易记录 (Local trade records)
    """
    print(f"从本地CSV获取{symbol}交易历史 ({start_date} 至 {end_date})")
    broker = Broker("", "", trades_dir=trades_dir)
    return broker.get_all_trades(symbol, start_date, end_date)


def compare_trades(
    exchange_trades: pd.DataFrame, local_trades: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    比较交易所交易与本地交易记录。
    Compare exchange trades with local trade records.

    参数 (Parameters):
        exchange_trades: 交易所交易记录 (Exchange trade records)
        local_trades: 本地交易记录 (Local trade records)

    返回 (Returns):
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            匹配的交易 (Matched trades),
            仅交易所有的交易 (Exchange-only trades),
            仅本地有的交易 (Local-only trades)
    """
    if exchange_trades.empty and local_trades.empty:
        print("没有交易数据可比较 (No trade data to compare)")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if exchange_trades.empty:
        print("警告: 无交易所交易数据 (Warning: No exchange trade data)")
        return pd.DataFrame(), pd.DataFrame(), local_trades

    if local_trades.empty:
        print("警告: 无本地交易数据 (Warning: No local trade data)")
        return pd.DataFrame(), exchange_trades, pd.DataFrame()

    # 确保两个DataFrame有相同的列 (Ensure both DataFrames have same columns)
    exchange_df = exchange_trades.copy()
    local_df = local_trades.copy()

    # 使用order_id作为主键进行匹配 (Use order_id as primary key for matching)
    if "order_id" in exchange_df and "order_id" in local_df:
        # 匹配交易 (Match trades)
        matched = pd.merge(
            exchange_df, local_df, on="order_id", suffixes=("_exchange", "_local")
        )

        # 仅交易所有的交易 (Exchange-only trades)
        exchange_only = exchange_df[~exchange_df["order_id"].isin(matched["order_id"])]

        # 仅本地有的交易 (Local-only trades)
        local_only = local_df[~local_df["order_id"].isin(matched["order_id"])]

    else:
        # 如果没有order_id，尝试使用其他字段匹配 (If no order_id, try matching with other fields)
        print(
            "警告: 未找到order_id列，使用timestamp、symbol、side、price和quantity匹配"
        )
        match_cols = ["timestamp", "symbol", "side", "price", "quantity"]

        # 确保所有匹配列都存在 (Ensure all matching columns exist)
        for col in match_cols:
            if col not in exchange_df or col not in local_df:
                print(f"错误: 缺少匹配列 {col}")
                return pd.DataFrame(), exchange_df, local_df

        # 匹配交易 (Match trades)
        matched = pd.merge(
            exchange_df, local_df, on=match_cols, suffixes=("_exchange", "_local")
        )

        # 创建用于比较的组合键 (Create composite key for comparison)
        def create_key(df, cols):
            return df.apply(lambda row: "_".join([str(row[c]) for c in cols]), axis=1)

        exchange_keys = create_key(exchange_df, match_cols)
        local_keys = create_key(local_df, match_cols)
        matched_keys = create_key(matched, match_cols)

        # 仅交易所有的交易 (Exchange-only trades)
        exchange_only = exchange_df[~exchange_keys.isin(matched_keys)]

        # 仅本地有的交易 (Local-only trades)
        local_only = local_df[~local_keys.isin(matched_keys)]

    print(f"匹配的交易: {len(matched)}条")
    print(f"仅交易所有的交易: {len(exchange_only)}条")
    print(f"仅本地有的交易: {len(local_only)}条")

    return matched, exchange_only, local_only


def verify_balances(symbol: str, api_key: str, api_secret: str) -> Dict[str, Any]:
    """
    验证账户余额。
    Verify account balances.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        api_key: API密钥 (API key)
        api_secret: API密钥 (API secret)

    返回 (Returns):
        Dict[str, Any]: 余额信息 (Balance information)
    """
    # 这里应实际调用交易所API获取余额
    # This should call exchange API to get balances
    # 示例返回模拟数据，实际使用时应连接API获取数据
    print(f"验证{symbol}账户余额")

    # 解析交易对获取币种 (Parse trading pair to get currency)
    base_currency = symbol.split("USDT")[0] if "USDT" in symbol else symbol

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "base_currency": base_currency,
        "quote_currency": "USDT",
        "base_balance": 1.0,  # 示例值 (Example value)
        "quote_balance": 10000.0,  # 示例值 (Example value)
        "total_value_usdt": 50000.0,  # 示例值 (Example value)
    }


def log_reconciliation_results(
    symbol: str,
    date: str,
    matched: pd.DataFrame,
    exchange_only: pd.DataFrame,
    local_only: pd.DataFrame,
    balances: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> None:
    """
    记录对账结果。
    Log reconciliation results.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        date: 日期 (Date) 'YYYY-MM-DD'
        matched: 匹配的交易 (Matched trades)
        exchange_only: 仅交易所有的交易 (Exchange-only trades)
        local_only: 仅本地有的交易 (Local-only trades)
        balances: 余额信息 (Balance information)
        output_dir: 输出目录 (Output directory)
    """
    # 确定输出目录 (Determine output directory)
    if output_dir is None:
        output_dir = utils.get_trades_dir() / "reconciliation"
    else:
        output_dir = Path(output_dir) / "reconciliation"

    # 确保目录存在 (Ensure directory exists)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成文件名 (Generate filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"reconciliation_{symbol}_{date}_{timestamp}"

    # 保存匹配的交易 (Save matched trades)
    if not matched.empty:
        matched_file = output_dir / f"{base_filename}_matched.csv"
        matched.to_csv(matched_file, index=False)
        print(f"匹配的交易已保存至 {matched_file}")

    # 保存仅交易所有的交易 (Save exchange-only trades)
    if not exchange_only.empty:
        exchange_file = output_dir / f"{base_filename}_exchange_only.csv"
        exchange_only.to_csv(exchange_file, index=False)
        print(f"仅交易所有的交易已保存至 {exchange_file}")

    # 保存仅本地有的交易 (Save local-only trades)
    if not local_only.empty:
        local_file = output_dir / f"{base_filename}_local_only.csv"
        local_only.to_csv(local_file, index=False)
        print(f"仅本地有的交易已保存至 {local_file}")

    # 保存余额信息 (Save balance information)
    balance_file = output_dir / f"{base_filename}_balance.json"
    pd.Series(balances).to_json(balance_file)
    print(f"余额信息已保存至 {balance_file}")

    # 生成摘要报告 (Generate summary report)
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": date,
        "symbol": symbol,
        "matched_count": len(matched),
        "exchange_only_count": len(exchange_only),
        "local_only_count": len(local_only),
        "base_balance": balances.get("base_balance", 0),
        "quote_balance": balances.get("quote_balance", 0),
        "total_value_usdt": balances.get("total_value_usdt", 0),
    }

    summary_file = output_dir / f"{base_filename}_summary.json"
    pd.Series(summary).to_json(summary_file)
    print(f"摘要报告已保存至 {summary_file}")


def daily_reconciliation(
    symbol: str,
    api_key: str,
    api_secret: str,
    date: Optional[str] = None,
    trades_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
    notify: bool = True,
) -> None:
    """
    执行日终对账。
    Perform daily reconciliation.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        api_key: API密钥 (API key)
        api_secret: API密钥 (API secret)
        date: 日期 (Date) 'YYYY-MM-DD'，默认为昨天
        trades_dir: 交易数据目录 (Trades data directory)
        output_dir: 输出目录 (Output directory)
        notify: 是否发送通知 (Whether to send notification)
    """
    # 默认使用昨天的日期 (Default to yesterday's date)
    if date is None:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")

    print(f"开始对账: {symbol} ({date})")

    # 获取交易所交易 (Get exchange trades)
    exchange_trades = get_exchange_trades(symbol, date, date, api_key, api_secret)

    # 获取本地交易 (Get local trades)
    local_trades = get_local_trades(symbol, date, date, trades_dir)

    # 比较交易 (Compare trades)
    matched, exchange_only, local_only = compare_trades(exchange_trades, local_trades)

    # 验证余额 (Verify balances)
    balances = verify_balances(symbol, api_key, api_secret)

    # 记录结果 (Log results)
    log_reconciliation_results(
        symbol, date, matched, exchange_only, local_only, balances, output_dir
    )

    # 发送通知 (Send notification)
    if notify and (len(exchange_only) > 0 or len(local_only) > 0):
        # 初始化通知器 (Initialize notifier)
        broker = Broker(api_key, api_secret)

        # 构建通知消息 (Build notification message)
        message = (
            f"⚠️ 对账异常 (Reconciliation Issue)\n"
            f"日期 (Date): {date}\n"
            f"品种 (Symbol): {symbol}\n"
            f"匹配交易 (Matched): {len(matched)}条\n"
            f"仅交易所 (Exchange only): {len(exchange_only)}条\n"
            f"仅本地 (Local only): {len(local_only)}条\n"
            f"请检查对账报告 (Please check reconciliation report)"
        )

        broker.notifier.notify(message, "WARN")

    print(f"对账完成: {symbol} ({date})")


if __name__ == "__main__":
    # 解析命令行参数 (Parse command-line arguments)
    parser = argparse.ArgumentParser(
        description="交易对账工具 (Trade reconciliation tool)"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="交易对 (Trading pair)"
    )
    parser.add_argument("--date", type=str, help="日期 (Date) 'YYYY-MM-DD'，默认为昨天")
    parser.add_argument(
        "--trades-dir", type=str, help="交易数据目录 (Trades data directory)"
    )
    parser.add_argument("--output-dir", type=str, help="输出目录 (Output directory)")
    parser.add_argument(
        "--no-notify", action="store_true", help="不发送通知 (Don't send notification)"
    )
    args = parser.parse_args()

    # 获取API密钥和密钥 (Get API keys)
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")

    if not api_key or not api_secret:
        print("错误: 环境变量API_KEY和API_SECRET未设置")
        sys.exit(1)

    # 执行对账 (Perform reconciliation)
    daily_reconciliation(
        symbol=args.symbol,
        api_key=api_key,
        api_secret=api_secret,
        date=args.date,
        trades_dir=args.trades_dir,
        output_dir=args.output_dir,
        notify=not args.no_notify,
    )
