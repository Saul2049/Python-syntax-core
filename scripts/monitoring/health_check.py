#!/usr/bin/env python3
"""
M1-5: 一键本地/CI 健康扫描
Health Check Script for Trading System

轻量级健康检查工具，支持快速检查和完整检查模式
"""

import argparse
import gc
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import psutil

# 导入我们的指标收集器
# MetricsCollector导入已移除，因为在此脚本中未使用


@dataclass
class HealthStatus:
    """健康检查状态"""

    component: str
    status: str  # OK, WARNING, CRITICAL
    message: str
    details: Dict[str, Any]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HealthChecker:
    """交易系统健康检查器"""

    def __init__(self, mode: str = "quick"):
        self.mode = mode  # quick, full
        self.checks: List[HealthStatus] = []
        self.start_time = time.time()

        # 健康阈值配置（可通过环境变量覆盖）
        self.thresholds = {
            "memory_warning_mb": int(os.getenv("HEALTH_MEMORY_WARNING", "100")),
            "memory_critical_mb": int(os.getenv("HEALTH_MEMORY_CRITICAL", "200")),
            "cpu_warning_percent": float(os.getenv("HEALTH_CPU_WARNING", "70")),
            "cpu_critical_percent": float(os.getenv("HEALTH_CPU_CRITICAL", "90")),
            "disk_warning_percent": float(os.getenv("HEALTH_DISK_WARNING", "80")),
            "disk_critical_percent": float(os.getenv("HEALTH_DISK_CRITICAL", "95")),
            "fd_warning": int(os.getenv("HEALTH_FD_WARNING", "100")),
            "fd_critical": int(os.getenv("HEALTH_FD_CRITICAL", "500")),
        }

    def _determine_status(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
        reverse: bool = False,
    ) -> str:
        """根据阈值确定状态"""
        if reverse:  # 值越小越好（如可用空间）
            if value <= critical_threshold:
                return "CRITICAL"
            elif value <= warning_threshold:
                return "WARNING"
            else:
                return "OK"
        else:  # 值越大越差（如内存使用）
            if value >= critical_threshold:
                return "CRITICAL"
            elif value >= warning_threshold:
                return "WARNING"
            else:
                return "OK"

    def check_memory(self) -> HealthStatus:
        """检查内存使用"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            rss_mb = memory_info.rss / 1024 / 1024

            status = self._determine_status(
                rss_mb, self.thresholds["memory_warning_mb"], self.thresholds["memory_critical_mb"]
            )

            # 系统内存
            system_memory = psutil.virtual_memory()

            details = {
                "process_rss_mb": round(rss_mb, 2),
                "process_vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "system_total_gb": round(system_memory.total / 1024 / 1024 / 1024, 2),
                "system_available_gb": round(system_memory.available / 1024 / 1024 / 1024, 2),
                "system_percent": system_memory.percent,
                "thresholds": {
                    "warning_mb": self.thresholds["memory_warning_mb"],
                    "critical_mb": self.thresholds["memory_critical_mb"],
                },
            }

            if status == "OK":
                message = f"Memory usage normal: {rss_mb:.1f}MB"
            elif status == "WARNING":
                message = f"Memory usage elevated: {rss_mb:.1f}MB (>{self.thresholds['memory_warning_mb']}MB)"
            else:
                message = f"Memory usage critical: {rss_mb:.1f}MB (>{self.thresholds['memory_critical_mb']}MB)"

            return HealthStatus("memory", status, message, details, time.time())

        except Exception as e:
            return HealthStatus(
                "memory", "CRITICAL", f"Memory check failed: {e}", {"error": str(e)}, time.time()
            )

    def check_cpu(self) -> HealthStatus:
        """检查CPU使用"""
        try:
            # 获取进程CPU使用率（需要两次采样）
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)  # 100ms采样

            status = self._determine_status(
                cpu_percent,
                self.thresholds["cpu_warning_percent"],
                self.thresholds["cpu_critical_percent"],
            )

            # 系统CPU
            system_cpu = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            details = {
                "process_cpu_percent": round(cpu_percent, 2),
                "system_cpu_percent": round(system_cpu, 2),
                "cpu_count": cpu_count,
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
                "thresholds": {
                    "warning_percent": self.thresholds["cpu_warning_percent"],
                    "critical_percent": self.thresholds["cpu_critical_percent"],
                },
            }

            if status == "OK":
                message = f"CPU usage normal: {cpu_percent:.1f}%"
            elif status == "WARNING":
                message = f"CPU usage elevated: {cpu_percent:.1f}% (>{self.thresholds['cpu_warning_percent']}%)"
            else:
                message = f"CPU usage critical: {cpu_percent:.1f}% (>{self.thresholds['cpu_critical_percent']}%)"

            return HealthStatus("cpu", status, message, details, time.time())

        except Exception as e:
            return HealthStatus(
                "cpu", "CRITICAL", f"CPU check failed: {e}", {"error": str(e)}, time.time()
            )

    def check_disk(self) -> HealthStatus:
        """检查磁盘空间"""
        try:
            disk_usage = psutil.disk_usage(".")
            used_percent = (disk_usage.used / disk_usage.total) * 100
            free_gb = disk_usage.free / 1024 / 1024 / 1024

            status = self._determine_status(
                used_percent,
                self.thresholds["disk_warning_percent"],
                self.thresholds["disk_critical_percent"],
            )

            details = {
                "total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk_usage.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 2),
                "thresholds": {
                    "warning_percent": self.thresholds["disk_warning_percent"],
                    "critical_percent": self.thresholds["disk_critical_percent"],
                },
            }

            if status == "OK":
                message = f"Disk space sufficient: {used_percent:.1f}% used, {free_gb:.1f}GB free"
            elif status == "WARNING":
                message = f"Disk space low: {used_percent:.1f}% used (>{self.thresholds['disk_warning_percent']}%)"
            else:
                message = f"Disk space critical: {used_percent:.1f}% used (>{self.thresholds['disk_critical_percent']}%)"

            return HealthStatus("disk", status, message, details, time.time())

        except Exception as e:
            return HealthStatus(
                "disk", "CRITICAL", f"Disk check failed: {e}", {"error": str(e)}, time.time()
            )

    def check_file_descriptors(self) -> HealthStatus:
        """检查文件描述符"""
        try:
            process = psutil.Process()

            # 获取文件描述符数量
            if hasattr(process, "num_fds"):
                num_fds = process.num_fds()
            else:
                # Windows系统
                num_fds = len(process.open_files()) + len(process.connections())

            status = self._determine_status(
                num_fds, self.thresholds["fd_warning"], self.thresholds["fd_critical"]
            )

            details = {
                "open_fds": num_fds,
                "open_files": len(process.open_files()),
                "connections": len(process.connections()),
                "thresholds": {
                    "warning": self.thresholds["fd_warning"],
                    "critical": self.thresholds["fd_critical"],
                },
            }

            if status == "OK":
                message = f"File descriptors normal: {num_fds} open"
            elif status == "WARNING":
                message = (
                    f"File descriptors elevated: {num_fds} open (>{self.thresholds['fd_warning']})"
                )
            else:
                message = (
                    f"File descriptors critical: {num_fds} open (>{self.thresholds['fd_critical']})"
                )

            return HealthStatus("file_descriptors", status, message, details, time.time())

        except Exception as e:
            return HealthStatus(
                "file_descriptors",
                "WARNING",
                f"FD check failed: {e}",
                {"error": str(e)},
                time.time(),
            )

    def check_gc_health(self) -> HealthStatus:
        """检查垃圾回收健康状态"""
        try:
            gc_stats = gc.get_stats()
            counts = gc.get_count()
            thresholds = gc.get_threshold()

            # 检查是否有过多的Gen0回收
            gen0_collections = gc_stats[0].get("collections", 0) if gc_stats else 0
            gen0_ratio = counts[0] / thresholds[0] if thresholds[0] > 0 else 0

            if gen0_ratio > 0.8:
                status = "WARNING"
                message = f"GC Gen0 near threshold: {counts[0]}/{thresholds[0]} ({gen0_ratio:.1%})"
            elif gen0_collections > 1000:  # 经验值
                status = "WARNING"
                message = f"High GC Gen0 collections: {gen0_collections}"
            else:
                status = "OK"
                message = f"GC healthy: Gen0 {counts[0]}/{thresholds[0]}"

            details = {
                "gc_counts": counts,
                "gc_thresholds": thresholds,
                "gc_stats": gc_stats,
                "gen0_ratio": round(gen0_ratio, 3),
                "total_objects": sum(counts),
            }

            return HealthStatus("gc", status, message, details, time.time())

        except Exception as e:
            return HealthStatus(
                "gc", "WARNING", f"GC check failed: {e}", {"error": str(e)}, time.time()
            )

    def check_processes(self) -> HealthStatus:
        """检查关键进程状态"""
        try:
            current_process = psutil.Process()
            details = {
                "pid": current_process.pid,
                "ppid": current_process.ppid(),
                "status": current_process.status(),
                "create_time": current_process.create_time(),
                "num_threads": current_process.num_threads(),
                "uptime_seconds": time.time() - current_process.create_time(),
            }

            # 检查特定的交易系统进程
            trading_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if any(
                        "stress" in str(cmd).lower() or "trading" in str(cmd).lower()
                        for cmd in proc.info["cmdline"] or []
                    ):
                        trading_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "cmdline": " ".join(proc.info["cmdline"] or [])[
                                    :100
                                ],  # 截断长命令行
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            details["trading_processes"] = trading_processes

            if len(trading_processes) > 0:
                status = "OK"
                message = f"Found {len(trading_processes)} trading processes"
            else:
                status = "WARNING"
                message = "No trading processes detected"

            return HealthStatus("processes", status, message, details, time.time())

        except Exception as e:
            return HealthStatus(
                "processes", "WARNING", f"Process check failed: {e}", {"error": str(e)}, time.time()
            )

    def run_quick_check(self) -> List[HealthStatus]:
        """快速健康检查（<1秒）"""
        checks = [self.check_memory(), self.check_file_descriptors(), self.check_processes()]
        return checks

    def run_full_check(self) -> List[HealthStatus]:
        """完整健康检查（1-3秒）"""
        checks = [
            self.check_memory(),
            self.check_cpu(),
            self.check_disk(),
            self.check_file_descriptors(),
            self.check_gc_health(),
            self.check_processes(),
        ]
        return checks

    def run_checks(self) -> List[HealthStatus]:
        """根据模式运行检查"""
        if self.mode == "quick":
            self.checks = self.run_quick_check()
        else:
            self.checks = self.run_full_check()
        return self.checks

    def get_overall_status(self) -> str:
        """获取整体健康状态"""
        if not self.checks:
            return "UNKNOWN"

        statuses = [check.status for check in self.checks]
        if "CRITICAL" in statuses:
            return "CRITICAL"
        elif "WARNING" in statuses:
            return "WARNING"
        else:
            return "OK"

    def to_json(self) -> str:
        """输出JSON格式报告"""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "overall_status": self.get_overall_status(),
            "execution_time_seconds": round(time.time() - self.start_time, 3),
            "checks": [check.to_dict() for check in self.checks],
            "summary": {
                "total_checks": len(self.checks),
                "ok": len([c for c in self.checks if c.status == "OK"]),
                "warning": len([c for c in self.checks if c.status == "WARNING"]),
                "critical": len([c for c in self.checks if c.status == "CRITICAL"]),
            },
        }
        return json.dumps(report, indent=2)

    def to_text(self) -> str:
        """输出文本格式报告"""
        lines = []
        lines.append("🏥 Trading System Health Check")
        lines.append("=" * 40)
        lines.append(f"Mode: {self.mode}")
        lines.append(f"Overall Status: {self.get_overall_status()}")
        lines.append(f"Execution Time: {time.time() - self.start_time:.3f}s")
        lines.append("")

        for check in self.checks:
            emoji = {"OK": "✅", "WARNING": "⚠️", "CRITICAL": "🔴"}.get(check.status, "❓")
            lines.append(f"{emoji} {check.component.upper()}: {check.status}")
            lines.append(f"   {check.message}")
            lines.append("")

        return "\n".join(lines)


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description="Trading System Health Check")
    parser.add_argument(
        "--mode",
        choices=["quick", "full"],
        default="quick",
        help="Check mode: quick (<1s) or full (1-3s)",
    )
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument(
        "--exit-code", action="store_true", help="Exit with non-zero code if unhealthy"
    )

    args = parser.parse_args()

    # 运行健康检查
    checker = HealthChecker(args.mode)
    checker.run_checks()

    # 生成报告
    if args.format == "json":
        output = checker.to_json()
    else:
        output = checker.to_text()

    # 输出结果
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Health check report saved to {args.output}")
    else:
        print(output)

    # 根据健康状态设置退出码
    if args.exit_code:
        overall_status = checker.get_overall_status()
        if overall_status == "CRITICAL":
            sys.exit(2)
        elif overall_status == "WARNING":
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
