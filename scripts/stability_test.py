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
import signal
import sys
import time
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stability_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("stability_test")

# 确保将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    # 导入自定义模块
    # 注意：只导入确实存在的模块，避免不必要的依赖
    from src import utils
    
    # 检查关键模块是否存在
    if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "market_simulator.py")):
        logger.warning("找不到market_simulator.py，将使用模拟对象")
        # 创建模拟对象用于测试
        class MockMarketSimulator:
            def __init__(self, symbols, initial_balance, fee_rate):
                self.symbols = symbols
                self.balance = initial_balance
                self.fee_rate = fee_rate
                logger.info(f"创建模拟市场：{symbols}, 初始余额：{initial_balance}")
                
        class MockTradingLoop:
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
                # 随机生成信号
                import random
                if random.random() < 0.1:  # 10%概率产生信号
                    symbol = self.symbols[random.randint(0, len(self.symbols)-1)]
                    signal = {"symbol": symbol, "action": "BUY" if random.random() > 0.5 else "SELL", "price": 30000 + random.random() * 1000}
                    logger.info(f"模拟信号: {signal}")
                    return [signal]
                return []
                
        MarketSimulator = MockMarketSimulator
        TradingLoop = MockTradingLoop
    else:
        from src.market_simulator import MarketSimulator
        from src.trading_loop import TradingLoop
    
except ImportError as e:
    logger.error(f"导入错误: {e}")
    logger.error("请确保您在项目根目录下运行此脚本")
    sys.exit(1)

class StabilityTest:
    """长期稳定性测试类"""
    
    def __init__(self, 
                 symbols=["BTC/USDT", "ETH/USDT"],
                 duration_days=3, 
                 check_interval=60,
                 test_mode=True,
                 log_dir="logs/stability_test",
                 risk_percent=0.5):
        """
        初始化稳定性测试
        
        参数:
            symbols: 要测试的交易对列表
            duration_days: 测试持续天数
            check_interval: 检查间隔(秒)
            test_mode: 是否为测试模式(不执行实际交易)
            log_dir: 日志目录
            risk_percent: 风险百分比(测试时降低风险)
        """
        self.symbols = symbols
        self.duration_seconds = duration_days * 24 * 60 * 60
        self.check_interval = check_interval
        self.test_mode = test_mode
        self.risk_percent = risk_percent
        
        # 创建日志目录
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置停止标志
        self.stop_requested = False
        
        # 统计数据
        self.stats = {
            "start_time": None,
            "total_signals": 0,
            "errors": 0,
            "data_interruptions": 0,
            "reconnections": 0,
            "memory_usage": []
        }
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info(f"初始化稳定性测试: {symbols}, 持续{duration_days}天")
    
    def signal_handler(self, sig, frame):
        """处理终止信号"""
        logger.info("收到终止信号，准备清理...")
        self.stop_requested = True
    
    def setup_trading_system(self):
        """设置交易系统组件"""
        try:
            # 如果在测试模式，使用模拟市场
            if self.test_mode:
                logger.info("使用市场模拟器进行测试")
                self.market = MarketSimulator(
                    symbols=self.symbols,
                    initial_balance=10000.0,
                    fee_rate=0.001
                )
                
            # 创建交易循环
            self.trading_loop = TradingLoop(
                market=self.market,
                symbols=self.symbols,
                risk_percent=self.risk_percent,
                fast_ma=7,
                slow_ma=25,
                atr_period=14,
                test_mode=self.test_mode
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
            
            # 如果内存使用超过1GB，发出警告
            if memory_mb > 1000:
                logger.warning("内存使用量较高!")
                
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
            while time.time() < end_time and not self.stop_requested:
                iteration += 1
                
                try:
                    # 每小时记录一次系统资源
                    if iteration % (3600 // self.check_interval) == 0:
                        self.monitor_system_resources()
                    
                    # 运行交易循环一次
                    signals = self.trading_loop.check_and_execute()
                    if signals:
                        self.stats["total_signals"] += len(signals)
                        
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
            self.generate_report((time.time() - start_time) / 86400, is_final=True)
            return False
    
    def generate_report(self, days_running, is_final=False):
        """生成测试报告"""
        report_type = "最终" if is_final else "中期"
        
        # 计算每小时错误率
        hours_running = days_running * 24
        errors_per_hour = self.stats["errors"] / hours_running if hours_running > 0 else 0
        
        # 计算平均内存使用
        avg_memory = sum(self.stats["memory_usage"]) / len(self.stats["memory_usage"]) if self.stats["memory_usage"] else 0
        max_memory = max(self.stats["memory_usage"]) if self.stats["memory_usage"] else 0
        
        # 生成报告
        report = f"""
====== {report_type}稳定性测试报告 ======
开始时间: {self.stats["start_time"]}
运行时长: {days_running:.2f} 天
交易对: {', '.join(self.symbols)}

性能指标:
- 总信号数: {self.stats["total_signals"]}
- 错误次数: {self.stats["errors"]}
- 每小时错误率: {errors_per_hour:.4f}
- 数据中断次数: {self.stats["data_interruptions"]}
- 重连次数: {self.stats["reconnections"]}
- 平均内存使用: {avg_memory:.2f} MB
- 最大内存使用: {max_memory:.2f} MB

系统状态: {'稳定' if errors_per_hour < 0.1 else '不稳定'}
        """
        
        logger.info(report)
        
        # 将报告写入文件
        report_file = self.log_dir / f"stability_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
            
        logger.info(f"报告已保存到 {report_file}")
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="加密货币交易系统稳定性测试")
    parser.add_argument("--symbols", type=str, default="BTC/USDT,ETH/USDT", 
                        help="要测试的交易对，用逗号分隔")
    parser.add_argument("--days", type=int, default=3,
                        help="测试持续天数")
    parser.add_argument("--interval", type=int, default=60,
                        help="检查间隔(秒)")
    parser.add_argument("--risk", type=float, default=0.5,
                        help="风险百分比")
    parser.add_argument("--log-dir", type=str, default="logs/stability_test",
                        help="日志目录")
    parser.add_argument("--production", action="store_true",
                        help="生产模式(警告:将执行实际交易!)")
    
    args = parser.parse_args()
    
    # 安全检查
    if args.production:
        logger.warning("警告: 您正在生产模式下运行测试，这将执行实际交易!")
        confirm = input("确认继续? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("测试已取消")
            return
    
    # 解析交易对
    symbols = [s.strip() for s in args.symbols.split(",")]
    
    # 创建并运行测试
    test = StabilityTest(
        symbols=symbols,
        duration_days=args.days,
        check_interval=args.interval,
        test_mode=not args.production,
        log_dir=args.log_dir,
        risk_percent=args.risk
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