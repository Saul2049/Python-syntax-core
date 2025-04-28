import os
from typing import Optional
from datetime import datetime
from src.telegram import TelegramBot


class Notifier:
    """Telegram notification handler with error logging."""

    def __init__(self, token: Optional[str] = None):
        """
        初始化通知器。
        Initialize notifier.

        参数 (Parameters):
            token: Telegram bot token (从环境变量获取 if None)
                  Telegram bot token (from env var if None)
        """
        self.token = token or os.getenv("TG_TOKEN")
        if not self.token:
            raise ValueError("Telegram token not found in environment")
        self.bot = TelegramBot(self.token)
        self.chat_id = os.getenv("TG_CHAT_ID")
        if not self.chat_id:
            raise ValueError("Telegram chat ID not found in environment")

    def _format_message(self, message: str, level: str = "INFO") -> str:
        """
        格式化消息，添加时间戳和级别。
        Format message with timestamp and level.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] {level} - {message}"

    def notify(self, message: str, level: str = "INFO") -> None:
        """
        发送通知消息。
        Send notification message.

        参数 (Parameters):
            message: 消息内容 (Message content)
            level: 消息级别 (Message level)
                  INFO: 普通信息 (Normal information)
                  WARN: 警告信息 (Warning)
                  ERROR: 错误信息 (Error)
        """
        formatted_msg = self._format_message(message, level)
        try:
            self.bot.send_message(self.chat_id, formatted_msg)
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")

    def notify_error(self, error: Exception, context: str = "") -> None:
        """
        发送错误通知。
        Send error notification.

        参数 (Parameters):
            error: 异常对象 (Exception object)
            context: 错误上下文 (Error context)
        """
        error_msg = (
            f"❗️Error in {context}: {str(error)}"
            if context
            else f"❗️Error: {str(error)}"
        )
        self.notify(error_msg, "ERROR")

    def notify_trade(
        self,
        action: str,
        symbol: str,
        price: float,
        quantity: float,
        reason: Optional[str] = None,
    ) -> None:
        """
        发送交易通知。
        Send trade notification.

        参数 (Parameters):
            action: 交易动作 (Trade action) - BUY/SELL
            symbol: 交易对 (Trading pair)
            price: 成交价格 (Execution price)
            quantity: 成交数量 (Execution quantity)
            reason: 交易原因 (Trade reason)
        """
        emoji = "🟢" if action == "BUY" else "🔴"
        message = f"{emoji} {action} {symbol} @ {price:.8f} x {quantity:.8f}"
        if reason:
            message += f"\nReason: {reason}"
        self.notify(message, "INFO")
