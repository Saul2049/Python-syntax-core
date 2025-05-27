#!/usr/bin/env python3
"""
M4阶段异步订单代理
Live Broker Async for M4 Phase

用途：
- 异步订单执行（非阻塞）
- 订单往返延迟监控
- 并发订单处理
"""

import asyncio
import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import aiohttp

from src.monitoring.metrics_collector import get_metrics_collector


class LiveBrokerAsync:
    """异步实时交易代理"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True) -> None:
        """
        初始化异步交易代理

        Args:
            api_key: API密钥 (API key)
            api_secret: API密钥 (API secret)
            testnet: 是否使用测试网 (Whether to use testnet)
        """
        self.api_key: str = api_key  # API密钥
        self.api_secret: str = api_secret  # API密钥
        self.testnet: bool = testnet  # 测试网标志

        # API端点
        if testnet:
            self.base_url: str = "https://testnet.binance.vision"
        else:
            self.base_url: str = "https://api.binance.com"

        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None  # HTTP会话对象

        # 监控指标
        self.metrics = get_metrics_collector()

        # 订单状态跟踪
        self.pending_orders: Dict[str, Dict[str, Any]] = {}  # 待处理订单字典
        self.order_history: List[Dict[str, Any]] = []  # 订单历史列表

        # 性能统计
        self.order_count: int = 0  # 订单总数
        self.error_count: int = 0  # 错误计数

    async def __aenter__(self) -> "LiveBrokerAsync":
        """异步上下文管理器入口"""
        await self.init_session()
        return self

    async def __aexit__(
        self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]
    ) -> None:
        """异步上下文管理器出口"""
        await self.close_session()

    async def init_session(self) -> None:
        """初始化HTTP会话"""
        connector: aiohttp.TCPConnector = aiohttp.TCPConnector(
            limit=100,  # 连接池大小
            limit_per_host=30,  # 每主机连接数
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,
        )

        timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(
            total=30, connect=10, sock_read=10  # 总超时  # 连接超时  # 读取超时
        )

        self.session = aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers={"X-MBX-APIKEY": self.api_key}
        )

    async def close_session(self) -> None:
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        生成API签名

        Args:
            params: 请求参数字典 (Request parameters dictionary)

        Returns:
            签名字符串 (Signature string)
        """
        query_string: str = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        异步HTTP请求

        Args:
            method: HTTP方法 (HTTP method)
            endpoint: API端点 (API endpoint)
            params: 请求参数 (Request parameters)
            signed: 是否需要签名 (Whether signature is required)

        Returns:
            响应数据字典 (Response data dictionary)

        Raises:
            Exception: 请求失败时抛出异常
        """
        if params is None:
            params = {}

        # 添加时间戳（签名请求）
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._generate_signature(params)

        url: str = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                async with self.session.get(url, params=params) as response:
                    return await self._handle_response(response)
            elif method.upper() == "POST":
                async with self.session.post(url, data=params) as response:
                    return await self._handle_response(response)
            elif method.upper() == "DELETE":
                async with self.session.delete(url, params=params) as response:
                    return await self._handle_response(response)

        except asyncio.TimeoutError:
            self.error_count += 1
            raise Exception("API请求超时")
        except aiohttp.ClientError as e:
            self.error_count += 1
            raise Exception(f"API请求失败: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        处理API响应

        Args:
            response: HTTP响应对象 (HTTP response object)

        Returns:
            解析后的响应数据 (Parsed response data)

        Raises:
            Exception: 响应状态码非200时抛出异常
        """
        if response.status == 200:
            return await response.json()
        else:
            error_text: str = await response.text()
            raise Exception(f"API错误 {response.status}: {error_text}")

    async def place_order_async(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        异步下单

        Args:
            symbol: 交易对 (Trading pair)
            side: 买卖方向 (BUY/SELL)
            order_type: 订单类型 (MARKET/LIMIT)
            quantity: 数量 (Quantity)
            price: 价格（限价单） (Price for limit orders)
            time_in_force: 有效期 (Time in force)

        Returns:
            订单信息字典 (Order information dictionary)
            - order_id: 订单ID
            - client_order_id: 客户端订单ID
            - symbol: 交易对
            - side: 买卖方向
            - type: 订单类型
            - quantity: 数量
            - price: 价格
            - status: 订单状态
            - submit_time: 提交时间
            - response: 原始响应

        Raises:
            Exception: 下单失败时抛出异常
        """
        start_time: float = time.perf_counter()

        try:
            # 构建订单参数
            params: Dict[str, Union[str, float]] = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "timeInForce": time_in_force,
            }

            if order_type == "LIMIT" and price:
                params["price"] = price

            # 记录并发任务开始
            self.metrics.update_concurrent_tasks("order_execution", len(self.pending_orders) + 1)

            # 执行下单请求
            response: Dict[str, Any] = await self._request(
                "POST", "/api/v3/order", params, signed=True
            )

            # 生成订单ID
            order_id: str = response.get("orderId", f"async_{int(time.time())}")
            client_order_id: str = response.get("clientOrderId", f"client_{order_id}")

            # 记录订单信息
            order_info: Dict[str, Any] = {
                "order_id": order_id,
                "client_order_id": client_order_id,
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "price": price,
                "status": response.get("status", "NEW"),
                "submit_time": start_time,
                "response": response,
            }

            # 添加到待处理订单
            self.pending_orders[order_id] = order_info

            # 启动订单状态监控任务
            asyncio.create_task(self._monitor_order_status(order_id))

            self.order_count += 1

            print(f"✅ 异步下单成功: {symbol} {side} {quantity} @ {price or 'MARKET'}")

            return order_info

        except Exception as e:
            self.error_count += 1
            self.metrics.record_exception("live_broker_async", e)

            # 记录失败的订单往返延迟
            failed_latency: float = time.perf_counter() - start_time
            self.metrics.observe_order_roundtrip_latency(failed_latency)

            print(f"❌ 异步下单失败: {e}")
            raise
        finally:
            # 更新并发任务计数
            self.metrics.update_concurrent_tasks("order_execution", len(self.pending_orders))

    async def _monitor_order_status(self, order_id: str) -> None:
        """
        监控订单状态直到完成

        Args:
            order_id: 订单ID (Order ID)
        """
        max_attempts: int = 30  # 最多监控30次
        attempt: int = 0

        while attempt < max_attempts:
            try:
                if order_id not in self.pending_orders:
                    break

                order_info: Dict[str, Any] = self.pending_orders[order_id]

                # 查询订单状态
                params: Dict[str, str] = {"symbol": order_info["symbol"], "orderId": order_id}

                response: Dict[str, Any] = await self._request(
                    "GET", "/api/v3/order", params, signed=True
                )
                status: str = response.get("status", "UNKNOWN")

                # 更新订单状态
                order_info["status"] = status
                order_info["last_update"] = time.perf_counter()

                # 检查是否完成
                if status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                    # 计算订单往返延迟
                    roundtrip_latency: float = time.perf_counter() - order_info["submit_time"]
                    self.metrics.observe_order_roundtrip_latency(roundtrip_latency)

                    # 移动到历史记录
                    order_info["complete_time"] = time.perf_counter()
                    order_info["roundtrip_latency"] = roundtrip_latency
                    self.order_history.append(order_info)

                    # 从待处理中移除
                    del self.pending_orders[order_id]

                    print(
                        f"🏁 订单完成: {order_id} 状态:{status} 延迟:{roundtrip_latency*1000:.1f}ms"
                    )
                    break

                # 等待后再次检查
                await asyncio.sleep(1)
                attempt += 1

            except Exception as e:
                print(f"⚠️ 订单状态监控错误: {e}")
                attempt += 1
                await asyncio.sleep(2)

        # 超时处理
        if attempt >= max_attempts and order_id in self.pending_orders:
            print(f"⏰ 订单监控超时: {order_id}")
            order_info = self.pending_orders[order_id]
            order_info["status"] = "TIMEOUT"
            self.order_history.append(order_info)
            del self.pending_orders[order_id]

    async def cancel_order_async(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        异步撤单

        Args:
            symbol: 交易对 (Trading pair)
            order_id: 订单ID (Order ID)

        Returns:
            撤单响应字典 (Cancel order response dictionary)

        Raises:
            Exception: 撤单失败时抛出异常
        """
        try:
            params: Dict[str, str] = {"symbol": symbol, "orderId": order_id}

            response: Dict[str, Any] = await self._request(
                "DELETE", "/api/v3/order", params, signed=True
            )

            print(f"✅ 异步撤单成功: {order_id}")
            return response

        except Exception as e:
            self.error_count += 1
            print(f"❌ 异步撤单失败: {e}")
            raise

    async def get_account_info_async(self) -> Dict[str, Any]:
        """
        异步获取账户信息

        Returns:
            账户信息字典 (Account information dictionary)

        Raises:
            Exception: 获取账户信息失败时抛出异常
        """
        try:
            response: Dict[str, Any] = await self._request("GET", "/api/v3/account", signed=True)
            return response

        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取账户信息失败: {e}")
            raise

    async def get_open_orders_async(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        异步获取未完成订单

        Args:
            symbol: 交易对（可选） (Trading pair, optional)

        Returns:
            未完成订单列表 (List of open orders)

        Raises:
            Exception: 获取未完成订单失败时抛出异常
        """
        try:
            params: Dict[str, str] = {}
            if symbol:
                params["symbol"] = symbol

            response: List[Dict[str, Any]] = await self._request(
                "GET", "/api/v3/openOrders", params, signed=True
            )
            return response

        except Exception as e:
            self.error_count += 1
            print(f"❌ 获取未完成订单失败: {e}")
            raise

    def get_performance_stats(self) -> Dict[str, Union[int, float]]:
        """
        获取性能统计

        Returns:
            性能统计字典 (Performance statistics dictionary)
            - total_orders: 总订单数
            - completed_orders: 完成订单数
            - pending_orders: 待处理订单数
            - error_count: 错误计数
            - avg_roundtrip_latency_ms: 平均往返延迟(毫秒)
            - success_rate: 成功率(百分比)
        """
        total_orders: int = len(self.order_history)
        if total_orders > 0:
            avg_latency: float = (
                sum(o.get("roundtrip_latency", 0) for o in self.order_history) / total_orders
            )
            completed_orders: int = len(
                [o for o in self.order_history if o.get("status") == "FILLED"]
            )
        else:
            avg_latency = 0
            completed_orders = 0

        return {
            "total_orders": self.order_count,
            "completed_orders": completed_orders,
            "pending_orders": len(self.pending_orders),
            "error_count": self.error_count,
            "avg_roundtrip_latency_ms": avg_latency * 1000,
            "success_rate": completed_orders / max(total_orders, 1) * 100,
        }


# 工具函数
async def create_async_broker(
    api_key: str, api_secret: str, testnet: bool = True
) -> LiveBrokerAsync:
    """
    创建异步代理实例

    Args:
        api_key: API密钥 (API key)
        api_secret: API密钥 (API secret)
        testnet: 是否使用测试网 (Whether to use testnet)

    Returns:
        初始化的异步代理实例 (Initialized async broker instance)
    """
    broker: LiveBrokerAsync = LiveBrokerAsync(api_key, api_secret, testnet)
    await broker.init_session()
    return broker


# 示例用法
async def main() -> None:
    """测试异步代理"""
    print("🚀 测试异步订单代理")

    # 注意：实际使用时需要真实的API密钥
    api_key: str = "test_key"
    api_secret: str = "test_secret"

    async with LiveBrokerAsync(api_key, api_secret, testnet=True) as broker:
        try:
            # 模拟下单
            order: Dict[str, Any] = await broker.place_order_async(
                symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=0.001, price=30000.0
            )

            print(f"订单结果: {order}")

            # 等待订单处理
            await asyncio.sleep(5)

            # 显示统计
            stats: Dict[str, Union[int, float]] = broker.get_performance_stats()
            print(f"性能统计: {stats}")

        except Exception as e:
            print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
