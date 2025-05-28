#!/usr/bin/env python3
"""
M1-1: 统一指标汇总 SDK (Prometheus格式)
Unified Metrics Collector SDK (Prometheus Format)

轻量级、高性能的指标收集器，专为交易系统优化
"""

import time
import psutil
import gc
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os


@dataclass
class Metric:
    """单个指标的数据结构"""

    name: str
    value: Union[float, int]
    labels: Dict[str, str] = field(default_factory=dict)
    help_text: str = ""
    metric_type: str = "gauge"  # gauge, counter, histogram, summary
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_prometheus_line(self) -> str:
        """转换为Prometheus exposition格式"""
        if self.help_text:
            help_line = f"# HELP {self.name} {self.help_text}\n"
            type_line = f"# TYPE {self.name} {self.metric_type}\n"
        else:
            help_line = type_line = ""

        if self.labels:
            label_str = "{" + ",".join([f'{k}="{v}"' for k, v in self.labels.items()]) + "}"
        else:
            label_str = ""

        return f"{help_line}{type_line}{self.name}{label_str} {self.value}"


class MetricsCollector:
    """高性能指标收集器 - 专为交易系统优化"""

    def __init__(self, process_name: str = "trading_system"):
        self.process_name = process_name
        self.process = psutil.Process()
        self.metrics: List[Metric] = []
        self.start_time = time.time()

        # 性能优化：缓存常用对象
        self._memory_info_cache = None
        self._cache_time = 0
        self._cache_ttl = 1.0  # 1秒缓存TTL

    def clear_metrics(self):
        """清空指标缓存"""
        self.metrics.clear()
        return self

    def add_metric(
        self,
        name: str,
        value: Union[float, int],
        labels: Optional[Dict[str, str]] = None,
        help_text: str = "",
        metric_type: str = "gauge",
    ) -> "MetricsCollector":
        """添加自定义指标（链式调用）"""
        self.metrics.append(
            Metric(
                name=name,
                value=value,
                labels=labels or {},
                help_text=help_text,
                metric_type=metric_type,
            )
        )
        return self

    def _get_memory_info(self):
        """获取内存信息（带缓存优化）"""
        now = time.time()
        if now - self._cache_time > self._cache_ttl:
            self._memory_info_cache = self.process.memory_info()
            self._cache_time = now
        return self._memory_info_cache

    def collect_system_metrics(self) -> "MetricsCollector":
        """收集系统级指标"""
        try:
            # 内存指标
            memory_info = self._get_memory_info()
            self.add_metric(
                "process_memory_rss_bytes",
                memory_info.rss,
                help_text="Resident Set Size in bytes",
                metric_type="gauge",
            )
            self.add_metric(
                "process_memory_vms_bytes",
                memory_info.vms,
                help_text="Virtual Memory Size in bytes",
                metric_type="gauge",
            )

            # CPU指标
            cpu_percent = self.process.cpu_percent()
            self.add_metric(
                "process_cpu_usage_percent",
                cpu_percent,
                help_text="CPU usage percentage",
                metric_type="gauge",
            )

            # 文件描述符
            try:
                num_fds = self.process.num_fds() if hasattr(self.process, "num_fds") else 0
                self.add_metric(
                    "process_open_fds",
                    num_fds,
                    help_text="Number of open file descriptors",
                    metric_type="gauge",
                )
            except (AttributeError, psutil.AccessDenied):
                pass  # Windows或权限问题

            # 系统整体指标
            system_memory = psutil.virtual_memory()
            self.add_metric(
                "system_memory_usage_percent",
                system_memory.percent,
                help_text="System memory usage percentage",
                metric_type="gauge",
            )

            # 运行时长
            uptime = time.time() - self.start_time
            self.add_metric(
                "process_uptime_seconds",
                uptime,
                help_text="Process uptime in seconds",
                metric_type="counter",
            )

        except Exception as e:
            # 错误指标
            self.add_metric(
                "metrics_collection_errors_total",
                1,
                labels={"error_type": type(e).__name__},
                help_text="Total metrics collection errors",
                metric_type="counter",
            )

        return self

    def collect_gc_metrics(self) -> "MetricsCollector":
        """收集垃圾回收指标"""
        try:
            # GC统计
            gc_stats = gc.get_stats()
            for i, stats in enumerate(gc_stats):
                self.add_metric(
                    "gc_collections_total",
                    stats.get("collections", 0),
                    labels={"generation": str(i)},
                    help_text="Total GC collections",
                    metric_type="counter",
                )
                self.add_metric(
                    "gc_collected_total",
                    stats.get("collected", 0),
                    labels={"generation": str(i)},
                    help_text="Total GC collected objects",
                    metric_type="counter",
                )
                self.add_metric(
                    "gc_uncollectable_total",
                    stats.get("uncollectable", 0),
                    labels={"generation": str(i)},
                    help_text="Total GC uncollectable objects",
                    metric_type="counter",
                )

            # GC阈值
            thresholds = gc.get_threshold()
            for i, threshold in enumerate(thresholds):
                self.add_metric(
                    "gc_threshold",
                    threshold,
                    labels={"generation": str(i)},
                    help_text="GC threshold by generation",
                    metric_type="gauge",
                )

            # GC计数
            counts = gc.get_count()
            for i, count in enumerate(counts):
                self.add_metric(
                    "gc_objects_count",
                    count,
                    labels={"generation": str(i)},
                    help_text="Objects count by GC generation",
                    metric_type="gauge",
                )

        except Exception as e:
            self.add_metric(
                "gc_metrics_errors_total",
                1,
                labels={"error_type": type(e).__name__},
                help_text="Total GC metrics errors",
                metric_type="counter",
            )

        return self

    def collect_trading_metrics(
        self, additional_metrics: Optional[Dict[str, Any]] = None
    ) -> "MetricsCollector":
        """收集交易相关指标"""
        if additional_metrics:
            for name, value in additional_metrics.items():
                if isinstance(value, dict) and "value" in value:
                    # 复杂指标格式：{'value': 123, 'labels': {...}, 'help': '...'}
                    self.add_metric(
                        name=name,
                        value=value["value"],
                        labels=value.get("labels", {}),
                        help_text=value.get("help", ""),
                        metric_type=value.get("type", "gauge"),
                    )
                else:
                    # 简单指标格式
                    self.add_metric(name, value)

        return self

    def to_prometheus_format(self) -> str:
        """导出为Prometheus exposition格式"""
        if not self.metrics:
            return "# No metrics available\n"

        lines = []
        lines.append(f"# Generated by MetricsCollector at {datetime.now(timezone.utc).isoformat()}")
        lines.append(f"# Process: {self.process_name}")
        lines.append("")

        for metric in self.metrics:
            lines.append(metric.to_prometheus_line())

        return "\n".join(lines) + "\n"

    def to_json(self) -> str:
        """导出为JSON格式（便于调试）"""
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "process_name": self.process_name,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "labels": m.labels,
                    "type": m.metric_type,
                    "help": m.help_text,
                    "timestamp": m.timestamp,
                }
                for m in self.metrics
            ],
        }
        return json.dumps(data, indent=2)

    def save_to_file(self, filepath: str, format_type: str = "prometheus") -> bool:
        """保存指标到文件"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            if format_type == "prometheus":
                content = self.to_prometheus_format()
            elif format_type == "json":
                content = self.to_json()
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def collect_all(self, trading_metrics: Optional[Dict[str, Any]] = None) -> "MetricsCollector":
        """一键收集所有指标"""
        return (
            self.clear_metrics()
            .collect_system_metrics()
            .collect_gc_metrics()
            .collect_trading_metrics(trading_metrics)
        )


def create_metrics_snapshot(
    process_name: str = "trading_system", trading_metrics: Optional[Dict[str, Any]] = None
) -> str:
    """快速创建指标快照（一行调用）"""
    collector = MetricsCollector(process_name)
    collector.collect_all(trading_metrics)
    return collector.to_prometheus_format()


# 命令行接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Metrics Collector for Trading System")
    parser.add_argument(
        "--format", choices=["prometheus", "json"], default="prometheus", help="Output format"
    )
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--process-name", default="trading_system", help="Process name")

    args = parser.parse_args()

    collector = MetricsCollector(args.process_name)
    collector.collect_all()

    if args.output:
        success = collector.save_to_file(args.output, args.format)
        print(f"Metrics {'saved' if success else 'failed'} to {args.output}")
    else:
        if args.format == "json":
            print(collector.to_json())
        else:
            print(collector.to_prometheus_format())
