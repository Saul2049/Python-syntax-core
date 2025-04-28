#!/usr/bin/env python3
"""
测试Telegram通知功能
"""
import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

# 尝试加载.env文件中的环境变量
load_dotenv()

# 最大重试次数
MAX_RETRIES = 3
# 重试延迟(秒)
RETRY_DELAY = 2


def setup_parser():
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(description="测试Telegram通知功能")

    parser.add_argument(
        "--token", type=str, help="Telegram Bot Token (可选，优先使用环境变量)"
    )
    parser.add_argument(
        "--chat", type=str, help="Telegram Chat ID (可选，优先使用环境变量)"
    )
    parser.add_argument(
        "--message",
        type=str,
        default="✅ 交易系统通知测试成功!",
        help="要发送的测试消息 (默认: ✅ 交易系统通知测试成功!)",
    )
    parser.add_argument(
        "--full-test",
        action="store_true",
        help="直接运行完整通知测试，无需交互确认",
    )
    parser.add_argument(
        "--debug", action="store_true", help="显示详细的调试信息和API响应"
    )
    parser.add_argument(
        "--format",
        choices=["text", "html", "markdown"],
        default="html",
        help="消息格式化方式 (默认: html)",
    )

    return parser


def check_network_connection(url="https://api.telegram.org"):
    """检查网络连接是否正常"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def send_telegram(
    token, chat_id, message, parse_mode="HTML", debug=False, retry=0
):
    """发送Telegram消息"""
    if not token or not chat_id:
        print("错误: 未提供Telegram Token或Chat ID")
        return False

    # 检查网络连接
    if not check_network_connection():
        print("错误: 无法连接到Telegram API，请检查网络连接")
        return False

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}

        # 仅当非纯文本时添加parse_mode
        if parse_mode.lower() != "text":
            payload["parse_mode"] = parse_mode

        if debug:
            print(f"DEBUG - 请求URL: {url}")
            print(
                "DEBUG - 请求参数: "
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
            )

        response = requests.post(url, json=payload)

        if debug:
            print(f"DEBUG - 状态码: {response.status_code}")
            print(f"DEBUG - 响应内容: {response.text}")

        if response.status_code == 200:
            print("Telegram通知发送成功!")
            return True
        elif response.status_code == 429 and retry < MAX_RETRIES:  # 分割长行
            # 处理API速率限制
            print(f"警告: API速率限制，等待{RETRY_DELAY}秒后重试...")
            time.sleep(RETRY_DELAY)
            return send_telegram(
                token, chat_id, message, parse_mode, debug, retry + 1
            )
        else:
            print(f"Telegram通知发送失败: HTTP {response.status_code}")
            print(f"错误详情: {response.text}")

            # 重试逻辑
            if retry < MAX_RETRIES:
                print(f"尝试重试 ({retry+1}/{MAX_RETRIES})...")
                time.sleep(RETRY_DELAY)
                return send_telegram(
                    token, chat_id, message, parse_mode, debug, retry + 1
                )
            return False
    except requests.exceptions.ConnectionError:
        print("错误: 网络连接问题，无法连接到Telegram API")
        if retry < MAX_RETRIES:
            print(f"尝试重试 ({retry+1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            result = send_telegram(
                token, chat_id, message, parse_mode, debug, retry + 1
            )
            return result
        return False
    except Exception as e:
        print(f"Telegram通知错误: {e}")
        if retry < MAX_RETRIES:
            print(f"尝试重试 ({retry+1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            result = send_telegram(
                token, chat_id, message, parse_mode, debug, retry + 1
            )
            return result
        return False


def get_formatted_messages(format_type):
    """根据格式类型获取适当格式化的消息"""
    if format_type.lower() == "html":
        return [
            # 买入信号
            "🟢 <b>买入信号</b>\n0.123 BTC @ 50123.45 USDT\n"
            "止损价: 49500.00 USDT\n账户余额: 12345.67 USDT",
            # 等待2秒
            None,
            # 止损更新
            "🔶 <b>止损更新</b>\n0.123 BTC 持仓\n"
            "新止损价: 49800.00 USDT\n账户余额: 12345.67 USDT",
            # 等待2秒
            None,
            # 卖出信号
            "🔴 <b>卖出信号</b>\n0.123 BTC @ 51234.56 USDT\n"
            "账户余额: 12678.90 USDT",
        ]
    elif format_type.lower() == "markdown":
        return [
            # 买入信号
            "🟢 *买入信号*\n0.123 BTC @ 50123.45 USDT\n"
            "止损价: 49500.00 USDT\n账户余额: 12345.67 USDT",
            # 等待2秒
            None,
            # 止损更新
            "🔶 *止损更新*\n0.123 BTC 持仓\n"
            "新止损价: 49800.00 USDT\n账户余额: 12345.67 USDT",
            # 等待2秒
            None,
            # 卖出信号
            "🔴 *卖出信号*\n0.123 BTC @ 51234.56 USDT\n"
            "账户余额: 12678.90 USDT",
        ]
    else:  # text
        return [
            # 买入信号
            "🟢 买入信号\n0.123 BTC @ 50123.45 USDT\n"
            "止损价: 49500.00 USDT\n账户余额: 12345.67 USDT",
            # 等待2秒
            None,
            # 止损更新
            "🔶 止损更新\n0.123 BTC 持仓\n"
            "新止损价: 49800.00 USDT\n账户余额: 12345.67 USDT",
            # 等待2秒
            None,
            # 卖出信号
            "🔴 卖出信号\n0.123 BTC @ 51234.56 USDT\n"
            "账户余额: 12678.90 USDT",
        ]


def test_trade_notifications(token, chat_id, format_type="html", debug=False):
    """测试各种交易通知格式"""
    # 获取相应格式的消息
    messages = get_formatted_messages(format_type)

    if debug:
        print(f"DEBUG - 使用 {format_type} 格式发送通知")

    success = True
    for msg in messages:
        if msg is None:
            # 这是一个暂停
            time.sleep(2)
            continue

        if not send_telegram(token, chat_id, msg, format_type, debug):
            success = False
            break
        time.sleep(1)  # 发送消息之间的短暂停顿

    return success


def secure_token_display(token):
    """安全显示Token，只显示首尾字符"""
    if not token or len(token) < 8:
        return "***"
    return f"{token[:5]}...{token[-5:]}"


def main():
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()

    # 从命令行参数或环境变量获取凭据
    token = args.token or os.getenv("TG_TOKEN")
    chat_id = args.chat or os.getenv("TG_CHAT")
    debug = args.debug
    format_type = args.format

    if not token or not chat_id:
        print("\n错误: 未找到Telegram凭据")
        print("请通过以下方式之一提供凭据:")
        print("1. 命令行参数: --token YOUR_TOKEN --chat YOUR_CHAT_ID")
        print("2. 环境变量: 设置 TG_TOKEN 和 TG_CHAT")
        print(
            "3. 使用load_env.py脚本: python load_env.py "
            "--tg_token=YOUR_TOKEN --tg_chat=YOUR_CHAT_ID --save"
        )
        return 1

    print("Telegram配置:")
    print(f"Token: {secure_token_display(token)}")
    print(f"Chat ID: {chat_id}")
    print(f"格式: {format_type}")

    if debug:
        print("调试模式已启用")

    # 发送单个测试消息
    success = send_telegram(token, chat_id, args.message, format_type, debug)

    # 如果成功且请求完整测试或以非交互方式测试
    if success and (
        args.full_test
        or (
            not args.full_test
            and sys.stdin.isatty()
            and input("是否要测试完整的交易通知系列? (Y/n): ").strip().lower()
            in ["", "y", "yes"]
        )
    ):
        print("\n测试交易通知序列...")
        test_success = test_trade_notifications(
            token, chat_id, format_type, debug
        )
        if test_success:
            print("所有通知发送成功!")
        else:
            print("通知测试过程中发生错误")
            return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
