#!/usr/bin/env python3
"""
Binance API 客户端 - 支持Testnet和生产环境
"""
import configparser
import hashlib
import hmac
import logging
import os
import time
from functools import wraps
from urllib.parse import urlencode

import pandas as pd
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rate_limit_retry(max_retries=3, base_delay=1):
    """
    处理HTTP 429 (Too Many Requests) 的装饰器

    参数:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间(秒)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Too Many Requests
                        retries += 1
                        if retries == max_retries:
                            logger.error(
                                f"达到最大重试次数 {max_retries}，请求失败"
                            )
                            raise

                        # 计算退避时间，使用指数退避
                        delay = base_delay * (2 ** (retries - 1))
                        logger.warning(
                            f"遇到速率限制，等待 {delay} 秒后重试 (尝试 {retries}/{max_retries})"
                        )
                        time.sleep(delay)
                    else:
                        raise
            return None

        return wrapper

    return decorator


class BinanceClient:
    """Binance API客户端，支持Testnet"""

    def __init__(
        self,
        api_key=None,
        api_secret=None,
        testnet=True,
        load_from_env=False,
        config_file=None,
    ):
        """
        初始化Binance客户端

        参数:
            api_key: API Key，如果为None则尝试从环境变量或配置文件读取
            api_secret: API Secret，如果为None则尝试从环境变量或配置文件读取
            testnet: 是否使用测试网络 (默认: True)
            load_from_env: 是否从环境变量加载凭据 (默认: False)
            config_file: 配置文件路径，如果提供则从配置文件加载凭据
        """
        self.testnet = testnet

        # 从环境变量加载
        if load_from_env and not (api_key and api_secret):
            api_key = os.environ.get(
                "BINANCE_TESTNET_API_KEY" if testnet else "BINANCE_API_KEY"
            )
            api_secret = os.environ.get(
                "BINANCE_TESTNET_API_SECRET"
                if testnet
                else "BINANCE_API_SECRET"
            )

        # 从配置文件加载
        if config_file and not (api_key and api_secret):
            config = configparser.ConfigParser()
            config.read(config_file)
            api_key = config["BINANCE"]["API_KEY"]
            api_secret = config["BINANCE"]["API_SECRET"]

        if not api_key or not api_secret:
            raise ValueError(
                "API Key和Secret必须提供，或从环境变量/配置文件加载"
            )

        self.api_key = api_key
        self.api_secret = api_secret

        # 设置API URL
        if testnet:
            self.base_url = "https://testnet.binance.vision/api"
        else:
            self.base_url = "https://api.binance.com/api"

    def _generate_signature(self, params):
        """生成API请求签名"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def get_server_time(self):
        """获取服务器时间"""
        response = requests.get(f"{self.base_url}/v3/time")
        return response.json()

    def get_account_info(self):
        """获取账户信息"""
        endpoint = "/v3/account"
        timestamp = int(time.time() * 1000)
        params = {"timestamp": timestamp}
        params["signature"] = self._generate_signature(params)

        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.get(
            f"{self.base_url}{endpoint}", headers=headers, params=params
        )
        return response.json()

    @rate_limit_retry(max_retries=3, base_delay=1)
    def get_klines(self, symbol, interval="1d", limit=100):
        """
        获取K线数据

        参数:
            symbol: 交易对，如'BTCUSDT'
            interval: K线周期，如'1m', '5m', '1h', '1d'
            limit: 获取的K线数量

        返回:
            pandas.DataFrame: 包含K线数据的DataFrame
        """
        endpoint = "/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}

        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        response.raise_for_status()  # 检查HTTP错误
        data = response.json()

        # 转换为DataFrame
        df = pd.DataFrame(
            data,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )

        # 转换数据类型
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
            df[col] = df[col].astype(float)

        return df

    def place_order(
        self, symbol, side, order_type, quantity, price=None, stop_price=None
    ):
        """
        下单

        参数:
            symbol: 交易对，如'BTCUSDT'
            side: 方向，'BUY' 或 'SELL'
            order_type: 订单类型，如'LIMIT', 'MARKET', 'STOP_LOSS_LIMIT'
            quantity: 数量
            price: 价格（限价单必需）
            stop_price: 止损价（止损单必需）

        返回:
            dict: 订单信息
        """
        endpoint = "/v3/order"
        timestamp = int(time.time() * 1000)

        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timestamp": timestamp,
        }

        if price:
            params["price"] = price
        if stop_price:
            params["stopPrice"] = stop_price

        params["signature"] = self._generate_signature(params)

        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.post(
            f"{self.base_url}{endpoint}", headers=headers, params=params
        )
        response.raise_for_status()

        result = response.json()

        # 检查订单是否成功
        if result.get("code") != 0:
            error_msg = result.get("msg", "未知错误")
            logger.error(f"下单失败: {error_msg}")
            raise Exception(f"下单失败: {error_msg}")

        return result

    def cancel_order(self, symbol, order_id=None, orig_client_order_id=None):
        """取消订单"""
        endpoint = "/v3/order"
        timestamp = int(time.time() * 1000)

        params = {"symbol": symbol, "timestamp": timestamp}

        # 可以使用订单ID或客户端订单ID
        if order_id:
            params["orderId"] = order_id
        elif orig_client_order_id:
            params["origClientOrderId"] = orig_client_order_id
        else:
            raise ValueError("必须提供order_id或orig_client_order_id")

        params["signature"] = self._generate_signature(params)

        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.delete(
            f"{self.base_url}{endpoint}", headers=headers, params=params
        )

        return response.json()

    def get_open_orders(self, symbol=None):
        """获取当前挂单"""
        endpoint = "/v3/openOrders"
        timestamp = int(time.time() * 1000)

        params = {"timestamp": timestamp}
        if symbol:
            params["symbol"] = symbol

        params["signature"] = self._generate_signature(params)

        headers = {"X-MBX-APIKEY": self.api_key}
        response = requests.get(
            f"{self.base_url}{endpoint}", headers=headers, params=params
        )

        return response.json()

    def get_balance(self, asset=None):
        """
        获取账户余额

        参数:
            asset: 资产名称，如'BTC'，如不提供则返回所有资产

        返回:
            float或dict: 如果提供asset，返回该资产余额，否则返回所有资产余额字典
        """
        account_info = self.get_account_info()
        balances = {
            b["asset"]: float(b["free"]) for b in account_info["balances"]
        }

        if asset:
            return balances.get(asset, 0.0)
        return balances


# 测试模块
if __name__ == "__main__":
    # 从配置文件或环境变量加载
    client = BinanceClient(config_file="config.ini", testnet=True)

    try:
        # 测试连接
        server_time = client.get_server_time()
        print(f"服务器时间: {server_time}")

        # 获取账户信息
        account = client.get_account_info()
        print(f"账户信息: {account}")

        # 获取BTC余额
        btc_balance = client.get_balance("BTC")
        print(f"BTC余额: {btc_balance}")

        # 获取K线数据
        klines = client.get_klines("BTCUSDT", "1d", 5)
        print(f"最近5日K线数据:\n{klines}")

    except Exception as e:
        print(f"错误: {e}")
