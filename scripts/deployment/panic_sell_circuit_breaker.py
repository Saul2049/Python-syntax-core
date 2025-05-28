#!/usr/bin/env python3
"""
交易系统灾难熔断机制
实时监控回撤，触发紧急止损和告警
"""
import logging
import time
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import smtplib
from email.mime.text import MIMEText
import requests


class AlertLevel(Enum):
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    max_drawdown_pct: float = 5.0  # 最大回撤百分比
    min_balance_usd: float = 1000.0  # 最小余额
    check_interval_seconds: int = 10  # 检查间隔
    alert_cooldown_seconds: int = 300  # 告警冷却时间


class CircuitBreaker:
    """交易系统熔断器"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_alert_time = 0
        self.is_tripped = False
        self.peak_balance = 0.0

        # 告警配置 (从环境变量读取)
        import os

        self.email_config = {
            "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "email_user": os.getenv("ALERT_EMAIL_USER"),
            "email_pass": os.getenv("ALERT_EMAIL_PASS"),
            "alert_recipients": os.getenv("ALERT_RECIPIENTS", "").split(","),
        }

        self.telegram_config = {
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        }

    def check_circuit_conditions(self, current_balance: float) -> Optional[AlertLevel]:
        """检查熔断条件"""
        # 更新峰值余额
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        # 计算当前回撤
        if self.peak_balance > 0:
            drawdown_pct = (self.peak_balance - current_balance) / self.peak_balance * 100
        else:
            drawdown_pct = 0

        # 检查熔断条件
        if current_balance < self.config.min_balance_usd:
            return AlertLevel.EMERGENCY
        elif drawdown_pct > self.config.max_drawdown_pct:
            return AlertLevel.CRITICAL
        elif drawdown_pct > self.config.max_drawdown_pct * 0.7:
            return AlertLevel.WARNING

        return None

    def panic_sell(self, exchange_client) -> bool:
        """紧急平仓"""
        try:
            self.logger.critical("🚨 PANIC SELL TRIGGERED - Liquidating all positions")

            # 获取所有持仓
            positions = exchange_client.get_open_positions()

            # 紧急平仓
            for position in positions:
                try:
                    result = exchange_client.market_sell(
                        symbol=position["symbol"], quantity=position["quantity"]
                    )
                    self.logger.critical(f"Emergency sell: {position['symbol']} - {result}")
                except Exception as e:
                    self.logger.error(f"Failed to sell {position['symbol']}: {e}")

            # 取消所有挂单
            try:
                exchange_client.cancel_all_orders()
                self.logger.critical("All open orders cancelled")
            except Exception as e:
                self.logger.error(f"Failed to cancel orders: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Panic sell failed: {e}")
            return False

    def send_email_alert(self, level: AlertLevel, message: str):
        """发送邮件告警"""
        try:
            if not self.email_config["email_user"]:
                return

            subject = f"🚨 Trading Alert - {level.value.upper()}"
            body = f"""
            Trading System Alert
            ====================
            
            Level: {level.value.upper()}
            Time: {time.strftime('%Y-%m-%d %H:%M:%S')}
            
            Message:
            {message}
            
            Peak Balance: ${self.peak_balance:.2f}
            Current Drawdown: {self._calculate_current_drawdown():.2f}%
            
            Please check your trading system immediately!
            """

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.email_config["email_user"]
            msg["To"] = ", ".join(self.email_config["alert_recipients"])

            with smtplib.SMTP(
                self.email_config["smtp_host"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(self.email_config["email_user"], self.email_config["email_pass"])
                server.send_message(msg)

            self.logger.info("Email alert sent successfully")

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    def send_telegram_alert(self, level: AlertLevel, message: str):
        """发送Telegram告警"""
        try:
            if not self.telegram_config["bot_token"]:
                return

            emoji = {"warning": "⚠️", "critical": "🚨", "emergency": "🆘"}

            text = f"""
{emoji.get(level.value, '⚠️')} *Trading Alert - {level.value.upper()}*

*Time:* {time.strftime('%Y-%m-%d %H:%M:%S')}
*Peak Balance:* ${self.peak_balance:.2f}
*Current Drawdown:* {self._calculate_current_drawdown():.2f}%

*Message:*
{message}

Please check your trading system immediately!
            """

            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            data = {
                "chat_id": self.telegram_config["chat_id"],
                "text": text,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            self.logger.info("Telegram alert sent successfully")

        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")

    def _calculate_current_drawdown(self) -> float:
        """计算当前回撤百分比"""
        # 这里需要从实际系统获取当前余额
        # 暂时返回0作为占位符
        return 0.0

    def monitor(self, get_balance_func: Callable[[], float], exchange_client):
        """主监控循环"""
        self.logger.info("Circuit breaker monitoring started")

        while True:
            try:
                current_balance = get_balance_func()
                alert_level = self.check_circuit_conditions(current_balance)

                if alert_level and not self._is_in_cooldown():
                    if alert_level == AlertLevel.EMERGENCY:
                        # 紧急情况：立即平仓
                        message = f"EMERGENCY: Balance below minimum (${current_balance:.2f} < ${self.config.min_balance_usd})"
                        self.panic_sell(exchange_client)
                        self.is_tripped = True

                    elif alert_level == AlertLevel.CRITICAL:
                        # 严重情况：回撤过大，平仓
                        drawdown = self._calculate_drawdown(current_balance)
                        message = f"CRITICAL: Drawdown exceeded limit ({drawdown:.2f}% > {self.config.max_drawdown_pct}%)"
                        self.panic_sell(exchange_client)
                        self.is_tripped = True

                    elif alert_level == AlertLevel.WARNING:
                        # 警告：接近限制
                        drawdown = self._calculate_drawdown(current_balance)
                        message = f"WARNING: Approaching drawdown limit ({drawdown:.2f}%)"

                    # 发送告警
                    self.send_email_alert(alert_level, message)
                    self.send_telegram_alert(alert_level, message)
                    self.last_alert_time = time.time()

                    if self.is_tripped:
                        self.logger.critical("Circuit breaker tripped - stopping monitoring")
                        break

                time.sleep(self.config.check_interval_seconds)

            except Exception as e:
                self.logger.error(f"Circuit breaker monitoring error: {e}")
                time.sleep(self.config.check_interval_seconds)

    def _is_in_cooldown(self) -> bool:
        """检查是否在告警冷却期"""
        return time.time() - self.last_alert_time < self.config.alert_cooldown_seconds

    def _calculate_drawdown(self, current_balance: float) -> float:
        """计算回撤百分比"""
        if self.peak_balance > 0:
            return (self.peak_balance - current_balance) / self.peak_balance * 100
        return 0.0


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # 创建熔断器
    config = CircuitBreakerConfig(
        max_drawdown_pct=5.0, min_balance_usd=1000.0, check_interval_seconds=10
    )

    circuit_breaker = CircuitBreaker(config)

    # 模拟监控
    def mock_get_balance():
        import random

        return random.uniform(900, 1100)  # 模拟余额波动

    class MockExchangeClient:
        def get_open_positions(self):
            return [{"symbol": "BTCUSDT", "quantity": 0.1}]

        def market_sell(self, symbol, quantity):
            return {"status": "success", "symbol": symbol, "quantity": quantity}

        def cancel_all_orders(self):
            return {"status": "success"}

    # 启动监控
    circuit_breaker.monitor(mock_get_balance, MockExchangeClient())
