"""
核心交易引擎模块 (Core Trading Engine Module)

提供核心交易执行逻辑，包括：
- 交易决策引擎
- 订单执行逻辑
- 风险控制集成
- 状态监控
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional

from src.brokers import Broker
from src.core.price_fetcher import calculate_atr, fetch_price_data
from src.core.signal_processor import get_trading_signals, validate_signal


class TradingEngine:
    """核心交易引擎类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        telegram_token: Optional[str] = None,
    ):
        """
        初始化交易引擎

        参数:
            api_key: API密钥
            api_secret: API密钥
            telegram_token: Telegram通知令牌
        """
        self.broker = Broker(
            api_key=api_key or os.getenv("API_KEY"),
            api_secret=api_secret or os.getenv("API_SECRET"),
            telegram_token=telegram_token or os.getenv("TG_TOKEN"),
        )

        # 配置参数
        self.account_equity = float(os.getenv("ACCOUNT_EQUITY", "10000.0"))
        self.risk_percent = float(os.getenv("RISK_PERCENT", "0.01"))
        self.atr_multiplier = float(os.getenv("ATR_MULTIPLIER", "2.0"))

        # 状态变量
        self.last_status_update = datetime.now() - timedelta(hours=1)

    def calculate_position_size(self, current_price: float, atr: float, symbol: str) -> float:
        """
        计算仓位大小

        参数:
            current_price: 当前价格
            atr: ATR值
            symbol: 交易对

        返回:
            float: 仓位大小
        """
        risk_amount = self.account_equity * self.risk_percent
        stop_price = current_price - (atr * self.atr_multiplier)
        risk_per_unit = current_price - stop_price

        if risk_per_unit <= 0:
            return 0.0

        quantity = risk_amount / risk_per_unit

        # 限制数量小数位 (根据交易对精度要求调整)
        return round(quantity, 3)

    def process_buy_signal(self, symbol: str, signals: dict, atr: float) -> bool:
        """
        处理买入信号

        参数:
            symbol: 交易对
            signals: 信号字典
            atr: ATR值

        返回:
            bool: 是否执行了买入
        """
        if not signals["buy_signal"] or symbol in self.broker.positions:
            return False

        current_price = signals["current_price"]
        quantity = self.calculate_position_size(current_price, atr, symbol)

        if quantity <= 0:
            return False

        # 执行买入订单
        reason = f"MA交叉: 快线 {signals['fast_ma']:.2f} " f"上穿 慢线 {signals['slow_ma']:.2f}"

        try:
            self.broker.execute_order(
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                reason=reason,
            )
            return True
        except Exception as e:
            self.broker.notifier.notify_error(e, f"买入订单执行失败: {symbol}")
            return False

    def process_sell_signal(self, symbol: str, signals: dict) -> bool:
        """
        处理卖出信号

        参数:
            symbol: 交易对
            signals: 信号字典

        返回:
            bool: 是否执行了卖出
        """
        if not signals["sell_signal"] or symbol not in self.broker.positions:
            return False

        position = self.broker.positions[symbol]
        reason = f"MA交叉: 快线 {signals['fast_ma']:.2f} " f"下穿 慢线 {signals['slow_ma']:.2f}"

        try:
            self.broker.execute_order(
                symbol=symbol,
                side="SELL",
                quantity=position["quantity"],
                reason=reason,
            )
            return True
        except Exception as e:
            self.broker.notifier.notify_error(e, f"卖出订单执行失败: {symbol}")
            return False

    def update_positions(self, symbol: str, current_price: float, atr: float) -> None:
        """
        更新仓位状态

        参数:
            symbol: 交易对
            current_price: 当前价格
            atr: ATR值
        """
        # 更新持仓止损价
        self.broker.update_position_stops(symbol, current_price, atr)

        # 检查止损
        self.broker.check_stop_loss(symbol, current_price)

    def send_status_update(self, symbol: str, signals: dict, atr: float) -> None:
        """
        发送状态更新通知

        参数:
            symbol: 交易对
            signals: 信号字典
            atr: ATR值
        """
        current_time = datetime.now()

        # 每小时发送状态通知
        if (current_time - self.last_status_update).total_seconds() < 3600:
            return

        current_price = signals["current_price"]
        status_msg = (
            f"📈 状态更新 (Status Update)\n"
            f"品种 (Symbol): {symbol}\n"
            f"价格 (Price): {current_price:.8f}\n"
            f"ATR: {atr:.8f}\n"
            f"快线 (Fast MA): {signals['fast_ma']:.8f}\n"
            f"慢线 (Slow MA): {signals['slow_ma']:.8f}\n"
            f"头寸 (Position): {'有' if symbol in self.broker.positions else '无'}"
        )

        if symbol in self.broker.positions:
            position = self.broker.positions[symbol]
            status_msg += f"\n入场价 (Entry): {position['entry_price']:.8f}"
            status_msg += f"\n止损价 (Stop): {position['stop_price']:.8f}"
            status_msg += f"\n数量 (Quantity): {position['quantity']:.8f}"

            pnl = (current_price - position["entry_price"]) * position["quantity"]
            pnl_percent = (
                (current_price - position["entry_price"]) / position["entry_price"]
            ) * 100

            status_msg += f"\n盈亏 (P/L): {pnl:.8f} USDT"
            status_msg += f"\n盈亏% (P/L%): {pnl_percent:.2f}%"

        self.broker.notifier.notify(status_msg, "INFO")
        self.last_status_update = current_time

    def execute_trading_cycle(self, symbol: str, fast_win: int = 7, slow_win: int = 25) -> bool:
        """
        执行一个交易周期

        参数:
            symbol: 交易对
            fast_win: 快线窗口
            slow_win: 慢线窗口

        返回:
            bool: 是否成功执行
        """
        try:
            # 获取市场数据
            price_data = fetch_price_data(symbol)

            # 计算ATR
            atr = calculate_atr(price_data)

            # 获取交易信号
            signals = get_trading_signals(price_data, fast_win, slow_win)

            # 验证信号
            if not validate_signal(signals, price_data):
                print("信号验证失败，跳过此周期")
                return False

            current_price = signals["current_price"]

            # 更新仓位状态
            self.update_positions(symbol, current_price, atr)

            # 检查是否触发止损
            stop_triggered = self.broker.check_stop_loss(symbol, current_price)

            if stop_triggered:
                print("止损已触发，跳过信号处理")
            else:
                # 处理交易信号
                buy_executed = self.process_buy_signal(symbol, signals, atr)
                sell_executed = self.process_sell_signal(symbol, signals)

                if buy_executed or sell_executed:
                    action = "买入" if buy_executed else "卖出"
                    print(f"执行{action}订单: {symbol} @ {current_price:.2f}")

            # 发送状态更新
            self.send_status_update(symbol, signals, atr)

            # 打印状态
            signal_status = (
                "BUY" if signals["buy_signal"] else "SELL" if signals["sell_signal"] else "HOLD"
            )
            print(
                f"[{datetime.now()}] 价格: {current_price:.2f}, ATR: {atr:.2f}, "
                f"信号: {signal_status}"
            )

            return True

        except Exception as e:
            self.broker.notifier.notify_error(e, "交易周期执行错误")
            print(f"交易周期错误: {e}")
            return False

    def start_trading_loop(
        self,
        symbol: str = "BTCUSDT",
        interval_seconds: int = 60,
        fast_win: int = 7,
        slow_win: int = 25,
    ) -> None:
        """
        启动交易循环

        参数:
            symbol: 交易对
            interval_seconds: 循环间隔（秒）
            fast_win: 快线窗口
            slow_win: 慢线窗口
        """
        print(f"启动交易循环，交易对: {symbol}, 循环间隔: {interval_seconds}秒")

        try:
            # 发送启动通知
            self.broker.notifier.notify(
                f"🚀 交易机器人启动 (Trading bot started)\n交易对: {symbol}",
                "INFO",
            )

            while True:
                success = self.execute_trading_cycle(symbol, fast_win, slow_win)

                if not success:
                    print("交易周期执行失败，继续下一个周期")

                # 等待下一次循环
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            # 发送关闭通知
            self.broker.notifier.notify("🛑 交易机器人关闭 (Trading bot stopped)", "INFO")
            print("交易循环已关闭")


# 向后兼容函数
def trading_loop(symbol: str = "BTCUSDT", interval_seconds: int = 60):
    """
    交易循环 - 向后兼容函数
    Trading loop - backward compatibility function
    """
    engine = TradingEngine()
    engine.start_trading_loop(symbol, interval_seconds)
