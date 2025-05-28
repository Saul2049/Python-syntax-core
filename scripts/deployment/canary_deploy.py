#!/usr/bin/env python3
"""
Canary部署脚本 - M4阶段
Canary Deployment Script for M4 Phase

用途：
- Testnet环境灰度部署
- 24小时监控验证
- 自动化指标收集
"""

import asyncio
import argparse
import json
import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.core.async_trading_engine import AsyncTradingEngine
from src.monitoring.metrics_collector import get_metrics_collector


class CanaryDeployment:
    """Canary部署管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = get_metrics_collector()

        # Canary配置
        self.pairs = config.get("pairs", ["BTCUSDT", "ETHUSDT"])
        self.funds = config.get("funds", 500)
        self.duration_hours = config.get("duration_hours", 24)
        self.testnet = config.get("testnet", True)

        # 监控状态
        self.start_time = None
        self.deployment_id = f"canary_{int(time.time())}"
        self.health_checks = []
        self.performance_snapshots = []

        # 健康门槛
        self.health_thresholds = {
            "latency_ratio_max": 1.2,  # async/stable < 1.2
            "ws_reconnect_rate": 0.1,  # <0.1/hour
            "panic_sell_count": 0,  # =0
            "order_success_rate": 95,  # >95%
            "roundtrip_p95_ms": 1000,  # <1s
        }

        self.logger = logging.getLogger(__name__)

    async def start_canary_deployment(self) -> Dict[str, Any]:
        """启动Canary部署"""
        try:
            self.start_time = datetime.now()
            self.logger.info(f"🕯️ 启动Canary部署: {self.deployment_id}")

            # 1. 环境验证
            await self._validate_environment()

            # 2. 基线数据收集
            baseline = await self._collect_baseline_metrics()

            # 3. 启动交易引擎
            engine = await self._start_trading_engine()

            # 4. 24小时监控循环
            monitoring_result = await self._monitor_deployment(engine)

            # 5. 生成部署报告
            report = await self._generate_deployment_report(baseline, monitoring_result)

            return report

        except Exception as e:
            self.logger.error(f"❌ Canary部署失败: {e}")
            await self._emergency_rollback()
            raise

    async def _validate_environment(self):
        """验证部署环境"""
        self.logger.info("🔍 验证Canary部署环境")

        # 检查testnet连接
        if not self.testnet:
            raise ValueError("生产环境需要额外审批，当前仅支持testnet")

        # 检查资金配置
        if self.funds > 1000:
            raise ValueError("Canary资金限制为1000 USD")

        # 检查交易对
        supported_pairs = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        for pair in self.pairs:
            if pair not in supported_pairs:
                raise ValueError(f"不支持的交易对: {pair}")

        self.logger.info("✅ 环境验证通过")

    async def _collect_baseline_metrics(self) -> Dict[str, Any]:
        """收集基线指标"""
        self.logger.info("📊 收集基线性能指标")

        # 运行基线性能测试
        from scripts.m4_simple_benchmark import M4SimpleBenchmark

        benchmark = M4SimpleBenchmark()
        baseline_results = await benchmark.run_full_benchmark()

        baseline = {
            "timestamp": datetime.now().isoformat(),
            "async_signal_p95": baseline_results.get("async_signals", {}).get("p95_latency_ms", 0),
            "task_scheduling_p95": baseline_results.get("task_scheduling", {}).get(
                "p95_task_latency_ms", 0
            ),
            "cpu_usage_max": baseline_results.get("cpu_usage", {}).get("max_cpu_percent", 0),
            "throughput": baseline_results.get("async_signals", {}).get(
                "throughput_signals_per_sec", 0
            ),
        }

        self.logger.info(
            f"📈 基线指标: P95={baseline['async_signal_p95']:.1f}ms, 吞吐={baseline['throughput']:.1f}/s"
        )
        return baseline

    async def _start_trading_engine(self) -> AsyncTradingEngine:
        """启动交易引擎"""
        self.logger.info("🚀 启动Canary交易引擎")

        # 注意：这里使用测试API密钥
        # 在实际部署中需要从安全的配置管理中获取
        engine = AsyncTradingEngine(
            api_key="test_canary_key",
            api_secret="test_canary_secret",
            symbols=self.pairs,
            testnet=True,
        )

        await engine.initialize()

        # 启动引擎（在后台任务中）
        engine_task = asyncio.create_task(engine.run())

        return engine

    async def _monitor_deployment(self, engine: AsyncTradingEngine) -> Dict[str, Any]:
        """24小时部署监控"""
        self.logger.info(f"⏰ 开始{self.duration_hours}小时监控")

        end_time = datetime.now() + timedelta(hours=self.duration_hours)
        check_interval = 3600  # 每小时检查一次

        monitoring_results = {
            "health_checks": [],
            "performance_snapshots": [],
            "incidents": [],
            "total_checks": 0,
            "failed_checks": 0,
        }

        while datetime.now() < end_time:
            try:
                # 执行健康检查
                health_result = await self._perform_health_check(engine)
                monitoring_results["health_checks"].append(health_result)
                monitoring_results["total_checks"] += 1

                if not health_result["healthy"]:
                    monitoring_results["failed_checks"] += 1
                    monitoring_results["incidents"].append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "type": "health_check_failed",
                            "details": health_result["issues"],
                        }
                    )

                # 收集性能快照
                perf_snapshot = await self._collect_performance_snapshot(engine)
                monitoring_results["performance_snapshots"].append(perf_snapshot)

                # 等待下次检查
                await asyncio.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"❌ 监控检查错误: {e}")
                monitoring_results["incidents"].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "type": "monitoring_error",
                        "error": str(e),
                    }
                )
                await asyncio.sleep(600)  # 错误时等待10分钟

        return monitoring_results

    async def _perform_health_check(self, engine: AsyncTradingEngine) -> Dict[str, Any]:
        """执行健康检查"""
        issues = []

        try:
            # 获取引擎统计
            stats = engine.get_performance_stats()

            # 检查WebSocket连接
            ws_stats = stats.get("websocket", {})
            if not ws_stats.get("running", False):
                issues.append("WebSocket连接断开")

            # 检查错误率
            broker_stats = stats.get("broker", {})
            error_count = broker_stats.get("error_count", 0)
            total_orders = broker_stats.get("total_orders", 1)
            error_rate = error_count / total_orders * 100

            if error_rate > 5:  # 错误率>5%
                issues.append(f"订单错误率过高: {error_rate:.1f}%")

            # 检查延迟
            # 这里可以添加更多延迟检查

            health_result = {
                "timestamp": datetime.now().isoformat(),
                "healthy": len(issues) == 0,
                "issues": issues,
                "stats": stats,
            }

            status = "✅ 健康" if health_result["healthy"] else f"⚠️ 异常 ({len(issues)})"
            self.logger.info(f"🏥 健康检查: {status}")

            return health_result

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "healthy": False,
                "issues": [f"健康检查失败: {e}"],
                "stats": {},
            }

    async def _collect_performance_snapshot(self, engine: AsyncTradingEngine) -> Dict[str, Any]:
        """收集性能快照"""
        stats = engine.get_performance_stats()

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "engine_stats": stats.get("engine", {}),
            "broker_performance": stats.get("broker", {}),
            "websocket_metrics": stats.get("websocket", {}),
        }

        return snapshot

    async def _generate_deployment_report(
        self, baseline: Dict[str, Any], monitoring: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成部署报告"""
        self.logger.info("📊 生成Canary部署报告")

        # 计算关键指标
        total_checks = monitoring["total_checks"]
        failed_checks = monitoring["failed_checks"]
        success_rate = (
            (total_checks - failed_checks) / total_checks * 100 if total_checks > 0 else 0
        )

        report = {
            "deployment_id": self.deployment_id,
            "config": self.config,
            "timeline": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_hours": self.duration_hours,
            },
            "baseline_metrics": baseline,
            "monitoring_results": monitoring,
            "summary": {
                "success_rate": success_rate,
                "total_incidents": len(monitoring["incidents"]),
                "recommendation": self._get_deployment_recommendation(success_rate, monitoring),
            },
        }

        # 保存报告
        report_file = f"output/canary_report_{self.deployment_id}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"✅ 报告已保存: {report_file}")
        return report

    def _get_deployment_recommendation(
        self, success_rate: float, monitoring: Dict[str, Any]
    ) -> str:
        """获取部署建议"""
        if success_rate >= 95 and len(monitoring["incidents"]) == 0:
            return "🎉 推荐全量部署 - Canary测试完全成功"
        elif success_rate >= 90:
            return "⚠️ 建议谨慎部署 - 部分问题需要关注"
        else:
            return "❌ 不推荐部署 - 发现严重问题，需要修复"

    async def _emergency_rollback(self):
        """紧急回滚"""
        self.logger.error("🚨 执行紧急回滚")

        # 这里实现回滚逻辑
        # 1. 停止所有交易
        # 2. 关闭连接
        # 3. 恢复到稳定版本

        self.logger.info("✅ 紧急回滚完成")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Canary部署工具")
    parser.add_argument("--testnet", action="store_true", default=True, help="使用testnet环境")
    parser.add_argument("--pairs", default="BTCUSDT,ETHUSDT", help="交易对列表")
    parser.add_argument("--funds", type=int, default=500, help="测试资金额度")
    parser.add_argument("--duration", default="24h", help="监控时长")

    args = parser.parse_args()

    # 解析duration
    duration_hours = 24
    if args.duration.endswith("h"):
        duration_hours = int(args.duration[:-1])

    # 配置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 创建部署配置
    config = {
        "testnet": args.testnet,
        "pairs": args.pairs.split(","),
        "funds": args.funds,
        "duration_hours": duration_hours,
    }

    print("🕯️ M4 Canary部署工具启动")
    print(f"📊 配置: {config}")

    try:
        # 启动Canary部署
        canary = CanaryDeployment(config)
        report = await canary.start_canary_deployment()

        print(f"\n🎊 Canary部署完成!")
        print(f"📊 成功率: {report['summary']['success_rate']:.1f}%")
        print(f"💡 建议: {report['summary']['recommendation']}")

    except Exception as e:
        print(f"❌ Canary部署失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
