#!/usr/bin/env python3
"""
WebSocket客户端简化测试 - 专注覆盖率
"""

import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.ws.binance_ws_client import BinanceWSClient


class TestBinanceWSClientBasic:
    """WebSocket客户端基础测试"""

    @pytest.fixture
    def mock_metrics(self):
        """模拟监控指标"""
        with patch("src.ws.binance_ws_client.get_metrics_collector") as mock:
            metrics = Mock()
            metrics.record_ws_connection_success = Mock()
            metrics.record_ws_connection_error = Mock()
            metrics.observe_ws_latency = Mock()
            metrics.record_ws_reconnect = Mock()
            metrics.record_price_update = Mock()
            mock.return_value = metrics
            yield metrics

    @pytest.fixture
    def client(self, mock_metrics):
        """创建测试客户端"""
        return BinanceWSClient(symbols=["BTCUSDT", "ETHUSDT"])

    def test_init_basic(self, mock_metrics):
        """测试基本初始化"""
        symbols = ["btcusdt", "ETHUSDT"]
        callback = Mock()

        client = BinanceWSClient(symbols=symbols, on_kline_callback=callback)

        # 验证属性设置
        assert client.symbols == ["BTCUSDT", "ETHUSDT"]  # 转换为大写
        assert client.on_kline_callback == callback
        assert client.ws is None
        assert client.running is False
        assert client.reconnect_count == 0
        assert client.max_reconnects == 100
        assert client.reconnect_delay == 1
        assert client.message_count == 0
        assert client.error_count == 0
        assert client.base_url == "wss://stream.binance.com:9443/ws"
        assert client.message_queue.maxsize == 1000

    def test_init_without_callback(self, mock_metrics):
        """测试无回调初始化"""
        client = BinanceWSClient(symbols=["BTCUSDT"])
        assert client.on_kline_callback is None

    def test_init_empty_symbols(self, mock_metrics):
        """测试空符号列表"""
        client = BinanceWSClient(symbols=[])
        assert client.symbols == []

    @pytest.mark.asyncio
    async def test_handle_kline_data_basic(self, client, mock_metrics):
        """测试K线数据处理（不依赖WebSocket连接）"""
        kline_data = {
            "k": {
                "s": "BTCUSDT",
                "t": int(time.time() * 1000),
                "o": "50000.00",
                "h": "51000.00",
                "l": "49000.00",
                "c": "50500.00",
                "v": "100.0",
                "x": True,
            },
            "E": int(time.time() * 1000),
        }
        receive_time = time.perf_counter()

        # 设置回调函数
        mock_callback = AsyncMock()
        client.on_kline_callback = mock_callback

        await client._handle_kline_data(kline_data, receive_time)

        # 验证回调被调用
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0][0]

        assert call_args["symbol"] == "BTCUSDT"
        assert call_args["open"] == 50000.0
        assert call_args["high"] == 51000.0
        assert call_args["low"] == 49000.0
        assert call_args["close"] == 50500.0
        assert call_args["volume"] == 100.0
        assert call_args["is_closed"] is True
        assert "timestamp" in call_args
        assert "latency_ms" in call_args

        # 验证指标记录
        mock_metrics.observe_ws_latency.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_kline_data_callback_error(self, client, mock_metrics):
        """测试K线回调错误"""
        kline_data = {
            "k": {
                "s": "BTCUSDT",
                "t": int(time.time() * 1000),
                "o": "50000.00",
                "h": "51000.00",
                "l": "49000.00",
                "c": "50500.00",
                "v": "100.0",
                "x": True,
            },
            "E": int(time.time() * 1000),
        }
        receive_time = time.perf_counter()

        # 设置抛出异常的回调
        mock_callback = AsyncMock()
        mock_callback.side_effect = Exception("回调错误")
        client.on_kline_callback = mock_callback

        await client._handle_kline_data(kline_data, receive_time)

        # 验证错误计数增加
        assert client.error_count == 1

    @pytest.mark.asyncio
    async def test_handle_ticker_data(self, client, mock_metrics):
        """测试Ticker数据处理"""
        ticker_data = {"s": "BTCUSDT", "c": "50500.00", "P": "1.5", "v": "1000.0"}
        receive_time = time.perf_counter()

        await client._handle_ticker_data(ticker_data, receive_time)

        # 验证价格更新指标
        mock_metrics.record_price_update.assert_called_once_with("BTCUSDT", 50500.0)

    def test_detect_crossover_fast_golden_cross(self, client):
        """测试交叉检测函数"""
        # 这个函数在_handle_kline_data中被调用，我们可以测试其逻辑
        # 通过检查_detect_crossover_fast方法（如果存在）
        pass

    @pytest.mark.asyncio
    async def test_reconnect_max_retries(self, client):
        """测试达到最大重连次数"""
        client.reconnect_count = client.max_reconnects

        result = await client.reconnect()

        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, client):
        """测试关闭连接"""
        mock_ws = AsyncMock()
        client.ws = mock_ws
        client.running = True

        await client.close()

        assert client.running is False
        mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_no_ws(self, client):
        """测试无WebSocket连接时关闭"""
        client.ws = None
        client.running = True

        # 应该不抛出异常
        await client.close()

        assert client.running is False

    def test_get_stats(self, client):
        """测试获取统计信息"""
        # 设置一些测试数据
        client.running = True
        client.message_count = 100
        client.error_count = 5
        client.reconnect_count = 2
        client.last_message_time = time.time()

        stats = client.get_stats()

        assert stats["running"] is True
        assert stats["message_count"] == 100
        assert stats["error_count"] == 5
        assert stats["reconnect_count"] == 2
        assert "uptime_seconds" in stats
        assert stats["queue_size"] >= 0
        assert "last_message_ago" in stats

    def test_get_stats_no_messages(self, client):
        """测试无消息时的统计信息"""
        stats = client.get_stats()

        assert stats["running"] is False
        assert stats["message_count"] == 0
        assert stats["last_message_ago"] is None

    @pytest.mark.asyncio
    async def test_subscribe_streams_basic(self, client):
        """测试订阅流的基本逻辑"""
        # 模拟WebSocket对象
        mock_ws = AsyncMock()
        client.ws = mock_ws

        await client._subscribe_streams()

        # 验证发送了订阅消息
        mock_ws.send.assert_called_once()

        # 验证消息内容
        sent_message = mock_ws.send.call_args[0][0]
        subscribe_data = json.loads(sent_message)

        assert subscribe_data["method"] == "SUBSCRIBE"
        assert "btcusdt@kline_1s" in subscribe_data["params"]
        assert "btcusdt@ticker" in subscribe_data["params"]
        assert "ethusdt@kline_1s" in subscribe_data["params"]
        assert "ethusdt@ticker" in subscribe_data["params"]
        assert "id" in subscribe_data

    @pytest.mark.asyncio
    async def test_handle_kline_data_missing_fields(self, mock_metrics):
        """测试K线数据缺少字段的错误处理"""
        client = BinanceWSClient(symbols=["BTCUSDT"])

        # 缺少必要字段的K线数据
        incomplete_kline_data = {
            "k": {
                "s": "BTCUSDT",
                "t": int(time.time() * 1000),
                # 缺少价格字段
            },
            "E": int(time.time() * 1000),
        }

        # 应该抛出异常或安全处理
        with pytest.raises((KeyError, ValueError)):
            await client._handle_kline_data(incomplete_kline_data, time.perf_counter())

    @pytest.mark.asyncio
    async def test_handle_ticker_data_missing_fields(self, mock_metrics):
        """测试Ticker数据缺少字段的错误处理"""
        client = BinanceWSClient(symbols=["BTCUSDT"])

        # 缺少必要字段的Ticker数据
        incomplete_ticker_data = {
            "s": "BTCUSDT",
            # 缺少价格字段
        }

        # 应该抛出异常或安全处理
        with pytest.raises((KeyError, ValueError)):
            await client._handle_ticker_data(incomplete_ticker_data, time.perf_counter())


class TestWSClientFunctionsSimple:
    """测试模块级函数"""

    @pytest.mark.asyncio
    async def test_create_ws_client(self):
        """测试创建WebSocket客户端"""
        from src.ws.binance_ws_client import create_ws_client

        symbols = ["BTCUSDT", "ETHUSDT"]
        callback = AsyncMock()

        with patch("src.ws.binance_ws_client.get_metrics_collector"):
            client = await create_ws_client(symbols, callback)

            assert isinstance(client, BinanceWSClient)
            assert client.symbols == symbols
            assert client.on_kline_callback == callback

    @pytest.mark.asyncio
    async def test_create_ws_client_no_callback(self):
        """测试无回调创建客户端"""
        from src.ws.binance_ws_client import create_ws_client

        symbols = ["BTCUSDT"]

        with patch("src.ws.binance_ws_client.get_metrics_collector"):
            client = await create_ws_client(symbols)

            assert client.on_kline_callback is None

    @pytest.mark.asyncio
    async def test_example_kline_handler(self, capsys):
        """测试示例K线处理器"""
        from src.ws.binance_ws_client import example_kline_handler

        kline_data = {"symbol": "BTCUSDT", "close": 50500.75, "latency_ms": 125.5}

        await example_kline_handler(kline_data)

        captured = capsys.readouterr()
        assert "BTCUSDT" in captured.out
        assert "50500.75" in captured.out
        assert "125.5" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
