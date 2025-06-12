#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 src.brokers.live_broker_async 模块的所有功能
Live Broker Async Module Tests

覆盖目标:
- LiveBrokerAsync 类的所有方法
- 异步订单执行和监控
- HTTP会话管理
- 订单状态跟踪
- 性能统计
- 工具函数
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.brokers.live_broker_async import LiveBrokerAsync, create_async_broker, main


class TestLiveBrokerAsync:
    """测试 LiveBrokerAsync 类"""

    def setup_method(self):
        """测试设置"""
        with patch("src.brokers.live_broker_async.get_metrics_collector") as mock_metrics:
            mock_metrics.return_value = Mock()
            self.broker = LiveBrokerAsync(
                api_key="test_key", api_secret="test_secret", testnet=True
            )

    def test_init_testnet(self):
        """测试测试网初始化"""
        assert self.broker.api_key == "test_key"
        assert self.broker.api_secret == "test_secret"
        assert self.broker.testnet is True
        assert self.broker.base_url == "https://testnet.binance.vision"
        assert self.broker.session is None
        assert self.broker.pending_orders == {}
        assert self.broker.order_history == []
        assert self.broker.order_count == 0
        assert self.broker.error_count == 0

    def test_init_mainnet(self):
        """测试主网初始化"""
        with patch("src.brokers.live_broker_async.get_metrics_collector"):
            broker = LiveBrokerAsync("key", "secret", testnet=False)
            assert broker.base_url == "https://api.binance.com"
            assert broker.testnet is False

    @pytest.mark.asyncio
    async def test_aenter_aexit(self):
        """测试异步上下文管理器"""
        with patch.object(self.broker, "init_session") as mock_init:
            with patch.object(self.broker, "close_session") as mock_close:
                async with self.broker as broker:
                    assert broker is self.broker
                    mock_init.assert_called_once()

                mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_session(self):
        """测试初始化HTTP会话"""
        with patch("aiohttp.ClientSession") as mock_session_class:
            with patch("aiohttp.TCPConnector") as mock_connector_class:
                with patch("aiohttp.ClientTimeout") as mock_timeout_class:
                    mock_session = Mock()
                    mock_session_class.return_value = mock_session

                    await self.broker.init_session()

                    assert self.broker.session == mock_session
                    mock_connector_class.assert_called_once()
                    mock_timeout_class.assert_called_once()
                    mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_with_session(self):
        """测试关闭HTTP会话（有会话）"""
        mock_session = AsyncMock()
        self.broker.session = mock_session

        await self.broker.close_session()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_no_session(self):
        """测试关闭HTTP会话（无会话）"""
        self.broker.session = None

        # 应该不抛出异常
        await self.broker.close_session()

    def test_generate_signature(self):
        """测试生成API签名"""
        params = {"symbol": "BTCUSDT", "side": "BUY", "quantity": "0.001"}

        signature = self.broker._generate_signature(params)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length

    def test_generate_signature_empty_params(self):
        """测试空参数的签名生成"""
        signature = self.broker._generate_signature({})

        assert isinstance(signature, str)
        assert len(signature) == 64

    @pytest.mark.asyncio
    async def test_handle_response_success(self):
        """测试成功处理响应"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"data": "test"}

        result = await self.broker._handle_response(mock_response)

        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_handle_response_error(self):
        """测试错误响应处理"""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"

        with pytest.raises(Exception, match="API错误 400: Bad Request"):
            await self.broker._handle_response(mock_response)

    @pytest.mark.asyncio
    async def test_place_order_async_with_mocked_request(self):
        """测试下单功能（使用mock的_request方法）"""
        mock_response = {"orderId": "12345", "clientOrderId": "client_12345", "status": "NEW"}

        with patch.object(self.broker, "_request", return_value=mock_response):
            with patch("asyncio.create_task"):
                with patch("time.perf_counter", return_value=1000.0):
                    with patch("time.time", return_value=1000):
                        with patch("builtins.print"):
                            result = await self.broker.place_order_async(
                                symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.001
                            )

        assert result["order_id"] == "12345"
        assert result["symbol"] == "BTCUSDT"
        assert self.broker.order_count == 1

    @pytest.mark.asyncio
    async def test_cancel_order_async_with_mocked_request(self):
        """测试撤单功能（使用mock的_request方法）"""
        mock_response = {"orderId": "12345", "status": "CANCELED"}

        with patch.object(self.broker, "_request", return_value=mock_response):
            with patch("builtins.print"):
                result = await self.broker.cancel_order_async("BTCUSDT", "12345")

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_account_info_async_with_mocked_request(self):
        """测试获取账户信息（使用mock的_request方法）"""
        mock_response = {"balances": [{"asset": "USDT", "free": "1000.0"}]}

        with patch.object(self.broker, "_request", return_value=mock_response):
            result = await self.broker.get_account_info_async()

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_open_orders_async_with_mocked_request(self):
        """测试获取未完成订单（使用mock的_request方法）"""
        mock_response = [{"orderId": "123", "symbol": "BTCUSDT"}]

        with patch.object(self.broker, "_request", return_value=mock_response):
            result = await self.broker.get_open_orders_async("BTCUSDT")

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_place_order_async_market_success(self):
        """测试成功的市价单下单"""
        mock_response = {
            "orderId": "12345",
            "clientOrderId": "client_12345",
            "status": "NEW",
        }

        with patch.object(self.broker, "_request", return_value=mock_response):
            with patch("asyncio.create_task"):
                with patch("time.perf_counter", side_effect=[1000.0, 1000.5]):
                    with patch("time.time", return_value=1000):
                        with patch("builtins.print"):
                            result = await self.broker.place_order_async(
                                symbol="BTCUSDT",
                                side="BUY",
                                order_type="MARKET",
                                quantity=0.001,
                            )

        assert result["order_id"] == "12345"
        assert result["symbol"] == "BTCUSDT"
        assert result["side"] == "BUY"
        assert result["type"] == "MARKET"
        assert result["quantity"] == 0.001
        assert self.broker.order_count == 1
        assert "12345" in self.broker.pending_orders

    @pytest.mark.asyncio
    async def test_place_order_async_limit_success(self):
        """测试成功的限价单下单"""
        mock_response = {"orderId": "67890", "clientOrderId": "client_67890", "status": "NEW"}

        with patch.object(self.broker, "_request", return_value=mock_response):
            with patch("asyncio.create_task"):
                with patch("time.perf_counter", return_value=1000.0):
                    with patch("time.time", return_value=1000):
                        with patch("builtins.print"):
                            result = await self.broker.place_order_async(
                                symbol="ETHUSDT",
                                side="SELL",
                                order_type="LIMIT",
                                quantity=0.1,
                                price=2000.0,
                            )

        assert result["order_id"] == "67890"
        assert result["price"] == 2000.0
        assert result["type"] == "LIMIT"

    @pytest.mark.asyncio
    async def test_place_order_async_failure(self):
        """测试下单失败"""
        with patch.object(self.broker, "_request", side_effect=Exception("Order failed")):
            with patch("time.perf_counter", side_effect=[1000.0, 1000.1]):
                with patch("builtins.print"):
                    with pytest.raises(Exception, match="Order failed"):
                        await self.broker.place_order_async(
                            symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.001
                        )

        assert self.broker.error_count == 1
        self.broker.metrics.record_exception.assert_called_once()
        self.broker.metrics.observe_order_roundtrip_latency.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitor_order_status_filled(self):
        """测试订单状态监控 - 成交"""
        order_id = "test_order_123"
        self.broker.pending_orders[order_id] = {"symbol": "BTCUSDT", "submit_time": 1000.0}

        mock_response = {"status": "FILLED"}

        with patch.object(self.broker, "_request", return_value=mock_response):
            with patch("time.perf_counter", side_effect=[1000.0, 1000.5, 1000.5]):
                with patch("asyncio.sleep"):
                    with patch("builtins.print"):
                        await self.broker._monitor_order_status(order_id)

        assert order_id not in self.broker.pending_orders
        assert len(self.broker.order_history) == 1
        assert self.broker.order_history[0]["status"] == "FILLED"
        assert "roundtrip_latency" in self.broker.order_history[0]

    @pytest.mark.asyncio
    async def test_monitor_order_status_timeout(self):
        """测试订单状态监控 - 超时"""
        order_id = "timeout_order"
        self.broker.pending_orders[order_id] = {"symbol": "BTCUSDT", "submit_time": 1000.0}

        # 模拟一直返回NEW状态，直到超时
        mock_response = {"status": "NEW"}

        with patch.object(self.broker, "_request", return_value=mock_response):
            with patch("asyncio.sleep"):
                with patch("builtins.print"):
                    await self.broker._monitor_order_status(order_id)

        assert order_id not in self.broker.pending_orders
        assert len(self.broker.order_history) == 1
        assert self.broker.order_history[0]["status"] == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_monitor_order_status_order_not_found(self):
        """测试订单状态监控 - 订单不存在"""
        order_id = "nonexistent_order"

        # 订单不在pending_orders中
        await self.broker._monitor_order_status(order_id)

        # 应该立即退出，不做任何操作
        assert len(self.broker.order_history) == 0

    @pytest.mark.asyncio
    async def test_monitor_order_status_exception(self):
        """测试订单状态监控 - 异常处理"""
        order_id = "error_order"
        self.broker.pending_orders[order_id] = {"symbol": "BTCUSDT", "submit_time": 1000.0}

        with patch.object(self.broker, "_request", side_effect=Exception("Network error")):
            with patch("asyncio.sleep"):
                with patch("builtins.print"):
                    await self.broker._monitor_order_status(order_id)

        # 应该在最大尝试次数后超时
        assert order_id not in self.broker.pending_orders
        assert len(self.broker.order_history) == 1
        assert self.broker.order_history[0]["status"] == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_get_account_info_async_failure(self):
        """测试获取账户信息失败"""
        with patch.object(self.broker, "_request", side_effect=Exception("Account error")):
            with patch("builtins.print"):
                with pytest.raises(Exception, match="Account error"):
                    await self.broker.get_account_info_async()

        assert self.broker.error_count == 1

    @pytest.mark.asyncio
    async def test_get_open_orders_async_with_symbol(self):
        """测试获取指定交易对的未完成订单"""
        mock_response = [{"orderId": "123", "symbol": "BTCUSDT"}]

        with patch.object(self.broker, "_request", return_value=mock_response):
            result = await self.broker.get_open_orders_async("BTCUSDT")

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_open_orders_async_all_symbols(self):
        """测试获取所有交易对的未完成订单"""
        mock_response = [
            {"orderId": "123", "symbol": "BTCUSDT"},
            {"orderId": "456", "symbol": "ETHUSDT"},
        ]

        with patch.object(self.broker, "_request", return_value=mock_response):
            result = await self.broker.get_open_orders_async()

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_get_open_orders_async_failure(self):
        """测试获取未完成订单失败"""
        with patch.object(self.broker, "_request", side_effect=Exception("Orders error")):
            with patch("builtins.print"):
                with pytest.raises(Exception, match="Orders error"):
                    await self.broker.get_open_orders_async()

        assert self.broker.error_count == 1

    def test_get_performance_stats_with_history(self):
        """测试有历史记录的性能统计"""
        # 添加一些历史订单
        self.broker.order_history = [
            {"status": "FILLED", "roundtrip_latency": 0.1},
            {"status": "FILLED", "roundtrip_latency": 0.2},
            {"status": "CANCELED", "roundtrip_latency": 0.05},
        ]
        self.broker.order_count = 5
        self.broker.error_count = 1
        self.broker.pending_orders = {"order1": {}, "order2": {}}

        stats = self.broker.get_performance_stats()

        assert stats["total_orders"] == 5
        assert stats["completed_orders"] == 2  # 2个FILLED
        assert stats["pending_orders"] == 2
        assert stats["error_count"] == 1
        assert abs(stats["avg_roundtrip_latency_ms"] - 116.67) < 0.1  # 允许小的浮点误差
        assert abs(stats["success_rate"] - 66.67) < 0.1  # 2/3 * 100

    def test_get_performance_stats_no_history(self):
        """测试无历史记录的性能统计"""
        stats = self.broker.get_performance_stats()

        assert stats["total_orders"] == 0
        assert stats["completed_orders"] == 0
        assert stats["pending_orders"] == 0
        assert stats["error_count"] == 0
        assert stats["avg_roundtrip_latency_ms"] == 0
        assert stats["success_rate"] == 0

    def test_request_method_signature_validation(self):
        """测试请求方法的参数验证"""
        # 测试_generate_signature方法
        params = {"symbol": "BTCUSDT", "side": "BUY"}
        signature = self.broker._generate_signature(params)
        assert isinstance(signature, str)
        assert len(signature) == 64


class TestUtilityFunctions:
    """测试工具函数"""

    @pytest.mark.asyncio
    async def test_create_async_broker(self):
        """测试创建异步代理实例"""
        with patch("src.brokers.live_broker_async.LiveBrokerAsync") as mock_broker_class:
            mock_broker = AsyncMock()
            mock_broker_class.return_value = mock_broker

            result = await create_async_broker("test_key", "test_secret", testnet=True)

            assert result == mock_broker
            mock_broker_class.assert_called_once_with("test_key", "test_secret", True)
            mock_broker.init_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_success(self):
        """测试主函数成功执行"""
        mock_broker = AsyncMock()
        mock_order = {"order_id": "123", "status": "NEW"}
        mock_stats = {"total_orders": 1, "success_rate": 100.0}

        mock_broker.place_order_async.return_value = mock_order
        mock_broker.get_performance_stats.return_value = mock_stats

        with patch("src.brokers.live_broker_async.LiveBrokerAsync") as mock_broker_class:
            mock_broker_class.return_value.__aenter__.return_value = mock_broker
            mock_broker_class.return_value.__aexit__.return_value = None

            with patch("asyncio.sleep"):
                with patch("builtins.print"):
                    await main()

            mock_broker.place_order_async.assert_called_once_with(
                symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=0.001, price=30000.0
            )
            mock_broker.get_performance_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_function_exception(self):
        """测试主函数异常处理"""
        mock_broker = AsyncMock()
        mock_broker.place_order_async.side_effect = Exception("Test error")

        with patch("src.brokers.live_broker_async.LiveBrokerAsync") as mock_broker_class:
            mock_broker_class.return_value.__aenter__.return_value = mock_broker
            mock_broker_class.return_value.__aexit__.return_value = None

            with patch("builtins.print") as mock_print:
                await main()

            # 验证错误被打印
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("测试失败" in msg for msg in print_calls)


class TestLiveBrokerAsyncIntegration:
    """异步代理集成测试"""

    @pytest.mark.asyncio
    async def test_full_order_workflow(self):
        """测试完整订单工作流"""
        with patch("src.brokers.live_broker_async.get_metrics_collector"):
            broker = LiveBrokerAsync("test_key", "test_secret", testnet=True)

            # 模拟下单响应
            order_response = {"orderId": "12345", "clientOrderId": "client_12345", "status": "NEW"}

            # 模拟订单状态查询响应
            status_response = {"status": "FILLED"}

            with patch.object(broker, "_request", side_effect=[order_response, status_response]):
                with patch("asyncio.create_task"):
                    with patch("time.perf_counter", side_effect=[1000.0, 1000.5, 1001.0, 1001.0]):
                        with patch("time.time", return_value=1000):
                            with patch("builtins.print"):
                                # 下单
                                order = await broker.place_order_async(
                                    symbol="BTCUSDT",
                                    side="BUY",
                                    order_type="MARKET",
                                    quantity=0.001,
                                )

                                # 模拟订单监控
                                await broker._monitor_order_status("12345")

            # 验证订单流程
            assert order["order_id"] == "12345"
            assert len(broker.order_history) == 1
            assert broker.order_history[0]["status"] == "FILLED"
            assert "12345" not in broker.pending_orders

    @pytest.mark.asyncio
    async def test_concurrent_orders(self):
        """测试并发订单处理"""
        with patch("src.brokers.live_broker_async.get_metrics_collector"):
            broker = LiveBrokerAsync("test_key", "test_secret", testnet=True)

            order_responses = [
                {"orderId": "order1", "status": "NEW"},
                {"orderId": "order2", "status": "NEW"},
            ]

            with patch.object(broker, "_request", side_effect=order_responses):
                with patch("asyncio.create_task"):
                    with patch("time.perf_counter", return_value=1000.0):
                        with patch("time.time", return_value=1000):
                            with patch("builtins.print"):
                                # 并发下单
                                tasks = [
                                    broker.place_order_async("BTCUSDT", "BUY", "MARKET", 0.001),
                                    broker.place_order_async("ETHUSDT", "SELL", "MARKET", 0.1),
                                ]

                                results = await asyncio.gather(*tasks)

            assert len(results) == 2
            assert results[0]["order_id"] == "order1"
            assert results[1]["order_id"] == "order2"
            assert len(broker.pending_orders) == 2
