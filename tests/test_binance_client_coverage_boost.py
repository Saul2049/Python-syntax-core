"""
Binance客户端覆盖率提升测试 (Binance Client Coverage Boost Tests)

专门针对 src/brokers/binance/client.py 中未覆盖的代码行进行测试，
将覆盖率从 22% 提升到接近 90%。
"""

import tempfile
from unittest.mock import Mock, patch

import pytest
import requests

from src.brokers.binance.client import BinanceClient, rate_limit_retry


class TestRateLimitRetryAdvanced:
    """测试速率限制重试装饰器的高级场景"""

    def test_rate_limit_retry_no_response_attribute(self):
        """测试HTTP错误但没有response属性的情况"""

        @rate_limit_retry(max_retries=2, base_delay=0.1)
        def mock_function():
            error = requests.exceptions.HTTPError("Network error")
            raise error

        with pytest.raises(requests.exceptions.HTTPError):
            mock_function()

    def test_rate_limit_retry_none_response(self):
        """测试response为None的情况"""

        @rate_limit_retry(max_retries=2, base_delay=0.1)
        def mock_function():
            error = requests.exceptions.HTTPError()
            error.response = None
            raise error

        with pytest.raises(requests.exceptions.HTTPError):
            mock_function()


class TestBinanceClientInitializationEdgeCases:
    """测试Binance客户端初始化的边缘情况"""

    def test_init_load_from_env_testnet_missing_vars(self):
        """测试从环境变量加载但变量不存在的情况"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API Key和Secret必须提供"):
                BinanceClient(load_from_env=True, testnet=True)

    def test_init_config_file_missing_section(self):
        """测试配置文件缺少BINANCE节的情况"""
        config_content = """
[OTHER_SECTION]
KEY = value
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write(config_content)
            f.flush()

            with pytest.raises(KeyError):
                BinanceClient(config_file=f.name)


class TestBinanceClientMethodsEdgeCases:
    """测试Binance客户端方法的边缘情况"""

    @pytest.fixture
    def client(self):
        return BinanceClient(api_key="test_key", api_secret="test_secret", testnet=True)

    @patch("requests.get")
    def test_get_server_time_request_failure(self, mock_get, client):
        """测试获取服务器时间请求失败"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(requests.exceptions.RequestException):
            client.get_server_time()

    @patch("requests.get")
    @patch("time.time")
    def test_get_account_info_request_failure(self, mock_time, mock_get, client):
        """测试获取账户信息请求失败"""
        mock_time.return_value = 1234567890
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        with pytest.raises(requests.exceptions.RequestException):
            client.get_account_info()


class TestBinanceClientPlaceOrderEdgeCases:
    """测试下单方法的边缘情况"""

    @pytest.fixture
    def client(self):
        return BinanceClient(api_key="test_key", api_secret="test_secret", testnet=True)

    @patch("requests.post")
    @patch("time.time")
    def test_place_order_api_error_response(self, mock_time, mock_post, client):
        """测试API返回错误响应"""
        mock_time.return_value = 1234567890
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"code": -1013, "msg": "Invalid quantity"}
        mock_post.return_value = mock_response

        with pytest.raises(Exception, match="下单失败: Invalid quantity"):
            client.place_order(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=0.00001)


class TestBinanceClientCancelOrderEdgeCases:
    """测试取消订单方法的边缘情况"""

    @pytest.fixture
    def client(self):
        return BinanceClient(api_key="test_key", api_secret="test_secret", testnet=True)

    def test_cancel_order_no_id_provided(self, client):
        """测试取消订单时没有提供任何ID"""
        with pytest.raises(ValueError, match="必须提供order_id或orig_client_order_id"):
            client.cancel_order("BTCUSDT")


class TestBinanceClientGetBalanceEdgeCases:
    """测试获取余额方法的边缘情况"""

    @pytest.fixture
    def client(self):
        return BinanceClient(api_key="test_key", api_secret="test_secret", testnet=True)

    def test_get_balance_specific_asset_not_exists(self, client):
        """测试获取不存在的资产余额"""
        mock_account_info = {
            "balances": [
                {"asset": "BTC", "free": "1.5", "locked": "0.0"},
                {"asset": "ETH", "free": "10.0", "locked": "0.0"},
            ]
        }

        with patch.object(client, "get_account_info", return_value=mock_account_info):
            balance = client.get_balance("DOGE")  # 不存在的资产
            assert balance == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
