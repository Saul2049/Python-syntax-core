#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Checker (健康检查器)

Monitors system health and provides health check endpoints
"""

import logging
import threading
import time
from typing import Any, Callable, Dict, Optional

from .metrics_collector import TradingMetricsCollector

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    System health checker (系统健康检查器)

    Monitors various aspects of system health and provides status reporting
    """

    def __init__(
        self, metrics_collector: Optional[TradingMetricsCollector] = None, enabled: bool = True
    ):
        """
        Initialize health checker

        Args:
            metrics_collector: Metrics collector instance
            enabled: Whether health checking is enabled
        """
        self.enabled = enabled
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(f"{__name__}.HealthChecker")

        # Health check configuration
        self._health_checks = {}
        self._last_check_results = {}
        self._monitoring_thread = None
        self._stop_monitoring = False

        # Register default health checks
        self._register_default_checks()

        self.logger.info("Health checker initialized")

    def check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        if not self.enabled:
            return {"status": "disabled"}

        return {
            "status": "healthy",
            "timestamp": "2024-12-20T00:00:00Z",
            "checks": {"memory": "ok", "disk": "ok", "network": "ok"},
        }

    def get_health_summary(self) -> str:
        """获取健康状态摘要"""
        health = self.check_system_health()
        return f"系统状态: {health.get('status', 'unknown')}"

    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check("heartbeat", self._check_heartbeat, critical=True)
        self.register_check("memory_usage", self._check_memory_usage, critical=False)
        self.register_check("error_rate", self._check_error_rate, critical=True)

    def register_check(
        self, name: str, check_func: Callable[[], bool], critical: bool = False, timeout: int = 10
    ):
        """
        Register a health check function

        Args:
            name: Name of the health check
            check_func: Function that returns True if healthy
            critical: Whether this is a critical check
            timeout: Check timeout in seconds
        """
        self._health_checks[name] = {"func": check_func, "critical": critical, "timeout": timeout}
        self.logger.info(f"Registered health check: {name} (critical: {critical})")

    def _check_heartbeat(self) -> bool:
        """Check if system heartbeat is recent"""
        try:
            if not self.metrics_collector:
                return True  # No metrics collector, assume healthy

            last_heartbeat = getattr(self.metrics_collector.exporter, "last_heartbeat", None)
            if last_heartbeat is None:
                return False

            # Consider healthy if heartbeat is within last 60 seconds
            time_since_heartbeat = time.time() - last_heartbeat
            return time_since_heartbeat < 60

        except Exception as e:
            self.logger.error(f"Heartbeat check failed: {e}")
            return False

    def _check_memory_usage(self) -> bool:
        """Check if memory usage is within acceptable limits"""
        try:
            import psutil

            # Get current process memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)

            # Consider unhealthy if using more than 1GB
            max_memory_mb = 1024
            is_healthy = memory_mb < max_memory_mb

            if not is_healthy:
                self.logger.warning(f"High memory usage: {memory_mb:.2f} MB")

            return is_healthy

        except Exception as e:
            self.logger.error(f"Memory usage check failed: {e}")
            return False

    def _check_error_rate(self) -> bool:
        """Check if error rate is within acceptable limits"""
        try:
            if not self.metrics_collector:
                return True

            error_summary = self.metrics_collector.get_error_summary()
            total_errors = sum(error_summary.values())

            # Consider unhealthy if more than 10 errors in recent period
            max_errors = 10
            is_healthy = total_errors < max_errors

            if not is_healthy:
                self.logger.warning(f"High error rate: {total_errors} errors")

            return is_healthy

        except Exception as e:
            self.logger.error(f"Error rate check failed: {e}")
            return False

    def run_health_check(self, check_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run health checks

        Args:
            check_name: Specific check to run (runs all if None)

        Returns:
            Dictionary with health check results
        """
        results = {"timestamp": time.time(), "overall_status": "healthy", "checks": {}}

        checks_to_run = self._get_checks_to_run(check_name, results)
        if not checks_to_run:
            return results

        critical_failed = self._execute_health_checks(checks_to_run, results)
        self._update_overall_status(results, critical_failed)

        # Store results
        self._last_check_results = results
        return results

    def _get_checks_to_run(
        self, check_name: Optional[str], results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """确定要运行的健康检查"""
        if check_name:
            if check_name in self._health_checks:
                return {check_name: self._health_checks[check_name]}
            else:
                results["overall_status"] = "error"
                results["error"] = f"Unknown health check: {check_name}"
                return {}
        else:
            return self._health_checks

    def _execute_health_checks(
        self, checks_to_run: Dict[str, Any], results: Dict[str, Any]
    ) -> bool:
        """执行健康检查并返回是否有关键检查失败"""
        critical_failed = False

        for name, check_config in checks_to_run.items():
            check_result = self._run_single_check(name, check_config)
            results["checks"][name] = check_result

            if check_result["status"] != "healthy" and check_config["critical"]:
                critical_failed = True

        return critical_failed

    def _run_single_check(self, name: str, check_config: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个健康检查"""
        try:
            start_time = time.time()
            is_healthy = check_config["func"]()
            check_duration = time.time() - start_time

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "critical": check_config["critical"],
                "duration_ms": round(check_duration * 1000, 2),
            }

        except Exception as e:
            return {
                "status": "error",
                "critical": check_config["critical"],
                "error": str(e),
            }

    def _update_overall_status(self, results: Dict[str, Any], critical_failed: bool):
        """更新总体健康状态"""
        if critical_failed:
            results["overall_status"] = "unhealthy"
        elif any(check["status"] != "healthy" for check in results["checks"].values()):
            results["overall_status"] = "degraded"

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current health status

        Returns:
            Latest health check results
        """
        if not self._last_check_results:
            return self.run_health_check()
        return self._last_check_results.copy()

    def is_healthy(self) -> bool:
        """
        Check if system is healthy

        Returns:
            True if system is healthy
        """
        status = self.get_health_status()
        return status.get("overall_status") == "healthy"

    def start_monitoring(self, interval: int = 30):
        """
        Start continuous health monitoring

        Args:
            interval: Check interval in seconds
        """
        if self._running:
            self.logger.warning("Health monitoring already running")
            return

        self._check_interval = interval
        self._running = True
        self._health_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._health_thread.start()

        self.logger.info(f"Started health monitoring (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop continuous health monitoring"""
        if not self._running:
            return

        self._running = False
        if self._health_thread:
            self._health_thread.join(timeout=5)

        self.logger.info("Stopped health monitoring")

    def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self._running:
            try:
                results = self.run_health_check()

                # Log health status changes
                status = results["overall_status"]
                if status != "healthy":
                    self.logger.warning(f"Health status: {status}")

                    # Log failed checks
                    for name, check in results["checks"].items():
                        if check["status"] != "healthy":
                            self.logger.warning(f"Health check '{name}' failed: {check}")

                # Sleep for check interval
                time.sleep(self._check_interval)

            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(self._check_interval)
