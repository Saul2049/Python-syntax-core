"""
仓位管理模块 (Position Management Module)

提供交易仓位管理功能，包括：
- 仓位状态跟踪
- 止损价格更新
- 仓位风险监控
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.core.risk_management import update_trailing_stop_atr
from src.notify import Notifier


class PositionManager:
    """仓位管理器"""

    def __init__(self, positions_file: Optional[str] = None):
        """
        初始化仓位管理器

        参数:
            positions_file: 仓位状态文件路径
        """
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.positions_file = positions_file or "position_state.json"

    def add_position(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        stop_price: float,
        side: str = "LONG",
    ) -> None:
        """
        添加新仓位

        参数:
            symbol: 交易对符号
            quantity: 数量
            entry_price: 入场价格
            stop_price: 止损价格
            side: 方向 (LONG/SHORT)
        """
        self.positions[symbol] = {
            "quantity": quantity,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "side": side,
            "entry_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
        }
        self._save_positions()

    def remove_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        移除仓位

        参数:
            symbol: 交易对符号

        返回:
            Dict: 被移除的仓位信息，如果不存在则返回None
        """
        position = self.positions.pop(symbol, None)
        if position:
            self._save_positions()
        return position

    def update_stop_price(self, symbol: str, new_stop_price: float) -> bool:
        """
        更新止损价格

        参数:
            symbol: 交易对符号
            new_stop_price: 新的止损价格

        返回:
            bool: 是否成功更新
        """
        if symbol in self.positions:
            self.positions[symbol]["stop_price"] = new_stop_price
            self.positions[symbol]["last_update"] = datetime.now().isoformat()
            self._save_positions()
            return True
        return False

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取仓位信息

        参数:
            symbol: 交易对符号

        返回:
            Dict: 仓位信息，如果不存在则返回None
        """
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """
        检查是否有仓位

        参数:
            symbol: 交易对符号

        返回:
            bool: 是否有仓位
        """
        return symbol in self.positions

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有仓位

        返回:
            Dict: 所有仓位信息
        """
        return self.positions.copy()

    def update_trailing_stops(
        self, symbol: str, current_price: float, atr: float, notifier: Optional[Notifier] = None
    ) -> bool:
        """
        更新跟踪止损

        参数:
            symbol: 交易对符号
            current_price: 当前价格
            atr: ATR值
            notifier: 通知器

        返回:
            bool: 是否更新了止损
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]
        new_stop, updated = update_trailing_stop_atr(
            position, current_price, atr, notifier=notifier
        )

        if updated:
            self.update_stop_price(symbol, new_stop)
            return True

        return False

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发止损

        参数:
            symbol: 交易对符号
            current_price: 当前价格

        返回:
            bool: 是否触发止损
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]
        stop_price = position["stop_price"]
        side = position.get("side", "LONG")

        if side == "LONG":
            return current_price <= stop_price
        else:  # SHORT
            return current_price >= stop_price

    def calculate_unrealized_pnl(self, symbol: str, current_price: float) -> float:
        """
        计算未实现盈亏

        参数:
            symbol: 交易对符号
            current_price: 当前价格

        返回:
            float: 未实现盈亏
        """
        if symbol not in self.positions:
            return 0.0

        position = self.positions[symbol]
        entry_price = position["entry_price"]
        quantity = position["quantity"]
        side = position.get("side", "LONG")

        if side == "LONG":
            return (current_price - entry_price) * quantity
        else:  # SHORT
            return (entry_price - current_price) * quantity

    def _save_positions(self) -> None:
        """保存仓位状态到文件"""
        try:
            with open(self.positions_file, "w", encoding="utf-8") as f:
                json.dump(self.positions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存仓位状态失败: {e}")

    def _load_positions(self) -> None:
        """从文件加载仓位状态"""
        try:
            if Path(self.positions_file).exists():
                with open(self.positions_file, "r", encoding="utf-8") as f:
                    self.positions = json.load(f)
        except Exception as e:
            print(f"加载仓位状态失败: {e}")
            self.positions = {}

    def load_from_file(self) -> None:
        """从文件加载仓位状态（公共方法）"""
        self._load_positions()

    def get_position_summary(self) -> Dict[str, Any]:
        """
        获取仓位汇总信息

        返回:
            Dict: 仓位汇总
        """
        return {
            "total_positions": len(self.positions),
            "symbols": list(self.positions.keys()),
            "total_quantity": sum(pos["quantity"] for pos in self.positions.values()),
            "oldest_position": min(
                (pos["entry_time"] for pos in self.positions.values()), default=None
            ),
            "newest_position": max(
                (pos["entry_time"] for pos in self.positions.values()), default=None
            ),
        }
