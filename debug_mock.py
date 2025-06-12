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

        mock_broker = Mock()
        mock_broker.get_account_balance.return_value = {"balance": 10000.0}
        mock_broker_class.return_value = mock_broker
        mock_metrics.return_value = Mock()
        mock_processor.return_value = Mock()

        from src.core.trading_engine import TradingEngine

        engine = TradingEngine()

        print("=== 调试信息 ===")
        print("account_equity type:", type(engine.account_equity))
        print("account_equity value:", engine.account_equity)
        print("peak_balance type:", type(engine.peak_balance))
        print("peak_balance value:", engine.peak_balance)

        # 测试get_account_balance
        account_info = engine.broker.get_account_balance()
        print("account_info:", account_info)
        current_balance = account_info.get("balance", engine.account_equity)
        print("current_balance type:", type(current_balance))
        print("current_balance value:", current_balance)

        # 手动设置
        engine.account_equity = 10000.0
        engine.peak_balance = 10000.0
        print("=== 手动设置后 ===")
        print("account_equity type:", type(engine.account_equity))
        print("peak_balance type:", type(engine.peak_balance))

        # 再次测试
        current_balance = account_info.get("balance", engine.account_equity)
        print("current_balance type after manual set:", type(current_balance))
        print("current_balance value after manual set:", current_balance)
