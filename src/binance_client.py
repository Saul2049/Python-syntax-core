#!/usr/bin/env python3
"""
Binance API 客户端 - 支持Testnet和生产环境
"""
import os
import time
import hmac
import hashlib
import configparser
from urllib.parse import urlencode
import requests
import pandas as pd

class BinanceClient:
    """Binance API客户端，支持Testnet"""
    
    def __init__(self, api_key=None, api_secret=None, testnet=True, load_from_env=False, config_file=None):
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
            api_key = os.environ.get('BINANCE_TESTNET_API_KEY' if testnet else 'BINANCE_API_KEY')
            api_secret = os.environ.get('BINANCE_TESTNET_API_SECRET' if testnet else 'BINANCE_API_SECRET')
        
        # 从配置文件加载
        if config_file and not (api_key and api_secret):
            config = configparser.ConfigParser()
            config.read(config_file)
            api_key = config['BINANCE']['API_KEY']
            api_secret = config['BINANCE']['API_SECRET']
        
        if not api_key or not api_secret:
            raise ValueError("API Key和Secret必须提供，或从环境变量/配置文件加载")
            
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
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
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
        params = {'timestamp': timestamp}
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
        return response.json()
    
    def get_klines(self, symbol, interval='1d', limit=100):
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
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(f"{self.base_url}{endpoint}", params=params)
        data = response.json()
        
        # 转换为DataFrame
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base', 
            'taker_buy_quote', 'ignore'
        ])
        
        # 转换数据类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = df[col].astype(float)
            
        # 转换时间戳
        df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # 设置索引
        df.set_index('open_time', inplace=True)
        
        return df
    
    def place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
        """
        下单
        
        参数:
            symbol: 交易对，如'BTCUSDT'
            side: 方向，'BUY' 或 'SELL'
            order_type: 订单类型，'LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT'等
            quantity: 数量
            price: 价格 (限价单必填)
            stop_price: 触发价格 (止损单必填)
            
        返回:
            dict: API响应
        """
        endpoint = "/v3/order"
        timestamp = int(time.time() * 1000)
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'timestamp': timestamp,
            'newOrderRespType': 'FULL'  # 返回完整响应
        }
        
        # 添加价格参数
        if price and order_type not in ['MARKET', 'STOP_LOSS']:
            params['price'] = f"{price:.8f}"
            
        # 添加止损价参数
        if stop_price and order_type in ['STOP_LOSS', 'STOP_LOSS_LIMIT']:
            params['stopPrice'] = f"{stop_price:.8f}"
            
        # 市价单特殊处理
        if order_type == 'MARKET':
            params['timeInForce'] = 'GTC'
            
        # 添加签名
        params['signature'] = self._generate_signature(params)
        
        # 发送请求
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.post(f"{self.base_url}{endpoint}", headers=headers, params=params)
        
        return response.json()
    
    def cancel_order(self, symbol, order_id=None, orig_client_order_id=None):
        """取消订单"""
        endpoint = "/v3/order"
        timestamp = int(time.time() * 1000)
        
        params = {
            'symbol': symbol,
            'timestamp': timestamp
        }
        
        # 可以使用订单ID或客户端订单ID
        if order_id:
            params['orderId'] = order_id
        elif orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        else:
            raise ValueError("必须提供order_id或orig_client_order_id")
            
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.delete(f"{self.base_url}{endpoint}", headers=headers, params=params)
        
        return response.json()
    
    def get_open_orders(self, symbol=None):
        """获取当前挂单"""
        endpoint = "/v3/openOrders"
        timestamp = int(time.time() * 1000)
        
        params = {'timestamp': timestamp}
        if symbol:
            params['symbol'] = symbol
            
        params['signature'] = self._generate_signature(params)
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
        
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
        balances = {b['asset']: float(b['free']) for b in account_info['balances']}
        
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