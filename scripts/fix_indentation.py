#!/usr/bin/env python3
"""
修复trading_engine.py中的缩进问题
"""

import re

def fix_indentation():
    """修复缩进问题"""
    file_path = "src/core/trading_engine.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复常见的缩进问题
    fixes = [
        # 修复docstring后的缩进
        (r'(\s+"""[^"]*"""\n)\s+return', r'\1        return'),
        
        # 修复if语句的缩进
        (r'\n\s+# 风险管理检查\n\s+if not force_trade', r'\n        # 风险管理检查\n        if not force_trade'),
        
        # 修复注释的缩进
        (r'\n\s+# 计算仓位大小\n', r'\n        # 计算仓位大小\n'),
        
        # 修复if语句块的缩进
        (r'\n\s+if atr_value > 0:\n\s+risk_amount', r'\n        if atr_value > 0:\n            risk_amount'),
        (r'\n\s+else:\n\s+position_size', r'\n        else:\n            position_size'),
        
        # 修复函数调用的缩进
        (r'order_result = self\.broker\.place_order\(\n\s+symbol=', r'order_result = self.broker.place_order(\n            symbol='),
        
        # 修复变量赋值的缩进
        (r'\n\s+positions = self\.broker\.get_positions\(\)', r'\n        positions = self.broker.get_positions()'),
        (r'\n\s+if btc_position > min_quantity:', r'\n        if btc_position > min_quantity:'),
        (r'\n\s+order_result = self\.broker\.place_order\(\n\s+symbol=', r'\n            order_result = self.broker.place_order(\n                symbol='),
    ]
    
    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content)
    
    # 手动修复特定的缩进问题
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # 修复docstring后的return语句
        if '"""创建错误结果字典"""' in line and i + 1 < len(lines):
            fixed_lines.append(line)
            if lines[i + 1].strip().startswith('return'):
                fixed_lines.append('        return {')
                continue
        
        # 修复其他缩进问题
        if line.strip() and not line.startswith('    ') and not line.startswith('#') and not line.startswith('"""'):
            # 如果这行应该缩进但没有缩进
            if any(keyword in line for keyword in ['return', 'if ', 'else:', 'for ', 'while ', 'try:', 'except']):
                if not line.startswith('def ') and not line.startswith('class '):
                    line = '        ' + line.lstrip()
        
        fixed_lines.append(line)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✅ 缩进问题已修复")

if __name__ == "__main__":
    fix_indentation() 