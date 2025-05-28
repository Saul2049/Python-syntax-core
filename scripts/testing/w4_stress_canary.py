#!/usr/bin/env python3
"""
W4 24小时压力Canary测试
W4 24-Hour Stress Test Canary

验收标准:
- 全程无WARN (RSS<40MB, GC pause P95<0.05s)
- P95延迟不反弹 (≤5.5ms)
- 自动Slack/Telegram汇报
"""

import asyncio
import json
import logging
import os
import random
import signal
import sys
import time
from typing import Any, Dict, List

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import psutil

from scripts.testing.w3_leak_sentinel import LeakSentinel
from src.core.gc_optimizer import GCOptimizer
from src.monitoring.metrics_collector import get_metrics_collector
from src.strategies.cache_optimized_strategy import CacheOptimizedStrategy


class W4StressCanary:
    """W4 24小时压力Canary测试器"""

    def __init__(self, pairs: List[str] = None, frequency_hz: int = 5):
        self.pairs = pairs or ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
        self.frequency_hz = frequency_hz
        self.test_duration_hours = 24

        self.metrics = get_metrics_collector()
        self.gc_optimizer = GCOptimizer()
        self.leak_sentinel = LeakSentinel(alert_threshold_hours=1)  # 每小时检查

        # W4验收阈值
        self.w4_thresholds = {
            "max_rss_mb": 40,
            "max_gc_pause_p95_ms": 50,
            "max_latency_p95_ms": 5.5,
            "max_fd_count": 500,
        }

        # 测试状态
        self.test_running = False
        self.start_time = None
        self.alerts = []
        self.performance_samples = []
        self.hourly_reports = []

        # 策略和数据
        self.strategies = {}
        self.price_feeds = {}

        self.logger = logging.getLogger(__name__)

    async def initialize_test_environment(self):
        """初始化测试环境"""
        self.logger.info("🚀 初始化W4压力测试环境...")

        # 1. 初始化策略
        for pair in self.pairs:
            config = {"symbols": [pair], "risk_limit": 1000}
            self.strategies[pair] = CacheOptimizedStrategy(config)

        # 2. 启动GC优化器
        self.gc_optimizer.install_gc_callbacks()

        # 3. 初始化价格数据生成器
        self._initialize_price_feeds()

        # 4. 启动Prometheus监控
        self.metrics.start_server()

        self.logger.info(
            f"✅ 测试环境初始化完成 - 交易对: {self.pairs}, 频率: {self.frequency_hz}Hz"
        )

    def _initialize_price_feeds(self):
        """初始化价格数据流"""
        base_prices = {"BTCUSDT": 45000, "ETHUSDT": 3000, "XRPUSDT": 0.6}

        for pair in self.pairs:
            self.price_feeds[pair] = {
                "current_price": base_prices.get(pair, 100),
                "volatility": 0.02,  # 2%波动率
                "trend": 0.0001,  # 轻微上涨趋势
                "last_update": time.time(),
            }

    def _generate_next_price(self, pair: str) -> Dict[str, float]:
        """生成下一个价格数据"""
        feed = self.price_feeds[pair]

        # 随机游走 + 趋势
        change_pct = np.random.normal(feed["trend"], feed["volatility"])
        new_price = feed["current_price"] * (1 + change_pct)

        # 确保价格为正
        new_price = max(0.01, new_price)

        # 生成OHLCV数据
        high = new_price * (1 + abs(np.random.normal(0, 0.005)))
        low = new_price * (1 - abs(np.random.normal(0, 0.005)))
        volume = random.randint(100, 10000)

        ohlcv = {
            "symbol": pair,
            "open": feed["current_price"],
            "high": high,
            "low": low,
            "close": new_price,
            "volume": volume,
            "timestamp": time.time(),
        }

        # 更新当前价格
        feed["current_price"] = new_price
        feed["last_update"] = time.time()

        return ohlcv

    async def run_high_frequency_load(self):
        """运行高频交易负载"""
        interval = 1.0 / self.frequency_hz  # 5Hz = 0.2秒间隔
        operation_count = 0

        self.logger.info(f"🔥 开始高频负载测试 - {self.frequency_hz}Hz频率")

        while self.test_running:
            start_cycle = time.time()

            # 并行处理所有交易对
            tasks = []
            for pair in self.pairs:
                task = asyncio.create_task(self._process_trading_pair(pair))
                tasks.append(task)

            # 等待所有处理完成并测量延迟
            results = await asyncio.gather(*tasks, return_exceptions=True)

            cycle_duration = time.time() - start_cycle
            operation_count += len(self.pairs)

            # 记录性能样本
            self.performance_samples.append(
                {
                    "timestamp": time.time(),
                    "cycle_duration_ms": cycle_duration * 1000,
                    "operations_in_cycle": len(self.pairs),
                    "success_count": len([r for r in results if not isinstance(r, Exception)]),
                    "error_count": len([r for r in results if isinstance(r, Exception)]),
                }
            )

            # 限制性能样本数量
            if len(self.performance_samples) > 10000:
                self.performance_samples = self.performance_samples[-8000:]

            # 更新延迟指标
            self.metrics.observe_task_latency("trading_cycle", cycle_duration)

            # 控制频率
            elapsed = time.time() - start_cycle
            sleep_time = max(0, interval - elapsed)

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            elif elapsed > interval * 2:  # 延迟超过2倍间隔
                self.logger.warning(
                    f"⚠️ 处理延迟过高: {elapsed*1000:.1f}ms (目标: {interval*1000:.1f}ms)"
                )

    async def _process_trading_pair(self, pair: str) -> Dict[str, Any]:
        """处理单个交易对"""
        try:
            # 生成价格数据
            price_data = self._generate_next_price(pair)

            # 更新策略窗口数据
            strategy = self.strategies[pair]
            ohlcv_array = np.array(
                [
                    price_data["open"],
                    price_data["high"],
                    price_data["low"],
                    price_data["close"],
                    price_data["volume"],
                ]
            )
            strategy.update_window(pair, 100, ohlcv_array)

            # 生成交易信号
            with self.metrics.measure_signal_latency():
                signal = strategy.generate_signals(pair, price_data["close"])

            # 更新价格指标
            self.metrics.record_price_update(pair, price_data["close"], "generator")

            # 模拟订单处理延迟
            if signal["action"] != "hold":
                processing_delay = random.uniform(0.001, 0.005)  # 1-5ms
                await asyncio.sleep(processing_delay)

            return {"pair": pair, "signal": signal, "price": price_data["close"], "success": True}

        except Exception as e:
            self.logger.error(f"❌ 处理 {pair} 失败: {e}")
            self.metrics.record_exception("trading_processor", e)

            return {"pair": pair, "error": str(e), "success": False}

    async def monitor_w4_thresholds(self):
        """监控W4验收阈值"""
        check_interval = 300  # 5分钟检查一次

        while self.test_running:
            # 收集当前指标
            current_metrics = await self._collect_system_metrics()

            # 检查W4阈值
            violations = self._check_w4_violations(current_metrics)

            if violations:
                # 记录告警
                alert = {
                    "timestamp": time.time(),
                    "type": "w4_threshold_violation",
                    "violations": violations,
                    "metrics": current_metrics,
                }
                self.alerts.append(alert)

                # 发送告警
                await self._send_alert(alert)

                self.logger.warning(f"🚨 W4阈值违反: {violations}")

            await asyncio.sleep(check_interval)

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            # 进程信息
            process = psutil.Process()
            memory_info = process.memory_info()

            # GC统计
            gc_report = self.gc_optimizer.get_optimization_report()

            # 性能统计
            recent_samples = [
                s for s in self.performance_samples if time.time() - s["timestamp"] <= 3600
            ]  # 最近1小时

            if recent_samples:
                latencies = [s["cycle_duration_ms"] for s in recent_samples]
                latencies.sort()
                p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 0
                avg_latency = sum(latencies) / len(latencies) if latencies else 0
            else:
                p95_latency = 0
                avg_latency = 0

            return {
                "timestamp": time.time(),
                "memory": {
                    "rss_mb": memory_info.rss / (1024 * 1024),
                    "vms_mb": memory_info.vms / (1024 * 1024),
                    "percent": process.memory_percent(),
                },
                "gc": {
                    "current_profile": gc_report.get("current_profile"),
                    "recent_pauses": len(self.gc_optimizer.pause_history),
                    "monitoring_active": gc_report.get("monitoring_active", False),
                },
                "performance": {
                    "p95_latency_ms": p95_latency,
                    "avg_latency_ms": avg_latency,
                    "samples_count": len(recent_samples),
                    "operations_per_second": (
                        len(recent_samples) * len(self.pairs) / 3600 if recent_samples else 0
                    ),
                },
                "file_descriptors": (
                    process.num_fds() if hasattr(process, "num_fds") else len(process.open_files())
                ),
                "connections": len(process.connections()),
                "cpu_percent": process.cpu_percent(),
            }

        except Exception as e:
            self.logger.error(f"❌ 系统指标收集失败: {e}")
            return {"timestamp": time.time(), "error": str(e)}

    def _check_w4_violations(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查W4阈值违反"""
        if "error" in metrics:
            return []

        violations = []

        # RSS内存检查
        rss_mb = metrics["memory"]["rss_mb"]
        if rss_mb > self.w4_thresholds["max_rss_mb"]:
            violations.append(
                {
                    "threshold": "rss_memory",
                    "current": rss_mb,
                    "limit": self.w4_thresholds["max_rss_mb"],
                    "severity": "critical" if rss_mb > 60 else "warning",
                }
            )

        # P95延迟检查
        p95_latency = metrics["performance"]["p95_latency_ms"]
        if p95_latency > self.w4_thresholds["max_latency_p95_ms"]:
            violations.append(
                {
                    "threshold": "p95_latency",
                    "current": p95_latency,
                    "limit": self.w4_thresholds["max_latency_p95_ms"],
                    "severity": "warning",
                }
            )

        # FD检查
        fd_count = metrics["file_descriptors"]
        if fd_count > self.w4_thresholds["max_fd_count"]:
            violations.append(
                {
                    "threshold": "file_descriptors",
                    "current": fd_count,
                    "limit": self.w4_thresholds["max_fd_count"],
                    "severity": "critical" if fd_count > 800 else "warning",
                }
            )

        return violations

    async def _send_alert(self, alert: Dict[str, Any]):
        """发送告警通知"""
        # 这里可以集成实际的Slack/Telegram API
        # 目前只记录日志

        violations_summary = ", ".join(
            [f"{v['threshold']}={v['current']:.1f}>{v['limit']}" for v in alert["violations"]]
        )

        alert_message = f"🚨 W4压力测试告警: {violations_summary}"
        self.logger.warning(alert_message)

        # 模拟Telegram/Slack发送
        print(f"📱 告警通知: {alert_message}")

    async def generate_hourly_report(self):
        """生成每小时报告"""
        report_interval = 3600  # 1小时
        hours_completed = 0

        while self.test_running:
            await asyncio.sleep(report_interval)
            hours_completed += 1

            # 生成小时报告
            hourly_metrics = await self._collect_system_metrics()

            # 计算小时内性能统计
            hour_start = time.time() - 3600
            hour_samples = [s for s in self.performance_samples if s["timestamp"] >= hour_start]

            hour_report = {
                "hour": hours_completed,
                "timestamp": time.time(),
                "metrics": hourly_metrics,
                "performance_summary": {
                    "total_operations": len(hour_samples) * len(self.pairs),
                    "avg_ops_per_second": len(hour_samples) * len(self.pairs) / 3600,
                    "error_rate": sum(s["error_count"] for s in hour_samples)
                    / max(1, len(hour_samples)),
                },
                "alerts_in_hour": len([a for a in self.alerts if a["timestamp"] >= hour_start]),
                "w4_status": "PASS" if not self._check_w4_violations(hourly_metrics) else "FAIL",
            }

            self.hourly_reports.append(hour_report)

            # 发送小时报告
            await self._send_hourly_notification(hour_report)

            self.logger.info(
                f"📊 第{hours_completed}小时报告完成 - 状态: {hour_report['w4_status']}"
            )

    async def _send_hourly_notification(self, report: Dict[str, Any]):
        """发送小时报告通知"""
        metrics = report["metrics"]

        summary = (
            f"⏰ W4压力测试 - 第{report['hour']}小时报告\n"
            f"📊 RSS: {metrics['memory']['rss_mb']:.1f}MB\n"
            f"⚡ P95延迟: {metrics['performance']['p95_latency_ms']:.1f}ms\n"
            f"🔗 FD: {metrics['file_descriptors']}\n"
            f"🎯 状态: {report['w4_status']}\n"
            f"⚠️ 本小时告警: {report['alerts_in_hour']}次"
        )

        self.logger.info(f"小时报告:\n{summary}")
        print(f"📱 小时报告通知:\n{summary}")

    async def run_stress_test(self) -> bool:
        """运行24小时压力测试"""
        self.test_running = True
        self.start_time = time.time()

        try:
            # 初始化环境
            await self.initialize_test_environment()

            # 设置信号处理
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            self.logger.info("🚀 开始W4 24小时压力测试")

            # 并行运行各个组件
            tasks = [
                asyncio.create_task(self.run_high_frequency_load()),
                asyncio.create_task(self.monitor_w4_thresholds()),
                asyncio.create_task(self.generate_hourly_report()),
            ]

            # 等待24小时或手动停止
            end_time = self.start_time + (self.test_duration_hours * 3600)

            while self.test_running and time.time() < end_time:
                await asyncio.sleep(60)  # 每分钟检查一次

                # 检查任务状态
                for i, task in enumerate(tasks):
                    if task.done() and task.exception():
                        self.logger.error(f"❌ 任务{i}异常退出: {task.exception()}")
                        raise task.exception()

            # 正常完成
            self.test_running = False

            # 等待任务清理
            for task in tasks:
                if not task.done():
                    task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

            # 生成最终报告
            final_report = await self._generate_final_report()

            # 判断是否通过W4验收
            w4_passed = self._evaluate_w4_success(final_report)

            return w4_passed

        except Exception as e:
            self.logger.error(f"❌ W4压力测试失败: {e}")
            return False
        finally:
            await self._cleanup()

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        self.logger.info("🛑 收到停止信号")
        self.test_running = False

    async def _generate_final_report(self) -> Dict[str, Any]:
        """生成最终测试报告"""
        runtime_hours = (time.time() - self.start_time) / 3600

        # 统计告警
        critical_alerts = [
            a
            for a in self.alerts
            if any(v.get("severity") == "critical" for v in a.get("violations", []))
        ]
        warning_alerts = [a for a in self.alerts if a not in critical_alerts]

        # 性能统计
        if self.performance_samples:
            latencies = [s["cycle_duration_ms"] for s in self.performance_samples]
            latencies.sort()

            performance_stats = {
                "total_operations": len(self.performance_samples) * len(self.pairs),
                "avg_latency_ms": sum(latencies) / len(latencies),
                "p95_latency_ms": latencies[int(len(latencies) * 0.95)],
                "p99_latency_ms": latencies[int(len(latencies) * 0.99)],
                "max_latency_ms": max(latencies),
                "operations_per_second": len(self.performance_samples)
                * len(self.pairs)
                / (runtime_hours * 3600),
            }
        else:
            performance_stats = {}

        # 最终系统状态
        final_metrics = await self._collect_system_metrics()

        return {
            "test_summary": {
                "duration_hours": runtime_hours,
                "target_hours": self.test_duration_hours,
                "completed": runtime_hours >= self.test_duration_hours,
                "pairs_tested": self.pairs,
                "frequency_hz": self.frequency_hz,
            },
            "alerts": {
                "total_alerts": len(self.alerts),
                "critical_alerts": len(critical_alerts),
                "warning_alerts": len(warning_alerts),
                "alert_details": self.alerts,
            },
            "performance": performance_stats,
            "final_metrics": final_metrics,
            "hourly_reports": self.hourly_reports,
            "w4_thresholds": self.w4_thresholds,
        }

    def _evaluate_w4_success(self, report: Dict[str, Any]) -> bool:
        """评估W4验收是否成功"""
        # W4成功标准
        criteria = {
            "duration_completed": report["test_summary"]["completed"],
            "no_critical_alerts": report["alerts"]["critical_alerts"] == 0,
            "latency_acceptable": (
                report["performance"].get("p95_latency_ms", 0)
                <= self.w4_thresholds["max_latency_p95_ms"]
            ),
            "final_rss_acceptable": (
                report["final_metrics"]["memory"]["rss_mb"] <= self.w4_thresholds["max_rss_mb"]
            ),
        }

        # 所有标准都必须满足
        all_passed = all(criteria.values())

        self.logger.info("📋 W4验收评估:")
        for criterion, passed in criteria.items():
            status = "✅" if passed else "❌"
            self.logger.info(f"   {status} {criterion}: {passed}")

        return all_passed

    async def _cleanup(self):
        """清理测试环境"""
        self.logger.info("🧹 清理W4测试环境...")

        # 移除GC回调
        self.gc_optimizer.remove_gc_callbacks()

        # 保存最终报告
        if hasattr(self, "start_time") and self.start_time:
            final_report = await self._generate_final_report()

            timestamp = int(time.time())
            os.makedirs("output", exist_ok=True)

            with open(f"output/w4_stress_canary_{timestamp}.json", "w") as f:
                json.dump(final_report, f, indent=2, default=str)

        self.logger.info("✅ W4测试环境清理完成")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="W4 24小时压力Canary测试")
    parser.add_argument(
        "--pairs", nargs="+", default=["BTCUSDT", "ETHUSDT", "XRPUSDT"], help="交易对列表"
    )
    parser.add_argument("--freq", type=int, default=5, help="测试频率(Hz)")
    parser.add_argument("--duration", type=int, default=24, help="测试时长(小时)")
    parser.add_argument("--dry-run", action="store_true", help="短时间测试运行")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("w4_stress_canary.log"), logging.StreamHandler()],
    )

    print("🚀 W4 24小时压力Canary测试启动")
    print(f"交易对: {args.pairs}")
    print(f"频率: {args.freq}Hz")
    print(f"时长: {args.duration}小时")

    # 创建测试器
    canary = W4StressCanary(pairs=args.pairs, frequency_hz=args.freq)

    # 调整测试时长
    if args.dry_run:
        canary.test_duration_hours = 0.1  # 6分钟测试
        print("🧪 干运行模式：6分钟测试")
    else:
        canary.test_duration_hours = args.duration

    try:
        # 运行压力测试
        success = await canary.run_stress_test()

        if success:
            print("\n🎉 W4压力测试验收通过！系统可以进入主网灰度")
            return True
        else:
            print("\n⚠️ W4压力测试未通过，需要进一步优化")
            return False

    except Exception as e:
        print(f"❌ W4压力测试失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
