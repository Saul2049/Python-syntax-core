#!/usr/bin/env python3
"""
每日自动健康检查脚本
Daily Automated Health Check Script

用于CI/CD和定时监控的综合健康检查
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import requests
except ImportError:
    requests = None


class DailyHealthChecker:
    """每日健康检查器"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        self.health_report = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "unknown",
            "failed_checks": [],
            "recommendations": [],
        }

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

    def run_makefile_command(self, command: str) -> Dict:
        """运行Makefile命令并收集结果"""
        self.logger.info(f"🔍 Running: make {command}")

        try:
            start_time = time.time()
            result = subprocess.run(
                ["make", command], capture_output=True, text=True, timeout=300  # 5分钟超时
            )
            duration = time.time() - start_time

            return {
                "command": f"make {command}",
                "success": result.returncode == 0,
                "duration_seconds": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "command": f"make {command}",
                "success": False,
                "error": "timeout",
                "duration_seconds": 300,
            }
        except Exception as e:
            return {
                "command": f"make {command}",
                "success": False,
                "error": str(e),
                "duration_seconds": 0,
            }

    def check_prometheus_health(self) -> Dict:
        """检查Prometheus健康状态"""
        if not requests:
            return {
                "success": False,
                "error": "requests module not available",
                "metrics_available": False,
            }

        try:
            response = requests.get("http://localhost:8000/metrics", timeout=10)

            if response.status_code == 200:
                metrics_text = response.text

                # 检查关键M5指标
                required_metrics = [
                    "process_memory_rss_bytes",
                    "process_open_fds",
                    "gc_pause_duration_seconds",
                ]

                available_metrics = []
                missing_metrics = []

                for metric in required_metrics:
                    if metric in metrics_text:
                        available_metrics.append(metric)
                    else:
                        missing_metrics.append(metric)

                return {
                    "success": len(missing_metrics) == 0,
                    "metrics_available": True,
                    "total_metrics": len(metrics_text.split("\n")),
                    "available_m5_metrics": available_metrics,
                    "missing_m5_metrics": missing_metrics,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "metrics_available": False,
                }

        except requests.RequestException as e:
            return {"success": False, "error": str(e), "metrics_available": False}

    def extract_memory_stats(self, output: str) -> Dict:
        """从输出中提取内存统计信息"""
        stats = {}

        for line in output.split("\n"):
            if "RSS:" in line and "MB" in line:
                try:
                    # 尝试提取内存数值
                    import re

                    match = re.search(r"(\d+\.?\d*)\s*MB", line)
                    if match:
                        stats["rss_mb"] = float(match.group(1))
                except:
                    pass
            elif "GC counts:" in line:
                stats["gc_info"] = line.strip()
            elif "Open FDs:" in line:
                try:
                    import re

                    match = re.search(r"(\d+)", line)
                    if match:
                        stats["open_fds"] = int(match.group(1))
                except:
                    pass

        return stats

    def run_comprehensive_health_check(self) -> Dict:
        """运行综合健康检查"""

        self.logger.info("🚀 Starting daily health check...")

        # 1. 基础健康检查
        self.logger.info("📋 Running basic health check...")
        basic_health = self.run_makefile_command("health")
        self.health_report["checks"]["basic_health"] = basic_health

        # 2. 内存健康检查
        self.logger.info("🧠 Running memory health check...")
        mem_health = self.run_makefile_command("mem-health")
        self.health_report["checks"]["memory_health"] = mem_health

        # 提取内存统计
        if mem_health["success"]:
            mem_stats = self.extract_memory_stats(mem_health["stdout"])
            self.health_report["checks"]["memory_stats"] = mem_stats

        # 3. Prometheus检查
        self.logger.info("📊 Checking Prometheus metrics...")
        prometheus_health = self.check_prometheus_health()
        self.health_report["checks"]["prometheus_health"] = prometheus_health

        # 4. M5基础设施检查
        self.logger.info("📈 Checking M5 infrastructure...")
        m5_completion = self.run_makefile_command("m5-completion")
        self.health_report["checks"]["m5_completion"] = m5_completion

        # 5. Canary状态检查
        self.logger.info("🕯️ Checking canary status...")
        canary_status = self.run_makefile_command("canary-status")
        self.health_report["checks"]["canary_status"] = canary_status

        # 分析结果
        self._analyze_results()

        return self.health_report

    def _analyze_results(self):
        """分析健康检查结果"""
        failed_checks = []
        warnings = []

        # 检查各项结果
        for check_name, result in self.health_report["checks"].items():
            if isinstance(result, dict) and not result.get("success", False):
                failed_checks.append(check_name)

        # 内存状态分析
        mem_stats = self.health_report["checks"].get("memory_stats", {})
        if "rss_mb" in mem_stats:
            rss_mb = mem_stats["rss_mb"]
            if rss_mb > 60:
                warnings.append(f"Memory usage high: {rss_mb}MB > 60MB threshold")
            elif rss_mb > 40:
                warnings.append(f"Memory usage elevated: {rss_mb}MB > 40MB target")

        if "open_fds" in mem_stats:
            fds = mem_stats["open_fds"]
            if fds > 800:
                warnings.append(f"File descriptors high: {fds} > 800 threshold")
            elif fds > 500:
                warnings.append(f"File descriptors elevated: {fds} > 500 target")

        # Prometheus指标分析
        prom_health = self.health_report["checks"].get("prometheus_health", {})
        if prom_health.get("missing_m5_metrics"):
            warnings.append(f"Missing M5 metrics: {prom_health['missing_m5_metrics']}")

        # 设置总体状态
        if failed_checks:
            self.health_report["overall_status"] = "unhealthy"
            self.health_report["failed_checks"] = failed_checks
        elif warnings:
            self.health_report["overall_status"] = "warning"
        else:
            self.health_report["overall_status"] = "healthy"

        # 生成建议
        recommendations = []
        if failed_checks:
            recommendations.append("Review failed checks and address underlying issues")
        if warnings:
            recommendations.extend(warnings)
        if not failed_checks and not warnings:
            recommendations.append("System is healthy - continue monitoring")

        self.health_report["recommendations"] = recommendations

    def save_report(self) -> str:
        """保存健康检查报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"daily_health_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w") as f:
            json.dump(self.health_report, f, indent=2, default=str)

        self.logger.info(f"📄 Health report saved to: {filepath}")
        return filepath

    def print_summary(self):
        """打印健康检查摘要"""
        status = self.health_report["overall_status"]

        print("\n" + "=" * 60)
        print("🏥 Daily Health Check Summary")
        print("=" * 60)

        # 状态图标
        status_icons = {"healthy": "✅", "warning": "⚠️", "unhealthy": "❌"}

        icon = status_icons.get(status, "❓")
        print(f"\n{icon} Overall Status: {status.upper()}")

        # 检查结果
        print("\n📋 Check Results:")
        for check_name, result in self.health_report["checks"].items():
            if isinstance(result, dict):
                success = result.get("success", False)
                duration = result.get("duration_seconds", 0)

                check_icon = "✅" if success else "❌"
                print(
                    f"   {check_icon} {check_name}: {'PASS' if success else 'FAIL'} ({duration:.1f}s)"
                )

        # 失败项目
        if self.health_report["failed_checks"]:
            print("\n❌ Failed Checks:")
            for check in self.health_report["failed_checks"]:
                print(f"   - {check}")

        # 建议
        if self.health_report["recommendations"]:
            print("\n💡 Recommendations:")
            for rec in self.health_report["recommendations"]:
                print(f"   - {rec}")

        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Daily automated health check")
    parser.add_argument("--output-dir", default="output", help="Output directory for reports")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode - minimal output")

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.quiet:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    print("🏥 Daily Health Check Tool")
    print(f"Output directory: {args.output_dir}")

    # 创建健康检查器
    checker = DailyHealthChecker(args.output_dir)

    try:
        # 运行健康检查
        report = checker.run_comprehensive_health_check()

        # 保存报告
        report_file = checker.save_report()

        # 打印摘要
        if not args.quiet:
            checker.print_summary()

        # 返回状态码
        if report["overall_status"] == "healthy":
            return 0
        elif report["overall_status"] == "warning":
            return 1  # 警告状态
        else:
            return 2  # 不健康状态

    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
