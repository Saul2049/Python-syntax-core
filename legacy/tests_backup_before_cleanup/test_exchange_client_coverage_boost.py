"""
交易所客户端模块覆盖率提升测试 (Exchange Client Coverage Boost Tests)

专门针对 src/brokers/exchange/client.py 中未覆盖的代码行进行测试，
将覆盖率从 17% 提升到 85%+。

目标缺失行: 37-59, 63-75, 92-97, 101-109, 113-117, 121-132, 136-149, 153-158, 162-167, 171-197, 220-256, 260-265, 288-291, 297-303, 309-323, 327-350, 361-373, 387-424
"""

import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests
from requests.exceptions import ConnectionError, Timeout

from src.brokers.exchange.client import ExchangeClient


class TestExchangeClientInitialization:
    """测试交易所客户端初始化"""

    def test_client_initialization_full_params(self):
        """测试完整参数初始化 (Lines 37-59)"""
        client = ExchangeClient(
            api_key="test_api_key",
            api_secret="test_api_secret",
            base_url="https://test.api.com",
            timeout=30,
            retry_count=5,
            retry_delay=2,
            demo_mode=True,
        )

        assert client.api_key == "test_api_key"
        assert client.api_secret == "test_api_secret"
        assert client.base_url == "https://test.api.com"
        assert client.timeout == 30
        assert client.retry_count == 5
        assert client.retry_delay == 2
        assert client.demo_mode == True
        assert client.session is not None
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"] == "Bearer test_api_key"
        assert client.session.headers["Content-Type"] == "application/json"
        assert client._rate_limit_per_sec == 5

        # 验证演示模式初始化
        assert isinstance(client._demo_balances, dict)
        assert isinstance(client._demo_orders, list)
        assert isinstance(client._demo_market_data, dict)

    def test_load_demo_data_with_csv_success(self):
        """测试成功从CSV文件加载演示数据 (Lines 63-75)"""
        with patch("pandas.read_csv") as mock_read_csv:
            mock_df = pd.DataFrame(
                {"btc": [50000, 51000], "eth": [3000, 3100]},
                index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
            )
            mock_read_csv.return_value = mock_df

            client = ExchangeClient("key", "secret", demo_mode=True)

            assert "BTC/USDT" in client._demo_market_data
            assert "ETH/USDT" in client._demo_market_data

    def test_load_demo_data_file_not_found(self):
        """测试CSV文件不存在时的回退逻辑 (Lines 70-75)"""
        with patch("pandas.read_csv", side_effect=FileNotFoundError("File not found")):
            client = ExchangeClient("key", "secret", demo_mode=True)

            # 应该创建随机数据作为备用
            assert isinstance(client._demo_market_data, dict)
            assert "BTC/USDT" in client._demo_market_data
            assert "ETH/USDT" in client._demo_market_data


class TestExchangeClientRequestMethods:
    """测试请求相关方法"""

    @pytest.fixture
    def client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=False)

    @pytest.fixture
    def demo_client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=True)

    def test_simulate_demo_mode_issues_normal_mode(self, client):
        """测试非演示模式不模拟问题 (Lines 101-109)"""
        # 非演示模式应该不做任何事情
        client._simulate_demo_mode_issues()  # 不应该抛出异常

    def test_simulate_demo_mode_issues_with_delay_and_errors(self, demo_client):
        """测试演示模式模拟延迟和错误 (Lines 101-109)"""
        with (
            patch("time.sleep") as mock_sleep,
            patch("random.random", return_value=0.01),
            patch("random.choice", return_value=ConnectionError),
        ):

            with pytest.raises(ConnectionError, match="模拟网络错误"):
                demo_client._simulate_demo_mode_issues()

            mock_sleep.assert_called()  # 应该有延迟

    def test_apply_rate_limiting_with_delay(self, client):
        """测试速率限制应用 (Lines 113-117)"""
        # 设置上次请求时间为现在
        client._last_request_time = time.time()

        # 立即调用应该触发延迟
        with patch("time.sleep") as mock_sleep:
            client._apply_rate_limiting()
            mock_sleep.assert_called()

    def test_execute_request_with_retry_success_first_try(self, client):
        """测试首次尝试成功的请求 (Lines 121-132)"""
        with patch.object(
            client, "_make_single_request", return_value={"success": True}
        ) as mock_request:
            result = client._execute_request_with_retry("GET", "http://test.com", {}, {})

            assert result == {"success": True}
            mock_request.assert_called_once()

    def test_execute_request_with_retry_success_after_retries(self, client):
        """测试重试后成功的请求 (Lines 121-132)"""
        with (
            patch.object(client, "_make_single_request") as mock_request,
            patch.object(client, "_handle_retry_delay") as mock_delay,
        ):

            # 前两次失败，第三次成功
            mock_request.side_effect = [
                ConnectionError("Network error"),
                Timeout("Timeout error"),
                {"success": True},
            ]

            result = client._execute_request_with_retry("GET", "http://test.com", {}, {})

            assert result == {"success": True}
            assert mock_request.call_count == 3
            assert mock_delay.call_count == 2

    def test_execute_request_with_retry_max_retries_exceeded(self, client):
        """测试超过最大重试次数 (Lines 121-132)"""
        with (
            patch.object(
                client, "_make_single_request", side_effect=ConnectionError("Network error")
            ),
            patch.object(client, "_handle_retry_delay"),
        ):

            with pytest.raises(ConnectionError):
                client._execute_request_with_retry("GET", "http://test.com", {}, {})

    def test_execute_request_with_retry_non_retryable_error(self, client):
        """测试不可重试的错误 (Lines 121-132)"""
        with patch.object(client, "_make_single_request", side_effect=ValueError("Invalid data")):

            with pytest.raises(ValueError):
                client._execute_request_with_retry("GET", "http://test.com", {}, {})

    def test_make_single_request_success(self, client):
        """测试单次请求成功 (Lines 136-149)"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None

        with patch.object(client.session, "request", return_value=mock_response):
            result = client._make_single_request(
                "GET", "http://test.com", {"param": "value"}, {"data": "test"}
            )

            assert result == {"data": "test"}
            assert client._last_request_time > 0

    def test_make_single_request_http_error(self, client):
        """测试HTTP错误响应 (Lines 136-149)"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("HTTP 404")

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(requests.HTTPError):
                client._make_single_request("GET", "http://test.com", {}, {})

    def test_handle_retry_delay(self, client):
        """测试重试延迟处理 (Lines 153-158)"""
        with patch("time.sleep") as mock_sleep:
            error = ConnectionError("Test error")
            client._handle_retry_delay(2, error)

            # 应该使用指数退避：retry_delay * (2^attempt) = 1 * (2^2) = 4秒
            mock_sleep.assert_called_once_with(4)


class TestExchangeClientAPIData:
    """测试API数据获取方法"""

    @pytest.fixture
    def client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=False)

    @pytest.fixture
    def demo_client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=True)

    def test_get_account_balance_api_mode(self, client):
        """测试API模式获取账户余额 (Lines 162-167)"""
        mock_response = {"BTC": "1.5", "ETH": "10.0", "USDT": "5000.0"}

        with patch.object(client, "_request", return_value=mock_response):
            result = client.get_account_balance()

            expected = {"BTC": 1.5, "ETH": 10.0, "USDT": 5000.0}
            assert result == expected

    def test_get_ticker_demo_mode_with_rate_limiting(self, demo_client):
        """测试演示模式获取行情（包含速率限制）(Lines 171-197)"""
        # 设置上次请求时间为现在，触发速率限制
        demo_client._last_request_time = time.time()

        with (
            patch("time.sleep") as mock_sleep,
            patch("random.random", return_value=0.9),
        ):  # 避免模拟错误

            result = demo_client.get_ticker("BTC/USDT")

            # 应该触发速率限制延迟
            mock_sleep.assert_called()
            assert isinstance(result, dict)
            assert "price" in result
            assert "volume" in result

    def test_get_ticker_demo_mode_network_errors(self, demo_client):
        """测试演示模式网络错误模拟 (Lines 171-197)"""
        with patch("random.random", return_value=0.01):
            # 测试不同类型的网络错误
            for error_type in [ConnectionError, TimeoutError, OSError]:
                with patch("random.choice", return_value=error_type):
                    with pytest.raises(error_type, match="模拟网络错误"):
                        demo_client.get_ticker("BTC/USDT")

    def test_get_ticker_demo_mode_unknown_symbol(self, demo_client):
        """测试演示模式未知交易对 (Lines 171-197)"""
        with patch("random.random", return_value=0.9):
            result = demo_client.get_ticker("UNKNOWN/USDT")

            assert result == {"price": 0.0, "volume": 0.0}

    def test_get_ticker_api_mode(self, client):
        """测试API模式获取行情 (Lines 171-197)"""
        mock_response = {"price": 50000.0, "volume": 1000.0}

        with patch.object(client, "_request", return_value=mock_response):
            result = client.get_ticker("BTC/USDT")

            assert result == mock_response


class TestExchangeClientTrading:
    """测试交易相关方法"""

    @pytest.fixture
    def demo_client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=True)

    @pytest.fixture
    def client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=False)

    def test_place_order_demo_mode_buy_market(self, demo_client):
        """测试演示模式买入市价单 (Lines 220-256)"""
        initial_btc = demo_client._demo_balances["BTC"]
        initial_usdt = demo_client._demo_balances["USDT"]

        with patch.object(demo_client, "get_ticker", return_value={"price": 50000.0}):
            result = demo_client.place_order(
                symbol="BTC/USDT", side="buy", order_type="market", quantity=0.1
            )

            assert "id" in result
            assert result["symbol"] == "BTC/USDT"
            assert result["side"] == "buy"
            assert result["status"] == "filled"

            # 检查余额变化
            assert demo_client._demo_balances["BTC"] == initial_btc + 0.1
            assert demo_client._demo_balances["USDT"] == initial_usdt - (0.1 * 50000.0)

    def test_place_order_demo_mode_sell_market(self, demo_client):
        """测试演示模式卖出市价单 (Lines 220-256)"""
        initial_btc = demo_client._demo_balances["BTC"]
        initial_usdt = demo_client._demo_balances["USDT"]

        with patch.object(demo_client, "get_ticker", return_value={"price": 50000.0}):
            result = demo_client.place_order(
                symbol="BTC/USDT", side="sell", order_type="market", quantity=0.1
            )

            assert result["side"] == "sell"

            # 检查余额变化
            assert demo_client._demo_balances["BTC"] == initial_btc - 0.1
            assert demo_client._demo_balances["USDT"] == initial_usdt + (0.1 * 50000.0)

    def test_place_order_demo_mode_limit_order(self, demo_client):
        """测试演示模式限价单 (Lines 220-256)"""
        result = demo_client.place_order(
            symbol="BTC/USDT", side="buy", order_type="limit", quantity=0.1, price=49000.0
        )

        assert result["type"] == "limit"
        assert result["price"] == 49000.0

    def test_place_order_api_mode(self, client):
        """测试API模式下单 (Lines 220-256)"""
        mock_response = {"orderId": "12345", "status": "NEW"}

        with patch.object(client, "_request", return_value=mock_response):
            result = client.place_order(
                symbol="BTC/USDT", side="buy", order_type="limit", quantity=0.1, price=50000.0
            )

            assert result == mock_response

    def test_get_historical_trades_demo_mode(self, demo_client):
        """测试演示模式获取历史交易 (Lines 260-265)"""
        # 先添加一些演示订单
        demo_client._demo_orders = [
            {"id": "1", "symbol": "BTC/USDT"},
            {"id": "2", "symbol": "ETH/USDT"},
        ]

        result = demo_client.get_historical_trades("BTC/USDT")

        assert result == demo_client._demo_orders

    def test_get_historical_trades_api_mode(self, client):
        """测试API模式获取历史交易 (Lines 260-265)"""
        mock_response = [{"id": "1", "price": 50000}]

        with patch.object(client, "_request", return_value=mock_response):
            result = client.get_historical_trades("BTC/USDT", limit=50)

            assert result == mock_response


class TestExchangeClientKlines:
    """测试K线数据相关方法"""

    @pytest.fixture
    def demo_client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=True)

    @pytest.fixture
    def client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=False)

    def test_get_historical_klines_demo_mode(self, demo_client):
        """测试演示模式获取K线数据 (Lines 288-291)"""
        with patch.object(demo_client, "_get_demo_klines", return_value=[]) as mock_get_demo:
            result = demo_client.get_historical_klines(
                symbol="BTC/USDT",
                interval="1d",
                start_time=1640995200000,
                end_time=1641081600000,
                limit=100,
            )

            mock_get_demo.assert_called_once_with("BTC/USDT", 1640995200000, 1641081600000, 100)
            assert result == []

    def test_get_historical_klines_api_mode(self, client):
        """测试API模式获取K线数据 (Lines 288-291)"""
        with patch.object(client, "_get_api_klines", return_value=[]) as mock_get_api:
            result = client.get_historical_klines(
                symbol="BTC/USDT",
                interval="1h",
                start_time=1640995200000,
                end_time=1641081600000,
                limit=200,
            )

            mock_get_api.assert_called_once_with(
                "BTC/USDT", "1h", 1640995200000, 1641081600000, 200
            )
            assert result == []

    def test_get_demo_klines_no_data(self, demo_client):
        """测试演示模式无数据情况 (Lines 297-303)"""
        demo_client._demo_market_data = {}

        result = demo_client._get_demo_klines("UNKNOWN/USDT", None, None, 100)

        assert result == []

    def test_get_demo_klines_with_data(self, demo_client):
        """测试演示模式有数据情况 (Lines 297-303)"""
        # 设置演示数据
        test_dates = [datetime.now() - timedelta(days=i) for i in range(5)]
        demo_client._demo_market_data["BTC/USDT"] = {
            d: 50000 + i * 100 for i, d in enumerate(test_dates)
        }

        with (
            patch.object(demo_client, "_filter_demo_dates", return_value=test_dates) as mock_filter,
            patch.object(demo_client, "_generate_demo_klines", return_value=[]) as mock_generate,
        ):

            result = demo_client._get_demo_klines("BTC/USDT", None, None, 100)

            mock_filter.assert_called_once()
            mock_generate.assert_called_once()

    def test_filter_demo_dates_with_time_range(self, demo_client):
        """测试演示数据日期过滤 (Lines 309-323)"""
        # 创建测试数据
        test_dates = [datetime(2024, 1, i) for i in range(1, 11)]  # 10天数据
        market_data = {d: 50000 + i * 100 for i, d in enumerate(test_dates)}

        # 测试开始时间过滤
        start_timestamp = int(datetime(2024, 1, 5).timestamp() * 1000)
        result = demo_client._filter_demo_dates(market_data, start_timestamp, None, None)

        assert len(result) == 6  # 应该从1月5日开始

        # 测试结束时间过滤
        end_timestamp = int(datetime(2024, 1, 7).timestamp() * 1000)
        result = demo_client._filter_demo_dates(market_data, None, end_timestamp, None)

        assert len(result) == 7  # 应该到1月7日结束

        # 测试限制数量
        result = demo_client._filter_demo_dates(market_data, None, None, 5)

        assert len(result) == 5  # 应该只返回最后5个

    def test_generate_demo_klines(self, demo_client):
        """测试演示模式K线生成 (Lines 327-350)"""
        test_dates = [datetime(2024, 1, 1), datetime(2024, 1, 2)]
        market_data = {test_dates[0]: 50000, test_dates[1]: 51000}

        result = demo_client._generate_demo_klines(test_dates, market_data)

        assert len(result) == 2
        assert len(result[0]) == 6  # [timestamp, open, high, low, close, volume]
        assert isinstance(result[0][0], int)  # timestamp应该是整数

        # 验证OHLCV数据结构
        for kline in result:
            timestamp, open_p, high, low, close, volume = kline
            assert isinstance(timestamp, int)
            assert isinstance(open_p, (int, float))
            assert isinstance(high, (int, float))
            assert isinstance(low, (int, float))
            assert isinstance(close, (int, float))
            assert isinstance(volume, (int, float))

    def test_get_api_klines_with_all_params(self, client):
        """测试API模式K线获取（包含所有参数）(Lines 361-373)"""
        mock_response = [[1640995200000, 50000, 51000, 49000, 50500, 100]]

        with patch.object(client, "_request", return_value=mock_response):
            result = client._get_api_klines(
                symbol="BTC/USDT",
                interval="1d",
                start_time=1640995200000,
                end_time=1641081600000,
                limit=100,
            )

            assert result == mock_response

    def test_get_api_klines_minimal_params(self, client):
        """测试API模式K线获取（最少参数）(Lines 361-373)"""
        mock_response = [[1640995200000, 50000, 51000, 49000, 50500, 100]]

        with patch.object(client, "_request", return_value=mock_response):
            result = client._get_api_klines(
                symbol="BTC/USDT", interval="1d", start_time=None, end_time=None, limit=100
            )

            assert result == mock_response


class TestMarketDataSync:
    """测试市场数据同步"""

    @pytest.fixture
    def demo_client(self):
        return ExchangeClient("test_key", "test_secret", demo_mode=True)

    def test_sync_market_data_success(self, demo_client):
        """测试市场数据同步成功 (Lines 387-424)"""
        mock_klines = [
            [1640995200000, 50000, 51000, 49000, 50500, 100],
            [1641081600000, 50500, 52000, 50000, 51500, 150],
        ]

        with patch.object(demo_client, "get_historical_klines", return_value=mock_klines):
            result = demo_client.sync_market_data("BTC/USDT", "1d", 30)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2
            assert "timestamp" in result.columns
            assert "open" in result.columns
            assert "high" in result.columns
            assert "low" in result.columns
            assert "close" in result.columns
            assert "volume" in result.columns

    def test_sync_market_data_no_data(self, demo_client):
        """测试市场数据同步无数据情况 (Lines 387-424)"""
        with patch.object(demo_client, "get_historical_klines", return_value=[]):
            result = demo_client.sync_market_data("BTC/USDT", "1d", 30)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
