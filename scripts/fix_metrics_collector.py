#!/usr/bin/env python3
"""
修复metrics_collector.py中的缩进问题
"""

def fix_metrics_collector():
    """修复metrics_collector.py的缩进问题"""
    file_path = "src/monitoring/metrics_collector.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复明显的缩进错误
    fixes = [
        # 修复第733行附近的缩进
        ('    def _extract_error_counts_from_registry(self, registry) -> Dict[str, int]:\n        """从Prometheus注册表提取错误计数"""\n            error_counts = {}', 
         '    def _extract_error_counts_from_registry(self, registry) -> Dict[str, int]:\n        """从Prometheus注册表提取错误计数"""\n        error_counts = {}'),
        
        # 修复except语句的缩进
        ('                    except Exception:\n                        pass', 
         '            except Exception:\n                pass'),
        
        # 修复return语句的缩进
        ('            return error_counts', 
         '        return error_counts'),
        
        # 修复其他函数的缩进问题
        ('    def _extract_trade_summary_from_registry(self, registry) -> Dict[str, Any]:\n        """从Prometheus注册表提取交易摘要"""\n            summary = {}', 
         '    def _extract_trade_summary_from_registry(self, registry) -> Dict[str, Any]:\n        """从Prometheus注册表提取交易摘要"""\n        summary = {}'),
        
        ('                try:\n                self._process_trade_samples(collector, summary)', 
         '            try:\n                self._process_trade_samples(collector, summary)'),
        
        # 修复for循环的缩进
        ('                    for sample in collector.collect():\n                        for metric_sample in sample.samples:\n                            if "price_updates_total" in metric_sample.name:\n                    self._update_trade_summary_for_symbol(metric_sample, summary)', 
         '        for sample in collector.collect():\n            for metric_sample in sample.samples:\n                if "price_updates_total" in metric_sample.name:\n                    self._update_trade_summary_for_symbol(metric_sample, summary)'),
        
        # 修复变量赋值的缩进
        ('                                    symbol = metric_sample.labels["symbol"]\n                                    if symbol not in summary:\n                                        summary[symbol] = {"trades": 0, "price_updates": 0}\n\n                                    summary[symbol]["price_updates"] += int(metric_sample.value)\n                                    summary[symbol]["trades"] += 1', 
         '        symbol = metric_sample.labels["symbol"]\n        if symbol not in summary:\n            summary[symbol] = {"trades": 0, "price_updates": 0}\n\n        summary[symbol]["price_updates"] += int(metric_sample.value)\n        summary[symbol]["trades"] += 1'),
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ metrics_collector.py 缩进问题已修复")

if __name__ == "__main__":
    fix_metrics_collector() 