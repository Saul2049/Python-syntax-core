#!/usr/bin/env python3

import os
from unittest.mock import Mock, patch

# 设置环境变量
os.environ["TELEGRAM_CHAT_ID"] = "test_chat_id_12345"
os.environ["TELEGRAM_TOKEN"] = "test_token_67890"

with patch.dict(
    "sys.modules",
    {
        "src.brokers": Mock(),
        "src.brokers.exchange": Mock(),
        "src.brokers.binance": Mock(),
        "src.monitoring.metrics_collector": Mock(),
        "src.core.signal_processor_vectorized": Mock(),
        "src.core.signal_processor": Mock(),
    },
):
    with (
        patch("src.brokers.broker.Broker") as mock_broker_class,
        patch("src.monitoring.get_metrics_collector") as mock_metrics,
        patch("src.core.signal_processor_vectorized.OptimizedSignalProcessor") as mock_processor,
    ):

        # 正确配置Mock broker
        mock_broker = Mock()
        # 关键修复：确保get_account_balance返回真正的字典，而不是Mock
        mock_broker.get_account_balance.return_value = {"balance": 10000.0}
        mock_broker.positions = {}
        mock_broker_class.return_value = mock_broker

        mock_metrics.return_value = Mock()
        mock_processor.return_value = Mock()

        from src.core.trading_engine import TradingEngine

        engine = TradingEngine()

        print("=== 修复后调试信息 ===")
        print("account_equity type:", type(engine.account_equity))
        print("account_equity value:", engine.account_equity)
        print("peak_balance type:", type(engine.peak_balance))
        print("peak_balance value:", engine.peak_balance)

        # 测试get_account_balance
        account_info = engine.broker.get_account_balance()
        print("account_info type:", type(account_info))
        print("account_info:", account_info)
        current_balance = account_info.get("balance", engine.account_equity)
        print("current_balance type:", type(current_balance))
        print("current_balance value:", current_balance)

        # 测试比较
        try:
            result = current_balance > engine.peak_balance
            print("比较结果:", result)
            print("✅ 比较成功!")
        except Exception as e:
            print("❌ 比较失败:", e)
