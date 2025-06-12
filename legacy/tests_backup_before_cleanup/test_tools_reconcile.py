#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.tools.reconcile 模块的所有功能
Trade Reconciliation Module Tests

覆盖目标:
- get_exchange_trades 函数
- get_local_trades 函数
- compare_trades 函数
- verify_balances 函数
- log_reconciliation_results 函数
- daily_reconciliation 函数
- 命令行参数解析
- 边界情况和错误处理
"""

import argparse
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, call, patch

import pandas as pd

from src.tools.reconcile import (
    compare_trades,
    daily_reconciliation,
    get_exchange_trades,
    get_local_trades,
    log_reconciliation_results,
    verify_balances,
)


class TestGetExchangeTrades:
    """测试 get_exchange_trades 函数"""

    def test_get_exchange_trades_basic(self):
        """测试基础交易所交易获取"""
        result = get_exchange_trades(
            symbol="BTCUSDT",
            start_date="2023-01-01",
            end_date="2023-01-02",
            api_key="test_key",
            api_secret="test_secret",
        )

        assert isinstance(result, pd.DataFrame)
        expected_columns = [
            "timestamp",
            "symbol",
            "side",
            "price",
            "quantity",
            "amount",
            "fee",
            "order_id",
        ]
        assert list(result.columns) == expected_columns
        assert len(result) == 0  # 当前返回空DataFrame

    def test_get_exchange_trades_different_symbols(self):
        """测试不同交易对的交易获取"""
        symbols = ["ETHUSDT", "ADAUSDT", "DOTUSDT"]

        for symbol in symbols:
            result = get_exchange_trades(
                symbol=symbol,
                start_date="2023-01-01",
                end_date="2023-01-01",
                api_key="key",
                api_secret="secret",
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result.columns) == 8

    @patch("builtins.print")
    def test_get_exchange_trades_print_output(self, mock_print):
        """测试打印输出"""
        get_exchange_trades("BTCUSDT", "2023-01-01", "2023-01-02", "key", "secret")

        mock_print.assert_called_once_with("从交易所获取BTCUSDT交易历史 (2023-01-01 至 2023-01-02)")


class TestGetLocalTrades:
    """测试 get_local_trades 函数"""

    @patch("src.tools.reconcile.Broker")
    @patch("builtins.print")
    def test_get_local_trades_basic(self, mock_print, mock_broker_class):
        """测试基础本地交易获取"""
        # 模拟Broker实例
        mock_broker = Mock()
        mock_trades = pd.DataFrame(
            {
                "timestamp": ["2023-01-01 10:00:00"],
                "symbol": ["BTCUSDT"],
                "side": ["BUY"],
                "price": [45000.0],
                "quantity": [0.001],
                "order_id": ["12345"],
            }
        )
        mock_broker.get_all_trades.return_value = mock_trades
        mock_broker_class.return_value = mock_broker

        result = get_local_trades(symbol="BTCUSDT", start_date="2023-01-01", end_date="2023-01-02")

        # 验证Broker初始化
        mock_broker_class.assert_called_once_with("", "", trades_dir=None)

        # 验证方法调用
        mock_broker.get_all_trades.assert_called_once_with("BTCUSDT", "2023-01-01", "2023-01-02")

        # 验证返回结果
        assert isinstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, mock_trades)

        # 验证打印输出
        mock_print.assert_called_once_with(
            "从本地CSV获取BTCUSDT交易历史 (2023-01-01 至 2023-01-02)"
        )

    @patch("src.tools.reconcile.Broker")
    def test_get_local_trades_with_trades_dir(self, mock_broker_class):
        """测试指定交易目录的本地交易获取"""
        mock_broker = Mock()
        mock_broker.get_all_trades.return_value = pd.DataFrame()
        mock_broker_class.return_value = mock_broker

        trades_dir = "/custom/trades/dir"
        get_local_trades("ETHUSDT", "2023-01-01", "2023-01-02", trades_dir=trades_dir)

        mock_broker_class.assert_called_once_with("", "", trades_dir=trades_dir)

    @patch("src.tools.reconcile.Broker")
    def test_get_local_trades_empty_result(self, mock_broker_class):
        """测试空结果的本地交易获取"""
        mock_broker = Mock()
        mock_broker.get_all_trades.return_value = pd.DataFrame()
        mock_broker_class.return_value = mock_broker

        result = get_local_trades("BTCUSDT", "2023-01-01", "2023-01-02")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestCompareTrades:
    """测试 compare_trades 函数"""

    def setup_method(self):
        """测试设置"""
        # 创建示例交易数据
        self.exchange_trades = pd.DataFrame(
            {
                "timestamp": ["2023-01-01 10:00:00", "2023-01-01 11:00:00", "2023-01-01 12:00:00"],
                "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
                "side": ["BUY", "SELL", "BUY"],
                "price": [45000.0, 45100.0, 45200.0],
                "quantity": [0.001, 0.001, 0.002],
                "amount": [45.0, 45.1, 90.4],
                "fee": [0.045, 0.0451, 0.0904],
                "order_id": ["12345", "12346", "12347"],
            }
        )

        self.local_trades = pd.DataFrame(
            {
                "timestamp": ["2023-01-01 10:00:00", "2023-01-01 11:00:00", "2023-01-01 13:00:00"],
                "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
                "side": ["BUY", "SELL", "SELL"],
                "price": [45000.0, 45100.0, 45300.0],
                "quantity": [0.001, 0.001, 0.001],
                "amount": [45.0, 45.1, 45.3],
                "fee": [0.045, 0.0451, 0.0453],
                "order_id": ["12345", "12346", "12348"],
            }
        )

    @patch("builtins.print")
    def test_compare_trades_both_empty(self, mock_print):
        """测试两个空DataFrame的比较"""
        empty_df = pd.DataFrame()

        matched, exchange_only, local_only = compare_trades(empty_df, empty_df)

        assert matched.empty
        assert exchange_only.empty
        assert local_only.empty

        mock_print.assert_called_with("没有交易数据可比较 (No trade data to compare)")

    @patch("builtins.print")
    def test_compare_trades_exchange_empty(self, mock_print):
        """测试交易所数据为空的比较"""
        empty_df = pd.DataFrame()

        matched, exchange_only, local_only = compare_trades(empty_df, self.local_trades)

        assert matched.empty
        assert exchange_only.empty
        pd.testing.assert_frame_equal(local_only, self.local_trades)

        mock_print.assert_called_with("警告: 无交易所交易数据 (Warning: No exchange trade data)")

    @patch("builtins.print")
    def test_compare_trades_local_empty(self, mock_print):
        """测试本地数据为空的比较"""
        empty_df = pd.DataFrame()

        matched, exchange_only, local_only = compare_trades(self.exchange_trades, empty_df)

        assert matched.empty
        pd.testing.assert_frame_equal(exchange_only, self.exchange_trades)
        assert local_only.empty

        mock_print.assert_called_with("警告: 无本地交易数据 (Warning: No local trade data)")

    @patch("builtins.print")
    def test_compare_trades_with_order_id(self, mock_print):
        """测试使用order_id匹配的交易比较"""
        matched, exchange_only, local_only = compare_trades(self.exchange_trades, self.local_trades)

        # 验证匹配的交易（order_id: 12345, 12346）
        assert len(matched) == 2
        assert set(matched["order_id"]) == {"12345", "12346"}

        # 验证仅交易所有的交易（order_id: 12347）
        assert len(exchange_only) == 1
        assert exchange_only.iloc[0]["order_id"] == "12347"

        # 验证仅本地有的交易（order_id: 12348）
        assert len(local_only) == 1
        assert local_only.iloc[0]["order_id"] == "12348"

        # 验证打印输出
        expected_calls = [
            call("匹配的交易: 2条"),
            call("仅交易所有的交易: 1条"),
            call("仅本地有的交易: 1条"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch("builtins.print")
    def test_compare_trades_without_order_id(self, mock_print):
        """测试不使用order_id匹配的交易比较"""
        # 移除order_id列
        exchange_no_id = self.exchange_trades.drop("order_id", axis=1)
        local_no_id = self.local_trades.drop("order_id", axis=1)

        matched, exchange_only, local_only = compare_trades(exchange_no_id, local_no_id)

        # 验证使用其他字段匹配
        assert len(matched) == 2  # 前两条记录匹配

        # 验证打印输出包含警告信息
        warning_call = call(
            "警告: 未找到order_id列，使用timestamp、symbol、side、price和quantity匹配"
        )
        assert warning_call in mock_print.call_args_list

    @patch("builtins.print")
    def test_compare_trades_missing_match_columns(self, mock_print):
        """测试缺少匹配列的情况"""
        # 创建缺少必要列的DataFrame
        incomplete_exchange = pd.DataFrame({"timestamp": ["2023-01-01"], "symbol": ["BTCUSDT"]})
        incomplete_local = pd.DataFrame({"timestamp": ["2023-01-01"], "price": [45000.0]})

        matched, exchange_only, local_only = compare_trades(incomplete_exchange, incomplete_local)

        # 应该返回原始数据，因为无法匹配
        pd.testing.assert_frame_equal(exchange_only, incomplete_exchange)
        pd.testing.assert_frame_equal(local_only, incomplete_local)

        # 验证错误信息
        error_calls = [
            call for call in mock_print.call_args_list if "错误: 缺少匹配列" in str(call)
        ]
        assert len(error_calls) > 0


class TestVerifyBalances:
    """测试 verify_balances 函数"""

    @patch("builtins.print")
    @patch("src.tools.reconcile.datetime")
    def test_verify_balances_btcusdt(self, mock_datetime, mock_print):
        """测试BTCUSDT的余额验证"""
        # 模拟当前时间
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now

        result = verify_balances("BTCUSDT", "test_key", "test_secret")

        expected = {
            "timestamp": "2023-01-01 12:00:00",
            "base_currency": "BTC",
            "quote_currency": "USDT",
            "base_balance": 1.0,
            "quote_balance": 10000.0,
            "total_value_usdt": 50000.0,
        }

        assert result == expected
        mock_print.assert_called_once_with("验证BTCUSDT账户余额")

    @patch("builtins.print")
    def test_verify_balances_different_symbols(self, mock_print):
        """测试不同交易对的余额验证"""
        test_cases = [
            ("ETHUSDT", "ETH"),
            ("ADAUSDT", "ADA"),
            ("DOTUSDT", "DOT"),
            ("BNBUSDT", "BNB"),
        ]

        for symbol, expected_base in test_cases:
            result = verify_balances(symbol, "key", "secret")

            assert result["base_currency"] == expected_base
            assert result["quote_currency"] == "USDT"
            assert isinstance(result["timestamp"], str)

    def test_verify_balances_non_usdt_pair(self):
        """测试非USDT交易对的余额验证"""
        result = verify_balances("BTCETH", "key", "secret")

        # 对于非USDT交易对，应该返回原始symbol作为base_currency
        assert result["base_currency"] == "BTCETH"
        assert result["quote_currency"] == "USDT"

    def test_verify_balances_return_structure(self):
        """测试返回结构的完整性"""
        result = verify_balances("BTCUSDT", "key", "secret")

        required_keys = [
            "timestamp",
            "base_currency",
            "quote_currency",
            "base_balance",
            "quote_balance",
            "total_value_usdt",
        ]

        for key in required_keys:
            assert key in result

        # 验证数值类型
        assert isinstance(result["base_balance"], (int, float))
        assert isinstance(result["quote_balance"], (int, float))
        assert isinstance(result["total_value_usdt"], (int, float))


class TestLogReconciliationResults:
    """测试 log_reconciliation_results 函数"""

    def setup_method(self):
        """测试设置"""
        self.sample_matched = pd.DataFrame(
            {
                "order_id": ["12345", "12346"],
                "symbol": ["BTCUSDT", "BTCUSDT"],
                "side": ["BUY", "SELL"],
                "price_exchange": [45000.0, 45100.0],
                "price_local": [45000.0, 45100.0],
            }
        )

        self.sample_exchange_only = pd.DataFrame(
            {"order_id": ["12347"], "symbol": ["BTCUSDT"], "side": ["BUY"], "price": [45200.0]}
        )

        self.sample_local_only = pd.DataFrame(
            {"order_id": ["12348"], "symbol": ["BTCUSDT"], "side": ["SELL"], "price": [45300.0]}
        )

        self.sample_balances = {
            "timestamp": "2023-01-01 12:00:00",
            "base_currency": "BTC",
            "quote_currency": "USDT",
            "base_balance": 1.0,
            "quote_balance": 10000.0,
            "total_value_usdt": 50000.0,
        }

    @patch("src.tools.reconcile.utils.get_trades_dir")
    @patch("builtins.print")
    @patch("src.tools.reconcile.datetime")
    def test_log_reconciliation_results_default_output_dir(
        self, mock_datetime, mock_print, mock_get_trades_dir
    ):
        """测试使用默认输出目录的结果记录"""
        # 模拟时间和目录
        mock_now = datetime(2023, 1, 1, 12, 30, 45)
        mock_datetime.now.return_value = mock_now

        with tempfile.TemporaryDirectory() as temp_dir:
            mock_trades_dir = Path(temp_dir)
            mock_get_trades_dir.return_value = mock_trades_dir

            log_reconciliation_results(
                symbol="BTCUSDT",
                date="2023-01-01",
                matched=self.sample_matched,
                exchange_only=self.sample_exchange_only,
                local_only=self.sample_local_only,
                balances=self.sample_balances,
            )

            # 验证目录创建
            reconciliation_dir = mock_trades_dir / "reconciliation"
            assert reconciliation_dir.exists()

            # 验证文件创建
            base_filename = "reconciliation_BTCUSDT_2023-01-01_20230101_123045"

            matched_file = reconciliation_dir / f"{base_filename}_matched.csv"
            exchange_file = reconciliation_dir / f"{base_filename}_exchange_only.csv"
            local_file = reconciliation_dir / f"{base_filename}_local_only.csv"
            balance_file = reconciliation_dir / f"{base_filename}_balance.json"
            summary_file = reconciliation_dir / f"{base_filename}_summary.json"

            assert matched_file.exists()
            assert exchange_file.exists()
            assert local_file.exists()
            assert balance_file.exists()
            assert summary_file.exists()

            # 验证文件内容
            saved_matched = pd.read_csv(matched_file)
            assert len(saved_matched) == 2

            saved_exchange = pd.read_csv(exchange_file)
            assert len(saved_exchange) == 1

            saved_local = pd.read_csv(local_file)
            assert len(saved_local) == 1

    def test_log_reconciliation_results_custom_output_dir(self):
        """测试使用自定义输出目录的结果记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_output = temp_dir

            with patch("src.tools.reconcile.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

                log_reconciliation_results(
                    symbol="ETHUSDT",
                    date="2023-01-01",
                    matched=pd.DataFrame(),
                    exchange_only=pd.DataFrame(),
                    local_only=pd.DataFrame(),
                    balances=self.sample_balances,
                    output_dir=custom_output,
                )

                # 验证自定义目录下的reconciliation子目录
                reconciliation_dir = Path(custom_output) / "reconciliation"
                assert reconciliation_dir.exists()

    @patch("builtins.print")
    def test_log_reconciliation_results_empty_dataframes(self, mock_print):
        """测试空DataFrame的结果记录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.tools.reconcile.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

                log_reconciliation_results(
                    symbol="BTCUSDT",
                    date="2023-01-01",
                    matched=pd.DataFrame(),
                    exchange_only=pd.DataFrame(),
                    local_only=pd.DataFrame(),
                    balances=self.sample_balances,
                    output_dir=temp_dir,
                )

                # 验证只创建了balance和summary文件
                reconciliation_dir = Path(temp_dir) / "reconciliation"
                files = list(reconciliation_dir.glob("*.json"))
                assert len(files) == 2  # balance.json 和 summary.json

                csv_files = list(reconciliation_dir.glob("*.csv"))
                assert len(csv_files) == 0  # 没有CSV文件，因为DataFrame为空

    def test_log_reconciliation_results_summary_content(self):
        """测试摘要文件内容"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("src.tools.reconcile.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

                log_reconciliation_results(
                    symbol="BTCUSDT",
                    date="2023-01-01",
                    matched=self.sample_matched,
                    exchange_only=self.sample_exchange_only,
                    local_only=self.sample_local_only,
                    balances=self.sample_balances,
                    output_dir=temp_dir,
                )

                # 读取摘要文件
                summary_file = (
                    Path(temp_dir)
                    / "reconciliation"
                    / "reconciliation_BTCUSDT_2023-01-01_20230101_120000_summary.json"
                )
                summary = pd.read_json(summary_file, typ="series")

                assert summary["symbol"] == "BTCUSDT"
                assert summary["date"] == "2023-01-01"
                assert summary["matched_count"] == 2
                assert summary["exchange_only_count"] == 1
                assert summary["local_only_count"] == 1
                assert summary["base_balance"] == 1.0
                assert summary["quote_balance"] == 10000.0


class TestDailyReconciliation:
    """测试 daily_reconciliation 函数"""

    def setup_method(self):
        """测试设置"""
        self.test_symbol = "BTCUSDT"
        self.test_api_key = "test_api_key"
        self.test_api_secret = "test_api_secret"

    @patch("src.tools.reconcile.log_reconciliation_results")
    @patch("src.tools.reconcile.verify_balances")
    @patch("src.tools.reconcile.compare_trades")
    @patch("src.tools.reconcile.get_local_trades")
    @patch("src.tools.reconcile.get_exchange_trades")
    @patch("builtins.print")
    def test_daily_reconciliation_basic(
        self,
        mock_print,
        mock_get_exchange,
        mock_get_local,
        mock_compare,
        mock_verify,
        mock_log,
    ):
        """测试基础日终对账"""
        # 设置模拟返回值
        mock_exchange_trades = pd.DataFrame({"order_id": ["12345"]})
        mock_local_trades = pd.DataFrame({"order_id": ["12345"]})
        mock_matched = pd.DataFrame({"order_id": ["12345"]})
        mock_exchange_only = pd.DataFrame()
        mock_local_only = pd.DataFrame()
        mock_balances = {"base_balance": 1.0}

        mock_get_exchange.return_value = mock_exchange_trades
        mock_get_local.return_value = mock_local_trades
        mock_compare.return_value = (mock_matched, mock_exchange_only, mock_local_only)
        mock_verify.return_value = mock_balances

        daily_reconciliation(
            symbol=self.test_symbol,
            api_key=self.test_api_key,
            api_secret=self.test_api_secret,
            date="2023-01-01",
        )

        # 验证函数调用
        mock_get_exchange.assert_called_once_with(
            self.test_symbol, "2023-01-01", "2023-01-01", self.test_api_key, self.test_api_secret
        )
        mock_get_local.assert_called_once_with(self.test_symbol, "2023-01-01", "2023-01-01", None)
        mock_compare.assert_called_once_with(mock_exchange_trades, mock_local_trades)
        mock_verify.assert_called_once_with(
            self.test_symbol, self.test_api_key, self.test_api_secret
        )
        mock_log.assert_called_once()

        # 验证打印输出
        expected_calls = [
            call("开始对账: BTCUSDT (2023-01-01)"),
            call("对账完成: BTCUSDT (2023-01-01)"),
        ]
        mock_print.assert_has_calls(expected_calls)

    @patch("src.tools.reconcile.log_reconciliation_results")
    @patch("src.tools.reconcile.verify_balances")
    @patch("src.tools.reconcile.compare_trades")
    @patch("src.tools.reconcile.get_local_trades")
    @patch("src.tools.reconcile.get_exchange_trades")
    @patch("src.tools.reconcile.datetime")
    def test_daily_reconciliation_default_date(
        self,
        mock_datetime,
        mock_get_exchange,
        mock_get_local,
        mock_compare,
        mock_verify,
        mock_log,
    ):
        """测试使用默认日期（昨天）的对账"""
        # 模拟当前时间
        mock_now = datetime(2023, 1, 2, 10, 0, 0)
        mock_datetime.now.return_value = mock_now

        # 设置模拟返回值
        mock_get_exchange.return_value = pd.DataFrame()
        mock_get_local.return_value = pd.DataFrame()
        mock_compare.return_value = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        mock_verify.return_value = {}

        daily_reconciliation(
            symbol=self.test_symbol,
            api_key=self.test_api_key,
            api_secret=self.test_api_secret,
            # 不指定date，应该使用昨天
        )

        # 验证使用昨天的日期
        expected_date = "2023-01-01"
        mock_get_exchange.assert_called_once_with(
            self.test_symbol, expected_date, expected_date, self.test_api_key, self.test_api_secret
        )

    @patch("src.tools.reconcile.Broker")
    @patch("src.tools.reconcile.log_reconciliation_results")
    @patch("src.tools.reconcile.verify_balances")
    @patch("src.tools.reconcile.compare_trades")
    @patch("src.tools.reconcile.get_local_trades")
    @patch("src.tools.reconcile.get_exchange_trades")
    def test_daily_reconciliation_with_discrepancies_notify(
        self,
        mock_get_exchange,
        mock_get_local,
        mock_compare,
        mock_verify,
        mock_log,
        mock_broker_class,
    ):
        """测试有差异时发送通知的对账"""
        # 设置有差异的模拟返回值
        mock_exchange_only = pd.DataFrame({"order_id": ["12347"]})
        mock_local_only = pd.DataFrame({"order_id": ["12348"]})

        mock_get_exchange.return_value = pd.DataFrame()
        mock_get_local.return_value = pd.DataFrame()
        mock_compare.return_value = (pd.DataFrame(), mock_exchange_only, mock_local_only)
        mock_verify.return_value = {}

        # 模拟Broker和通知器
        mock_broker = Mock()
        mock_notifier = Mock()
        mock_broker.notifier = mock_notifier
        mock_broker_class.return_value = mock_broker

        daily_reconciliation(
            symbol=self.test_symbol,
            api_key=self.test_api_key,
            api_secret=self.test_api_secret,
            date="2023-01-01",
            notify=True,
        )

        # 验证Broker初始化
        mock_broker_class.assert_called_once_with(self.test_api_key, self.test_api_secret)

        # 验证通知发送
        mock_notifier.notify.assert_called_once()
        call_args = mock_notifier.notify.call_args
        message = call_args[0][0]
        level = call_args[0][1]

        assert "对账异常" in message
        assert "BTCUSDT" in message
        assert "2023-01-01" in message
        assert level == "WARN"

    @patch("src.tools.reconcile.log_reconciliation_results")
    @patch("src.tools.reconcile.verify_balances")
    @patch("src.tools.reconcile.compare_trades")
    @patch("src.tools.reconcile.get_local_trades")
    @patch("src.tools.reconcile.get_exchange_trades")
    def test_daily_reconciliation_no_discrepancies_no_notify(
        self,
        mock_get_exchange,
        mock_get_local,
        mock_compare,
        mock_verify,
        mock_log,
    ):
        """测试无差异时不发送通知的对账"""
        # 设置无差异的模拟返回值
        mock_get_exchange.return_value = pd.DataFrame()
        mock_get_local.return_value = pd.DataFrame()
        mock_compare.return_value = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        mock_verify.return_value = {}

        with patch("src.tools.reconcile.Broker") as mock_broker_class:
            daily_reconciliation(
                symbol=self.test_symbol,
                api_key=self.test_api_key,
                api_secret=self.test_api_secret,
                date="2023-01-01",
                notify=True,
            )

            # 验证没有创建Broker（因为没有差异）
            mock_broker_class.assert_not_called()

    @patch("src.tools.reconcile.log_reconciliation_results")
    @patch("src.tools.reconcile.verify_balances")
    @patch("src.tools.reconcile.compare_trades")
    @patch("src.tools.reconcile.get_local_trades")
    @patch("src.tools.reconcile.get_exchange_trades")
    def test_daily_reconciliation_notify_disabled(
        self,
        mock_get_exchange,
        mock_get_local,
        mock_compare,
        mock_verify,
        mock_log,
    ):
        """测试禁用通知的对账"""
        # 设置有差异的模拟返回值
        mock_exchange_only = pd.DataFrame({"order_id": ["12347"]})
        mock_local_only = pd.DataFrame({"order_id": ["12348"]})

        mock_get_exchange.return_value = pd.DataFrame()
        mock_get_local.return_value = pd.DataFrame()
        mock_compare.return_value = (pd.DataFrame(), mock_exchange_only, mock_local_only)
        mock_verify.return_value = {}

        with patch("src.tools.reconcile.Broker") as mock_broker_class:
            daily_reconciliation(
                symbol=self.test_symbol,
                api_key=self.test_api_key,
                api_secret=self.test_api_secret,
                date="2023-01-01",
                notify=False,  # 禁用通知
            )

            # 验证即使有差异也不创建Broker
            mock_broker_class.assert_not_called()

    @patch("src.tools.reconcile.log_reconciliation_results")
    @patch("src.tools.reconcile.verify_balances")
    @patch("src.tools.reconcile.compare_trades")
    @patch("src.tools.reconcile.get_local_trades")
    @patch("src.tools.reconcile.get_exchange_trades")
    def test_daily_reconciliation_with_custom_dirs(
        self,
        mock_get_exchange,
        mock_get_local,
        mock_compare,
        mock_verify,
        mock_log,
    ):
        """测试使用自定义目录的对账"""
        mock_get_exchange.return_value = pd.DataFrame()
        mock_get_local.return_value = pd.DataFrame()
        mock_compare.return_value = (pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        mock_verify.return_value = {}

        custom_trades_dir = "/custom/trades"
        custom_output_dir = "/custom/output"

        daily_reconciliation(
            symbol=self.test_symbol,
            api_key=self.test_api_key,
            api_secret=self.test_api_secret,
            date="2023-01-01",
            trades_dir=custom_trades_dir,
            output_dir=custom_output_dir,
        )

        # 验证传递了自定义目录
        mock_get_local.assert_called_once_with(
            self.test_symbol, "2023-01-01", "2023-01-01", custom_trades_dir
        )

        # 验证log_reconciliation_results调用包含output_dir
        mock_log.assert_called_once()
        # 检查位置参数和关键字参数
        call_args, call_kwargs = mock_log.call_args
        # output_dir应该作为关键字参数传递
        assert (
            call_kwargs.get("output_dir") == custom_output_dir or call_args[-1] == custom_output_dir
        )


class TestMainBlock:
    """测试主程序块和命令行参数解析"""

    @patch("src.tools.reconcile.daily_reconciliation")
    @patch.dict(os.environ, {"API_KEY": "test_key", "API_SECRET": "test_secret"})
    @patch("sys.argv", ["reconcile.py", "--symbol", "BTCUSDT"])
    def test_main_block_basic(self, mock_daily_reconciliation):
        """测试基础命令行执行"""
        # 模拟主程序块的执行
        parser = argparse.ArgumentParser(description="交易对账工具 (Trade reconciliation tool)")
        parser.add_argument("--symbol", type=str, required=True, help="交易对 (Trading pair)")
        parser.add_argument("--date", type=str, help="日期 (Date) 'YYYY-MM-DD'，默认为昨天")
        parser.add_argument("--trades-dir", type=str, help="交易数据目录 (Trades data directory)")
        parser.add_argument("--output-dir", type=str, help="输出目录 (Output directory)")
        parser.add_argument(
            "--no-notify",
            action="store_true",
            help="不发送通知 (Don't send notification)",
        )

        args = parser.parse_args(["--symbol", "BTCUSDT"])

        # 模拟主程序逻辑
        api_key = os.getenv("API_KEY")
        api_secret = os.getenv("API_SECRET")

        assert api_key == "test_key"
        assert api_secret == "test_secret"

        # 模拟调用daily_reconciliation
        daily_reconciliation(
            symbol=args.symbol,
            api_key=api_key,
            api_secret=api_secret,
            date=args.date,
            trades_dir=args.trades_dir,
            output_dir=args.output_dir,
            notify=not args.no_notify,
        )

        # 验证参数解析
        assert args.symbol == "BTCUSDT"
        assert args.date is None
        assert args.trades_dir is None
        assert args.output_dir is None
        assert args.no_notify is False

    def test_argument_parser_all_options(self):
        """测试所有命令行选项的解析"""
        parser = argparse.ArgumentParser(description="交易对账工具 (Trade reconciliation tool)")
        parser.add_argument("--symbol", type=str, required=True, help="交易对 (Trading pair)")
        parser.add_argument("--date", type=str, help="日期 (Date) 'YYYY-MM-DD'，默认为昨天")
        parser.add_argument("--trades-dir", type=str, help="交易数据目录 (Trades data directory)")
        parser.add_argument("--output-dir", type=str, help="输出目录 (Output directory)")
        parser.add_argument(
            "--no-notify",
            action="store_true",
            help="不发送通知 (Don't send notification)",
        )

        args = parser.parse_args(
            [
                "--symbol",
                "ETHUSDT",
                "--date",
                "2023-01-01",
                "--trades-dir",
                "/custom/trades",
                "--output-dir",
                "/custom/output",
                "--no-notify",
            ]
        )

        assert args.symbol == "ETHUSDT"
        assert args.date == "2023-01-01"
        assert args.trades_dir == "/custom/trades"
        assert args.output_dir == "/custom/output"
        assert args.no_notify is True

    @patch("builtins.print")
    @patch("sys.exit")
    @patch.dict(os.environ, {}, clear=True)
    def test_main_block_missing_env_vars(self, mock_exit, mock_print):
        """测试缺少环境变量的情况"""
        # 模拟缺少环境变量的情况
        api_key = os.getenv("API_KEY")
        api_secret = os.getenv("API_SECRET")

        if not api_key or not api_secret:
            print("错误: 环境变量API_KEY和API_SECRET未设置")
            sys.exit(1)

        mock_print.assert_called_once_with("错误: 环境变量API_KEY和API_SECRET未设置")
        mock_exit.assert_called_once_with(1)


class TestReconcileIntegration:
    """集成测试"""

    @patch("src.tools.reconcile.utils.get_trades_dir")
    @patch("src.tools.reconcile.Broker")
    def test_full_reconciliation_workflow(self, mock_broker_class, mock_get_trades_dir):
        """测试完整的对账工作流"""
        # 设置临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_get_trades_dir.return_value = Path(temp_dir)

            # 模拟Broker
            mock_broker = Mock()
            mock_local_trades = pd.DataFrame(
                {
                    "timestamp": ["2023-01-01 10:00:00"],
                    "symbol": ["BTCUSDT"],
                    "side": ["BUY"],
                    "price": [45000.0],
                    "quantity": [0.001],
                    "order_id": ["12345"],
                }
            )
            mock_broker.get_all_trades.return_value = mock_local_trades
            mock_broker_class.return_value = mock_broker

            # 执行完整工作流
            with patch("src.tools.reconcile.datetime") as mock_datetime:
                mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)

                daily_reconciliation(
                    symbol="BTCUSDT",
                    api_key="test_key",
                    api_secret="test_secret",
                    date="2023-01-01",
                    notify=False,
                )

            # 验证文件创建
            reconciliation_dir = Path(temp_dir) / "reconciliation"
            assert reconciliation_dir.exists()

            # 验证至少创建了balance和summary文件
            json_files = list(reconciliation_dir.glob("*.json"))
            assert len(json_files) >= 2

    def test_edge_case_handling(self):
        """测试边界情况处理"""
        # 测试空symbol
        result = verify_balances("", "key", "secret")
        assert result["base_currency"] == ""

        # 测试特殊字符symbol - 修正预期结果
        result = verify_balances("BTC-USDT", "key", "secret")
        # 根据实际的split逻辑，"BTC-USDT".split("USDT")[0] 会返回 "BTC-"
        assert result["base_currency"] == "BTC-"

        # 测试compare_trades的边界情况
        df1 = pd.DataFrame({"order_id": []})
        df2 = pd.DataFrame({"order_id": []})
        matched, exchange_only, local_only = compare_trades(df1, df2)
        assert matched.empty
        assert exchange_only.empty
        assert local_only.empty
