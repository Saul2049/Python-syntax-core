#!/usr/bin/env python3
# exchange_client.py
# 加密货币交易所客户端接口

import logging
import random
import socket
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import requests
from requests.exceptions import ConnectionError, Timeout

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("exchange_client")


class ExchangeClient:
    """交易所API客户端接口"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://api.example.com",
        timeout: int = 10,
        retry_count: int = 3,
        retry_delay: int = 1,
        demo_mode: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.demo_mode = demo_mode
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        self._last_request_time = 0
        self._rate_limit_per_sec = 5  # 每秒请求限制

        # 用于演示模式的状态存储
        if demo_mode:
            self._demo_balances = {"BTC": 1.0, "ETH": 10.0, "USDT": 10000.0}
            self._demo_orders = []
            self._demo_market_data = {}
            self._load_demo_data()

    def _load_demo_data(self):
        """加载演示数据"""
        try:
            df = pd.read_csv("btc_eth.csv", parse_dates=["date"], index_col="date")
            self._demo_market_data = {
                "BTC/USDT": df["btc"].to_dict(),
                "ETH/USDT": df["eth"].to_dict(),
            }
            logger.info("已加载演示数据")
        except Exception as e:
            logger.warning(f"无法加载演示数据: {e}")
            # 创建一些随机数据作为备用
            now = datetime.now()
            dates = [now - timedelta(days=i) for i in range(100)]
            self._demo_market_data = {
                "BTC/USDT": {d: 30000 + random.randint(-1000, 1000) for d in dates},
                "ETH/USDT": {d: 2000 + random.randint(-100, 100) for d in dates},
            }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        data: dict = None,
    ) -> dict:
        """
        发送HTTP请求到交易所API

        包含速率限制、重试逻辑和错误处理
        """
        url = f"{self.base_url}{endpoint}"

        # 演示模式模拟网络错误和延迟
        if self.demo_mode:
            # 随机模拟网络延迟
            time.sleep(random.uniform(0.1, 0.5))
            # 随机模拟网络错误
            if random.random() < 0.05:  # 5%概率出错
                error_type = random.choice([ConnectionError, Timeout, socket.error])
                raise error_type("模拟网络错误")

        # 实现速率限制
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < 1.0 / self._rate_limit_per_sec:
            sleep_time = 1.0 / self._rate_limit_per_sec - time_since_last_request
            time.sleep(sleep_time)

        # 带重试的请求逻辑
        for attempt in range(self.retry_count):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=self.timeout,
                )
                self._last_request_time = time.time()

                # 检查HTTP状态码
                response.raise_for_status()

                # 解析并返回JSON响应
                return response.json()

            except (ConnectionError, Timeout, socket.error) as e:
                if attempt < self.retry_count - 1:
                    sleep_time = self.retry_delay * (2**attempt)  # 指数退避
                    logger.warning(
                        f"请求失败 (尝试 {attempt+1}/{self.retry_count}): " f"{str(e)}. 等待 {sleep_time}秒后重试..."
                    )
                    time.sleep(sleep_time)
                else:
                    logger.error(f"请求失败，已达到最大重试次数: {str(e)}")
                    raise

            except Exception as e:
                logger.error(f"请求过程中出现错误: {str(e)}")
                raise

    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        if self.demo_mode:
            return self._demo_balances.copy()

        endpoint = "/api/v1/account/balance"
        response = self._request("GET", endpoint)
        return {asset: float(balance) for asset, balance in response.items()}

    def get_ticker(self, symbol: str) -> Dict[str, float]:
        """获取交易对的最新行情"""
        if self.demo_mode:
            # 在演示模式下返回最新市场数据
            market_data = self._demo_market_data.get(symbol, {})
            if not market_data:
                return {"price": 0.0, "volume": 0.0}

            latest_date = max(market_data.keys())
            return {
                "price": market_data[latest_date],
                "volume": random.uniform(100, 1000),
            }

        endpoint = f"/api/v1/ticker/{symbol}"
        return self._request("GET", endpoint)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Dict:
        """
        下单接口

        参数:
            symbol: 交易对，如 "BTC/USDT"
            side: 买卖方向，"buy" 或 "sell"
            order_type: 订单类型，"limit" 或 "market"
            quantity: 数量
            price: 价格，仅限价单需要

        返回:
            包含订单ID和状态的字典
        """
        if self.demo_mode:
            order_id = f"demo_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
            order = {
                "id": order_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price if price else self.get_ticker(symbol)["price"],
                "status": "filled",
                "timestamp": datetime.now().isoformat(),
            }
            self._demo_orders.append(order)

            # 更新演示模式的余额
            base, quote = symbol.split("/")
            if side == "buy":
                self._demo_balances[quote] -= quantity * (price or self.get_ticker(symbol)["price"])
                self._demo_balances[base] += quantity
            else:
                self._demo_balances[base] -= quantity
                self._demo_balances[quote] += quantity * (price or self.get_ticker(symbol)["price"])

            return order

        endpoint = "/api/v1/order"
        data = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "limit" and price is not None:
            data["price"] = price

        return self._request("POST", endpoint, data=data)

    def get_historical_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """获取历史成交记录"""
        if self.demo_mode:
            return self._demo_orders

        endpoint = f"/api/v1/trades/{symbol}"
        params = {"limit": limit}
        return self._request("GET", endpoint, params=params)

    def get_historical_klines(
        self,
        symbol: str,
        interval: str = "1d",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[List]:
        """
        获取K线历史数据

        参数:
            symbol: 交易对
            interval: 时间间隔，如 "1m", "5m", "1h", "1d"
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            limit: 返回的数据点数量上限

        返回:
            K线数据列表，每个元素包含 [时间戳, 开盘价, 最高价, 最低价, 收盘价, 交易量]
        """
        if self.demo_mode:
            if symbol not in self._demo_market_data:
                return []

            market_data = self._demo_market_data[symbol]
            dates = sorted(market_data.keys())

            if start_time:
                start_date = datetime.fromtimestamp(start_time / 1000)
                dates = [d for d in dates if d >= start_date]

            if end_time:
                end_date = datetime.fromtimestamp(end_time / 1000)
                dates = [d for d in dates if d <= end_date]

            # 限制返回的数据点数量
            if limit and len(dates) > limit:
                dates = dates[-limit:]

            result = []
            for date in dates:
                price = market_data[date]
                timestamp = int(date.timestamp() * 1000)
                # 模拟生成 OHLCV 数据
                open_price = price * random.uniform(0.995, 1.005)
                high_price = price * random.uniform(1.005, 1.015)
                low_price = price * random.uniform(0.985, 0.995)
                close_price = price
                volume = random.uniform(100, 1000)

                result.append(
                    [
                        timestamp,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume,
                    ]
                )

            return result

        endpoint = f"/api/v1/klines/{symbol}"
        params = {
            "interval": interval,
            "limit": limit,
        }

        if start_time:
            params["startTime"] = start_time

        if end_time:
            params["endTime"] = end_time

        return self._request("GET", endpoint, params=params)

    def sync_market_data(self, symbol: str, interval: str = "1d", days: int = 30) -> pd.DataFrame:
        """
        同步并返回市场数据

        参数:
            symbol: 交易对
            interval: 时间间隔
            days: 获取过去多少天的数据

        返回:
            包含OHLCV数据的DataFrame
        """
        logger.info(f"同步{symbol}市场数据，间隔={interval}，天数={days}")

        end_time = int(time.time() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)

        klines = self.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )

        if not klines:
            logger.warning(f"未获取到{symbol}的市场数据")
            return pd.DataFrame()

        df = pd.DataFrame(
            klines,
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        # 转换时间戳为datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # 转换价格和交易量为数值类型
        numeric_columns = ["open", "high", "low", "close", "volume"]
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric)

        logger.info(f"成功同步{len(df)}条{symbol}市场数据")
        return df
