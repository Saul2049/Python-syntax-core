#!/usr/bin/env python3
"""
GC性能监控器 - M5阶段
GC Performance Profiler for M5 Phase

用途：
- GC暂停时间监控
- 分代回收统计
- Prometheus指标集成
"""

import gc
import time
import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import threading

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from prometheus_client import Summary, Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # 创建空的类避免错误
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass


class GCProfiler:
    """GC性能监控器"""
    
    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.gc_events = []
        self.monitoring = False
        self.start_time = None
        self.logger = logging.getLogger(__name__)
        
        # 🔥FAST模式支持
        self.fast_mode = os.getenv('FAST', '0') == '1'
        self.quiet_mode = os.getenv('QUIET', '0') == '1'
        
        # 🔥优化日志阈值 - 减少噪音
        if self.fast_mode:
            self.log_threshold_ms = 50.0   # FAST模式只记录>50ms的暂停
            self.max_events = 100          # 限制事件数量
        else:
            self.log_threshold_ms = 10.0   # 标准模式记录>10ms的暂停
            self.max_events = 1000
        
        # 🔥减少空GC日志
        self.last_empty_gc_log = 0
        self.empty_gc_log_interval = 60  # 每60秒最多记录一次"回收0个对象"
        
        # 初始化Prometheus指标
        if self.enable_prometheus:
            self._init_prometheus_metrics()
        
        # GC回调追踪
        self.original_callbacks = gc.callbacks.copy()
        
        if self.fast_mode:
            self.logger.info("⚡ GC Profiler - FAST模式 (减少日志输出)")
        
    def _init_prometheus_metrics(self):
        """初始化Prometheus指标"""
        self.gc_pause_duration = Summary(
            'gc_pause_seconds',
            'GC暂停时间',
            ['generation']
        )
        
        self.gc_collections_total = Counter(
            'gc_collections_total',
            'GC回收次数',
            ['generation']
        )
        
        self.gc_collected_objects = Counter(
            'gc_collected_objects_total',
            'GC回收对象数量',
            ['generation']
        )
        
        self.gc_pause_histogram = Histogram(
            'gc_pause_duration_seconds',
            'GC暂停时间分布',
            ['generation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
        
        self.gc_objects_tracked = Gauge(
            'gc_objects_tracked',
            '当前追踪的对象数量',
            ['generation']
        )
        
        self.logger.info("✅ Prometheus GC指标已初始化")
    
    def _gc_callback(self, phase: str, info: Dict[str, Any]):
        """GC回调函数 - 优化版"""
        try:
            timestamp = time.time()
            generation = info.get('generation', -1)
            
            if phase == 'start':
                # 记录开始时间
                if not hasattr(self, '_gc_start_times'):
                    self._gc_start_times = {}
                self._gc_start_times[generation] = timestamp
                
            elif phase == 'stop':
                # 计算暂停时间
                if hasattr(self, '_gc_start_times') and generation in self._gc_start_times:
                    pause_duration = timestamp - self._gc_start_times[generation]
                    collected = info.get('collected', 0)
                    
                    # 🔥优化事件记录 - 限制数量
                    if len(self.gc_events) < self.max_events:
                        gc_event = {
                            'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                            'generation': generation,
                            'pause_duration': pause_duration,
                            'collected_objects': collected,
                            'phase': phase
                        }
                        self.gc_events.append(gc_event)
                    
                    # 更新Prometheus指标
                    if self.enable_prometheus:
                        gen_label = str(generation)
                        self.gc_pause_duration.labels(generation=gen_label).observe(pause_duration)
                        self.gc_collections_total.labels(generation=gen_label).inc()
                        self.gc_collected_objects.labels(generation=gen_label).inc(collected)
                        self.gc_pause_histogram.labels(generation=gen_label).observe(pause_duration)
                    
                    # 🔥智能日志记录 - 减少噪音
                    pause_ms = pause_duration * 1000
                    
                    if not self.quiet_mode and pause_ms > self.log_threshold_ms:
                        # 有意义的暂停时间
                        self.logger.info(
                            f"🗑️ GC Gen{generation}: {pause_ms:.2f}ms, "
                            f"回收{collected}个对象"
                        )
                    elif collected == 0 and pause_ms > 5.0:  # 空GC但暂停时间长
                        # 🔥减少空GC日志频率
                        now = time.time()
                        if now - self.last_empty_gc_log > self.empty_gc_log_interval:
                            if not self.quiet_mode:
                                self.logger.warning(
                                    f"⚠️ GC Gen{generation}: {pause_ms:.2f}ms, "
                                    f"回收0个对象 (空GC暂停较长)"
                                )
                            self.last_empty_gc_log = now
                    
                    # 清理开始时间记录
                    del self._gc_start_times[generation]
                    
        except Exception as e:
            if not self.quiet_mode:
                self.logger.error(f"❌ GC回调错误: {e}")
    
    def start_monitoring(self):
        """开始GC监控"""
        if self.monitoring:
            if not self.quiet_mode:
                self.logger.warning("⚠️ GC监控已在运行")
            return
        
        self.monitoring = True
        self.start_time = time.time()
        self.gc_events.clear()
        
        # 注册GC回调
        gc.callbacks.append(self._gc_callback)
        
        # 🔥FAST模式不启动统计线程
        if not self.fast_mode:
            # 启动定期统计线程
            self._stats_thread = threading.Thread(target=self._periodic_stats_update, daemon=True)
            self._stats_thread.start()
        
        if not self.quiet_mode:
            mode = "FAST" if self.fast_mode else "标准"
            self.logger.info(f"✅ GC监控已启动 ({mode}模式)")
    
    def stop_monitoring(self):
        """停止GC监控"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        
        # 移除GC回调
        if self._gc_callback in gc.callbacks:
            gc.callbacks.remove(self._gc_callback)
        
        if not self.quiet_mode:
            self.logger.info("🛑 GC监控已停止")
    
    def _periodic_stats_update(self):
        """定期更新统计信息 - 非FAST模式"""
        while self.monitoring:
            try:
                if self.enable_prometheus:
                    # 更新当前对象追踪数量
                    for gen in range(3):
                        objects_count = len(gc.get_objects(gen))
                        self.gc_objects_tracked.labels(generation=str(gen)).set(objects_count)
                
                time.sleep(30)  # 每30秒更新一次
                
            except Exception as e:
                if not self.quiet_mode:
                    self.logger.error(f"❌ 定期统计更新错误: {e}")
                time.sleep(10)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取GC统计信息"""
        if not self.gc_events:
            return {'error': 'No GC events recorded'}
        
        # 按代分组统计
        by_generation = {}
        for event in self.gc_events:
            gen = event['generation']
            if gen not in by_generation:
                by_generation[gen] = {
                    'count': 0,
                    'total_pause_time': 0,
                    'total_collected': 0,
                    'max_pause': 0,
                    'min_pause': float('inf'),
                    'pause_times': []
                }
            
            stats = by_generation[gen]
            pause_time = event['pause_duration']
            
            stats['count'] += 1
            stats['total_pause_time'] += pause_time
            stats['total_collected'] += event['collected_objects']
            stats['max_pause'] = max(stats['max_pause'], pause_time)
            stats['min_pause'] = min(stats['min_pause'], pause_time)
            stats['pause_times'].append(pause_time)
        
        # 计算统计值
        for gen, stats in by_generation.items():
            if stats['count'] > 0:
                stats['avg_pause'] = stats['total_pause_time'] / stats['count']
                stats['avg_collected'] = stats['total_collected'] / stats['count']
                
                # 计算百分位数
                sorted_pauses = sorted(stats['pause_times'])
                count = len(sorted_pauses)
                if count > 0:
                    stats['p50_pause'] = sorted_pauses[int(count * 0.5)]
                    stats['p95_pause'] = sorted_pauses[int(count * 0.95)]
                    stats['p99_pause'] = sorted_pauses[int(count * 0.99)]
                
                # 清理不需要的详细数据
                del stats['pause_times']
        
        # 整体统计
        duration = time.time() - self.start_time if self.start_time else 0
        total_events = len(self.gc_events)
        total_pause_time = sum(event['pause_duration'] for event in self.gc_events)
        
        # 当前GC状态
        gc_counts = gc.get_count()
        gc_thresholds = gc.get_threshold()
        
        return {
            'monitoring_duration': duration,
            'total_gc_events': total_events,
            'total_pause_time': total_pause_time,
            'avg_pause_time': total_pause_time / total_events if total_events > 0 else 0,
            'gc_frequency': total_events / duration if duration > 0 else 0,
            'current_gc_counts': {
                'gen0': gc_counts[0],
                'gen1': gc_counts[1],
                'gen2': gc_counts[2]
            },
            'gc_thresholds': {
                'gen0': gc_thresholds[0],
                'gen1': gc_thresholds[1],
                'gen2': gc_thresholds[2]
            },
            'by_generation': by_generation
        }
    
    def optimize_gc_thresholds(self) -> Dict[str, Any]:
        """基于统计信息优化GC阈值"""
        stats = self.get_statistics()
        
        if 'error' in stats:
            return stats
        
        recommendations = {
            'current_thresholds': stats['gc_thresholds'],
            'recommendations': {},
            'rationale': {}
        }
        
        # 分析Gen0频率
        gen0_stats = stats['by_generation'].get(0, {})
        if gen0_stats.get('count', 0) > 0:
            frequency = gen0_stats['count'] / stats['monitoring_duration']
            avg_pause = gen0_stats.get('avg_pause', 0)
            
            if frequency > 10:  # 每秒>10次GC太频繁
                new_threshold = min(1000, int(stats['gc_thresholds']['gen0'] * 1.5))
                recommendations['recommendations']['gen0'] = new_threshold
                recommendations['rationale']['gen0'] = f"Gen0频率过高({frequency:.1f}/s)，建议增加阈值"
            
            elif avg_pause > 0.05:  # 平均暂停>50ms
                new_threshold = max(100, int(stats['gc_thresholds']['gen0'] * 0.8))
                recommendations['recommendations']['gen0'] = new_threshold
                recommendations['rationale']['gen0'] = f"Gen0暂停时间过长({avg_pause*1000:.1f}ms)，建议减少阈值"
        
        return recommendations
    
    def apply_optimized_thresholds(self, recommendations: Dict[str, Any]):
        """应用优化的GC阈值"""
        if 'recommendations' not in recommendations:
            return
        
        current = gc.get_threshold()
        new_thresholds = list(current)
        
        rec = recommendations['recommendations']
        if 'gen0' in rec:
            new_thresholds[0] = rec['gen0']
        if 'gen1' in rec:
            new_thresholds[1] = rec['gen1']  
        if 'gen2' in rec:
            new_thresholds[2] = rec['gen2']
        
        # 应用新阈值
        gc.set_threshold(*new_thresholds)
        
        self.logger.info(f"🔧 GC阈值已更新: {current} → {tuple(new_thresholds)}")
        
        return tuple(new_thresholds)
    
    def save_report(self, filename: str):
        """保存GC分析报告"""
        stats = self.get_statistics()
        recommendations = self.optimize_gc_thresholds()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'optimization_recommendations': recommendations,
            'events': self.gc_events[-100:] if len(self.gc_events) > 100 else self.gc_events  # 最近100个事件
        }
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"💾 GC报告已保存: {filename}")
        
        # 打印摘要
        if 'error' not in stats:
            print("\n" + "="*60)
            print("🗑️ GC性能分析报告")
            print("="*60)
            print(f"⏱️ 监控时长: {stats['monitoring_duration']:.1f}秒")
            print(f"📊 GC事件: {stats['total_gc_events']}次")
            print(f"⏸️ 总暂停时间: {stats['total_pause_time']*1000:.1f}ms")
            print(f"📈 平均暂停: {stats['avg_pause_time']*1000:.2f}ms")
            print(f"🔄 GC频率: {stats['gc_frequency']:.2f}/秒")
            
            print("\n🏷️ 分代统计:")
            for gen, gen_stats in stats['by_generation'].items():
                if gen_stats['count'] > 0:
                    print(f"   Gen{gen}: {gen_stats['count']}次, "
                          f"平均{gen_stats['avg_pause']*1000:.2f}ms, "
                          f"P95={gen_stats.get('p95_pause', 0)*1000:.2f}ms")
            
            # 优化建议
            if recommendations.get('recommendations'):
                print("\n💡 优化建议:")
                for param, value in recommendations['recommendations'].items():
                    rationale = recommendations['rationale'].get(param, '')
                    print(f"   {param}: {value} ({rationale})")
            else:
                print("\n✅ 当前GC配置看起来不错")
            
            print("="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GC性能监控工具")
    parser.add_argument("--duration", type=int, default=300, help="监控时长(秒)")
    parser.add_argument("--save", help="保存报告文件路径")
    parser.add_argument("--optimize", action="store_true", help="自动应用优化建议")
    parser.add_argument("--prometheus", action="store_true", help="启用Prometheus指标")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🗑️ M5 GC性能监控工具")
    print(f"⏱️ 监控时长: {args.duration}秒")
    
    # 创建GC监控器
    profiler = GCProfiler(enable_prometheus=args.prometheus)
    
    try:
        # 开始监控
        profiler.start_monitoring()
        print("🔄 开始GC监控...")
        
        # 运行指定时间
        time.sleep(args.duration)
        
        # 停止监控
        profiler.stop_monitoring()
        print("✅ GC监控完成")
        
        # 生成报告
        if args.save:
            profiler.save_report(args.save)
        else:
            timestamp = int(time.time())
            default_file = f"output/gc_profile_{timestamp}.json"
            os.makedirs('output', exist_ok=True)
            profiler.save_report(default_file)
        
        # 应用优化（如果请求）
        if args.optimize:
            recommendations = profiler.optimize_gc_thresholds()
            if recommendations.get('recommendations'):
                profiler.apply_optimized_thresholds(recommendations)
                print("🔧 GC优化已应用")
            else:
                print("✅ 无需GC优化")
                
    except KeyboardInterrupt:
        print("\n🛑 用户中断")
        profiler.stop_monitoring()
    except Exception as e:
        print(f"❌ 监控失败: {e}")
        profiler.stop_monitoring()
        raise


if __name__ == "__main__":
    main() 