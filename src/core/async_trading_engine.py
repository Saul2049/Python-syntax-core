#!/usr/bin/env python3
"""
M4阶段异步交易引擎
Async Trading Engine for M4 Phase

用途：
- 集成WebSocket实时行情流
- 异步并发处理：行情+指标+订单
- asyncio.gather并发调度
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.brokers.live_broker_async import LiveBrokerAsync
from src.core.signal_processor_vectorized import OptimizedSignalProcessor
from src.monitoring.metrics_collector import get_metrics_collector
from src.ws.binance_ws_client import BinanceWSClient


class AsyncTradingEngine:
    """异步交易引擎"""

    def __init__(
        self, api_key: str, api_secret: str, symbols: List[str] = ["BTCUSDT"], testnet: bool = True
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.symbols = [s.upper() for s in symbols]
        self.testnet = testnet

        # 核心组件
        self.ws_client: Optional[BinanceWSClient] = None
        self.broker: Optional[LiveBrokerAsync] = None
        self.signal_processor = OptimizedSignalProcessor()

        # 监控指标
        self.metrics = get_metrics_collector()

        # 数据缓存（内存窗口）
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.max_data_points = 200  # 保留最近200个数据点

        # 交易状态
        self.running = False
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.last_signals: Dict[str, Dict[str, Any]] = {}

        # 性能统计
        self.cycle_count = 0
        self.signal_count = 0
        self.order_count = 0

        # 配置参数
        self.fast_win = 7
        self.slow_win = 25
        self.risk_percent = 0.01
        self.account_equity = 10000.0

        # 并发任务管理
        self.concurrent_tasks: Dict[str, asyncio.Task] = {}

        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """初始化异步交易引擎"""
        try:
            self.logger.info("🚀 初始化异步交易引擎")

            # 1. 初始化WebSocket客户端
            self.ws_client = BinanceWSClient(
                symbols=self.symbols, on_kline_callback=self._handle_market_data
            )

            # 2. 初始化异步代理
            self.broker = LiveBrokerAsync(
                api_key=self.api_key, api_secret=self.api_secret, testnet=self.testnet
            )
            await self.broker.init_session()

            # 3. 初始化市场数据缓存
            for symbol in self.symbols:
                self.market_data[symbol] = pd.DataFrame()
                self.last_signals[symbol] = {}

            self.logger.info("✅ 异步交易引擎初始化完成")

        except Exception as e:
            self.logger.error(f"❌ 初始化失败: {e}")
            raise

    async def _handle_market_data(self, kline_data: Dict[str, Any]):
        """处理WebSocket市场数据"""
        try:
            symbol = kline_data["symbol"]

            # 只处理完成的K线
            if not kline_data.get("is_closed", False):
                return

            # 构建DataFrame行
            new_row = pd.DataFrame(
                [
                    {
                        "timestamp": kline_data["timestamp"],
                        "open": kline_data["open"],
                        "high": kline_data["high"],
                        "low": kline_data["low"],
                        "close": kline_data["close"],
                        "volume": kline_data["volume"],
                    }
                ]
            )
            new_row.set_index("timestamp", inplace=True)

            # 更新市场数据缓存
            if symbol in self.market_data:
                self.market_data[symbol] = pd.concat([self.market_data[symbol], new_row])

                # 限制数据点数量
                if len(self.market_data[symbol]) > self.max_data_points:
                    self.market_data[symbol] = self.market_data[symbol].tail(self.max_data_points)
            else:
                self.market_data[symbol] = new_row

            # 记录市场数据指标
            self.metrics.update_concurrent_tasks("market_data", 1)
            self.metrics.record_ws_message(symbol, "kline")

            # 异步触发交易信号处理
            if symbol not in self.concurrent_tasks or self.concurrent_tasks[symbol].done():
                self.concurrent_tasks[symbol] = asyncio.create_task(
                    self._process_trading_signal(symbol)
                )

        except Exception as e:
            self.logger.error(f"❌ 处理市场数据错误: {e}")
            self.metrics.record_exception("async_trading_engine", e)

    async def _process_trading_signal(self, symbol: str):
        """异步处理交易信号"""
        try:
            # 记录并发任务开始
            self.metrics.update_concurrent_tasks("signal_processing", 1)

            # 获取市场数据
            if symbol not in self.market_data or len(self.market_data[symbol]) < max(
                self.fast_win, self.slow_win
            ):
                return

            market_data = self.market_data[symbol].copy()

            # 使用M3优化版信号处理器
            with self.metrics.measure_signal_latency():
                signals = self.signal_processor.get_trading_signals_optimized(
                    market_data, self.fast_win, self.slow_win
                )

            # 计算ATR
            atr = self.signal_processor.compute_atr_optimized(market_data)

            # 缓存信号
            self.last_signals[symbol] = signals
            self.signal_count += 1

            # 异步处理交易逻辑
            await self._execute_trading_logic(symbol, signals, atr)

        except Exception as e:
            self.logger.error(f"❌ 信号处理错误: {e}")
            self.metrics.record_exception("async_trading_engine", e)
        finally:
            # 记录并发任务完成
            self.metrics.update_concurrent_tasks("signal_processing", 0)

    async def _execute_trading_logic(self, symbol: str, signals: Dict[str, Any], atr: float):
        """执行交易逻辑"""
        try:
            current_price = signals["current_price"]

            # 买入信号处理
            if signals["buy_signal"] and symbol not in self.positions:
                await self._execute_buy_order(symbol, current_price, atr)

            # 卖出信号处理
            elif signals["sell_signal"] and symbol in self.positions:
                await self._execute_sell_order(symbol, current_price)

            # 更新持仓监控
            if symbol in self.positions:
                await self._update_position_monitoring(symbol, current_price, atr)

            # 更新统计
            self.cycle_count += 1

            # 打印状态
            signal_type = (
                "BUY" if signals["buy_signal"] else "SELL" if signals["sell_signal"] else "HOLD"
            )
            self.logger.info(
                f"📊 {symbol}: {current_price:.2f} ATR:{atr:.2f} 信号:{signal_type} "
                f"(延迟: {signals.get('latency_ms', 0):.1f}ms)"
            )

        except Exception as e:
            self.logger.error(f"❌ 交易逻辑错误: {e}")
            self.metrics.record_exception("async_trading_engine", e)

    async def _execute_buy_order(self, symbol: str, current_price: float, atr: float):
        """执行买入订单"""
        try:
            # 计算仓位大小
            risk_amount = self.account_equity * self.risk_percent
            stop_price = current_price - (atr * 2.0)  # 2倍ATR止损
            risk_per_unit = current_price - stop_price

            if risk_per_unit <= 0:
                return

            quantity = round(risk_amount / risk_per_unit, 3)

            if quantity <= 0:
                return

            # 异步下单
            order = await self.broker.place_order_async(
                symbol=symbol, side="BUY", order_type="MARKET", quantity=quantity
            )

            # 记录持仓
            self.positions[symbol] = {
                "side": "LONG",
                "quantity": quantity,
                "entry_price": current_price,
                "stop_price": stop_price,
                "entry_time": datetime.now(),
                "order_id": order["order_id"],
            }

            self.order_count += 1
            self.logger.info(f"✅ 买入执行: {symbol} {quantity} @ {current_price:.2f}")

        except Exception as e:
            self.logger.error(f"❌ 买入订单失败: {e}")
            self.metrics.record_exception("async_trading_engine", e)

    async def _execute_sell_order(self, symbol: str, current_price: float):
        """执行卖出订单"""
        try:
            if symbol not in self.positions:
                return

            position = self.positions[symbol]
            quantity = position["quantity"]

            # 异步下单
            await self.broker.place_order_async(
                symbol=symbol, side="SELL", order_type="MARKET", quantity=quantity
            )

            # 计算盈亏
            pnl = (current_price - position["entry_price"]) * quantity

            # 移除持仓
            del self.positions[symbol]

            self.order_count += 1
            self.logger.info(f"✅ 卖出执行: {symbol} {quantity} @ {current_price:.2f} PnL: {pnl:.2f}")

        except Exception as e:
            self.logger.error(f"❌ 卖出订单失败: {e}")
            self.metrics.record_exception("async_trading_engine", e)

    async def _update_position_monitoring(self, symbol: str, current_price: float, atr: float):
        """更新持仓监控"""
        try:
            if symbol not in self.positions:
                return

            position = self.positions[symbol]

            # 检查止损
            if current_price <= position["stop_price"]:
                self.logger.warning(f"⚠️ 触发止损: {symbol} @ {current_price:.2f}")
                await self._execute_sell_order(symbol, current_price)
                return

            # 动态止损（可选）
            # 这里可以添加追踪止损逻辑

        except Exception as e:
            self.logger.error(f"❌ 持仓监控错误: {e}")
            self.metrics.record_exception("async_trading_engine", e)

    async def run(self):
        """运行异步交易引擎"""
        try:
            self.running = True
            self.logger.info("🚀 启动异步交易引擎")

            # 使用asyncio.gather并发运行多个任务
            tasks = [
                # 1. WebSocket行情流
                self.ws_client.run(),
                # 2. 状态监控任务
                self._status_monitoring_loop(),
                # 3. 性能统计任务
                self._performance_monitoring_loop(),
            ]

            # 并发执行所有任务
            await asyncio.gather(*tasks, return_exceptions=True)

        except KeyboardInterrupt:
            self.logger.info("🛑 用户中断")
        except Exception as e:
            self.logger.error(f"❌ 运行错误: {e}")
        finally:
            await self.cleanup()

    async def _status_monitoring_loop(self):
        """状态监控循环 - 优化版本避免gather竞争"""
        while self.running:
            try:
                # 异步任务开始时间
                start_time = time.perf_counter()

                # 更新账户余额等监控指标
                self.metrics.update_account_balance(self.account_equity)
                self.metrics.update_position_count(len(self.positions))

                # 记录处理时间用于监控
                processing_time = time.perf_counter() - start_time
                self.metrics.observe_task_latency("status_monitoring", processing_time)

                # 使用create_task避免阻塞gather
                sleep_task = asyncio.create_task(asyncio.sleep(60))
                await sleep_task

            except asyncio.CancelledError:
                self.logger.info("🛑 状态监控任务被取消")
                break
            except Exception as e:
                self.logger.error(f"❌ 状态监控错误: {e}")
                # 错误时短暂等待后重试
                sleep_task = asyncio.create_task(asyncio.sleep(10))
                await sleep_task

    async def _performance_monitoring_loop(self):
        """性能监控循环 - 优化版本支持批量推送"""
        batch_interval = 30  # 30秒批量推送
        last_push_time = time.time()

        while self.running:
            try:
                current_time = time.time()

                # 收集性能统计
                stats = self.get_performance_stats()

                # 批量推送指标（每30秒一次，减少I/O压力）
                if current_time - last_push_time >= batch_interval:
                    self.logger.info(f"📈 性能统计: {stats}")
                    last_push_time = current_time

                    # 批量更新监控指标
                    self._batch_update_metrics(stats)

                # 使用create_task避免阻塞gather
                sleep_task = asyncio.create_task(asyncio.sleep(30))  # 缩短到30秒
                await sleep_task

            except asyncio.CancelledError:
                self.logger.info("🛑 性能监控任务被取消")
                break
            except Exception as e:
                self.logger.error(f"❌ 性能监控错误: {e}")
                sleep_task = asyncio.create_task(asyncio.sleep(10))
                await sleep_task

    def _batch_update_metrics(self, stats: Dict[str, Any]):
        """批量更新监控指标，减少单次推送压力"""
        try:
            engine_stats = stats.get("engine", {})

            # 批量更新引擎指标
            self.metrics.update_concurrent_tasks(
                "engine_cycles", engine_stats.get("cycle_count", 0)
            )
            self.metrics.update_concurrent_tasks(
                "signal_processing", engine_stats.get("signal_count", 0)
            )

            # 更新WebSocket统计
            ws_stats = stats.get("websocket", {})
            if ws_stats:
                queue_size = ws_stats.get("queue_size", 0)
                if queue_size > 0:
                    self.metrics.update_concurrent_tasks("ws_queue", queue_size)

        except Exception as e:
            self.logger.warning(f"⚠️ 批量指标更新失败: {e}")

    async def cleanup(self):
        """清理资源"""
        try:
            self.running = False
            self.logger.info("🧹 清理资源")

            # 关闭WebSocket
            if self.ws_client:
                await self.ws_client.close()

            # 关闭异步代理
            if self.broker:
                await self.broker.close_session()

            # 取消所有未完成的任务
            for task in self.concurrent_tasks.values():
                if not task.done():
                    task.cancel()

            self.logger.info("✅ 资源清理完成")

        except Exception as e:
            self.logger.error(f"❌ 清理资源错误: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        broker_stats = self.broker.get_performance_stats() if self.broker else {}
        ws_stats = self.ws_client.get_stats() if self.ws_client else {}

        return {
            "engine": {
                "running": self.running,
                "cycle_count": self.cycle_count,
                "signal_count": self.signal_count,
                "order_count": self.order_count,
                "active_positions": len(self.positions),
                "symbols_monitored": len(self.symbols),
            },
            "broker": broker_stats,
            "websocket": ws_stats,
        }


# 工具函数
async def create_async_trading_engine(
    api_key: str, api_secret: str, symbols: List[str] = ["BTCUSDT"], testnet: bool = True
) -> AsyncTradingEngine:
    """创建并初始化异步交易引擎"""
    engine = AsyncTradingEngine(api_key, api_secret, symbols, testnet)
    await engine.initialize()
    return engine


# 示例用法
async def main():
    """测试异步交易引擎"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("🚀 启动M4异步交易引擎测试")

    # 注意：实际使用时需要真实的API密钥
    api_key = "test_key"
    api_secret = "test_secret"

    try:
        # 创建并运行引擎
        engine = await create_async_trading_engine(
            api_key=api_key, api_secret=api_secret, symbols=["BTCUSDT"], testnet=True
        )

        await engine.run()

    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
