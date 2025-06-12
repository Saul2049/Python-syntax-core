#!/usr/bin/env python3
"""
测试Binance客户端模块 (Test Binance Client Module)
"""

import hashlib
import hmac
import tempfile
from unittest.mock import Mock, patch
from urllib.parse import urlencode

import pandas as pd
import pytest
import requests

from src.brokers.binance.client import BinanceClient, rate_limit_retry


class TestRateLimitRetry:
    """测试速率限制重试装饰器 (Test Rate Limit Retry Decorator)"""

    def test_rate_limit_retry_success_first_attempt(self):
        """测试第一次尝试就成功"""

        @rate_limit_retry(max_retries=3, base_delay=0.1)
        def mock_function():
            return "success"

        result = mock_function()
        assert result == "success"

    def test_rate_limit_retry_success_after_retries(self):
        """测试重试后成功"""
        call_count = 0

        @rate_limit_retry(max_retries=3, base_delay=0.1)
        def mock_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # 模拟429错误
                response = Mock()
                response.status_code = 429
                error = requests.exceptions.HTTPError()
                error.response = response
                raise error
            return "success"

        result = mock_function()
        assert result == "success"
        assert call_count == 3

    def test_rate_limit_retry_max_retries_exceeded(self):
        """测试超过最大重试次数"""

        @rate_limit_retry(max_retries=2, base_delay=0.1)
        def mock_function():
            response = Mock()
            response.status_code = 429
            error = requests.exceptions.HTTPError()
            error.response = response
            raise error

        with pytest.raises(requests.exceptions.HTTPError):
            mock_function()

    def test_rate_limit_retry_non_429_error(self):
        """测试非429错误直接抛出"""

        @rate_limit_retry(max_retries=3, base_delay=0.1)
        def mock_function():
            response = Mock()
            response.status_code = 500
            error = requests.exceptions.HTTPError()
            error.response = response
            raise error

        with pytest.raises(requests.exceptions.HTTPError):
            mock_function()

    def test_rate_limit_retry_exponential_backoff(self):
        """测试指数退避算法"""
        delays = []

        def mock_sleep(seconds):
            delays.append(seconds)

        @rate_limit_retry(max_retries=3, base_delay=1)
        def mock_function():
            response = Mock()
            response.status_code = 429
            error = requests.exceptions.HTTPError()
            error.response = response
            raise error

        with patch("time.sleep", side_effect=mock_sleep):
            with pytest.raises(requests.exceptions.HTTPError):
                mock_function()

        # 验证指数退避：1, 2, 4 秒
        expected_delays = [1, 2]  # 第三次失败时不再sleep
        assert delays == expected_delays


class TestBinanceClientInitialization:
    """测试Binance客户端初始化 (Test Binance Client Initialization)"""

    def test_init_with_explicit_credentials(self):
        """测试使用显式凭据初始化"""
        client = BinanceClient(api_key="test_key", api_secret="test_secret", testnet=True)

        assert client.api_key == "test_key"
        assert client.api_secret == "test_secret"
        assert client.testnet is True
        assert client.base_url == "https://testnet.binance.vision/api"

    def test_init_with_production_url(self):
        """测试生产环境URL"""
        client = BinanceClient(api_key="test_key", api_secret="test_secret", testnet=False)

        assert client.base_url == "https://api.binance.com/api"

    def test_init_from_environment_variables(self):
        """测试从环境变量初始化"""
        with patch.dict(
            "os.environ",
            {
                "BINANCE_TESTNET_API_KEY": "env_test_key",
                "BINANCE_TESTNET_API_SECRET": "env_test_secret",
            },
        ):
            client = BinanceClient(load_from_env=True, testnet=True)

            assert client.api_key == "env_test_key"
            assert client.api_secret == "env_test_secret"

    def test_init_from_production_env_vars(self):
        """测试从生产环境变量初始化"""
        with patch.dict(
            "os.environ", {"BINANCE_API_KEY": "prod_key", "BINANCE_API_SECRET": "prod_secret"}
        ):
            client = BinanceClient(load_from_env=True, testnet=False)

            assert client.api_key == "prod_key"
            assert client.api_secret == "prod_secret"

    def test_init_from_config_file(self):
        """测试从配置文件加载凭据"""
        config_content = """
[BINANCE]
API_KEY = config_key
API_SECRET = config_secret
"""

        # 🧹 使用自动清理的临时文件替代delete=False
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini") as f:
            f.write(config_content)
            f.flush()  # 确保内容写入文件

            client = BinanceClient(config_file=f.name)

            assert client.api_key == "config_key"
            assert client.api_secret == "config_secret"

    def test_init_missing_credentials(self):
        """测试缺少凭据时抛出异常"""
        with pytest.raises(ValueError, match="API Key和Secret必须提供"):
            BinanceClient()

    def test_init_partial_credentials(self):
        """测试只提供部分凭据时抛出异常"""
        with pytest.raises(ValueError, match="API Key和Secret必须提供"):
            BinanceClient(api_key="test_key")

    def test_init_priority_explicit_over_env(self):
        """测试显式参数优先级高于环境变量"""
        with patch.dict(
            "os.environ",
            {"BINANCE_TESTNET_API_KEY": "env_key", "BINANCE_TESTNET_API_SECRET": "env_secret"},
        ):
            client = BinanceClient(
                api_key="explicit_key", api_secret="explicit_secret", load_from_env=True
            )

            assert client.api_key == "explicit_key"
            assert client.api_secret == "explicit_secret"


class TestBinanceClientSignature:
    """测试Binance客户端签名生成 (Test Binance Client Signature)"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return BinanceClient(api_key="test_key", api_secret="test_secret")

    def test_generate_signature_basic(self, client):
        """测试基本签名生成"""
        params = {"symbol": "BTCUSDT", "timestamp": 1234567890}
        signature = client._generate_signature(params)

        # 手动计算期望的签名
        query_string = urlencode(params)
        expected_signature = hmac.new(
            "test_secret".encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        assert signature == expected_signature

    def test_generate_signature_empty_params(self, client):
        """测试空参数的签名生成"""
        params = {}
        signature = client._generate_signature(params)

        expected_signature = hmac.new(
            "test_secret".encode("utf-8"), "".encode("utf-8"), hashlib.sha256
        ).hexdigest()

        assert signature == expected_signature

    def test_generate_signature_multiple_params(self, client):
        """测试多参数签名生成"""
        params = {
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "LIMIT",
            "quantity": "0.001",
            "price": "50000",
            "timestamp": 1234567890,
        }
        signature = client._generate_signature(params)

        # 验证签名是64字符的十六进制字符串
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)


class TestBinanceClientPublicMethods:
    """测试Binance客户端公共方法 (Test Binance Client Public Methods)"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return BinanceClient(api_key="test_key", api_secret="test_secret")

    @patch("requests.get")
    def test_get_server_time_success(self, mock_get, client):
        """测试获取服务器时间成功"""
        expected_response = {"serverTime": 1234567890000}
        mock_get.return_value.json.return_value = expected_response

        result = client.get_server_time()

        assert result == expected_response
        mock_get.assert_called_once_with(f"{client.base_url}/v3/time", timeout=10)

    @patch("requests.get")
    def test_get_klines_success(self, mock_get, client):
        """测试获取K线数据成功"""
        mock_data = [
            [
                1609459200000,
                "29000.0",
                "30000.0",
                "28000.0",
                "29500.0",
                "100.0",
                1609545599999,
                "2950000.0",
                1000,
                "50.0",
                "1475000.0",
                "0",
            ]
        ]
        mock_response = Mock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = client.get_klines("BTCUSDT", "1d", 1)

        # 验证返回的是DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.loc[0, "open"] == 29000.0
        assert result.loc[0, "high"] == 30000.0
        assert result.loc[0, "low"] == 28000.0
        assert result.loc[0, "close"] == 29500.0
        assert result.loc[0, "volume"] == 100.0

        # 验证请求参数
        mock_get.assert_called_once_with(
            f"{client.base_url}/v3/klines",
            params={"symbol": "BTCUSDT", "interval": "1d", "limit": 1},
            timeout=10,
        )

    @patch("requests.get")
    def test_get_klines_with_custom_params(self, mock_get, client):
        """测试自定义参数获取K线数据"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client.get_klines("ETHUSDT", "1h", 24)

        mock_get.assert_called_once_with(
            f"{client.base_url}/v3/klines",
            params={"symbol": "ETHUSDT", "interval": "1h", "limit": 24},
            timeout=10,
        )

    @patch("requests.get")
    def test_get_klines_http_error(self, mock_get, client):
        """测试K线数据请求HTTP错误"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            client.get_klines("BTCUSDT")

    @patch("requests.get")
    def test_get_klines_retry_on_429(self, mock_get, client):
        """测试K线数据请求遇到429自动重试"""
        # 第一次请求返回429，第二次成功
        mock_response_429 = Mock()
        mock_response_429.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_response_429.raise_for_status.side_effect.response = Mock(status_code=429)

        mock_response_success = Mock()
        mock_response_success.json.return_value = []
        mock_response_success.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response_429, mock_response_success]

        with patch("time.sleep"):  # 避免实际睡眠
            result = client.get_klines("BTCUSDT")

        assert isinstance(result, pd.DataFrame)
        assert mock_get.call_count == 2


class TestBinanceClientPrivateMethods:
    """测试Binance客户端私有方法 (Test Binance Client Private Methods)"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return BinanceClient(api_key="test_key", api_secret="test_secret")

    @patch("requests.get")
    @patch("time.time")
    def test_get_account_info_success(self, mock_time, mock_get, client):
        """测试获取账户信息成功"""
        mock_time.return_value = 1234567890
        expected_response = {
            "makerCommission": 15,
            "takerCommission": 15,
            "balances": [
                {"asset": "BTC", "free": "0.001", "locked": "0.0"},
                {"asset": "USDT", "free": "100.0", "locked": "0.0"},
            ],
        }
        mock_get.return_value.json.return_value = expected_response

        result = client.get_account_info()

        assert result == expected_response

        # 验证请求参数
        call_args = mock_get.call_args
        assert call_args[0][0] == f"{client.base_url}/v3/account"
        assert call_args[1]["headers"]["X-MBX-APIKEY"] == "test_key"
        assert "timestamp" in call_args[1]["params"]
        assert "signature" in call_args[1]["params"]

    @patch("requests.post")
    @patch("time.time")
    def test_place_order_limit_success(self, mock_time, mock_post, client):
        """测试限价单下单成功"""
        mock_time.return_value = 1234567890
        expected_response = {"symbol": "BTCUSDT", "orderId": 123456, "status": "NEW", "code": 0}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = client.place_order(
            symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity="0.001", price="50000"
        )

        assert result == expected_response

        # 验证请求参数
        call_args = mock_post.call_args
        assert call_args[0][0] == f"{client.base_url}/v3/order"
        assert call_args[1]["headers"]["X-MBX-APIKEY"] == "test_key"

        params = call_args[1]["params"]
        assert params["symbol"] == "BTCUSDT"
        assert params["side"] == "BUY"
        assert params["type"] == "LIMIT"
        assert params["quantity"] == "0.001"
        assert params["price"] == "50000"
        assert "timestamp" in params
        assert "signature" in params

    @patch("requests.post")
    @patch("time.time")
    def test_place_order_market_success(self, mock_time, mock_post, client):
        """测试市价单下单成功"""
        mock_time.return_value = 1234567890
        expected_response = {"orderId": 123456, "code": 0}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = client.place_order(
            symbol="BTCUSDT", side="SELL", order_type="MARKET", quantity="0.001"
        )

        assert result == expected_response

        # 验证市价单不包含price参数
        call_args = mock_post.call_args
        params = call_args[1]["params"]
        assert "price" not in params

    @patch("requests.post")
    @patch("time.time")
    def test_place_order_stop_loss_success(self, mock_time, mock_post, client):
        """测试止损单下单成功"""
        mock_time.return_value = 1234567890
        expected_response = {"orderId": 123456, "code": 0}
        mock_response = Mock()
        mock_response.json.return_value = expected_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = client.place_order(
            symbol="BTCUSDT",
            side="SELL",
            order_type="STOP_LOSS_LIMIT",
            quantity="0.001",
            price="48000",
            stop_price="49000",
        )

        assert result == expected_response

        # 验证止损单包含stopPrice参数
        call_args = mock_post.call_args
        params = call_args[1]["params"]
        assert params["stopPrice"] == "49000"

    @patch("requests.post")
    @patch("time.time")
    def test_place_order_failure(self, mock_time, mock_post, client):
        """测试下单失败"""
        mock_time.return_value = 1234567890
        error_response = {"code": -1013, "msg": "Filter failure: LOT_SIZE"}
        mock_response = Mock()
        mock_response.json.return_value = error_response
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="下单失败: Filter failure: LOT_SIZE"):
            client.place_order("BTCUSDT", "BUY", "LIMIT", "0.001", "50000")

    @patch("requests.delete")
    @patch("time.time")
    def test_cancel_order_by_id(self, mock_time, mock_delete, client):
        """测试通过订单ID取消订单"""
        mock_time.return_value = 1234567890
        expected_response = {"symbol": "BTCUSDT", "status": "CANCELED"}
        mock_delete.return_value.json.return_value = expected_response

        result = client.cancel_order("BTCUSDT", order_id=123456)

        assert result == expected_response

        # 验证请求参数
        call_args = mock_delete.call_args
        params = call_args[1]["params"]
        assert params["symbol"] == "BTCUSDT"
        assert params["orderId"] == 123456
        assert "signature" in params

    @patch("requests.delete")
    @patch("time.time")
    def test_cancel_order_by_client_id(self, mock_time, mock_delete, client):
        """测试通过客户端订单ID取消订单"""
        mock_time.return_value = 1234567890
        expected_response = {"status": "CANCELED"}
        mock_delete.return_value.json.return_value = expected_response

        result = client.cancel_order("BTCUSDT", orig_client_order_id="my_order_123")

        assert result == expected_response

        # 验证请求参数
        call_args = mock_delete.call_args
        params = call_args[1]["params"]
        assert params["origClientOrderId"] == "my_order_123"

    def test_cancel_order_missing_id(self, client):
        """测试取消订单时缺少ID参数"""
        with pytest.raises(ValueError, match="必须提供order_id或orig_client_order_id"):
            client.cancel_order("BTCUSDT")

    @patch("requests.get")
    @patch("time.time")
    def test_get_open_orders_all_symbols(self, mock_time, mock_get, client):
        """测试获取所有交易对的挂单"""
        mock_time.return_value = 1234567890
        expected_response = [
            {"symbol": "BTCUSDT", "orderId": 123456, "status": "NEW"},
            {"symbol": "ETHUSDT", "orderId": 789012, "status": "NEW"},
        ]
        mock_get.return_value.json.return_value = expected_response

        result = client.get_open_orders()

        assert result == expected_response

        # 验证请求参数
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert "symbol" not in params

    @patch("requests.get")
    @patch("time.time")
    def test_get_open_orders_specific_symbol(self, mock_time, mock_get, client):
        """测试获取特定交易对的挂单"""
        mock_time.return_value = 1234567890
        expected_response = [{"symbol": "BTCUSDT", "orderId": 123456}]
        mock_get.return_value.json.return_value = expected_response

        result = client.get_open_orders("BTCUSDT")

        assert result == expected_response

        # 验证请求参数
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["symbol"] == "BTCUSDT"


class TestBinanceClientBalance:
    """测试Binance客户端余额方法 (Test Binance Client Balance Methods)"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return BinanceClient(api_key="test_key", api_secret="test_secret")

    @patch.object(BinanceClient, "get_account_info")
    def test_get_balance_specific_asset(self, mock_get_account, client):
        """测试获取特定资产余额"""
        mock_account_info = {
            "balances": [
                {"asset": "BTC", "free": "0.001", "locked": "0.0"},
                {"asset": "USDT", "free": "100.0", "locked": "0.0"},
                {"asset": "ETH", "free": "0.5", "locked": "0.0"},
            ]
        }
        mock_get_account.return_value = mock_account_info

        btc_balance = client.get_balance("BTC")
        usdt_balance = client.get_balance("USDT")

        assert btc_balance == 0.001
        assert usdt_balance == 100.0

    @patch.object(BinanceClient, "get_account_info")
    def test_get_balance_nonexistent_asset(self, mock_get_account, client):
        """测试获取不存在资产的余额"""
        mock_account_info = {"balances": [{"asset": "BTC", "free": "0.001", "locked": "0.0"}]}
        mock_get_account.return_value = mock_account_info

        balance = client.get_balance("NONEXISTENT")

        assert balance == 0.0

    @patch.object(BinanceClient, "get_account_info")
    def test_get_balance_all_assets(self, mock_get_account, client):
        """测试获取所有资产余额"""
        mock_account_info = {
            "balances": [
                {"asset": "BTC", "free": "0.001", "locked": "0.0"},
                {"asset": "USDT", "free": "100.0", "locked": "0.0"},
                {"asset": "ETH", "free": "0.5", "locked": "0.0"},
            ]
        }
        mock_get_account.return_value = mock_account_info

        all_balances = client.get_balance()

        expected_balances = {"BTC": 0.001, "USDT": 100.0, "ETH": 0.5}

        assert all_balances == expected_balances


class TestBinanceClientIntegration:
    """测试Binance客户端集成 (Test Binance Client Integration)"""

    def test_full_workflow_simulation(self):
        """测试完整工作流程模拟"""
        client = BinanceClient(api_key="test_key", api_secret="test_secret")

        # 模拟各种API调用
        with (
            patch("requests.get") as mock_get,
            patch("requests.post") as mock_post,
            patch("requests.delete") as mock_delete,
            patch("time.time", return_value=1234567890),
        ):
            # 1. 获取服务器时间
            mock_get.return_value.json.return_value = {"serverTime": 1234567890000}
            server_time = client.get_server_time()
            assert "serverTime" in server_time

            # 2. 获取账户信息
            mock_get.return_value.json.return_value = {
                "balances": [{"asset": "USDT", "free": "1000.0", "locked": "0.0"}]
            }
            account_info = client.get_account_info()
            assert "balances" in account_info

            # 3. 获取余额
            usdt_balance = client.get_balance("USDT")
            assert usdt_balance == 1000.0

            # 4. 下单
            mock_response = Mock()
            mock_response.json.return_value = {"orderId": 123456, "code": 0}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            order_result = client.place_order("BTCUSDT", "BUY", "LIMIT", "0.001", "50000")
            assert order_result["orderId"] == 123456

            # 5. 取消订单
            mock_delete.return_value.json.return_value = {"status": "CANCELED"}
            cancel_result = client.cancel_order("BTCUSDT", order_id=123456)
            assert cancel_result["status"] == "CANCELED"

    def test_error_handling_workflow(self):
        """测试错误处理工作流程"""
        client = BinanceClient(api_key="test_key", api_secret="test_secret")

        # 测试网络错误
        with patch(
            "requests.get", side_effect=requests.exceptions.ConnectionError("Network error")
        ):
            with pytest.raises(requests.exceptions.ConnectionError):
                client.get_server_time()

        # 测试API错误响应
        with patch("requests.post") as mock_post, patch("time.time", return_value=1234567890):
            mock_response = Mock()
            mock_response.json.return_value = {"code": -1013, "msg": "Invalid quantity"}
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="下单失败: Invalid quantity"):
                client.place_order("BTCUSDT", "BUY", "LIMIT", "0.001", "50000")

    def test_configuration_priority(self):
        """测试配置优先级"""
        # 测试显式参数 > 环境变量 > 配置文件
        with patch.dict(
            "os.environ",
            {"BINANCE_TESTNET_API_KEY": "env_key", "BINANCE_TESTNET_API_SECRET": "env_secret"},
        ):
            # 显式参数应该优先
            client1 = BinanceClient(
                api_key="explicit_key", api_secret="explicit_secret", load_from_env=True
            )
            assert client1.api_key == "explicit_key"

            # 只有环境变量时使用环境变量
            client2 = BinanceClient(load_from_env=True)
            assert client2.api_key == "env_key"
