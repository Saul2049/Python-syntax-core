#!/usr/bin/env python3
"""
W3 泄漏哨兵 + W4 压力测试并行监控脚本
W3 Leak Sentinel + W4 Stress Test Parallel Monitor

监控两个并行任务的状态和资源使用
"""

import os
import sys
import json
import time
import psutil
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class ParallelTaskMonitor:
    """W3+W4 并行任务监控器"""

    def __init__(self):
        self.start_time = datetime.now()
        self.w3_status_file = "output/w3_sentinel_status_W3-Production.json"
        self.w4_status_pattern = "output/w4_stress_*.json"
        self.alerts = []

    def get_w3_status(self) -> Dict:
        """获取 W3 泄漏哨兵状态"""
        if os.path.exists(self.w3_status_file):
            try:
                with open(self.w3_status_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                return {"error": str(e), "status": "unknown"}
        return {"status": "not_found"}

    def get_w4_status(self) -> Dict:
        """获取 W4 压力测试状态"""
        import glob

        w4_files = glob.glob("output/w4_stress_*.json")
        if w4_files:
            try:
                # 选择最新的文件
                latest_file = max(w4_files, key=os.path.getctime)
                with open(latest_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                return {"error": str(e), "status": "unknown"}
        return {"status": "not_found"}

    def get_system_resources(self) -> Dict:
        """获取系统资源使用情况"""
        try:
            # 获取 Python 进程
            python_processes = []
            for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
                try:
                    if "python" in proc.info["name"].lower():
                        python_processes.append(
                            {
                                "pid": proc.info["pid"],
                                "name": proc.info["name"],
                                "rss_mb": proc.info["memory_info"].rss / 1024 / 1024,
                                "cpu_percent": proc.info["cpu_percent"],
                            }
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            total_rss = sum(p["rss_mb"] for p in python_processes)

            return {
                "python_processes": python_processes,
                "total_rss_mb": total_rss,
                "system_memory": {
                    "total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                    "available_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024,
                    "percent_used": psutil.virtual_memory().percent,
                },
                "system_cpu_percent": psutil.cpu_percent(),
            }
        except Exception as e:
            return {"error": str(e)}

    def check_thresholds(self, w3_status: Dict, w4_status: Dict, resources: Dict) -> List[Dict]:
        """检查阈值并生成告警"""
        alerts = []

        # RSS 总量检查 (≤ 40MB)
        total_rss = resources.get("total_rss_mb", 0)
        if total_rss > 40:
            alerts.append(
                {
                    "severity": "critical",
                    "type": "memory",
                    "message": f"总 RSS {total_rss:.1f}MB 超过 40MB 阈值",
                    "value": total_rss,
                    "threshold": 40,
                }
            )
        elif total_rss > 30:
            alerts.append(
                {
                    "severity": "warning",
                    "type": "memory",
                    "message": f"总 RSS {total_rss:.1f}MB 接近 40MB 阈值",
                    "value": total_rss,
                    "threshold": 40,
                }
            )

        # W3 状态检查
        if w3_status.get("status") == "failed":
            alerts.append(
                {
                    "severity": "critical",
                    "type": "w3_failure",
                    "message": "W3 泄漏哨兵失败",
                    "details": w3_status.get("error", "Unknown error"),
                }
            )

        # W4 状态检查
        if w4_status.get("status") == "failed":
            alerts.append(
                {
                    "severity": "critical",
                    "type": "w4_failure",
                    "message": "W4 压力测试失败",
                    "details": w4_status.get("error", "Unknown error"),
                }
            )

        return alerts

    def generate_report(self) -> Dict:
        """生成综合报告"""
        w3_status = self.get_w3_status()
        w4_status = self.get_w4_status()
        resources = self.get_system_resources()
        alerts = self.check_thresholds(w3_status, w4_status, resources)

        # 计算运行时长
        runtime = datetime.now() - self.start_time

        return {
            "timestamp": datetime.now().isoformat(),
            "runtime_hours": runtime.total_seconds() / 3600,
            "tasks": {
                "w3_leak_sentinel": {
                    "status": w3_status.get("status", "unknown"),
                    "start_time": w3_status.get("start_time"),
                    "target_hours": w3_status.get("target_hours"),
                    "clean_hours": w3_status.get(
                        "final_clean_hours", w3_status.get("clean_hours_count", 0)
                    ),
                },
                "w4_stress_test": {
                    "status": w4_status.get("status", "unknown"),
                    "signals_processed": w4_status.get("signals_processed", 0),
                    "avg_latency_ms": w4_status.get("avg_latency_ms", 0),
                    "p95_latency_ms": w4_status.get("p95_latency_ms", 0),
                },
            },
            "resources": resources,
            "alerts": alerts,
            "validation": {
                "rss_under_40mb": resources.get("total_rss_mb", 0) <= 40,
                "w3_running": w3_status.get("status") in ["running", "completed"],
                "w4_running": w4_status.get("status") in ["running", "completed"],
                "no_critical_alerts": not any(a["severity"] == "critical" for a in alerts),
            },
        }

    def print_status(self, report: Dict):
        """打印状态信息"""
        print(f"\n🔄 W3+W4 并行监控状态 ({datetime.now().strftime('%H:%M:%S')})")
        print("=" * 60)

        # 运行时长
        runtime_hours = report["runtime_hours"]
        print(f"⏰ 总运行时长: {runtime_hours:.1f} 小时")

        # 任务状态
        w3 = report["tasks"]["w3_leak_sentinel"]
        w4 = report["tasks"]["w4_stress_test"]

        print(f"\n🔍 W3 泄漏哨兵:")
        print(f"   状态: {w3['status']}")
        print(f"   清洁小时: {w3['clean_hours']:.1f}/{w3.get('target_hours', 6)}")

        print(f"\n🔥 W4 压力测试:")
        print(f"   状态: {w4['status']}")
        print(f"   信号处理: {w4['signals_processed']:,}")
        print(f"   P95延迟: {w4['p95_latency_ms']:.2f}ms")

        # 资源使用
        resources = report["resources"]
        print(f"\n📊 资源使用:")
        print(f"   总 RSS: {resources['total_rss_mb']:.1f} MB")
        print(f"   系统内存: {resources['system_memory']['percent_used']:.1f}%")
        print(f"   系统 CPU: {resources['system_cpu_percent']:.1f}%")

        # 告警
        alerts = report["alerts"]
        if alerts:
            print(f"\n🚨 告警 ({len(alerts)}):")
            for alert in alerts:
                icon = "🔴" if alert["severity"] == "critical" else "🟡"
                print(f"   {icon} {alert['message']}")
        else:
            print(f"\n✅ 无告警")

        # 验收状态
        validation = report["validation"]
        print(f"\n🎯 验收状态:")
        print(f"   RSS ≤ 40MB: {'✅' if validation['rss_under_40mb'] else '❌'}")
        print(f"   W3 运行: {'✅' if validation['w3_running'] else '❌'}")
        print(f"   W4 运行: {'✅' if validation['w4_running'] else '❌'}")
        print(f"   无严重告警: {'✅' if validation['no_critical_alerts'] else '❌'}")

        print("=" * 60)

    def save_report(self, report: Dict, filename: str = None):
        """保存报告"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"output/w3_w4_parallel_report_{timestamp}.json"

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 报告已保存: {filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="W3+W4 并行任务监控")
    parser.add_argument("--interval", type=int, default=60, help="监控间隔秒数 (默认: 60)")
    parser.add_argument("--duration", type=int, default=0, help="监控时长秒数 (0=持续监控)")
    parser.add_argument(
        "--save-interval", type=int, default=3600, help="报告保存间隔秒数 (默认: 3600)"
    )
    parser.add_argument("--quiet", action="store_true", help="静默模式，只保存报告")

    args = parser.parse_args()

    monitor = ParallelTaskMonitor()

    print(f"🚀 开始 W3+W4 并行监控")
    print(f"📊 监控间隔: {args.interval}秒")
    if args.duration > 0:
        print(f"⏰ 监控时长: {args.duration}秒")
    else:
        print(f"⏰ 持续监控 (Ctrl-C 停止)")
    print(f"💾 报告保存间隔: {args.save_interval}秒")

    start_time = time.time()
    last_save = start_time

    try:
        while True:
            # 生成报告
            report = monitor.generate_report()

            # 显示状态
            if not args.quiet:
                monitor.print_status(report)

            # 定期保存报告
            current_time = time.time()
            if current_time - last_save >= args.save_interval:
                monitor.save_report(report)
                last_save = current_time

            # 检查是否达到监控时长
            if args.duration > 0 and (current_time - start_time) >= args.duration:
                print(f"\n⏰ 监控时长 {args.duration}秒 达到，结束监控")
                break

            # 等待下次检查
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n⏸️ 用户中断监控")

        # 保存最终报告
        final_report = monitor.generate_report()
        monitor.save_report(final_report, "output/w3_w4_parallel_final_report.json")

        print(f"📊 监控总时长: {(time.time() - start_time) / 3600:.1f} 小时")


if __name__ == "__main__":
    main()
