#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alert Manager (告警管理器)

Manages alerts based on metrics and health checks
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Alert manager for monitoring system (监控系统告警管理器)

    Manages alert rules and notifications based on metrics
    """

    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize alert manager

        Args:
            metrics_collector: Metrics collector instance
        """
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(f"{__name__}.AlertManager")

        # Alert configuration
        self._alert_rules = {}
        self._alert_handlers = []
        self._fired_alerts = {}

        # Register default alert rules
        self._register_default_rules()

        self.logger.info("Alert manager initialized")

    def _register_default_rules(self):
        """Register default alert rules"""
        self.add_alert_rule(
            "high_error_rate",
            self._check_high_error_rate,
            severity="critical",
            description="High error rate detected",
        )

        self.add_alert_rule(
            "high_memory_usage",
            self._check_high_memory_usage,
            severity="warning",
            description="High memory usage detected",
        )

    def add_alert_rule(
        self,
        name: str,
        condition_func: Callable[[], bool],
        severity: str = "warning",
        description: str = "",
        cooldown_minutes: int = 5,
    ):
        """
        Add an alert rule

        Args:
            name: Alert rule name
            condition_func: Function that returns True if alert should fire
            severity: Alert severity (critical, warning, info)
            description: Alert description
            cooldown_minutes: Minimum time between repeated alerts
        """
        self._alert_rules[name] = {
            "condition": condition_func,
            "severity": severity,
            "description": description,
            "cooldown_seconds": cooldown_minutes * 60,
        }
        self.logger.info(f"Added alert rule: {name} ({severity})")

    def add_alert_handler(self, handler_func: Callable[[Dict[str, Any]], None]):
        """
        Add an alert handler function

        Args:
            handler_func: Function to handle fired alerts
        """
        self._alert_handlers.append(handler_func)
        self.logger.info("Added alert handler")

    def _check_high_error_rate(self) -> bool:
        """Check for high error rate"""
        try:
            if not self.metrics_collector:
                return False

            error_summary = self.metrics_collector.get_error_summary()
            total_errors = sum(error_summary.values())

            # Alert if more than 5 errors
            return total_errors > 5

        except Exception as e:
            self.logger.error(f"Error checking error rate: {e}")
            return False

    def _check_high_memory_usage(self) -> bool:
        """Check for high memory usage"""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)

            # Alert if using more than 500MB
            return memory_mb > 500

        except Exception as e:
            self.logger.error(f"Error checking memory usage: {e}")
            return False

    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check all alert rules and return fired alerts

        Returns:
            List of fired alerts
        """
        import time

        fired_alerts = []
        current_time = time.time()

        for name, rule in self._alert_rules.items():
            try:
                # Check if alert condition is met
                should_fire = rule["condition"]()

                if should_fire:
                    # Check cooldown period
                    last_fired = self._fired_alerts.get(name, 0)
                    if current_time - last_fired >= rule["cooldown_seconds"]:
                        alert = {
                            "name": name,
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "timestamp": current_time,
                            "status": "firing",
                        }

                        fired_alerts.append(alert)
                        self._fired_alerts[name] = current_time

                        # Send to handlers
                        self._handle_alert(alert)

            except Exception as e:
                self.logger.error(f"Error checking alert rule '{name}': {e}")

        return fired_alerts

    def _handle_alert(self, alert: Dict[str, Any]):
        """
        Handle a fired alert

        Args:
            alert: Alert information
        """
        # Log the alert
        severity = alert["severity"].upper()
        self.logger.warning(f"ALERT [{severity}] {alert['name']}: {alert['description']}")

        # Call registered handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """
        Get currently active alerts

        Returns:
            List of active alerts
        """
        import time

        active_alerts = []
        current_time = time.time()

        for name, rule in self._alert_rules.items():
            try:
                if rule["condition"]():
                    last_fired = self._fired_alerts.get(name, 0)
                    alert = {
                        "name": name,
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "last_fired": last_fired,
                        "age_seconds": current_time - last_fired if last_fired > 0 else 0,
                    }
                    active_alerts.append(alert)

            except Exception as e:
                self.logger.error(f"Error checking active alert '{name}': {e}")

        return active_alerts

    def clear_alert(self, alert_name: str):
        """
        Clear a specific alert

        Args:
            alert_name: Name of alert to clear
        """
        if alert_name in self._fired_alerts:
            del self._fired_alerts[alert_name]
            self.logger.info(f"Cleared alert: {alert_name}")
        else:
            self.logger.warning(f"Alert not found: {alert_name}")

    def clear_all_alerts(self):
        """Clear all fired alerts"""
        self._fired_alerts.clear()
        self.logger.info("Cleared all alerts")


# Default alert handlers
def log_alert_handler(alert: Dict[str, Any]):
    """
    Default log-based alert handler

    Args:
        alert: Alert information
    """
    severity = alert["severity"].upper()
    message = f"ALERT FIRED [{severity}] {alert['name']}: {alert['description']}"

    if alert["severity"] == "critical":
        logger.critical(message)
    elif alert["severity"] == "warning":
        logger.warning(message)
    else:
        logger.info(message)


def console_alert_handler(alert: Dict[str, Any]):
    """
    Console-based alert handler

    Args:
        alert: Alert information
    """
    import time

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(alert["timestamp"]))
    severity = alert["severity"].upper()

    print("\n🚨 ALERT FIRED 🚨")
    print(f"Time: {timestamp}")
    print(f"Severity: {severity}")
    print(f"Name: {alert['name']}")
    print(f"Description: {alert['description']}")
    print("-" * 50)
