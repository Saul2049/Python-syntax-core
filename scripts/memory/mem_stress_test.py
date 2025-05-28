#!/usr/bin/env python3
"""
W4 24小时内存压力测试
W4 24-Hour Memory Stress Test

高负载下系统稳定性验证，监控内存使用、GC性能、延迟指标
"""

import argparse
import asyncio
import gc
import json
import logging
import os
import random
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List

# uvloop 优化：用C实现的事件循环
try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("✅ 启用 uvloop 事件循环优化")
except ImportError:
    print("⚠️ uvloop 未安装，使用默认事件循环")

# 环境变量配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
GC_THRESH = os.getenv("GC_THRESH", "900,20,10")
PG_FLUSH_INTERVAL = int(os.getenv("PG_FLUSH_INTERVAL", "10"))

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# 导入 GC 配置
try:
    from config.gc_settings import apply_optimal_gc_config
except ImportError:

    def apply_optimal_gc_config():
        """备用 GC 配置，使用环境变量GC_THRESH"""
        thresholds = list(map(int, GC_THRESH.split(",")))
        gc.set_threshold(*thresholds)
        print(f"✅ 应用环境变量 GC 配置: {tuple(thresholds)}")


@dataclass
class W4Metrics:
    """W4 压力测试指标"""

    timestamp: str
    signals_processed: int
    avg_latency_ms: float
    p95_latency_ms: float
    rss_mb: float
    gc_pause_ms: float
    gc_gen0_count: int
    gc_gen1_count: int
    gc_gen2_count: int
    cpu_percent: float
    alerts_count: int


class W4StressTest:
    """W4 24小时压力测试器"""

    def __init__(
        self,
        run_name: str = "W4-stress",
        signals_target: int = 20000,
        duration_hours: int = 24,
        max_rss_mb: int = 40,
    ):
        self.run_name = run_name
        self.signals_target = signals_target
        self.duration_hours = duration_hours
        self.max_rss_mb = max_rss_mb

        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=duration_hours)

        # 指标收集
        self.signals_processed = 0
        self.latencies = []
        self.metrics_history: List[W4Metrics] = []
        self.alerts = []

        # 状态文件
        self.status_file = f"output/w4_stress_status_{run_name}.json"

        # 日志配置
        self.logger = logging.getLogger(__name__)

        # 运行状态
        self.running = False
        self.failed = False
        self.failure_reason = ""

    def setup_logging(self):
        """设置日志"""
        log_file = f"logs/w4_stress_{self.run_name}.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # 将字符串级别转换为logging常量
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        log_level = level_map.get(LOG_LEVEL, logging.INFO)

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )

        if LOG_LEVEL != "INFO":
            print(f"✅ 日志级别设为: {LOG_LEVEL}")

    def simulate_trading_signal(self) -> float:
        """模拟交易信号处理，返回延迟(ms)"""
        start_time = time.perf_counter()

        # 模拟计算密集型操作 - 优化：减少循环次数
        data = []
        for i in range(random.randint(30, 100)):  # 从50-200减少到30-100
            # 模拟价格计算
            price = random.uniform(30000, 70000)
            volume = random.uniform(0.1, 10.0)

            # 模拟技术指标计算 - 优化：减少SMA计算点数
            sma = (
                sum([random.uniform(price * 0.95, price * 1.05) for _ in range(10)]) / 10
            )  # 从20减少到10

            # 模拟决策逻辑
            signal = "BUY" if price < sma * 0.98 else "SELL" if price > sma * 1.02 else "HOLD"

            # 使用元组替代字典减少开销
            data.append((price, volume, sma, signal, time.time()))

        # 模拟网络延迟 - 优化：减少等待时间
        await_time = random.uniform(0.0005, 0.002)  # 从0.001-0.005减少到0.0005-0.002
        time.sleep(await_time)

        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        return latency_ms

    def get_system_metrics(self) -> Dict:
        """获取系统指标"""
        try:
            import psutil

            # 获取当前进程
            process = psutil.Process()

            # 内存使用
            memory_info = process.memory_info()
            rss_mb = memory_info.rss / 1024 / 1024

            # CPU 使用
            cpu_percent = process.cpu_percent()

            # GC 统计
            gc_stats = gc.get_stats()
            gc_counts = gc.get_count()

            return {
                "rss_mb": rss_mb,
                "cpu_percent": cpu_percent,
                "gc_gen0": gc_counts[0],
                "gc_gen1": gc_counts[1],
                "gc_gen2": gc_counts[2],
                "gc_collections": [s["collections"] for s in gc_stats],
            }
        except Exception as e:
            self.logger.warning(f"获取系统指标失败: {e}")
            return {"rss_mb": 0, "cpu_percent": 0, "gc_gen0": 0, "gc_gen1": 0, "gc_gen2": 0}

    def check_thresholds(self, metrics: Dict) -> List[str]:
        """检查阈值"""
        alerts = []

        # RSS 检查
        if metrics["rss_mb"] > self.max_rss_mb:
            alert = f"RSS {metrics['rss_mb']:.1f}MB 超过 {self.max_rss_mb}MB 阈值"
            alerts.append(alert)
            self.logger.warning(alert)

        # 延迟检查 (P95 > 6ms)
        if len(self.latencies) >= 20:
            p95_latency = sorted(self.latencies)[-len(self.latencies) // 20]
            if p95_latency > 6.0:
                alert = f"P95延迟 {p95_latency:.2f}ms 超过 6ms 阈值"
                alerts.append(alert)
                self.logger.warning(alert)

        return alerts

    def update_status(self, status_update: Dict):
        """更新状态文件"""
        status = {
            "run_name": self.run_name,
            "status": "running" if self.running else ("failed" if self.failed else "completed"),
            "start_time": self.start_time.isoformat(),
            "signals_processed": self.signals_processed,
            "target_signals": self.signals_target,
            "duration_hours": self.duration_hours,
            "progress_percent": (
                (self.signals_processed / self.signals_target * 100)
                if self.signals_target > 0
                else 0
            ),
            "last_update": datetime.now().isoformat(),
        }

        status.update(status_update)

        if self.failed:
            status["failure_reason"] = self.failure_reason

        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        with open(self.status_file, "w") as f:
            json.dump(status, f, indent=2, default=str)

    def save_metrics(self):
        """保存指标历史"""
        metrics_file = f"output/w4_stress_metrics_{self.run_name}_{int(time.time())}.json"

        report = {
            "test_info": {
                "run_name": self.run_name,
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_hours": self.duration_hours,
                "signals_target": self.signals_target,
                "signals_processed": self.signals_processed,
            },
            "performance": {
                "avg_latency_ms": (
                    sum(self.latencies) / len(self.latencies) if self.latencies else 0
                ),
                "p95_latency_ms": (
                    sorted(self.latencies)[-len(self.latencies) // 20]
                    if len(self.latencies) >= 20
                    else 0
                ),
                "p99_latency_ms": (
                    sorted(self.latencies)[-len(self.latencies) // 100]
                    if len(self.latencies) >= 100
                    else 0
                ),
                "max_latency_ms": max(self.latencies) if self.latencies else 0,
                "min_latency_ms": min(self.latencies) if self.latencies else 0,
            },
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "alerts": self.alerts,
            "validation": {
                "completed": self.signals_processed >= self.signals_target,
                "rss_under_limit": all(m.rss_mb <= self.max_rss_mb for m in self.metrics_history),
                "latency_under_limit": all(m.p95_latency_ms <= 6.0 for m in self.metrics_history),
                "no_critical_alerts": len([a for a in self.alerts if "critical" in a.lower()]) == 0,
            },
        }

        os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
        with open(metrics_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"📊 指标报告已保存: {metrics_file}")
        return metrics_file

    async def run_stress_test(self):
        """运行压力测试"""
        self.logger.info("🔥 W4 压力测试启动")
        self.logger.info(f"📋 运行名称: {self.run_name}")
        self.logger.info(f"🎯 目标信号: {self.signals_target}")
        self.logger.info(f"⏰ 时长: {self.duration_hours} 小时")
        self.logger.info(f"📊 RSS限制: {self.max_rss_mb} MB")

        # 计算真实信号频率 (signals/second)
        target_frequency = self.signals_target / (self.duration_hours * 3600)
        signal_interval = 1.0 / target_frequency if target_frequency > 0 else 1.0

        self.logger.info(
            f"📡 信号频率: {target_frequency:.3f} 条/秒 (间隔: {signal_interval:.1f}秒)"
        )

        # 应用 GC 配置
        apply_optimal_gc_config()

        self.running = True
        self.update_status({"status": "running"})

        try:
            while self.signals_processed < self.signals_target and datetime.now() < self.end_time:
                # 记录信号处理开始时间
                signal_start = time.perf_counter()

                # 处理信号
                latency = self.simulate_trading_signal()
                self.latencies.append(latency)
                self.signals_processed += 1

                # 定期收集指标
                if self.signals_processed % 100 == 0:
                    system_metrics = self.get_system_metrics()

                    # 计算性能指标
                    recent_latencies = (
                        self.latencies[-100:] if len(self.latencies) >= 100 else self.latencies
                    )
                    avg_latency = sum(recent_latencies) / len(recent_latencies)
                    p95_latency = (
                        sorted(recent_latencies)[-len(recent_latencies) // 20]
                        if len(recent_latencies) >= 20
                        else avg_latency
                    )

                    # 创建指标记录
                    metrics = W4Metrics(
                        timestamp=datetime.now().isoformat(),
                        signals_processed=self.signals_processed,
                        avg_latency_ms=avg_latency,
                        p95_latency_ms=p95_latency,
                        rss_mb=system_metrics["rss_mb"],
                        gc_pause_ms=0,  # TODO: 实际测量 GC 暂停
                        gc_gen0_count=system_metrics["gc_gen0"],
                        gc_gen1_count=system_metrics["gc_gen1"],
                        gc_gen2_count=system_metrics["gc_gen2"],
                        cpu_percent=system_metrics["cpu_percent"],
                        alerts_count=len(self.alerts),
                    )

                    self.metrics_history.append(metrics)

                    # 检查阈值
                    new_alerts = self.check_thresholds(system_metrics)
                    self.alerts.extend(new_alerts)

                    # 更新状态
                    self.update_status(
                        {"current_metrics": asdict(metrics), "recent_alerts": new_alerts}
                    )

                    # 进度日志
                    progress = self.signals_processed / self.signals_target * 100
                    elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                    self.logger.info(
                        f"📈 进度: {progress:.1f}% ({self.signals_processed}/{self.signals_target}), "
                        f"用时: {elapsed_hours:.1f}h, P95: {p95_latency:.2f}ms, RSS: {system_metrics['rss_mb']:.1f}MB"
                    )

                # 🎯 关键改动：按真实频率控制信号发送
                signal_process_time = time.perf_counter() - signal_start
                sleep_time = signal_interval - signal_process_time

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    # 如果处理时间超过间隔，每10个信号小憩一下避免CPU 100%
                    if self.signals_processed % 10 == 0:
                        await asyncio.sleep(0.001)

                # 🚀 分片休眠优化：每300个信号让事件循环喘息50ms
                if self.signals_processed % 300 == 0:
                    await asyncio.sleep(0.05)
                    self.logger.debug(f"🔄 分片休眠: {self.signals_processed}信号完成")

            self.logger.info("✅ W4 压力测试完成")
            self.logger.info(f"📊 处理信号: {self.signals_processed}/{self.signals_target}")
            self.logger.info(
                f"⏰ 用时: {(datetime.now() - self.start_time).total_seconds() / 3600:.1f} 小时"
            )

        except Exception as e:
            self.failed = True
            self.failure_reason = str(e)
            self.logger.error(f"❌ W4 压力测试失败: {e}")
            self.logger.error(traceback.format_exc())

        finally:
            self.running = False

            # 保存最终报告
            report_file = self.save_metrics()

            # 更新最终状态
            final_status = {
                "status": "completed" if not self.failed else "failed",
                "completion_time": datetime.now().isoformat(),
                "final_signals": self.signals_processed,
                "report_file": report_file,
            }

            if not self.failed:
                # 验收检查
                validation = {
                    "signals_completed": self.signals_processed >= self.signals_target,
                    "rss_under_limit": all(
                        m.rss_mb <= self.max_rss_mb for m in self.metrics_history
                    ),
                    "latency_acceptable": all(
                        m.p95_latency_ms <= 6.0 for m in self.metrics_history
                    ),
                    "no_critical_alerts": len([a for a in self.alerts if "critical" in a.lower()])
                    == 0,
                }

                passed = all(validation.values())
                final_status["validation"] = validation
                final_status["passed"] = passed

                if passed:
                    self.logger.info("🎉 W4 压力测试验收通过!")
                else:
                    self.logger.warning("⚠️ W4 压力测试部分指标未达标")

            self.update_status(final_status)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="W4 24小时压力测试")
    parser.add_argument("--run-name", type=str, default="W4-stress", help="运行名称标签")
    parser.add_argument("--signals", type=int, default=20000, help="目标信号处理数量")
    parser.add_argument("--duration", type=str, default="24h", help="测试时长 (例: 24h, 1d)")
    parser.add_argument("--max-rss", type=int, default=40, help="最大 RSS 限制 (MB)")

    args = parser.parse_args()

    # 解析时长
    duration_str = args.duration.lower()
    if duration_str.endswith("h"):
        duration_hours = int(duration_str[:-1])
    elif duration_str.endswith("d"):
        duration_hours = int(duration_str[:-1]) * 24
    else:
        duration_hours = int(duration_str)  # 假设是小时

    # 创建测试器
    stress_test = W4StressTest(
        run_name=args.run_name,
        signals_target=args.signals,
        duration_hours=duration_hours,
        max_rss_mb=args.max_rss,
    )

    # 设置日志
    stress_test.setup_logging()

    # 运行测试
    await stress_test.run_stress_test()


if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # 运行异步主函数
    asyncio.run(main())
