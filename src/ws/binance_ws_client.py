#!/usr/bin/env python3
"""
M4阶段 Binance WebSocket 客户端
Binance WebSocket Client for M4 Phase

用途：
- 实时行情流接入 (延迟≤200ms)
- 异步消息处理
- 连接监控和自动重连
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import websockets

from src.monitoring.metrics_collector import get_metrics_collector


class BinanceWSClient:
    """Binance WebSocket客户端"""

    def __init__(self, symbols: List[str], on_kline_callback: Optional[Callable] = None):
        self.symbols = [s.upper() for s in symbols]
        self.on_kline_callback = on_kline_callback
        self.ws = None
        self.running = False
        self.reconnect_count = 0
        self.max_reconnects = 100
        self.reconnect_delay = 1  # 指数退避基数

        # 监控指标
        self.metrics = get_metrics_collector()

        # 性能统计
        self.last_message_time = time.time()
        self.message_count = 0
        self.error_count = 0

        # 消息缓冲队列（防爆内存）
        self.message_queue = asyncio.Queue(maxsize=1000)

        # WebSocket URL
        self.base_url = "wss://stream.binance.com:9443/ws"

        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """建立WebSocket连接"""
        try:
            self.logger.info(f"🔗 连接WebSocket: {self.base_url}")
            self.ws = await websockets.connect(
                self.base_url,
                ping_interval=20,  # 心跳间隔
                ping_timeout=10,  # 心跳超时
                close_timeout=10,  # 关闭超时
            )

            # 订阅K线数据流
            await self._subscribe_streams()

            self.running = True
            self.reconnect_count = 0
            self.reconnect_delay = 1

            # 记录连接成功指标
            self.metrics.record_ws_connection_success()
            self.logger.info("✅ WebSocket连接成功")

        except Exception as e:
            self.logger.error(f"❌ WebSocket连接失败: {e}")
            self.metrics.record_ws_connection_error()
            raise

    async def _subscribe_streams(self):
        """订阅数据流"""
        # 构建订阅消息
        streams = []
        for symbol in self.symbols:
            # 1秒K线流
            streams.append(f"{symbol.lower()}@kline_1s")
            # 24hr ticker流（可选）
            streams.append(f"{symbol.lower()}@ticker")

        subscribe_msg = {"method": "SUBSCRIBE", "params": streams, "id": int(time.time())}

        await self.ws.send(json.dumps(subscribe_msg))
        self.logger.info(f"📡 订阅数据流: {streams}")

    async def listen(self):
        """监听WebSocket消息"""
        try:
            async for message in self.ws:
                # 记录接收时间用于延迟计算
                receive_time = time.perf_counter()

                try:
                    data = json.loads(message)

                    # 更新统计信息
                    self.message_count += 1
                    self.last_message_time = time.time()

                    # 处理K线数据
                    if "k" in data:
                        await self._handle_kline_data(data, receive_time)

                    # 处理Ticker数据
                    elif "c" in data:  # 24hr ticker
                        await self._handle_ticker_data(data, receive_time)

                except json.JSONDecodeError as e:
                    self.logger.warning(f"⚠️ JSON解析错误: {e}")
                    self.error_count += 1
                    continue

                except asyncio.QueueFull:
                    self.logger.warning("⚠️ 消息队列已满，丢弃消息")
                    continue

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("🔌 WebSocket连接断开")
            self.running = False

        except Exception as e:
            self.logger.error(f"❌ WebSocket监听错误: {e}")
            self.error_count += 1
            self.running = False

    async def _handle_kline_data(self, data: Dict[str, Any], receive_time: float):
        """处理K线数据"""
        kline = data["k"]

        # 计算消息延迟
        event_time = data.get("E", 0) / 1000  # 事件时间（秒）
        message_latency = receive_time - event_time

        # 记录WebSocket延迟指标
        self.metrics.observe_ws_latency(message_latency)

        # 构建标准化的K线数据
        kline_data = {
            "symbol": kline["s"],
            "timestamp": pd.to_datetime(kline["t"], unit="ms"),
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
            "is_closed": kline["x"],  # K线是否完成
            "receive_time": receive_time,
            "latency_ms": message_latency * 1000,
        }

        # 调用回调函数
        if self.on_kline_callback:
            try:
                await self.on_kline_callback(kline_data)
            except Exception as e:
                self.logger.error(f"❌ K线回调错误: {e}")
                self.error_count += 1

        # 添加到处理队列
        try:
            await self.message_queue.put(kline_data)
        except asyncio.QueueFull:
            # 队列满时，移除最旧的消息
            try:
                await self.message_queue.get_nowait()
                await self.message_queue.put(kline_data)
            except asyncio.QueueEmpty:
                pass

    async def _handle_ticker_data(self, data: Dict[str, Any], receive_time: float):
        """处理Ticker数据"""
        ticker_data = {
            "symbol": data["s"],
            "price": float(data["c"]),
            "change_24h": float(data["P"]),
            "volume_24h": float(data["v"]),
            "receive_time": receive_time,
        }

        # 记录价格更新
        self.metrics.record_price_update(ticker_data["symbol"], ticker_data["price"])

    async def reconnect(self):
        """重连WebSocket"""
        if self.reconnect_count >= self.max_reconnects:
            self.logger.error(f"❌ 达到最大重连次数 ({self.max_reconnects})")
            return False

        self.reconnect_count += 1

        # 指数退避
        delay = min(self.reconnect_delay * (2**self.reconnect_count), 60)
        self.logger.info(f"🔄 {delay}秒后重连 (尝试 {self.reconnect_count})")

        await asyncio.sleep(delay)

        try:
            # 记录重连指标
            self.metrics.record_ws_reconnect()

            await self.connect()
            return True

        except Exception as e:
            self.logger.error(f"❌ 重连失败: {e}")
            return False

    async def close(self):
        """关闭WebSocket连接"""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.logger.info("🔌 WebSocket连接已关闭")

    async def run(self):
        """运行WebSocket客户端（带自动重连）"""
        while True:
            try:
                if not self.running:
                    await self.connect()

                await self.listen()

            except Exception as e:
                self.logger.error(f"❌ WebSocket运行错误: {e}")

            # 连接断开，尝试重连
            if not await self.reconnect():
                self.logger.error("💥 WebSocket重连失败，停止运行")
                break

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - (self.last_message_time - 60) if self.message_count > 0 else 0
        return {
            "running": self.running,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "reconnect_count": self.reconnect_count,
            "uptime_seconds": uptime,
            "queue_size": self.message_queue.qsize(),
            "last_message_ago": (
                time.time() - self.last_message_time if self.message_count > 0 else None
            ),
        }


# 工具函数
async def create_ws_client(
    symbols: List[str], callback: Optional[Callable] = None
) -> BinanceWSClient:
    """创建并启动WebSocket客户端"""
    client = BinanceWSClient(symbols, callback)
    return client


# 示例用法
async def example_kline_handler(kline_data: Dict[str, Any]):
    """示例K线处理器"""
    print(
        f"📊 {kline_data['symbol']}: {kline_data['close']:.2f} "
        f"(延迟: {kline_data['latency_ms']:.1f}ms)"
    )


async def main():
    """测试主函数"""
    print("🚀 启动Binance WebSocket客户端测试")

    # 创建客户端
    client = await create_ws_client(["BTCUSDT"], example_kline_handler)

    try:
        # 运行客户端
        await client.run()
    except KeyboardInterrupt:
        print("🛑 用户中断")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
