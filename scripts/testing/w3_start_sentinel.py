#!/usr/bin/env python3
"""
W3 泄漏哨兵启动器
W3 Leak Sentinel Launcher

支持标签化运行和状态追踪
"""

import os
import sys
import json
import time
import argparse
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from scripts.testing.w3_leak_sentinel import W3LeakSentinel


class W3SentinelLauncher:
    """W3 泄漏哨兵启动器"""
    
    def __init__(self, run_name: str = None):
        self.run_name = run_name or f"W3-{int(time.time())}"
        self.logger = logging.getLogger(__name__)
        self.status_file = f"output/w3_sentinel_status_{self.run_name}.json"
        
    async def start_sentinel(self, 
                           target_hours: int = 6,
                           check_interval: int = 300,
                           memory_threshold: float = 0.1,
                           fd_threshold: float = 0.1) -> bool:
        """启动 W3 泄漏哨兵"""
        
        print(f"🔍 启动 W3 泄漏哨兵")
        print(f"📋 运行名称: {self.run_name}")
        print(f"🎯 目标: 连续{target_hours}小时无泄漏")
        print(f"📊 监控参数:")
        print(f"   检查间隔: {check_interval}秒")
        print(f"   内存阈值: {memory_threshold} MB/min")
        print(f"   FD阈值: {fd_threshold} FD/min")
        
        # 更新状态
        self._update_status({
            'run_name': self.run_name,
            'status': 'starting',
            'start_time': datetime.now().isoformat(),
            'target_hours': target_hours,
            'parameters': {
                'check_interval': check_interval,
                'memory_threshold': memory_threshold,
                'fd_threshold': fd_threshold
            }
        })
        
        try:
            # 创建哨兵
            sentinel = W3LeakSentinel(target_hours=target_hours)
            sentinel.check_interval = check_interval
            sentinel.memory_leak_threshold = memory_threshold
            sentinel.fd_leak_threshold = fd_threshold
            
            # 更新状态
            self._update_status({
                'status': 'running',
                'sentinel_started': datetime.now().isoformat()
            })
            
            # 开始监控
            await sentinel.start_monitoring()
            
            # 保存最终报告
            timestamp = int(time.time())
            report_file = f"output/w3_leak_sentinel_{self.run_name}_{timestamp}.json"
            os.makedirs('output', exist_ok=True)
            sentinel.save_report(report_file)
            
            # 更新最终状态
            self._update_status({
                'status': 'completed',
                'completion_time': datetime.now().isoformat(),
                'passed': sentinel.w3_status['passed'],
                'report_file': report_file,
                'final_clean_hours': sentinel.clean_hours_count
            })
            
            return sentinel.w3_status['passed']
            
        except KeyboardInterrupt:
            print("\n⏸️ 用户中断监控")
            self._update_status({
                'status': 'interrupted',
                'interrupt_time': datetime.now().isoformat()
            })
            return False
            
        except Exception as e:
            print(f"❌ W3 监控失败: {e}")
            self._update_status({
                'status': 'failed',
                'error': str(e),
                'error_time': datetime.now().isoformat()
            })
            return False
    
    def _update_status(self, updates: Dict):
        """更新状态文件"""
        status = {}
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    status = json.load(f)
            except:
                pass
        
        status.update(updates)
        status['last_update'] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'status': 'not_started'}
    
    def print_status(self):
        """打印状态信息"""
        status = self.get_status()
        
        print(f"\n📊 W3 哨兵状态: {self.run_name}")
        print("="*50)
        print(f"状态: {status.get('status', 'unknown')}")
        
        if 'start_time' in status:
            print(f"开始时间: {status['start_time']}")
        
        if 'target_hours' in status:
            print(f"目标小时: {status['target_hours']}")
        
        if 'final_clean_hours' in status:
            print(f"达成小时: {status['final_clean_hours']}")
        
        if 'passed' in status:
            result = "✅ PASS" if status['passed'] else "❌ FAIL"
            print(f"验收结果: {result}")
        
        if 'report_file' in status:
            print(f"报告文件: {status['report_file']}")
        
        print("="*50)


def create_scheduled_config(run_name: str, cron_schedule: str = "0 3 * * *") -> str:
    """创建定时任务配置"""
    config = {
        "w3_leak_sentinel_schedule": {
            "description": "W3 泄漏哨兵夜间定时监控",
            "cron": cron_schedule,
            "command": f"python scripts/testing/w3_start_sentinel.py --run-name {run_name}-scheduled",
            "timeout": "7h",
            "retry_on_failure": False,
            "notifications": {
                "on_start": True,
                "on_completion": True,
                "on_failure": True
            },
            "environment": {
                "W3_TARGET_HOURS": "6",
                "W3_CHECK_INTERVAL": "300",
                "W3_MEMORY_THRESHOLD": "0.1",
                "W3_FD_THRESHOLD": "0.1"
            }
        }
    }
    
    config_file = f"config/w3_scheduled_{run_name}.json"
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_file


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='W3 泄漏哨兵启动器')
    parser.add_argument('--run-name', type=str, default=None,
                       help='运行名称标签 (默认: W3-timestamp)')
    parser.add_argument('--target-hours', type=int, default=6,
                       help='目标清洁小时数 (默认: 6)')
    parser.add_argument('--check-interval', type=int, default=300,
                       help='检查间隔秒数 (默认: 300)')
    parser.add_argument('--memory-threshold', type=float, default=0.1,
                       help='内存泄漏阈值 MB/min (默认: 0.1)')
    parser.add_argument('--fd-threshold', type=float, default=0.1,
                       help='FD泄漏阈值 FD/min (默认: 0.1)')
    parser.add_argument('--status-only', action='store_true',
                       help='仅显示状态，不启动监控')
    parser.add_argument('--create-schedule', type=str,
                       help='创建定时任务配置 (cron表达式)')
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建启动器
    launcher = W3SentinelLauncher(run_name=args.run_name)
    
    # 仅显示状态
    if args.status_only:
        launcher.print_status()
        return
    
    # 创建定时任务配置
    if args.create_schedule:
        config_file = create_scheduled_config(launcher.run_name, args.create_schedule)
        print(f"✅ 定时任务配置已创建: {config_file}")
        print(f"📅 Cron 表达式: {args.create_schedule}")
        print("💡 使用 crontab 或系统调度器应用此配置")
        return
    
    # 启动哨兵
    try:
        success = await launcher.start_sentinel(
            target_hours=args.target_hours,
            check_interval=args.check_interval,
            memory_threshold=args.memory_threshold,
            fd_threshold=args.fd_threshold
        )
        
        exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 