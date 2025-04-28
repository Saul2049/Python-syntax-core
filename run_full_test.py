#!/usr/bin/env python3
"""
直接运行Telegram完整通知测试
"""
import os
from test_telegram import test_trade_notifications

# 设置Telegram凭据
TOKEN = os.getenv("TG_TOKEN") or "7599104627:AAEu3qFQjJvnjiodNjR1MOgp4pX0VVxU2Hk"
CHAT_ID = os.getenv("TG_CHAT") or "269242161"

# 测试参数
FORMAT = os.getenv("TG_FORMAT") or "html"  # 可选: text, html, markdown
DEBUG = os.getenv("TG_DEBUG") == "1"        # 设置环境变量 TG_DEBUG=1 启用调试

print(f"开始测试完整的交易通知系列...")
print(f"使用格式: {FORMAT}")
if DEBUG:
    print("调试模式已启用")

success = test_trade_notifications(TOKEN, CHAT_ID, FORMAT, DEBUG)

if success:
    print("✅ 测试完成！所有通知发送成功")
else:
    print("❌ 测试失败！部分通知发送失败")
    exit(1) 