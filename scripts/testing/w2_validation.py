#!/usr/bin/env python3
"""
W2 GC优化验证脚本
W2 GC Optimization Validation Script

目标: 验证W2 GC调参效果是否持续有效
验收标准:
- GC阈值 = (900, 20, 10)
- P95 GC暂停 ≤ 0.05ms (50ms)
- Gen0/Gen2触发率接近0
"""

import gc
import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Tuple
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from config.gc_settings import GCSettings
from scripts.memory.gc_profiler import GCProfiler


class W2Validator:
    """W2 GC优化验证器"""
    
    def __init__(self):
        self.gc_profiler = GCProfiler(enable_prometheus=False)
        self.logger = logging.getLogger(__name__)
        
        # W2验收标准
        self.w2_standards = {
            'gc_thresholds': (900, 20, 10),
            'max_p95_pause_ms': 50.0,
            'max_gen0_rate_per_min': 200.0,
            'max_gen2_rate_per_min': 5.0,
            'min_improvement_percent': 50.0
        }
        
        self.validation_results = {
            'timestamp': None,
            'w2_compliant': False,
            'config_check': {},
            'performance_check': {},
            'recommendations': []
        }
    
    async def run_validation(self, test_duration: int = 300) -> Dict:
        """运行W2验证测试"""
        self.validation_results['timestamp'] = datetime.now().isoformat()
        self.logger.info("🔍 开始W2 GC优化验证")
        
        # 1. 配置检查
        config_valid = self._validate_gc_configuration()
        
        # 2. 性能基准测试
        if config_valid:
            perf_valid = await self._validate_gc_performance(test_duration)
        else:
            perf_valid = False
            self.logger.error("❌ GC配置不符合W2标准，跳过性能测试")
        
        # 3. 综合评估
        overall_valid = config_valid and perf_valid
        self.validation_results['w2_compliant'] = overall_valid
        
        # 4. 生成建议
        self._generate_recommendations()
        
        return self.validation_results
    
    def _validate_gc_configuration(self) -> bool:
        """验证GC配置"""
        self.logger.info("🔧 检查GC配置...")
        
        current_thresholds = gc.get_threshold()
        expected_thresholds = self.w2_standards['gc_thresholds']
        
        config_check = {
            'current_thresholds': current_thresholds,
            'expected_thresholds': expected_thresholds,
            'thresholds_match': current_thresholds == expected_thresholds,
            'has_gc_freeze': hasattr(gc, 'freeze'),
            'auto_apply_enabled': os.getenv('AUTO_APPLY_GC', '0') == '1'
        }
        
        self.validation_results['config_check'] = config_check
        
        if config_check['thresholds_match']:
            self.logger.info(f"✅ GC阈值正确: {current_thresholds}")
        else:
            self.logger.error(f"❌ GC阈值错误: 当前{current_thresholds} vs 期望{expected_thresholds}")
        
        if config_check['has_gc_freeze']:
            self.logger.info("✅ gc.freeze() 支持可用")
        else:
            self.logger.warning("⚠️ gc.freeze() 不可用，建议升级Python版本")
        
        return config_check['thresholds_match']
    
    async def _validate_gc_performance(self, duration: int) -> bool:
        """验证GC性能"""
        self.logger.info(f"📊 开始{duration}秒GC性能测试...")
        
        # 启动GC监控
        self.gc_profiler.start_monitoring()
        
        # 运行负载测试
        await self._run_gc_load_test(duration)
        
        # 停止监控并获取统计
        self.gc_profiler.stop_monitoring()
        stats = self.gc_profiler.get_statistics()
        
        if 'error' in stats:
            self.logger.error(f"❌ GC性能测试失败: {stats['error']}")
            return False
        
        # 分析性能指标
        perf_check = self._analyze_gc_performance(stats)
        self.validation_results['performance_check'] = perf_check
        
        return perf_check['meets_w2_standards']
    
    async def _run_gc_load_test(self, duration: int):
        """运行GC负载测试"""
        from src.strategies.cache_optimized_strategy import CacheOptimizedStrategy
        
        strategy = CacheOptimizedStrategy({})
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'XRPUSDT']
        
        self.logger.info(f"🔄 运行GC负载测试 ({duration}秒)")
        
        start_time = time.time()
        signals_generated = 0
        
        while time.time() - start_time < duration:
            for symbol in test_symbols:
                # 模拟价格变动和信号生成
                price = 50000 + (time.time() % 1000)
                strategy.generate_signals(symbol, price)
                signals_generated += 1
                
                # 控制负载频率
                await asyncio.sleep(0.1)
        
        self.logger.info(f"✅ 负载测试完成: 生成{signals_generated}个信号")
    
    def _analyze_gc_performance(self, stats: Dict) -> Dict:
        """分析GC性能统计"""
        perf_check = {
            'test_duration': stats.get('monitoring_duration', 0),
            'total_gc_events': stats.get('total_gc_events', 0),
            'avg_pause_ms': stats.get('avg_pause_time', 0) * 1000,
            'gc_frequency': stats.get('gc_frequency', 0),
            'generation_stats': {}
        }
        
        # 分析各代GC性能
        for gen, gen_stats in stats.get('by_generation', {}).items():
            gen_info = {
                'count': gen_stats.get('count', 0),
                'frequency_per_min': (gen_stats.get('count', 0) / 
                                    (stats.get('monitoring_duration', 1) / 60)),
                'avg_pause_ms': gen_stats.get('avg_pause', 0) * 1000,
                'p95_pause_ms': gen_stats.get('p95_pause', 0) * 1000
            }
            perf_check['generation_stats'][f'gen{gen}'] = gen_info
        
        # W2标准检查
        gen0_freq = perf_check['generation_stats'].get('gen0', {}).get('frequency_per_min', 0)
        gen2_freq = perf_check['generation_stats'].get('gen2', {}).get('frequency_per_min', 0)
        
        # 计算P95暂停时间
        p95_pause_ms = 0
        for gen_stats in perf_check['generation_stats'].values():
            p95_pause_ms = max(p95_pause_ms, gen_stats.get('p95_pause_ms', 0))
        
        perf_check.update({
            'p95_pause_ms': p95_pause_ms,
            'gen0_frequency_per_min': gen0_freq,
            'gen2_frequency_per_min': gen2_freq,
            'meets_w2_standards': (
                p95_pause_ms <= self.w2_standards['max_p95_pause_ms'] and
                gen0_freq <= self.w2_standards['max_gen0_rate_per_min'] and
                gen2_freq <= self.w2_standards['max_gen2_rate_per_min']
            )
        })
        
        # 记录检查结果
        self.logger.info(f"📈 GC性能检查结果:")
        self.logger.info(f"   P95暂停: {p95_pause_ms:.1f}ms (标准: ≤{self.w2_standards['max_p95_pause_ms']}ms)")
        self.logger.info(f"   Gen0频率: {gen0_freq:.2f}/min (标准: ≤{self.w2_standards['max_gen0_rate_per_min']}/min)")
        self.logger.info(f"   Gen2频率: {gen2_freq:.2f}/min (标准: ≤{self.w2_standards['max_gen2_rate_per_min']}/min)")
        
        if perf_check['meets_w2_standards']:
            self.logger.info("✅ 性能符合W2标准")
        else:
            self.logger.error("❌ 性能不符合W2标准")
        
        return perf_check
    
    def _generate_recommendations(self):
        """生成改进建议"""
        recommendations = []
        
        config_check = self.validation_results['config_check']
        perf_check = self.validation_results.get('performance_check', {})
        
        # 配置建议
        if not config_check.get('thresholds_match', False):
            recommendations.append({
                'type': 'config',
                'priority': 'high',
                'action': 'apply_w2_gc_config',
                'description': f"应用W2最优GC配置: {self.w2_standards['gc_thresholds']}"
            })
        
        if not config_check.get('auto_apply_enabled', False):
            recommendations.append({
                'type': 'config',
                'priority': 'medium',
                'action': 'enable_auto_apply_gc',
                'description': "启用GC配置自动应用: 设置 AUTO_APPLY_GC=1"
            })
        
        if not config_check.get('has_gc_freeze', False):
            recommendations.append({
                'type': 'environment',
                'priority': 'low',
                'action': 'upgrade_python',
                'description': "升级到Python 3.12+以支持gc.freeze()优化"
            })
        
        # 性能建议
        if perf_check and not perf_check.get('meets_w2_standards', False):
            if perf_check.get('p95_pause_ms', 0) > self.w2_standards['max_p95_pause_ms']:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'action': 'investigate_gc_regression',
                    'description': f"GC暂停时间({perf_check['p95_pause_ms']:.1f}ms)超标，检查内存分配模式"
                })
            
            if perf_check.get('gen0_frequency_per_min', 0) > self.w2_standards['max_gen0_rate_per_min']:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'action': 'reduce_gen0_pressure',
                    'description': "Gen0 GC频率过高，检查短期对象分配"
                })
            
            if perf_check.get('gen2_frequency_per_min', 0) > self.w2_standards['max_gen2_rate_per_min']:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'high',
                    'action': 'investigate_long_lived_objects',
                    'description': "Gen2 GC频率过高，检查长期对象积累"
                })
        
        self.validation_results['recommendations'] = recommendations
    
    def save_validation_report(self, filename: str):
        """保存验证报告"""
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)
        
        self.logger.info(f"💾 W2验证报告已保存: {filename}")
        self._print_validation_summary()
    
    def _print_validation_summary(self):
        """打印验证总结"""
        print("\n" + "="*60)
        print("🔍 W2 GC优化验证报告")
        print("="*60)
        
        config_check = self.validation_results['config_check']
        perf_check = self.validation_results.get('performance_check', {})
        recommendations = self.validation_results['recommendations']
        
        print(f"🎯 W2验收状态: {'✅ PASS' if self.validation_results['w2_compliant'] else '❌ FAIL'}")
        
        print(f"\n🔧 配置检查:")
        print(f"   GC阈值: {config_check.get('current_thresholds', 'N/A')}")
        print(f"   配置正确: {'✅' if config_check.get('thresholds_match') else '❌'}")
        print(f"   gc.freeze(): {'✅' if config_check.get('has_gc_freeze') else '❌'}")
        
        if perf_check:
            print(f"\n📊 性能检查:")
            print(f"   P95暂停: {perf_check.get('p95_pause_ms', 0):.1f}ms (≤{self.w2_standards['max_p95_pause_ms']}ms)")
            print(f"   Gen0频率: {perf_check.get('gen0_frequency_per_min', 0):.2f}/min (≤{self.w2_standards['max_gen0_rate_per_min']}/min)")
            print(f"   Gen2频率: {perf_check.get('gen2_frequency_per_min', 0):.2f}/min (≤{self.w2_standards['max_gen2_rate_per_min']}/min)")
            print(f"   性能达标: {'✅' if perf_check.get('meets_w2_standards') else '❌'}")
        
        if recommendations:
            print(f"\n💡 改进建议:")
            for rec in recommendations:
                priority_icon = {'high': '🔥', 'medium': '⚠️', 'low': '💡'}.get(rec['priority'], '•')
                print(f"   {priority_icon} {rec['description']}")
        
        if self.validation_results['w2_compliant']:
            print(f"\n🎉 W2 GC优化验证通过！可以继续W3阶段")
        else:
            print(f"\n⚠️ W2 GC优化需要修复，请参考建议进行调整")
        
        print("="*60)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='W2 GC优化验证')
    parser.add_argument('--duration', type=int, default=300,
                       help='性能测试持续时间(秒) (默认: 300)')
    parser.add_argument('--fix-config', action='store_true',
                       help='自动修复GC配置问题')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🔍 W2 GC优化验证工具")
    print(f"🎯 验证W2调参效果是否持续有效")
    
    # 自动修复配置
    if args.fix_config:
        print("🔧 自动应用W2最优配置...")
        GCSettings.apply_w2_optimal()
    
    # 创建验证器
    validator = W2Validator()
    
    try:
        # 运行验证
        results = await validator.run_validation(args.duration)
        
        # 保存报告
        timestamp = int(time.time())
        report_file = f"output/w2_validation_{timestamp}.json"
        os.makedirs('output', exist_ok=True)
        validator.save_validation_report(report_file)
        
        return results['w2_compliant']
        
    except Exception as e:
        print(f"❌ W2验证失败: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 