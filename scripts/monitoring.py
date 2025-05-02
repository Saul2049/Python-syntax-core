#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控模块 - Prometheus Exporter
Monitoring Module - Prometheus Exporter

提供用于 Grafana 可视化和告警的指标收集功能
Provides metrics collection for Grafana visualization and alerting
"""

import time
import logging
import threading
from typing import Dict, Any, Optional
from prometheus_client import start_http_server, Gauge, Counter

# 设置日志记录器
logger = logging.getLogger("monitoring")

class PrometheusExporter:
    """Prometheus指标导出器类"""
    
    def __init__(self, port: int = 9090):
        """
        初始化Prometheus导出器
        
        参数:
            port: 监听端口号
        """
        self.port = port
        self.server_started = False
        
        # 创建监控指标
        # 交易次数指标
        self.trade_count = Counter(
            'trading_trade_count_total', 
            '交易总次数 (Total number of trades)',
            ['symbol', 'action']  # 标签: 交易对和操作类型
        )
        
        # 错误计数器
        self.error_count = Counter(
            'trading_error_count_total', 
            '错误总次数 (Total number of errors)',
            ['type']  # 标签: 错误类型
        )
        
        # 心跳时间
        self.heartbeat_age = Gauge(
            'trading_heartbeat_age_seconds', 
            '上次心跳距现在的秒数 (Seconds since last heartbeat)'
        )
        
        # 数据源状态指标
        self.data_source_status = Gauge(
            'trading_data_source_status', 
            '数据源状态 (Data source status: 1=active, 0=inactive)',
            ['source_name']  # 标签: 数据源名称
        )
        
        # 内存使用量
        self.memory_usage = Gauge(
            'trading_memory_usage_mb', 
            '内存使用量 (Memory usage in MB)'
        )
        
        # 交易对价格
        self.price = Gauge(
            'trading_price', 
            '交易对价格 (Current price)',
            ['symbol']  # 标签: 交易对
        )
        
        # 最后心跳时间
        self.last_heartbeat = time.time()
        
        # 启动心跳更新线程
        self.heartbeat_thread = threading.Thread(target=self._update_heartbeat, daemon=True)
        self.stop_heartbeat = False
        
        logger.info(f"初始化Prometheus指标导出器，端口: {port}")
    
    def start(self):
        """启动Prometheus指标导出服务器"""
        if not self.server_started:
            try:
                start_http_server(self.port)
                self.server_started = True
                
                # 启动心跳线程
                self.heartbeat_thread.start()
                
                logger.info(f"Prometheus导出器已启动于端口 {self.port}")
            except Exception as e:
                logger.error(f"启动Prometheus服务器失败: {e}")
        else:
            logger.warning("Prometheus服务器已经在运行")
    
    def _update_heartbeat(self):
        """更新心跳指标的后台线程"""
        while not self.stop_heartbeat:
            now = time.time()
            self.heartbeat_age.set(now - self.last_heartbeat)
            time.sleep(1)
    
    def record_trade(self, symbol: str, action: str):
        """
        记录交易事件
        
        参数:
            symbol: 交易对
            action: 操作类型 (BUY/SELL)
        """
        self.trade_count.labels(symbol=symbol, action=action).inc()
    
    def record_error(self, error_type: str = "general"):
        """
        记录错误事件
        
        参数:
            error_type: 错误类型
        """
        self.error_count.labels(type=error_type).inc()
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()
    
    def update_data_source_status(self, source_name: str, is_active: bool):
        """
        更新数据源状态
        
        参数:
            source_name: 数据源名称
            is_active: 是否活跃
        """
        self.data_source_status.labels(source_name=source_name).set(1 if is_active else 0)
    
    def update_memory_usage(self, memory_mb: float):
        """
        更新内存使用量
        
        参数:
            memory_mb: 内存使用量(MB)
        """
        self.memory_usage.set(memory_mb)
    
    def update_price(self, symbol: str, price: float):
        """
        更新交易对价格
        
        参数:
            symbol: 交易对
            price: 价格
        """
        self.price.labels(symbol=symbol).set(price)
    
    def stop(self):
        """停止心跳线程"""
        self.stop_heartbeat = True
        if self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)
            logger.info("心跳线程已停止")


# 全局导出器实例
_exporter = None

def get_exporter(port: int = 9090) -> PrometheusExporter:
    """
    获取全局Prometheus导出器实例
    
    参数:
        port: 监听端口
    
    返回:
        PrometheusExporter实例
    """
    global _exporter
    if _exporter is None:
        _exporter = PrometheusExporter(port=port)
    return _exporter


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    
    # 创建导出器
    exporter = get_exporter(port=9091)
    exporter.start()
    
    # 记录一些测试数据
    exporter.record_trade("BTC/USDT", "BUY")
    exporter.record_trade("ETH/USDT", "SELL")
    exporter.record_error("network")
    exporter.update_data_source_status("BinanceTestnet", True)
    exporter.update_data_source_status("MockMarket", False)
    exporter.update_memory_usage(42.5)
    exporter.update_price("BTC/USDT", 30123.45)
    
    # 保持程序运行一段时间
    logger.info("测试导出器已启动，访问 http://localhost:9091/metrics 查看指标")
    logger.info("按 Ctrl+C 停止")
    
    try:
        while True:
            # 每5秒更新一次心跳
            exporter.update_heartbeat()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("停止测试")
        exporter.stop() 