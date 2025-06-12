#!/usr/bin/env python3
"""
测试环境设置脚本
设置运行测试所需的环境变量
"""

import os


def setup_test_environment():
    """设置测试环境变量"""
    test_env_vars = {
        "TELEGRAM_CHAT_ID": "test_chat_id_12345",
        "TELEGRAM_TOKEN": "test_token_67890",
        "BINANCE_API_KEY": "test_binance_api_key",
        "BINANCE_SECRET_KEY": "test_binance_secret_key",
        "TRADING_ENV": "test",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": os.getcwd(),
    }

    for key, value in test_env_vars.items():
        os.environ[key] = value
        print(f"✅ 设置环境变量: {key} = {value}")

    print("\n🎯 测试环境设置完成！")
    return test_env_vars


if __name__ == "__main__":
    setup_test_environment()
