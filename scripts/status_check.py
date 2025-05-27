#!/usr/bin/env python3
"""
🔍 W3+W4 并行状态检查器
避免 jq 时间解析问题，直接用 Python 处理
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

def parse_iso_time(iso_string: str) -> datetime:
    """解析ISO时间字符串，兼容毫秒格式"""
    try:
        # 处理带毫秒的格式
        if '.' in iso_string:
            # 2025-05-24T22:58:38.007352
            return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        else:
            # 2025-05-24T22:58:38
            return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except:
        return None

def format_duration(seconds: float) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分钟"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}小时"

def check_w3_status():
    """检查W3泄漏哨兵状态"""
    status_file = "output/w3_sentinel_status_W3-Production.json"
    
    if not os.path.exists(status_file):
        return {"status": "not_found", "message": "状态文件不存在"}
    
    try:
        with open(status_file, 'r') as f:
            data = json.load(f)
        
        start_time_str = data.get('start_time')
        if start_time_str:
            start_time = parse_iso_time(start_time_str)
            if start_time:
                runtime = (datetime.now() - start_time).total_seconds()
                runtime_hours = runtime / 3600
            else:
                runtime = runtime_hours = 0
        else:
            runtime = runtime_hours = 0
        
        return {
            "status": data.get('status', 'unknown'),
            "target_hours": data.get('target_hours', 6),
            "runtime_seconds": runtime,
            "runtime_hours": runtime_hours,
            "rss_mb": data.get('rss_mb'),
            "fd_count": data.get('fd_count'),
            "clean_hours": data.get('clean_hours', 0)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def check_w4_status():
    """检查W4压力测试状态"""
    status_file = "output/w4_stress_status_W4-24h-real.json"
    
    if not os.path.exists(status_file):
        return {"status": "not_found", "message": "状态文件不存在"}
    
    try:
        with open(status_file, 'r') as f:
            data = json.load(f)
        
        start_time_str = data.get('start_time')
        if start_time_str:
            start_time = parse_iso_time(start_time_str)
            if start_time:
                runtime = (datetime.now() - start_time).total_seconds()
                runtime_hours = runtime / 3600
            else:
                runtime = runtime_hours = 0
        else:
            runtime = runtime_hours = 0
        
        return {
            "status": data.get('status', 'unknown'),
            "signals_processed": data.get('signals_processed', 0),
            "signals_target": data.get('signals_target', 20000),
            "progress_percent": data.get('progress_percent', 0),
            "runtime_seconds": runtime,
            "runtime_hours": runtime_hours,
            "latest_p95_latency": data.get('latest_p95_latency', 0),
            "max_rss_mb": data.get('max_rss_mb', 0),
            "avg_rss_mb": data.get('avg_rss_mb', 0)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    """主函数"""
    print("🕒 W3+W4 并行测试状态检查")
    print("=" * 60)
    print(f"⏰ 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # W3 状态
    w3_status = check_w3_status()
    print("🔍 W3 泄漏哨兵:")
    print("-" * 30)
    if w3_status["status"] == "not_found":
        print("❌ 状态文件不存在")
    elif w3_status["status"] == "error":
        print(f"❌ 错误: {w3_status['message']}")
    else:
        status_icon = "✅" if w3_status["status"] == "running" else "❌"
        print(f"状态: {status_icon} {w3_status['status']}")
        print(f"运行时长: {format_duration(w3_status['runtime_seconds'])} / {w3_status['target_hours']}小时")
        
        if w3_status['runtime_hours'] > 0:
            progress_pct = (w3_status['runtime_hours'] / w3_status['target_hours']) * 100
            print(f"进度: {progress_pct:.1f}%")
        
        if w3_status['rss_mb']:
            print(f"RSS内存: {w3_status['rss_mb']}MB")
        if w3_status['fd_count']:
            print(f"文件描述符: {w3_status['fd_count']}")
        if w3_status['clean_hours']:
            print(f"清洁小时: {w3_status['clean_hours']}h")
    
    print("")
    
    # W4 状态  
    w4_status = check_w4_status()
    print("🔥 W4 压力测试:")
    print("-" * 30)
    if w4_status["status"] == "not_found":
        print("❌ 状态文件不存在")
    elif w4_status["status"] == "error":
        print(f"❌ 错误: {w4_status['message']}")
    else:
        status_icon = "✅" if w4_status["status"] == "running" else "❌"
        print(f"状态: {status_icon} {w4_status['status']}")
        print(f"运行时长: {format_duration(w4_status['runtime_seconds'])}")
        print(f"信号处理: {w4_status['signals_processed']:,} / {w4_status['signals_target']:,}")
        print(f"进度: {w4_status['progress_percent']:.1f}%")
        
        if w4_status['latest_p95_latency'] > 0:
            latency_status = "✅" if w4_status['latest_p95_latency'] <= 6.0 else "⚠️"
            print(f"P95延迟: {latency_status} {w4_status['latest_p95_latency']:.2f}ms")
        
        if w4_status['avg_rss_mb'] > 0:
            rss_status = "✅" if w4_status['avg_rss_mb'] <= 40 else "⚠️"
            print(f"RSS内存: {rss_status} {w4_status['avg_rss_mb']:.1f}MB")
    
    print("")
    print("=" * 60)
    
    # 简化的验收状态
    w3_ok = w3_status.get("status") == "running"
    w4_ok = w4_status.get("status") == "running"
    
    print("🎯 验收状态概览:")
    print(f"W3 泄漏哨兵: {'✅ 运行中' if w3_ok else '❌ 未运行'}")
    print(f"W4 压力测试: {'✅ 运行中' if w4_ok else '❌ 未运行'}")
    
    if w3_ok and w4_ok:
        print("🚀 并行测试正常运行中！")
        
        # 预估完成时间
        if w3_status.get('runtime_hours', 0) > 0:
            w3_remaining = w3_status['target_hours'] - w3_status['runtime_hours']
            if w3_remaining > 0:
                print(f"📅 W3 预计剩余: {format_duration(w3_remaining * 3600)}")
        
        if w4_status.get('runtime_hours', 0) > 0 and w4_status.get('progress_percent', 0) > 0:
            w4_remaining_pct = 100 - w4_status['progress_percent']
            if w4_remaining_pct > 0 and w4_status['progress_percent'] > 0:
                estimated_total_hours = w4_status['runtime_hours'] / (w4_status['progress_percent'] / 100)
                w4_remaining_hours = estimated_total_hours - w4_status['runtime_hours']
                print(f"📅 W4 预计剩余: {format_duration(w4_remaining_hours * 3600)}")
    else:
        print("⚠️ 部分任务未运行，请检查")

if __name__ == "__main__":
    main() 