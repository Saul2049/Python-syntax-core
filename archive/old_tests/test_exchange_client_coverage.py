"""
交易所客户端覆盖率测试
(Exchange Client Coverage Tests)

针对 src/brokers/exchange/client.py 的综合测试，提升代码覆盖率
"""

import pytest
import time
import socket
from unittest.mock import patch, MagicMock, Mock
from requests.exceptions import ConnectionError, Timeout
import pandas as pd
from datetime import datetime, timedelta

from src.brokers.exchange.client import ExchangeClient


class TestExchangeClientInitialization:
    """测试交易所客户端初始化 (Test Exchange Client Initialization)"""

    def test_initialization_demo_mode(self):
        """测试演示模式初始化"""
        client = ExchangeClient(
            api_key="demo_key",
            api_secret="demo_secret",
            demo_mode=True
        )
        
        assert client.demo_mode is True
        assert client.api_key == "demo_key"
        assert client.api_secret == "demo_secret"
        assert hasattr(client, '_demo_balances')
        assert hasattr(client, '_demo_orders')
        assert hasattr(client, '_demo_market_data')

    def test_initialization_live_mode(self):
        """测试实盘模式初始化"""
        client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        assert client.demo_mode is False
        assert client.api_key == "live_key"
        assert client.api_secret == "live_secret"

    @patch('src.brokers.exchange.client.pd.read_csv')
    def test_load_demo_data_success(self, mock_read_csv):
        """测试成功加载演示数据"""
        # 模拟CSV数据
        mock_df = pd.DataFrame({
            'timestamp': ['2023-01-01', '2023-01-02'],
            'close': [100.0, 101.0]
        })
        mock_read_csv.return_value = mock_df
        
        client = ExchangeClient(
            api_key="demo_key",
            api_secret="demo_secret",
            demo_mode=True
        )
        
        # 验证数据被加载
        assert len(client._demo_market_data) > 0

    @patch('src.brokers.exchange.client.pd.read_csv')
    def test_load_demo_data_failure(self, mock_read_csv):
        """测试加载演示数据失败 - 覆盖第70-75行"""
        # 模拟读取CSV失败
        mock_read_csv.side_effect = Exception("文件不存在")
        
        client = ExchangeClient(
            api_key="demo_key",
            api_secret="demo_secret",
            demo_mode=True
        )
        
        # 验证创建了备用数据
        assert len(client._demo_market_data) > 0
        assert "BTC/USDT" in client._demo_market_data
        assert "ETH/USDT" in client._demo_market_data


class TestExchangeClientRequestMethods:
    """测试请求方法 (Test Request Methods)"""

    @pytest.fixture
    def demo_client(self):
        """创建演示模式客户端"""
        return ExchangeClient(
            api_key="demo_key",
            api_secret="demo_secret",
            demo_mode=True
        )

    @pytest.fixture
    def live_client(self):
        """创建实盘模式客户端"""
        return ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )

    def test_simulate_demo_mode_issues_no_demo(self, live_client):
        """测试非演示模式不模拟问题 - 覆盖第108-109行"""
        # 在非演示模式下，不应该模拟问题
        try:
            live_client._simulate_demo_mode_issues()
            # 应该正常执行，不抛出异常
            assert True
        except Exception:
            pytest.fail("非演示模式不应该模拟网络问题")

    @patch('random.random')
    @patch('time.sleep')
    def test_simulate_demo_mode_issues_with_delay(self, mock_sleep, mock_random, demo_client):
        """测试演示模式模拟延迟"""
        mock_random.return_value = 0.1  # 不触发错误
        
        demo_client._simulate_demo_mode_issues()
        
        # 验证调用了sleep（模拟延迟）
        mock_sleep.assert_called()

    @patch('random.random')
    @patch('random.choice')
    def test_simulate_demo_mode_issues_with_error(self, mock_choice, mock_random, demo_client):
        """测试演示模式模拟错误 - 覆盖第116-117行"""
        mock_random.return_value = 0.01  # 触发错误（小于0.05）
        mock_choice.return_value = ConnectionError
        
        with pytest.raises(ConnectionError, match="模拟网络错误"):
            demo_client._simulate_demo_mode_issues()

    @patch('time.time')
    @patch('time.sleep')
    def test_apply_rate_limiting(self, mock_sleep, mock_time, demo_client):
        """测试速率限制 - 覆盖第128-132行"""
        # 模拟时间
        mock_time.side_effect = [1000.0, 1000.1]  # 间隔0.1秒
        demo_client._last_request_time = 1000.0
        
        demo_client._apply_rate_limiting()
        
        # 验证调用了sleep（因为请求间隔太短）
        mock_sleep.assert_called()

    @patch.object(ExchangeClient, '_make_single_request')
    def test_execute_request_with_retry_success(self, mock_request, demo_client):
        """测试请求重试成功"""
        mock_request.return_value = {"success": True}
        
        result = demo_client._execute_request_with_retry("GET", "http://test.com", {}, {})
        
        assert result == {"success": True}
        mock_request.assert_called_once()

    @patch.object(ExchangeClient, '_make_single_request')
    @patch.object(ExchangeClient, '_handle_retry_delay')
    def test_execute_request_with_retry_failure(self, mock_delay, mock_request, demo_client):
        """测试请求重试失败 - 覆盖第165-167行"""
        mock_request.side_effect = ConnectionError("网络错误")
        
        with pytest.raises(ConnectionError):
            demo_client._execute_request_with_retry("GET", "http://test.com", {}, {})
        
        # 验证重试了指定次数
        assert mock_request.call_count == demo_client.retry_count
        assert mock_delay.call_count == demo_client.retry_count - 1

    @patch.object(ExchangeClient, '_make_single_request')
    def test_execute_request_with_other_error(self, mock_request, demo_client):
        """测试请求其他错误 - 覆盖第188行"""
        mock_request.side_effect = ValueError("其他错误")
        
        with pytest.raises(ValueError, match="其他错误"):
            demo_client._execute_request_with_retry("GET", "http://test.com", {}, {})

    @patch('time.sleep')
    def test_handle_retry_delay(self, mock_sleep, demo_client):
        """测试重试延迟处理 - 覆盖第196-197行"""
        error = ConnectionError("测试错误")
        
        demo_client._handle_retry_delay(1, error)  # 第2次尝试
        
        # 验证指数退避：delay * 2^attempt = 1 * 2^1 = 2
        mock_sleep.assert_called_with(2)


class TestExchangeClientTradingMethods:
    """测试交易方法 (Test Trading Methods)"""

    @pytest.fixture
    def demo_client(self):
        """创建演示模式客户端"""
        return ExchangeClient(
            api_key="demo_key",
            api_secret="demo_secret",
            demo_mode=True
        )

    def test_get_account_balance_demo(self, demo_client):
        """测试演示模式获取账户余额"""
        balance = demo_client.get_account_balance()
        
        assert isinstance(balance, dict)
        assert len(balance) > 0
        # 验证返回的是副本，不是原始数据
        original_balance = demo_client._demo_balances.copy()
        balance['TEST'] = 999
        assert demo_client._demo_balances == original_balance

    @patch.object(ExchangeClient, '_request')
    def test_get_account_balance_live(self, mock_request):
        """测试实盘模式获取账户余额"""
        live_client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        mock_request.return_value = {"BTC": "1.5", "USDT": "10000.0"}
        
        balance = live_client.get_account_balance()
        
        assert balance == {"BTC": 1.5, "USDT": 10000.0}
        mock_request.assert_called_once_with("GET", "/api/v1/account/balance")

    @patch('random.random')
    @patch('time.sleep')
    @patch('time.time')
    def test_get_ticker_demo_with_rate_limit(self, mock_time, mock_sleep, mock_random, demo_client):
        """测试演示模式获取行情（带速率限制）- 覆盖第245-256行"""
        mock_time.side_effect = [1000.0, 1000.1]  # 模拟时间间隔
        mock_random.return_value = 0.1  # 不触发网络错误
        demo_client._last_request_time = 1000.0
        
        ticker = demo_client.get_ticker("BTC/USDT")
        
        assert isinstance(ticker, dict)
        assert "price" in ticker
        assert "volume" in ticker
        mock_sleep.assert_called()  # 验证应用了速率限制

    @patch('random.random')
    @patch('random.choice')
    def test_get_ticker_demo_with_network_error(self, mock_choice, mock_random, demo_client):
        """测试演示模式网络错误 - 覆盖第263-265行"""
        mock_random.return_value = 0.01  # 触发网络错误
        mock_choice.return_value = ConnectionError
        
        with pytest.raises(ConnectionError, match="模拟网络错误"):
            demo_client.get_ticker("BTC/USDT")

    def test_get_ticker_demo_unknown_symbol(self, demo_client):
        """测试演示模式未知交易对"""
        ticker = demo_client.get_ticker("UNKNOWN/USDT")
        
        assert ticker == {"price": 0.0, "volume": 0.0}

    @patch.object(ExchangeClient, '_request')
    def test_get_ticker_live(self, mock_request):
        """测试实盘模式获取行情"""
        live_client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        mock_request.return_value = {"price": 50000.0, "volume": 1000.0}
        
        ticker = live_client.get_ticker("BTC/USDT")
        
        assert ticker == {"price": 50000.0, "volume": 1000.0}
        mock_request.assert_called_once_with("GET", "/api/v1/ticker/BTC/USDT")

    @patch.object(ExchangeClient, 'get_ticker')
    def test_place_order_demo_buy(self, mock_ticker, demo_client):
        """测试演示模式买单"""
        mock_ticker.return_value = {"price": 50000.0, "volume": 100.0}
        
        order = demo_client.place_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            quantity=0.1
        )
        
        assert isinstance(order, dict)
        assert order["symbol"] == "BTC/USDT"
        assert order["side"] == "buy"
        assert order["quantity"] == 0.1
        assert order["status"] == "filled"
        assert "id" in order

    @patch.object(ExchangeClient, 'get_ticker')
    def test_place_order_demo_sell(self, mock_ticker, demo_client):
        """测试演示模式卖单"""
        mock_ticker.return_value = {"price": 50000.0, "volume": 100.0}
        
        order = demo_client.place_order(
            symbol="BTC/USDT",
            side="sell",
            order_type="limit",
            quantity=0.1,
            price=51000.0
        )
        
        assert isinstance(order, dict)
        assert order["side"] == "sell"
        assert order["price"] == 51000.0

    @patch.object(ExchangeClient, '_request')
    def test_place_order_live_limit(self, mock_request):
        """测试实盘模式限价单 - 覆盖第291行"""
        live_client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        mock_request.return_value = {"id": "12345", "status": "pending"}
        
        order = live_client.place_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="limit",
            quantity=0.1,
            price=49000.0
        )
        
        assert order == {"id": "12345", "status": "pending"}
        # 验证请求包含价格
        call_args = mock_request.call_args
        assert call_args[1]["data"]["price"] == 49000.0

    @patch.object(ExchangeClient, '_request')
    def test_place_order_live_market(self, mock_request):
        """测试实盘模式市价单 - 覆盖第298行"""
        live_client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        mock_request.return_value = {"id": "12346", "status": "filled"}
        
        order = live_client.place_order(
            symbol="BTC/USDT",
            side="sell",
            order_type="market",
            quantity=0.1
        )
        
        assert order == {"id": "12346", "status": "filled"}
        # 验证请求不包含价格
        call_args = mock_request.call_args
        assert "price" not in call_args[1]["data"]

    def test_get_historical_trades_demo(self, demo_client):
        """测试演示模式获取历史交易"""
        trades = demo_client.get_historical_trades("BTC/USDT", limit=50)
        
        assert isinstance(trades, list)
        # 演示模式返回demo_orders
        assert trades == demo_client._demo_orders

    @patch.object(ExchangeClient, '_request')
    def test_get_historical_trades_live(self, mock_request):
        """测试实盘模式获取历史交易"""
        live_client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        mock_request.return_value = [{"id": "1", "price": 50000}]
        
        trades = live_client.get_historical_trades("BTC/USDT", limit=100)
        
        assert trades == [{"id": "1", "price": 50000}]
        mock_request.assert_called_once_with(
            "GET", 
            "/api/v1/trades/BTC/USDT", 
            params={"limit": 100}
        )


class TestExchangeClientKlinesMethods:
    """测试K线数据方法 (Test Klines Methods)"""

    @pytest.fixture
    def demo_client(self):
        """创建演示模式客户端"""
        return ExchangeClient(
            api_key="demo_key",
            api_secret="demo_secret",
            demo_mode=True
        )

    def test_get_demo_klines_basic(self, demo_client):
        """测试演示模式K线数据 - 覆盖第361-373行"""
        klines = demo_client._get_demo_klines("BTC/USDT", None, None, 10)
        
        assert isinstance(klines, list)
        assert len(klines) <= 10

    def test_filter_demo_dates_with_time_range(self, demo_client):
        """测试演示数据日期过滤"""
        # 创建测试数据
        now = datetime.now()
        market_data = {
            now - timedelta(days=5): 100,
            now - timedelta(days=3): 101,
            now - timedelta(days=1): 102,
        }
        
        start_time = int((now - timedelta(days=4)).timestamp() * 1000)
        end_time = int((now - timedelta(days=2)).timestamp() * 1000)
        
        filtered_dates = demo_client._filter_demo_dates(
            market_data, start_time, end_time, 100
        )
        
        assert len(filtered_dates) == 1  # 只有一个日期在范围内

    def test_generate_demo_klines(self, demo_client):
        """测试生成演示K线数据"""
        dates = [datetime.now() - timedelta(days=i) for i in range(3)]
        market_data = {date: 100 + i for i, date in enumerate(dates)}
        
        klines = demo_client._generate_demo_klines(dates, market_data)
        
        assert isinstance(klines, list)
        assert len(klines) == 3
        for kline in klines:
            assert len(kline) == 6  # [timestamp, open, high, low, close, volume]

    @patch.object(ExchangeClient, '_request')
    def test_get_api_klines(self, mock_request):
        """测试API K线数据 - 覆盖第387-424行"""
        live_client = ExchangeClient(
            api_key="live_key",
            api_secret="live_secret",
            demo_mode=False
        )
        
        mock_request.return_value = [
            [1640995200000, "50000", "51000", "49000", "50500", "100"]
        ]
        
        klines = live_client._get_api_klines(
            "BTC/USDT", "1d", 1640995200000, 1641081600000, 100
        )
        
        assert klines == [[1640995200000, "50000", "51000", "49000", "50500", "100"]]
        
        # 验证请求参数（symbol不在params中，而是在URL中）
        call_args = mock_request.call_args
        expected_params = {
            "interval": "1d",
            "startTime": 1640995200000,
            "endTime": 1641081600000,
            "limit": 100
        }
        assert call_args[1]["params"] == expected_params


class TestExchangeClientEdgeCases:
    """测试边缘情况 (Test Edge Cases)"""

    def test_demo_client_with_custom_config(self):
        """测试自定义配置的演示客户端"""
        client = ExchangeClient(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://custom.api.com",
            timeout=30,
            retry_count=5,
            retry_delay=2,
            demo_mode=True
        )
        
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 30
        assert client.retry_count == 5
        assert client.retry_delay == 2

    @patch('time.time')
    def test_rate_limiting_no_sleep_needed(self, mock_time):
        """测试不需要速率限制的情况"""
        client = ExchangeClient(
            api_key="test_key",
            api_secret="test_secret",
            demo_mode=True
        )
        
        # 模拟足够的时间间隔（超过1秒，满足速率限制要求）
        mock_time.return_value = 1002.0  # 当前时间
        client._last_request_time = 1000.0  # 上次请求时间
        
        with patch('time.sleep') as mock_sleep:
            client._apply_rate_limiting()
            # 时间间隔2秒 > 1.0/rate_limit_per_sec，所以不需要sleep
            mock_sleep.assert_not_called()

    def test_empty_demo_market_data(self):
        """测试空的演示市场数据"""
        client = ExchangeClient(
            api_key="test_key",
            api_secret="test_secret",
            demo_mode=True
        )
        
        # 清空演示数据
        client._demo_market_data = {}
        
        ticker = client.get_ticker("UNKNOWN/USDT")
        assert ticker == {"price": 0.0, "volume": 0.0} 