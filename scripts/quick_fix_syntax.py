#!/usr/bin/env python3
"""
快速修复trading_engine.py中的语法错误
"""


def quick_fix():
    """快速修复语法错误"""
    file_path = "src/core/trading_engine.py"

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 修复明显的缩进错误
    fixes = [
        # 修复重复的return语句
        ("        return {\n        return {", "        return {"),
        # 修复错误的缩进
        (
            "                position_size = min(position_size, max_quantity)",
            "            position_size = min(position_size, max_quantity)",
        ),
        # 修复函数调用的缩进
        (
            '        """执行买入交易"""\n            order_result = self.broker.place_order(',
            '        """执行买入交易"""\n        order_result = self.broker.place_order(',
        ),
        # 修复if语句的缩进
        (
            "        # 风险管理检查\n        if not force_trade and signal_strength < 0.6:\n                return {",
            "        # 风险管理检查\n        if not force_trade and signal_strength < 0.6:\n            return {",
        ),
        # 修复注释的缩进
        (
            "        # 计算仓位大小\n        position_size",
            "        # 计算仓位大小\n        position_size",
        ),
        # 修复if语句块的缩进
        (
            "        if atr_value > 0:\n            risk_amount",
            "        if atr_value > 0:\n            risk_amount",
        ),
        # 修复else语句的缩进
        (
            "        else:\n            position_size = available_balance * 0.02 / current_price\n\n            # 最小交易量检查",
            "        else:\n            position_size = available_balance * 0.02 / current_price\n\n        # 最小交易量检查",
        ),
        # 修复变量赋值的缩进
        (
            "        positions = self.broker.get_positions()",
            "        positions = self.broker.get_positions()",
        ),
        ("        if btc_position > min_quantity:", "        if btc_position > min_quantity:"),
        (
            '            order_result = self.broker.place_order(\n                symbol=symbol, side="SELL", order_type="MARKET", quantity=sell_quantity\n                    )',
            '            order_result = self.broker.place_order(\n                symbol=symbol, side="SELL", order_type="MARKET", quantity=sell_quantity\n            )',
        ),
    ]

    for old, new in fixes:
        content = content.replace(old, new)

    # 写回文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 语法错误已修复")


if __name__ == "__main__":
    quick_fix()
