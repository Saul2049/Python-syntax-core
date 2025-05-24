"""
经纪商接口模块 (Broker Interface Module)

提供简化的经纪商功能，包括：
- 订单执行
- 交易记录
- 基本的仓位管理接口
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src import utils
from src.core.position_management import PositionManager
from src.notify import Notifier


class Broker:
    """简化的经纪商类，专注于核心交易功能"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        telegram_token: Optional[str] = None,
        trades_dir: Optional[str] = None,
    ):
        """
        初始化经纪商。

        参数:
            api_key: API密钥 (API key)
            api_secret: API密钥 (API secret)
            telegram_token: Telegram机器人令牌 (Telegram bot token)
            trades_dir: 交易记录目录 (Trades directory)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.notifier = Notifier(telegram_token)
        self.trades_dir = trades_dir or utils.get_trades_dir()

        # 使用仓位管理器
        self.position_manager = PositionManager()
        self.position_manager.load_from_file()

        # 向后兼容的属性
        self.positions = self.position_manager.positions

    def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行交易订单。

        参数:
            symbol: 交易对符号 (Symbol)
            side: 交易方向 BUY/SELL (Side)
            quantity: 数量 (Quantity)
            price: 价格，None表示市价单 (Price, None for market order)
            reason: 交易原因 (Reason)

        返回:
            Dict[str, Any]: 交易结果 (Trade result)
        """
        try:
            # 执行内部订单逻辑
            result = self._execute_order_internal(symbol, side, quantity, price)

            # 更新仓位
            self._update_positions_after_trade(symbol, side, quantity, result.get("price", price))

            # 记录交易
            trade_data = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": result.get("price", price or 0),
                "reason": reason or "",
                "order_id": result.get("order_id", ""),
                "status": result.get("status", "FILLED"),
            }

            self._log_trade_to_csv(trade_data)

            # 发送通知
            self._send_trade_notification(trade_data)

            return result

        except Exception as e:
            self.notifier.notify_error(e, f"执行订单失败: {symbol} {side} {quantity}")
            raise

    def _execute_order_internal(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        内部订单执行逻辑（可被子类重写）。

        参数:
            symbol: 交易对符号
            side: 交易方向
            quantity: 数量
            price: 价格

        返回:
            Dict[str, Any]: 执行结果
        """
        # 模拟订单执行
        execution_price = price or self._get_mock_price(symbol)

        return {
            "order_id": f"mock_{int(time.time()*1000)}",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": execution_price,
            "status": "FILLED",
            "timestamp": datetime.now().isoformat(),
        }

    def _update_positions_after_trade(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> None:
        """交易后更新仓位"""
        if side.upper() == "BUY":
            if not self.position_manager.has_position(symbol):
                # 新开仓位，计算止损价格
                # 这里简化处理，实际应该传入ATR
                stop_price = price * 0.98  # 简单的2%止损
                self.position_manager.add_position(symbol, quantity, price, stop_price)
        elif side.upper() == "SELL":
            # 平仓
            self.position_manager.remove_position(symbol)

    def _log_trade_to_csv(self, trade_data: Dict[str, Any]) -> None:
        """记录交易到CSV文件"""
        try:
            trades_file = Path(self.trades_dir) / "trades.csv"
            trades_file.parent.mkdir(parents=True, exist_ok=True)

            # 创建DataFrame
            df = pd.DataFrame([trade_data])

            # 追加到文件
            if trades_file.exists():
                df.to_csv(trades_file, mode="a", header=False, index=False)
            else:
                df.to_csv(trades_file, mode="w", header=True, index=False)

        except Exception as e:
            print(f"记录交易失败: {e}")

    def _send_trade_notification(self, trade_data: Dict[str, Any]) -> None:
        """发送交易通知"""
        try:
            side_emoji = "🟢" if trade_data["side"] == "BUY" else "🔴"
            message = (
                f"{side_emoji} 交易执行 (Trade Executed)\n"
                f"符号 (Symbol): {trade_data['symbol']}\n"
                f"方向 (Side): {trade_data['side']}\n"
                f"数量 (Quantity): {trade_data['quantity']}\n"
                f"价格 (Price): {trade_data['price']:.8f}\n"
                f"原因 (Reason): {trade_data['reason']}"
            )
            self.notifier.notify_trade(trade_data, message)
        except Exception as e:
            print(f"发送通知失败: {e}")

    def get_all_trades(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取交易记录。

        参数:
            symbol: 交易对符号
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        返回:
            pd.DataFrame: 交易记录
        """
        try:
            trades_file = Path(self.trades_dir) / "trades.csv"
            if not trades_file.exists():
                return pd.DataFrame()

            df = pd.read_csv(trades_file)

            # 过滤符号
            if symbol:
                df = df[df["symbol"] == symbol]

            # 过滤日期
            if start_date or end_date:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                if start_date:
                    df = df[df["timestamp"] >= start_date]
                if end_date:
                    df = df[df["timestamp"] <= end_date]

            return df

        except Exception as e:
            print(f"读取交易记录失败: {e}")
            return pd.DataFrame()

    def update_position_stops(self, symbol: str, current_price: float, atr: float) -> None:
        """
        更新仓位止损价格。

        参数:
            symbol: 交易对符号
            current_price: 当前价格
            atr: ATR值
        """
        self.position_manager.update_trailing_stops(symbol, current_price, atr, self.notifier)

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        检查止损。

        参数:
            symbol: 交易对符号
            current_price: 当前价格

        返回:
            bool: 是否触发止损
        """
        if self.position_manager.check_stop_loss(symbol, current_price):
            # 执行止损订单
            position = self.position_manager.get_position(symbol)
            if position:
                self.execute_order(
                    symbol=symbol,
                    side="SELL",
                    quantity=position["quantity"],
                    reason=f"止损触发 @ {current_price:.6f}",
                )
                return True
        return False

    def _get_mock_price(self, symbol: str) -> float:
        """获取模拟价格（用于测试）"""
        # 简单的模拟价格逻辑
        import random

        base_prices = {
            "BTCUSDT": 50000,
            "ETHUSDT": 3000,
            "BNBUSDT": 400,
        }
        base_price = base_prices.get(symbol, 100)
        return base_price * (1 + random.uniform(-0.02, 0.02))

    @property
    def positions(self) -> Dict[str, Dict[str, Any]]:
        """向后兼容的仓位属性"""
        return self.position_manager.get_all_positions()

    @positions.setter
    def positions(self, value: Dict[str, Dict[str, Any]]) -> None:
        """向后兼容的仓位设置"""
        self.position_manager.positions = value
