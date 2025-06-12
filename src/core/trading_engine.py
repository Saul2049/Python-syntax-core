"""
核心交易引擎模块 (Core Trading Engine Module)

提供核心交易执行逻辑，包括：
- 交易决策引擎
- 订单执行逻辑
- 风险控制集成
- 状态监控
"""

import os
import time
from datetime import datetime, timedelta
from importlib import import_module
from typing import Any, Dict, Optional

from src.brokers import Broker
from src.core.price_fetcher import calculate_atr, fetch_price_data
from src.core.signal_processor_vectorized import OptimizedSignalProcessor

# 延迟导入模块对象 (而非函数引用)
_metrics_mod = import_module("src.monitoring.metrics_collector")


class TradingEngine:
    """核心交易引擎类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        telegram_token: Optional[str] = None,
    ) -> None:
        """
        初始化交易引擎

        Args:
            api_key: API密钥 (API key)
            api_secret: API密钥 (API secret)
            telegram_token: Telegram通知令牌 (Telegram notification token)
        """
        # 启用M3优化版信号处理器
        self.signal_processor: OptimizedSignalProcessor = OptimizedSignalProcessor()

        # ------------------------------------------------------------------
        # 监控指标
        # ------------------------------------------------------------------
        # 必须在运行时动态获取，以支持如下单元测试补丁：
        #   patch('src.monitoring.metrics_collector.get_metrics_collector', ...)
        # 如果直接在模块顶部 `from ... import get_metrics_collector`，
        # TradingEngine 在 import 时就绑定了函数对象，后续 patch 不会生效。

        self.metrics = _metrics_mod.get_metrics_collector()

        # 状态管理
        self.last_signal_time: Optional[datetime] = None  # 最后信号时间
        self.signal_count: int = 0  # 信号计数
        self.error_count: int = 0  # 错误计数
        self.last_status_update: datetime = datetime.now() - timedelta(hours=1)  # 最后状态更新时间
        self._last_position_state: bool = False

        # ------------------------------------------------------------------
        # Broker – 动态获取，确保单元测试对 ``src.brokers.Broker`` 的 patch
        # 可以正确注入自定义 Mock。
        # ------------------------------------------------------------------

        _brokers_mod = import_module("src.brokers")

        self.broker: Broker = _brokers_mod.Broker(
            api_key=api_key or os.getenv("API_KEY") or "",
            api_secret=api_secret or os.getenv("API_SECRET") or "",
            telegram_token=telegram_token or os.getenv("TG_TOKEN"),
        )

        # 配置参数
        self.account_equity: float = float(os.getenv("ACCOUNT_EQUITY", "10000.0"))  # 账户权益
        self.risk_percent: float = float(os.getenv("RISK_PERCENT", "0.01"))  # 风险百分比
        self.atr_multiplier: float = float(os.getenv("ATR_MULTIPLIER", "2.0"))  # ATR倍数

        # 状态变量
        self.peak_balance: float = self.account_equity  # 用于回撤计算

    def analyze_market_conditions(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        分析市场条件

        Args:
            symbol: 交易对符号 (Trading pair symbol)

        Returns:
            市场分析结果字典 (Market analysis result dictionary)
        """
        try:
            # 获取市场数据
            data = fetch_price_data(symbol)
            if data is None or data.empty:
                return self._create_error_result("无法获取市场数据")

            # 计算基础指标
            atr_value = calculate_atr(data)
            raw_signals = self.signal_processor.get_trading_signals_optimized(data)
            close_prices = data["close"]

            # 转换信号格式以适配旧的接口
            signals = self._convert_signal_format(raw_signals)

            # 分析各个组件
            trend_analysis = self._analyze_trend(close_prices)
            volatility_analysis = self._analyze_volatility(close_prices)
            recommendation = self._generate_recommendation(signals)

            # 构建结果
            result = {
                "atr": round(atr_value, 6),
                "volatility": volatility_analysis["level"],
                "volatility_percent": volatility_analysis["percent"],
                "trend": trend_analysis["direction"],
                "signal_strength": round(signals.get("confidence", 0.5), 2),
                "recommendation": recommendation,
                "signals": signals,
                "short_ma": round(trend_analysis["short_ma"], 2),
                "long_ma": round(trend_analysis["long_ma"], 2),
                "current_price": round(close_prices.iloc[-1], 2),
            }

            # 记录分析结果
            self.metrics.record_price_update(symbol, close_prices.iloc[-1])
            return result

        except Exception as e:
            self.error_count += 1
            self.metrics.record_exception("trading_engine", e)
            return self._create_error_result(f"市场分析失败: {e}")

    def _convert_signal_format(self, raw_signals: Dict[str, Any]) -> Dict[str, Any]:
        """转换新的信号格式到旧的格式"""
        # 首先检查是否已经有置信度，如果有就保留
        if "confidence" in raw_signals:
            confidence = raw_signals["confidence"]
        else:
            # 从新的格式 (buy_signal, sell_signal) 转换到旧的格式 (signal, confidence)
            if raw_signals.get("buy_signal", False):
                confidence = 0.8  # 默认置信度
            elif raw_signals.get("sell_signal", False):
                confidence = 0.8  # 默认置信度
            else:
                confidence = 0.5  # 默认置信度

        # 确定信号类型
        if "signal" in raw_signals:
            signal = raw_signals["signal"]
        elif raw_signals.get("buy_signal", False):
            signal = "BUY"
        elif raw_signals.get("sell_signal", False):
            signal = "SELL"
        else:
            signal = "HOLD"

        return {
            "signal": signal,
            "confidence": confidence,
            "buy_signal": raw_signals.get("buy_signal", False),
            "sell_signal": raw_signals.get("sell_signal", False),
            "current_price": raw_signals.get("current_price", 0),
            "fast_ma": raw_signals.get("fast_ma", 0),
            "slow_ma": raw_signals.get("slow_ma", 0),
        }

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """创建错误结果字典"""
        return {
            "error": error_message,
            "atr": 0,
            "volatility": "unknown",
            "trend": "unknown",
            "signal_strength": 0,
            "recommendation": "hold",
        }

    def _analyze_trend(self, close_prices) -> Dict[str, Any]:
        """分析趋势"""
        short_ma = close_prices.rolling(window=20).mean().iloc[-1]
        long_ma = close_prices.rolling(window=50).mean().iloc[-1]

        if short_ma > long_ma:
            direction = "bullish"
        elif short_ma < long_ma:
            direction = "bearish"
        else:
            direction = "neutral"

        return {"direction": direction, "short_ma": short_ma, "long_ma": long_ma}

    def _analyze_volatility(self, close_prices) -> Dict[str, Any]:
        """分析波动率"""
        returns = close_prices.pct_change().dropna()
        volatility = returns.std() * 100

        if volatility > 3:
            level = "high"
        elif volatility > 1.5:
            level = "medium"
        else:
            level = "low"

        return {"level": level, "percent": round(volatility, 2)}

    def _generate_recommendation(self, signals: Dict[str, Any]) -> str:
        """生成交易推荐"""
        signal_strength = signals.get("confidence", 0.5)
        main_signal = signals.get("signal", "HOLD")

        if main_signal == "BUY" and signal_strength > 0.7:
            return "strong_buy"
        elif main_signal == "BUY" and signal_strength > 0.5:
            return "buy"
        elif main_signal == "SELL" and signal_strength > 0.7:
            return "strong_sell"
        elif main_signal == "SELL" and signal_strength > 0.5:
            return "sell"
        else:
            return "hold"

    def execute_trade_decision(
        self, symbol: str = "BTCUSDT", force_trade: bool = False
    ) -> Dict[str, Any]:
        """
        执行交易决策

        Args:
            symbol: 交易对符号 (Trading pair symbol)
            force_trade: 是否强制交易 (Whether to force trade)

        Returns:
            交易执行结果字典 (Trade execution result dictionary)
        """
        try:
            # 1. 分析市场条件
            market_analysis = self.analyze_market_conditions(symbol)
            if "error" in market_analysis:
                return self._create_error_response(
                    "none", market_analysis["error"], market_analysis
                )

            # 2. 验证交易条件
            validation_result = self._validate_trading_conditions(market_analysis, force_trade)
            if validation_result:
                return validation_result

            # 3. 执行交易逻辑
            return self._execute_trading_logic(symbol, market_analysis)

        except Exception as e:
            self.error_count += 1
            self.metrics.record_exception("trading_engine", e)
            return self._create_error_response("error", f"交易执行失败: {e}")

    def _validate_trading_conditions(
        self, market_analysis: Dict[str, Any], force_trade: bool
    ) -> Optional[Dict[str, Any]]:
        """验证交易条件"""
        signal_strength = market_analysis["signal_strength"]
        # 风险管理检查
        if not force_trade and signal_strength < 0.6:
            return {
                "action": "hold",
                "success": True,
                "message": f"信号强度过低 ({signal_strength:.2f}), 保持持仓",
                "market_analysis": market_analysis,
            }

        # 检查账户余额
        account_info = self.broker.get_account_balance()
        available_balance = account_info.get("balance", 0)

        if available_balance < 100:
            return self._create_error_response(
                "none", f"余额不足 ({available_balance}), 无法交易", market_analysis
            )

        return None

    def _execute_trading_logic(
        self, symbol: str, market_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行交易逻辑"""
        recommendation = market_analysis["recommendation"]
        current_price = market_analysis["current_price"]
        # 计算仓位大小
        position_size = self._calculate_position_size_internal(market_analysis)

        # 执行具体交易
        if recommendation in ["strong_buy", "buy"]:
            return self._execute_buy_trade(symbol, position_size, current_price, market_analysis)
        elif recommendation in ["strong_sell", "sell"]:
            return self._execute_sell_trade(symbol, position_size, current_price, market_analysis)
        else:
            return self._create_hold_response(market_analysis, position_size)

    def _calculate_position_size_internal(self, market_analysis: Dict[str, Any]) -> float:
        """计算仓位大小"""
        account_info = self.broker.get_account_balance()
        available_balance = account_info.get("balance", 0)
        atr_value = market_analysis["atr"]
        current_price = market_analysis["current_price"]
        if atr_value > 0:
            risk_amount = available_balance * self.risk_percent
            stop_distance = atr_value * self.atr_multiplier
            position_size = risk_amount / stop_distance

            # 限制最大仓位
            max_position_value = available_balance * 0.1
            max_quantity = max_position_value / current_price
            position_size = min(position_size, max_quantity)
        else:
            position_size = available_balance * 0.02 / current_price

        # 最小交易量检查
        min_quantity = 0.001
        return max(position_size, min_quantity)

    def _execute_buy_trade(
        self,
        symbol: str,
        position_size: float,
        current_price: float,
        market_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行买入交易"""
        order_result = self.broker.place_order(
            symbol=symbol, side="BUY", order_type="MARKET", quantity=position_size
        )

        self._update_trade_statistics(symbol, current_price)

        return {
            "action": "buy",
            "success": True,
            "message": f"执行买入订单: {position_size:.6f} {symbol}",
            "order_info": order_result,
            "market_analysis": market_analysis,
            "position_size": round(position_size, 6),
            "signal_strength": market_analysis["signal_strength"],
        }

    def _execute_sell_trade(
        self,
        symbol: str,
        position_size: float,
        current_price: float,
        market_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行卖出交易"""
        positions = self.broker.get_positions()
        btc_position = positions.get("BTC", 0)
        min_quantity = 0.001
        if btc_position > min_quantity:
            sell_quantity = min(position_size, btc_position)
            order_result = self.broker.place_order(
                symbol=symbol, side="SELL", order_type="MARKET", quantity=sell_quantity
            )

            self._update_trade_statistics(symbol, current_price)

            return {
                "action": "sell",
                "success": True,
                "message": f"执行卖出订单: {sell_quantity:.6f} {symbol}",
                "order_info": order_result,
                "market_analysis": market_analysis,
                "position_size": round(sell_quantity, 6),
                "signal_strength": market_analysis["signal_strength"],
            }
        else:
            return self._create_hold_response(
                market_analysis, position_size, "无可卖持仓，保持观望"
            )

    def _create_hold_response(
        self,
        market_analysis: Dict[str, Any],
        position_size: float,
        message: str = "市场条件不明确，保持观望",
    ) -> Dict[str, Any]:
        """创建保持观望响应"""
        return {
            "action": "hold",
            "success": True,
            "message": message,
            "order_info": None,
            "market_analysis": market_analysis,
            "position_size": round(position_size, 6),
            "signal_strength": market_analysis["signal_strength"],
        }

    def _create_error_response(
        self, action: str, message: str, market_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建错误响应"""
        response = {"action": action, "success": False, "message": message}
        if market_analysis:
            response["market_analysis"] = market_analysis
        return response

    def _update_trade_statistics(self, symbol: str, current_price: float) -> None:
        """更新交易统计"""
        self.signal_count += 1
        self.last_signal_time = datetime.now()
        self.metrics.record_price_update(symbol, current_price)

    def get_engine_status(self) -> Dict[str, Any]:
        """
        获取引擎状态

        Returns:
            引擎状态字典 (Engine status dictionary)
            - status: 引擎状态
            - signal_count: 信号计数
            - error_count: 错误计数
            - last_signal_time: 最后信号时间
            - account_equity: 账户权益
            - uptime: 运行时间
        """
        current_time: datetime = datetime.now()

        # 计算运行时间
        if hasattr(self, "_start_time"):
            uptime_seconds: float = (current_time - self._start_time).total_seconds()
            uptime_hours: float = uptime_seconds / 3600
        else:
            uptime_hours = 0

        # 获取账户信息
        try:
            account_info: Dict[str, Any] = self.broker.get_account_balance()
            current_balance: float = account_info.get("balance", self.account_equity)
        except Exception:
            current_balance = self.account_equity

        # 计算回撤
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance

        drawdown_percent: float = 0
        if self.peak_balance > 0:
            drawdown_percent = (self.peak_balance - current_balance) / self.peak_balance * 100

        # 确定引擎状态
        if self.error_count > 10:
            status: str = "error"
        elif drawdown_percent > 20:
            status = "high_risk"
        elif self.signal_count > 0:
            status = "active"
        else:
            status = "standby"

        return {
            "status": status,
            "signal_count": self.signal_count,
            "error_count": self.error_count,
            "last_signal_time": (
                self.last_signal_time.isoformat() if self.last_signal_time else None
            ),
            "account_equity": round(current_balance, 2),
            "peak_balance": round(self.peak_balance, 2),
            "drawdown_percent": round(drawdown_percent, 2),
            "uptime_hours": round(uptime_hours, 2),
            "risk_percent": self.risk_percent * 100,
            "atr_multiplier": self.atr_multiplier,
            "timestamp": current_time.isoformat(),
        }

    def start_engine(self) -> Dict[str, Any]:
        """
        启动交易引擎

        Returns:
            启动结果字典 (Startup result dictionary)
        """
        try:
            self._start_time: datetime = datetime.now()

            # 初始化监控
            self.metrics.start_server()

            # 测试broker连接
            account_info: Dict[str, Any] = self.broker.get_account_balance()

            # 重置计数器
            self.signal_count = 0
            self.error_count = 0
            self.last_signal_time = None

            return {
                "success": True,
                "message": "交易引擎启动成功",
                "start_time": self._start_time.isoformat(),
                "account_balance": account_info.get("balance", 0),
            }

        except Exception as e:
            self.error_count += 1
            return {"success": False, "message": f"交易引擎启动失败: {e}", "error": str(e)}

    def stop_engine(self) -> Dict[str, Any]:
        """
        停止交易引擎

        Returns:
            停止结果字典 (Stop result dictionary)
        """
        try:
            end_time: datetime = datetime.now()

            # 计算运行统计
            if hasattr(self, "_start_time"):
                total_runtime: float = (end_time - self._start_time).total_seconds()
            else:
                total_runtime = 0

            # 获取最终账户状态
            final_account: Dict[str, Any] = self.broker.get_account_balance()

            return {
                "success": True,
                "message": "交易引擎停止成功",
                "stop_time": end_time.isoformat(),
                "total_runtime_hours": round(total_runtime / 3600, 2),
                "total_signals": self.signal_count,
                "total_errors": self.error_count,
                "final_balance": final_account.get("balance", 0),
            }

        except Exception as e:
            return {"success": False, "message": f"交易引擎停止失败: {e}", "error": str(e)}

    def calculate_position_size(self, current_price: float, atr: float, symbol: str) -> float:
        """
        计算仓位大小

        参数:
            current_price: 当前价格
            atr: ATR值
            symbol: 交易对

        返回:
            float: 仓位大小
        """
        risk_amount = self.account_equity * self.risk_percent
        stop_price = current_price - (atr * self.atr_multiplier)
        risk_per_unit = current_price - stop_price

        if risk_per_unit <= 0:
            return 0.0

        quantity = risk_amount / risk_per_unit

        # 限制数量小数位 (根据交易对精度要求调整)
        return round(quantity, 3)

    def process_buy_signal(self, symbol: str, signals: dict, atr: float) -> bool:
        """
        处理买入信号

        参数:
            symbol: 交易对
            signals: 信号字典
            atr: ATR值

        返回:
            bool: 是否执行了买入
        """
        if not signals["buy_signal"] or symbol in self.broker.positions:
            return False

        current_price = signals["current_price"]
        quantity = self.calculate_position_size(current_price, atr, symbol)

        if quantity <= 0:
            return False

        # 执行买入订单
        reason = f"MA交叉: 快线 {signals['fast_ma']:.2f} " f"上穿 慢线 {signals['slow_ma']:.2f}"

        try:
            start_time = time.perf_counter()
            self.broker.execute_order(
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                reason=reason,
            )
            # 手动记录延迟，避免依赖 contextmanager 的 __exit__ 返回值
            elapsed = round(time.perf_counter() - start_time, 10)
            if hasattr(self.metrics, "observe_task_latency"):
                self.metrics.observe_task_latency("order_execution", elapsed)
            return True
        except Exception as e:
            self.metrics.record_exception("trading_engine", e)
            self.broker.notifier.notify_error(e, f"买入订单执行失败: {symbol}")
            return False

    def process_sell_signal(self, symbol: str, signals: dict) -> bool:
        """
        处理卖出信号

        参数:
            symbol: 交易对
            signals: 信号字典

        返回:
            bool: 是否执行了卖出
        """
        if not signals["sell_signal"] or symbol not in self.broker.positions:
            return False

        position = self.broker.positions[symbol]
        reason = f"MA交叉: 快线 {signals['fast_ma']:.2f} " f"下穿 慢线 {signals['slow_ma']:.2f}"

        try:
            start_time = time.perf_counter()
            self.broker.execute_order(
                symbol=symbol,
                side="SELL",
                quantity=position["quantity"],
                reason=reason,
            )
            elapsed = round(time.perf_counter() - start_time, 10)
            if hasattr(self.metrics, "observe_task_latency"):
                self.metrics.observe_task_latency("order_execution", elapsed)
            return True
        except Exception as e:
            self.metrics.record_exception("trading_engine", e)
            self.broker.notifier.notify_error(e, f"卖出订单执行失败: {symbol}")
            return False

    def update_positions(self, symbol: str, current_price: float, atr: float) -> None:
        """
        更新仓位状态

        参数:
            symbol: 交易对
            current_price: 当前价格
            atr: ATR值
        """
        # 更新持仓止损价
        self.broker.update_position_stops(symbol, current_price, atr)

        # 检查止损
        self.broker.check_stop_loss(symbol, current_price)

    def send_status_update(self, symbol: str, signals: dict, atr: float) -> None:
        """
        发送状态更新通知

        参数:
            symbol: 交易对
            signals: 信号字典
            atr: ATR值
        """
        current_time = datetime.now()

        # 每小时发送状态通知；但若持仓状态发生变化，则立即推送一次
        has_position_now = symbol in self.broker.positions

        within_cooldown = (current_time - self.last_status_update).total_seconds() < 3600

        if within_cooldown and has_position_now == self._last_position_state:
            return

        current_price = signals["current_price"]
        status_msg = (
            f"📈 状态更新 (Status Update)\n"
            f"品种 (Symbol): {symbol}\n"
            f"价格 (Price): {current_price:.8f}\n"
            f"ATR: {atr:.8f}\n"
            f"快线 (Fast MA): {signals['fast_ma']:.8f}\n"
            f"慢线 (Slow MA): {signals['slow_ma']:.8f}\n"
            f"头寸 (Position): {'有' if symbol in self.broker.positions else '无'}"
        )

        if symbol in self.broker.positions:
            position = self.broker.positions[symbol]
            status_msg += f"\n入场价 (Entry): {position['entry_price']:.8f}"
            status_msg += f"\n止损价 (Stop): {position['stop_price']:.8f}"
            status_msg += f"\n数量 (Quantity): {position['quantity']:.8f}"

            pnl = (current_price - position["entry_price"]) * position["quantity"]
            pnl_percent = (
                (current_price - position["entry_price"]) / position["entry_price"]
            ) * 100

            status_msg += f"\n盈亏 (P/L): {pnl:.8f} USDT"
            status_msg += f"\n盈亏% (P/L%): {pnl_percent:.2f}%"

        self.broker.notifier.notify(status_msg, "INFO")
        self.last_status_update = current_time
        self._last_position_state = has_position_now

    def execute_trading_cycle(self, symbol: str, fast_win: int = 7, slow_win: int = 25) -> bool:
        """
        执行一个完整的交易周期

        参数:
            symbol: 交易对
            fast_win: 快速移动平均窗口
            slow_win: 慢速移动平均窗口

        返回:
            bool: 执行是否成功
        """
        try:
            start_time = time.time()

            # ------------------------------------------------------------------
            # 动态导入 price_fetcher / signal_processor — 允许单元测试 patch
            # ------------------------------------------------------------------

            _pf_mod = import_module("src.core.price_fetcher")
            _sig_mod = import_module("src.core.signal_processor")

            # 1. 获取价格数据（带监控）
            with self.metrics.measure_data_fetch_latency():
                price_data = _pf_mod.fetch_price_data(symbol)

            if price_data is None or price_data.empty:
                self.metrics.record_exception("trading_engine", Exception("空价格数据"))
                return False

            # 2. 使用M3优化版信号处理器计算交易信号
            with self.metrics.measure_signal_latency():
                signals = self.signal_processor.get_trading_signals_optimized(
                    price_data, fast_win, slow_win
                )

            # 3. 验证信号
            if not _sig_mod.validate_signal(signals, price_data):
                self.metrics.record_exception("trading_engine", Exception("信号验证失败"))
                return False

            # 4. 计算ATR（使用优化版本）
            atr = self.signal_processor.compute_atr_optimized(price_data)

            # 4.5 如果止损已触发，则跳过新的买卖信号处理
            stop_triggered = self.broker.check_stop_loss(symbol, signals["current_price"])

            # 仅在显式返回 True 时才认定触发止损，避免 Mock 对象意外被视为真值
            if stop_triggered is True:
                # 更新监控 / 状态，然后提前返回（不执行买卖逻辑）
                self.update_positions(symbol, signals["current_price"], atr)
                self.send_status_update(symbol, signals, atr)
                self._update_monitoring_metrics(symbol, signals["current_price"])
                return True

            # 5. 记录监控指标
            end_time = time.time()
            total_latency = end_time - start_time
            self.metrics.observe_task_latency("trading_cycle", total_latency)

            # 6. 处理交易信号
            buy_executed = self.process_buy_signal(symbol, signals, atr)
            sell_executed = self.process_sell_signal(symbol, signals)

            # 7. 更新持仓
            self.update_positions(symbol, signals["current_price"], atr)

            # 8. 发送状态更新
            self.send_status_update(symbol, signals, atr)

            # 9. 更新监控指标
            self._update_monitoring_metrics(symbol, signals["current_price"])

            # 10. 打印执行结果
            status = "BUY" if buy_executed else "SELL" if sell_executed else "HOLD"
            print(
                f"[{datetime.now()}] 价格: {signals['current_price']:.2f}, "
                f"ATR: {atr:.2f}, 信号: {status}"
            )

            return True

        except Exception as e:
            self.metrics.record_exception("trading_engine", e)
            try:
                self.broker.notifier.notify_error(e, "交易周期执行错误")
            except Exception:
                pass  # Notifier may be a Mock or missing during tests
            print(f"交易周期执行错误: {e}")
            return False

    def _update_monitoring_metrics(self, symbol: str, current_price: float):
        """更新监控指标"""
        try:
            # 价格更新
            self.metrics.record_price_update(symbol, current_price)

            # 更新账户余额
            self.metrics.update_account_balance(self.account_equity)

            # 更新回撤
            if self.account_equity > self.peak_balance:
                self.peak_balance = self.account_equity
            self.metrics.update_drawdown(self.account_equity, self.peak_balance)

            # 更新持仓数量
            position_count = len(self.broker.positions)
            self.metrics.update_position_count(position_count)

        except Exception as e:
            print(f"更新监控指标失败: {e}")

    def start_trading_loop(
        self,
        symbol: str = "BTCUSDT",
        interval_seconds: int = 60,
        fast_win: int = 7,
        slow_win: int = 25,
    ) -> None:
        """
        启动交易循环

        参数:
            symbol: 交易对
            interval_seconds: 循环间隔（秒）
            fast_win: 快线窗口
            slow_win: 慢线窗口
        """
        print(f"启动交易循环，交易对: {symbol}, 循环间隔: {interval_seconds}秒")

        try:
            # 发送启动通知
            self.broker.notifier.notify(
                f"🚀 交易机器人启动 (Trading bot started)\n交易对: {symbol}",
                "INFO",
            )

            while True:
                success = self.execute_trading_cycle(symbol, fast_win, slow_win)

                if not success:
                    print("交易周期执行失败，继续下一个周期")

                # 等待下一次循环
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            # 发送关闭通知
            self.broker.notifier.notify("🛑 交易机器人关闭 (Trading bot stopped)", "INFO")
            print("交易循环已关闭")


# 向后兼容函数
def trading_loop(symbol: str = "BTCUSDT", interval_seconds: int = 60):
    """
    交易循环 - 向后兼容函数
    Trading loop - backward compatibility function
    """
    engine = TradingEngine()
    engine.start_trading_loop(symbol, interval_seconds)


# ---------------------------------------------------------------------------
# Legacy free-function expected by archived tests (provides graceful fallback)
# ---------------------------------------------------------------------------


def get_trading_signals(data, fast_win: int = 7, slow_win: int = 25):  # type: ignore
    """Compatibility shim delegating to *OptimizedSignalProcessor*.

    The comprehensive *old_tests* suite patches this symbol; it therefore only
    needs to exist.  A minimal but functional implementation is provided so that
    real invocations keep working.
    """

    processor = OptimizedSignalProcessor()
    return processor.get_trading_signals_optimized(data, fast_win, slow_win)
