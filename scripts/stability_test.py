#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳定性测试脚本 - 运行交易系统并监控性能和错误
Stability Test Script - Run trading system and monitor performance and errors
"""

import argparse
import datetime
import logging
import os
import random
import signal
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# 确保将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# 导入配置管理器
try:
    # 尝试导入增强配置管理器
    from scripts.enhanced_config import get_config, setup_logging
    logger.info("使用增强配置管理器")
except ImportError:
    logger.info("无法导入增强配置管理器，尝试导入旧版配置管理器")
    try:
        # 如果无法导入增强版，则尝试导入旧版
        from scripts.config_manager import get_config
        logger.info("使用旧版配置管理器")
        setup_logging = None
    except ImportError:
        # 如果都无法导入，使用默认值
        logger.warning("无法导入配置管理器，将使用默认值")
        get_config = None
        setup_logging = None

# 设置日志
logging_config = get_config().get_log_level() if get_config() else "INFO"
logging.basicConfig(
    level=getattr(logging, logging_config),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("stability_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger("stability_test")

# 导入市场数据管理器
from scripts.market_data import create_market_data_manager, MarketDataManager

# 导入监控模块
try:
    from scripts.monitoring import get_exporter
    logger.info("已导入监控模块")
    MONITORING_ENABLED = True
except ImportError:
    logger.warning("无法导入监控模块，监控功能将被禁用")
    get_exporter = None
    MONITORING_ENABLED = False


# 定义模拟类
class MockMarketSimulator:
    """模拟市场类，用于测试"""

    def __init__(self, symbols, initial_balance, fee_rate, market_data_manager=None):
        self.symbols = symbols
        self.balance = initial_balance
        self.fee_rate = fee_rate
        # 使用市场数据管理器
        self.market_data = market_data_manager
        logger.info(f"创建模拟市场：{symbols}, 初始余额：{initial_balance}")
        
        # 记录当前使用的数据源
        if self.market_data:
            logger.info(f"使用数据源: {self.market_data.get_current_provider_name()}")
        
    def get_current_price(self, symbol):
        """获取当前价格"""
        if self.market_data:
            # 使用市场数据管理器获取价格
            ticker = self.market_data.get_ticker(symbol)
            if ticker and "price" in ticker:
                return float(ticker["price"])
        
        # 如果没有数据管理器或获取失败，使用随机价格
        return 30000 + random.random() * 1000
        
    def get_recent_klines(self, symbol, interval="1h", limit=24):
        """获取最近K线数据"""
        if self.market_data:
            # 使用市场数据管理器获取K线
            klines = self.market_data.get_klines(symbol, interval, limit)
            if klines:
                return klines
        
        # 如果获取失败，生成模拟数据
        return self._generate_mock_klines(symbol, limit)
    
    def _generate_mock_klines(self, symbol, limit):
        """生成模拟K线数据"""
        now = time.time() * 1000
        base_price = 30000 + random.random() * 1000
        klines = []
        
        for i in range(limit):
            timestamp = now - (limit - i) * 3600 * 1000  # 假设1小时间隔
            price = base_price * (1 + (random.random() - 0.5) * 0.01 * (i + 1))
            
            kline = [
                int(timestamp),  # 开盘时间
                str(price * 0.99),  # 开盘价
                str(price * 1.01),  # 最高价
                str(price * 0.98),  # 最低价
                str(price),  # 收盘价
                str(random.random() * 100),  # 成交量
                int(timestamp) + 3600 * 1000 - 1,  # 收盘时间
                str(random.random() * 100 * price),  # 成交额
                100,  # 成交笔数
                str(random.random() * 60),  # 主动买入成交量
                str(random.random() * 60 * price),  # 主动买入成交额
                "0"  # 忽略
            ]
            klines.append(kline)
            
        return klines


class MockTradingLoop:
    """模拟交易循环类，用于测试"""

    def __init__(self, market, symbols, risk_percent, fast_ma, slow_ma, atr_period, test_mode):
        self.market = market
        self.symbols = symbols
        self.risk = risk_percent
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.atr_period = atr_period
        self.test_mode = test_mode
        logger.info(f"创建模拟交易循环：风险={risk_percent}, 快线={fast_ma}, 慢线={slow_ma}")

    def check_and_execute(self):
        """模拟检查并执行交易信号"""
        # 随机生成信号
        if random.random() < 0.1:  # 10%概率产生信号
            symbol = self.symbols[random.randint(0, len(self.symbols) - 1)]
            
            # 使用市场对象获取当前价格
            price = self.market.get_current_price(symbol)
            
            signal = {
                "symbol": symbol,
                "action": "BUY" if random.random() > 0.5 else "SELL",
                "price": price,
            }
            logger.info(f"模拟信号: {signal}")
            return [signal]
        return []


# 设置全局模拟对象
MarketSimulator = MockMarketSimulator
TradingLoop = MockTradingLoop


class StabilityTest:
    """长期稳定性测试类"""

    def __init__(
        self,
        symbols=None,
        duration_days=None,
        check_interval=None,
        test_mode=None,
        log_dir=None,
        risk_percent=None,
        use_binance_testnet=None,
        monitoring_port=9090,
        preserve_logs=True,  # 新增参数，控制是否保留完整日志
    ):
        """
        初始化稳定性测试

        参数:
            symbols: 要测试的交易对列表
            duration_days: 测试持续天数
            check_interval: 检查间隔(秒)
            test_mode: 是否为测试模式(不执行实际交易)
            log_dir: 日志目录
            risk_percent: 风险百分比(测试时降低风险)
            use_binance_testnet: 是否使用币安测试网数据
            monitoring_port: Prometheus指标导出端口
            preserve_logs: 是否保留完整日志历史
        """
        # 获取配置管理器
        self.config = get_config()
        
        # 使用参数或配置值
        self.symbols = symbols or self.config.get_symbols()
        self.duration_seconds = (duration_days or 3) * 24 * 60 * 60
        self.check_interval = check_interval or self.config.get_check_interval()
        self.test_mode = test_mode if test_mode is not None else self.config.is_test_mode()
        self.risk_percent = risk_percent or self.config.get_risk_percent()
        self.use_binance_testnet = use_binance_testnet if use_binance_testnet is not None else self.config.use_binance_testnet()
        self.preserve_logs = preserve_logs  # 保存是否保留日志的设置

        # 创建日志目录
        self.log_dir = Path(log_dir or self.config.get_log_dir())
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志轮转
        self._setup_log_rotation()

        # 设置停止标志
        self.stop_requested = False

        # 统计数据
        self.stats = {
            "start_time": None,
            "total_signals": 0,
            "errors": 0,
            "data_interruptions": 0,
            "reconnections": 0,
            "memory_usage": [],
            "data_source_switches": 0,
        }

        # 初始化监控
        self.init_monitoring(monitoring_port)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        logger.info(f"初始化稳定性测试: {self.symbols}, 持续{duration_days or 3}天, 保留日志: {self.preserve_logs}")
        
        # 创建市场数据管理器
        self.market_data_manager = create_market_data_manager(use_binance_testnet=self.use_binance_testnet)

    def _setup_log_rotation(self):
        """设置日志轮转"""
        try:
            import logging.handlers
            
            # 为每个交易对创建单独的日志文件
            for symbol in self.symbols:
                symbol_safe = symbol.replace('/', '_')
                log_file = self.log_dir / f"{symbol_safe}.log"
                
                # 创建轮转日志处理器
                handler = logging.handlers.RotatingFileHandler(
                    log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5 if not self.preserve_logs else 100  # 如果保留日志，保存更多备份
                )
                
                # 设置格式
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                
                # 创建专用日志记录器
                symbol_logger = logging.getLogger(f"trading.{symbol_safe}")
                symbol_logger.addHandler(handler)
                symbol_logger.setLevel(logging.INFO)
                
            # 为系统指标创建单独的日志文件
            metrics_log = self.log_dir / "system_metrics.log"
            metrics_handler = logging.handlers.RotatingFileHandler(
                metrics_log,
                maxBytes=50*1024*1024,  # 50MB
                backupCount=10 if not self.preserve_logs else 200  # 保留更多历史数据用于分析
            )
            metrics_handler.setFormatter(formatter)
            metrics_logger = logging.getLogger("system.metrics")
            metrics_logger.addHandler(metrics_handler)
            metrics_logger.setLevel(logging.INFO)
            
            logger.info(f"日志轮转设置完成，日志目录: {self.log_dir}")
        except Exception as e:
            logger.error(f"设置日志轮转时出错: {e}")

    def init_monitoring(self, port=9090):
        """初始化监控系统"""
        if MONITORING_ENABLED and get_exporter:
            try:
                self.exporter = get_exporter(port=port)
                self.exporter.start()
                logger.info(f"监控系统已启动，端口：{port}")
                
                # 设置初始指标
                for symbol in self.symbols:
                    # 初始化交易对价格为0
                    self.exporter.update_price(symbol, 0)
                
                # 更新心跳
                self.exporter.update_heartbeat()
            except Exception as e:
                logger.error(f"初始化监控系统失败: {e}")
                self.exporter = None
        else:
            self.exporter = None
            logger.warning("监控系统未启用")

    def signal_handler(self, sig, frame):
        """处理终止信号"""
        logger.info("收到终止信号，准备清理...")
        self.stop_requested = True

    def setup_trading_system(self):
        """设置交易系统组件"""
        try:
            # 创建模拟市场对象，传入市场数据管理器
            logger.info("使用市场模拟器进行测试")
            self.market = MarketSimulator(
                symbols=self.symbols, 
                initial_balance=10000.0, 
                fee_rate=0.001,
                market_data_manager=self.market_data_manager
            )

            # 创建交易循环
            self.trading_loop = TradingLoop(
                market=self.market,
                symbols=self.symbols,
                risk_percent=self.risk_percent,
                fast_ma=7,
                slow_ma=25,
                atr_period=14,
                test_mode=self.test_mode,
            )

            logger.info("交易系统组件设置完成")
            return True
        except Exception as e:
            logger.error(f"设置交易系统时出错: {e}")
            return False

    def monitor_system_resources(self):
        """监控系统资源使用情况"""
        try:
            import psutil

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=1)

            self.stats["memory_usage"].append(memory_mb)

            logger.info(f"系统资源: 内存 {memory_mb:.2f} MB, CPU {cpu_percent:.1f}%")
            
            # 记录详细指标到专用日志
            metrics_logger = logging.getLogger("system.metrics")
            metrics_logger.info(f"memory={memory_mb:.2f},cpu={cpu_percent:.1f},threads={process.num_threads()}")

            # 如果内存使用超过1GB，发出警告
            if memory_mb > 1000:
                logger.warning("内存使用量较高!")
                
            # 更新监控指标
            if self.exporter:
                self.exporter.update_memory_usage(memory_mb)

            return memory_mb, cpu_percent
        except ImportError:
            logger.warning("无法导入psutil，跳过资源监控")
            return 0, 0

    def run(self):
        """运行稳定性测试"""
        if not self.setup_trading_system():
            logger.error("设置交易系统失败，退出测试")
            return False

        try:
            # 记录开始时间
            self.stats["start_time"] = datetime.datetime.now()
            start_time = time.time()
            end_time = start_time + self.duration_seconds

            logger.info(f"开始稳定性测试，计划结束时间: {datetime.datetime.fromtimestamp(end_time)}")

            # 主循环
            iteration = 0
            last_data_source = self.market_data_manager.get_current_provider_name()
            
            # 如果启用监控，设置初始数据源状态
            if self.exporter:
                self.exporter.update_data_source_status(last_data_source, True)
            
            while time.time() < end_time and not self.stop_requested:
                iteration += 1

                try:
                    # 更新心跳
                    if self.exporter:
                        self.exporter.update_heartbeat()
                    
                    # 每小时记录一次系统资源
                    if iteration % (3600 // self.check_interval) == 0:
                        self.monitor_system_resources()

                    # 检查数据源是否切换
                    current_data_source = self.market_data_manager.get_current_provider_name()
                    if current_data_source != last_data_source:
                        logger.info(f"数据源已切换: {last_data_source} -> {current_data_source}")
                        self.stats["data_source_switches"] += 1
                        last_data_source = current_data_source
                        
                        # 更新数据源状态指标
                        if self.exporter:
                            self.exporter.update_data_source_status(last_data_source, False)
                            self.exporter.update_data_source_status(current_data_source, True)

                    # 运行交易循环一次
                    signals = self.trading_loop.check_and_execute()
                    if signals:
                        self.stats["total_signals"] += len(signals)
                        
                        # 更新交易指标
                        if self.exporter:
                            for signal in signals:
                                # 记录交易信号
                                self.exporter.record_trade(signal['symbol'], signal['action'])
                                # 更新价格
                                self.exporter.update_price(signal['symbol'], float(signal['price']))
                                
                                # 记录信号到专用交易对日志
                                symbol_safe = signal['symbol'].replace('/', '_')
                                symbol_logger = logging.getLogger(f"trading.{symbol_safe}")
                                symbol_logger.info(f"信号: {signal['action']} @ {signal['price']}")

                    # 每天生成一次报告
                    if iteration % (86400 // self.check_interval) == 0:
                        days_running = (time.time() - start_time) / 86400
                        self.generate_report(days_running)

                    # 随机模拟网络中断和恢复
                    if iteration % 1000 == 0:
                        logger.info("模拟网络中断...")
                        self.stats["data_interruptions"] += 1
                        time.sleep(5)  # 暂停5秒
                        logger.info("恢复连接...")
                        self.stats["reconnections"] += 1

                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"迭代 {iteration} 出错: {e}")
                    
                    # 更新错误指标
                    if self.exporter:
                        self.exporter.record_error("iteration_error")

                    # 如果连续错误太多，暂停一段时间
                    if self.stats["errors"] > 5 and self.stats["errors"] % 5 == 0:
                        logger.warning("检测到多个错误，暂停5分钟后继续...")
                        time.sleep(300)

                # 等待下一个检查间隔
                time.sleep(self.check_interval)

            # 测试结束，生成最终报告
            total_duration = time.time() - start_time
            days_running = total_duration / 86400
            self.generate_report(days_running, is_final=True)

            if self.stop_requested:
                logger.info("测试被手动终止")
            else:
                logger.info("稳定性测试成功完成")

            return True

        except KeyboardInterrupt:
            logger.info("测试被用户中断")
            self.generate_report((time.time() - start_time) / 86400, is_final=True)
            return False
        except Exception as e:
            logger.critical(f"测试过程中发生严重错误: {e}")
            
            # 记录严重错误
            if self.exporter:
                self.exporter.record_error("critical")
            
            self.generate_report((time.time() - start_time) / 86400, is_final=True)
            return False

    def generate_report(self, days_running, is_final=False):
        """生成测试报告"""
        report_type = "最终" if is_final else "中期"

        # 计算每小时错误率
        hours_running = days_running * 24
        errors_per_hour = self.stats["errors"] / hours_running if hours_running > 0 else 0

        # 计算平均内存使用
        avg_memory = (
            sum(self.stats["memory_usage"]) / len(self.stats["memory_usage"]) if self.stats["memory_usage"] else 0
        )
        max_memory = max(self.stats["memory_usage"]) if self.stats["memory_usage"] else 0

        # 获取当前数据源
        current_data_source = self.market_data_manager.get_current_provider_name()

        # 生成报告
        report = f"""
====== {report_type}稳定性测试报告 ======
开始时间: {self.stats["start_time"]}
运行时长: {days_running:.2f} 天
交易对: {', '.join(self.symbols)}
当前数据源: {current_data_source}

性能指标:
- 总信号数: {self.stats["total_signals"]}
- 错误次数: {self.stats["errors"]}
- 每小时错误率: {errors_per_hour:.4f}
- 数据中断次数: {self.stats["data_interruptions"]}
- 重连次数: {self.stats["reconnections"]}
- 数据源切换次数: {self.stats["data_source_switches"]}
- 平均内存使用: {avg_memory:.2f} MB
- 最大内存使用: {max_memory:.2f} MB

系统状态: {'稳定' if errors_per_hour < 0.1 else '不稳定'}
        """

        logger.info(report)

        # 将报告写入文件
        report_file = self.log_dir / f"stability_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w") as f:
            f.write(report)

        logger.info(f"报告已保存到 {report_file}")

        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="加密货币交易系统稳定性测试")
    parser.add_argument("--symbols", type=str, help="要测试的交易对，用逗号分隔")
    parser.add_argument("--days", type=int, help="测试持续天数")
    parser.add_argument("--interval", type=int, help="检查间隔(秒)")
    parser.add_argument("--risk", type=float, help="风险百分比")
    parser.add_argument("--log-dir", type=str, help="日志目录")
    parser.add_argument("--production", action="store_true", help="生产模式(警告:将执行实际交易!)")
    parser.add_argument("--mock-only", action="store_true", help="仅使用模拟数据(不连接Binance测试网)")
    parser.add_argument("--config", type=str, help="配置文件路径(INI格式)")
    parser.add_argument("--config-yaml", type=str, help="YAML配置文件路径")
    parser.add_argument("--env-file", type=str, help="环境变量文件路径")
    parser.add_argument("--monitoring-port", type=int, default=9090, help="监控端口")
    parser.add_argument("--no-preserve-logs", action="store_true", help="不保留完整历史日志")

    args = parser.parse_args()

    # 初始化配置
    try:
        # 优先使用增强配置管理器
        if 'setup_logging' in globals() and setup_logging is not None:
            # 初始化配置
            global get_config
            get_config = lambda: get_config(
                config_yaml=args.config_yaml, 
                env_file=args.env_file,
                config_ini=args.config
            )
            
            # 设置日志
            setup_logging()
            logger.info("使用增强配置系统")
        elif args.config:
            # 如果使用旧版配置管理器且指定了配置文件
            from scripts.config_manager import ConfigManager
            global get_config
            get_config = lambda: ConfigManager(args.config)
            logger.info(f"使用旧版配置系统，配置文件: {args.config}")
    except Exception as e:
        logger.error(f"初始化配置系统时出错: {e}")
        logger.warning("使用默认配置")

    # 安全检查
    if args.production:
        logger.warning("警告: 您正在生产模式下运行测试，这将执行实际交易!")
        confirm = input("确认继续? (y/n): ")
        if confirm.lower() != "y":
            logger.info("测试已取消")
            return

    # 解析交易对
    symbols = None
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]

    # 创建并运行测试
    test = StabilityTest(
        symbols=symbols,
        duration_days=args.days,
        check_interval=args.interval,
        test_mode=not args.production,
        log_dir=args.log_dir,
        risk_percent=args.risk,
        use_binance_testnet=not args.mock_only if args.mock_only is not None else None,
        monitoring_port=args.monitoring_port,
        preserve_logs=not args.no_preserve_logs,
    )

    success = test.run()

    if success:
        logger.info("稳定性测试成功完成")
        return 0
    else:
        logger.error("稳定性测试失败或被中断")
        return 1


if __name__ == "__main__":
    sys.exit(main())
