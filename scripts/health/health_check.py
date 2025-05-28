#!/usr/bin/env python3
"""
交易系统健康检查脚本
验证系统各组件状态和业务指标
"""
import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import requests

# 添加src路径到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from src.brokers.exchange.client import ExchangeClient
    from src.monitoring.metrics_collector import get_metrics_collector
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


class HealthStatus(Enum):
    """健康状态枚举"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""

    component: str
    status: HealthStatus
    message: str
    details: Optional[Dict] = None
    duration_ms: Optional[float] = None


class TradingSystemHealthChecker:
    """交易系统健康检查器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.results: List[HealthCheckResult] = []

    def check_all(self) -> List[HealthCheckResult]:
        """执行所有健康检查"""
        self.results.clear()

        print("🏥 开始交易系统健康检查...")
        print("=" * 50)

        # 基础系统检查
        self._check_python_environment()
        self._check_dependencies()
        self._check_configuration()

        # 监控系统检查
        self._check_prometheus_metrics()

        # 网络连接检查
        self._check_exchange_connectivity()

        # 数据完整性检查
        self._check_data_integrity()

        # 业务逻辑检查
        self._check_trading_components()

        # 汇总报告
        self._generate_summary()

        return self.results

    def _check_python_environment(self):
        """检查Python环境"""
        start_time = time.time()

        try:
            python_version = sys.version
            if sys.version_info < (3, 8):
                status = HealthStatus.WARNING
                message = f"Python版本较低: {python_version}"
            else:
                status = HealthStatus.HEALTHY
                message = f"Python环境正常: {python_version}"

        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"Python环境检查失败: {e}"

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="Python环境", status=status, message=message, duration_ms=duration
            )
        )

    def _check_dependencies(self):
        """检查关键依赖"""
        start_time = time.time()

        required_packages = ["pandas", "numpy", "requests", "matplotlib"]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            status = HealthStatus.CRITICAL
            message = f"缺失依赖包: {', '.join(missing_packages)}"
        else:
            status = HealthStatus.HEALTHY
            message = "所有依赖包正常"

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="依赖包", status=status, message=message, duration_ms=duration
            )
        )

    def _check_configuration(self):
        """检查配置文件"""
        start_time = time.time()

        required_env_vars = [
            "ENVIRONMENT",
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        config_files = [".env.example", "Makefile"]
        missing_files = []

        for file_path in config_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        issues = []
        if missing_vars:
            issues.append(f"缺失环境变量: {', '.join(missing_vars)}")
        if missing_files:
            issues.append(f"缺失配置文件: {', '.join(missing_files)}")

        if issues:
            status = HealthStatus.WARNING
            message = "; ".join(issues)
        else:
            status = HealthStatus.HEALTHY
            message = "配置文件正常"

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="配置文件", status=status, message=message, duration_ms=duration
            )
        )

    def _check_prometheus_metrics(self):
        """检查Prometheus监控"""
        start_time = time.time()

        try:
            metrics_collector = get_metrics_collector()
            if not metrics_collector.config.enabled:
                status = HealthStatus.WARNING
                message = "监控已禁用"
            else:
                port = metrics_collector.config.port
                url = f"http://localhost:{port}/metrics"

                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        status = HealthStatus.HEALTHY
                        message = f"监控服务正常运行在端口 {port}"
                    else:
                        status = HealthStatus.WARNING
                        message = f"监控服务响应异常: {response.status_code}"
                except requests.RequestException:
                    status = HealthStatus.WARNING
                    message = f"无法连接监控服务 (端口 {port})"

        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"监控系统检查失败: {e}"

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="监控系统", status=status, message=message, duration_ms=duration
            )
        )

    def _check_exchange_connectivity(self):
        """检查交易所连接"""
        start_time = time.time()

        try:
            # 创建演示模式客户端进行连接测试
            client = ExchangeClient(api_key="test", api_secret="test", demo_mode=True)

            # 测试获取行情数据
            ticker = client.get_ticker("BTC/USDT")

            if ticker and "price" in ticker:
                status = HealthStatus.HEALTHY
                message = "交易所连接正常 (演示模式)"
                details = {"btc_price": ticker["price"], "demo_mode": True}
            else:
                status = HealthStatus.WARNING
                message = "交易所响应数据异常"
                details = {"response": str(ticker)}

        except Exception as e:
            status = HealthStatus.WARNING
            message = f"交易所连接测试失败: {e}"
            details = {"error": str(e)}

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="交易所连接",
                status=status,
                message=message,
                details=details,
                duration_ms=duration,
            )
        )

    def _check_data_integrity(self):
        """检查数据完整性"""
        start_time = time.time()

        try:
            # 检查数据目录
            data_dirs = ["src/", "tests/", "scripts/"]
            missing_dirs = [d for d in data_dirs if not os.path.exists(d)]

            # 检查关键文件
            key_files = [
                "src/core/trading_engine.py",
                "src/monitoring/metrics_collector.py",
                "scripts/prometheus_exporter_template.py",
                "scripts/panic_sell_circuit_breaker.py",
            ]
            missing_files = [f for f in key_files if not os.path.exists(f)]

            issues = []
            if missing_dirs:
                issues.append(f"缺失目录: {', '.join(missing_dirs)}")
            if missing_files:
                issues.append(f"缺失文件: {', '.join(missing_files)}")

            if issues:
                status = HealthStatus.CRITICAL
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = "数据完整性正常"

        except Exception as e:
            status = HealthStatus.CRITICAL
            message = f"数据完整性检查失败: {e}"

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="数据完整性", status=status, message=message, duration_ms=duration
            )
        )

    def _check_trading_components(self):
        """检查交易组件"""
        start_time = time.time()

        try:
            # 测试导入关键模块
            from src.core.price_fetcher import fetch_price_data
            from src.core.signal_processor import get_trading_signals
            from src.core.trading_engine import TradingEngine

            status = HealthStatus.HEALTHY
            message = "交易组件正常"

        except ImportError as e:
            status = HealthStatus.CRITICAL
            message = f"交易组件导入失败: {e}"
        except Exception as e:
            status = HealthStatus.WARNING
            message = f"交易组件检查异常: {e}"

        duration = (time.time() - start_time) * 1000
        self.results.append(
            HealthCheckResult(
                component="交易组件", status=status, message=message, duration_ms=duration
            )
        )

    def _generate_summary(self):
        """生成健康检查汇总"""
        print("\n" + "=" * 50)
        print("📊 健康检查汇总报告")
        print("=" * 50)

        status_counts = {status: 0 for status in HealthStatus}
        total_duration = 0

        for result in self.results:
            status_counts[result.status] += 1
            if result.duration_ms:
                total_duration += result.duration_ms

            # 状态图标
            icon = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.WARNING: "⚠️",
                HealthStatus.CRITICAL: "❌",
                HealthStatus.UNKNOWN: "❓",
            }[result.status]

            duration_str = f" ({result.duration_ms:.1f}ms)" if result.duration_ms else ""
            print(f"{icon} {result.component}: {result.message}{duration_str}")

            if result.details:
                for key, value in result.details.items():
                    print(f"   └─ {key}: {value}")

        print("\n📈 统计信息:")
        print(f"   总检查项: {len(self.results)}")
        print(f"   正常: {status_counts[HealthStatus.HEALTHY]}")
        print(f"   警告: {status_counts[HealthStatus.WARNING]}")
        print(f"   严重: {status_counts[HealthStatus.CRITICAL]}")
        print(f"   总耗时: {total_duration:.1f}ms")

        # 整体健康状态
        if status_counts[HealthStatus.CRITICAL] > 0:
            overall = "🚨 系统存在严重问题"
        elif status_counts[HealthStatus.WARNING] > 0:
            overall = "⚠️ 系统正常但有警告"
        else:
            overall = "🎉 系统完全健康"

        print(f"\n🏥 整体状态: {overall}")
        print("=" * 50)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="交易系统健康检查")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument(
        "--check", choices=["all", "basic", "monitoring", "network"], default="all", help="检查类型"
    )

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")

    # 执行健康检查
    checker = TradingSystemHealthChecker()
    results = checker.check_all()

    # 返回退出码
    critical_count = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
    warning_count = sum(1 for r in results if r.status == HealthStatus.WARNING)

    if critical_count > 0:
        sys.exit(2)  # 严重错误
    elif warning_count > 0:
        sys.exit(1)  # 警告
    else:
        sys.exit(0)  # 正常


if __name__ == "__main__":
    main()
