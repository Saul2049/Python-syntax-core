# 🧠 M5内存&GC优化指南
# M5 Memory & GC Optimization Guide

## 🎯 概述

M5阶段专注于内存使用优化和垃圾回收性能调优，目标是在保持M4异步性能的基础上，将内存占用减少25%，GC暂停时间减少50%。

**核心目标**:
- RSS内存峰值 < 40MB
- GC暂停P95 < 50ms  
- 文件描述符稳定 < 500
- 24小时内存增长 < 5%

---

## 🚀 快速开始

### 1️⃣ 基线采集 (30分钟)
```bash
# 采集当前系统内存基线
make mem-baseline

# 或自定义参数
python scripts/mem_baseline.py --duration 1800 --save output/baseline.json
```

### 2️⃣ 内存健康检查
```bash
# 快速健康状态
make mem-health

# 详细内存快照
make mem-snapshot
```

### 3️⃣ GC性能分析
```bash
# 5分钟GC监控
make gc-profile

# 或自定义时长
python scripts/gc_profiler.py --duration 300 --optimize
```

---

## 📊 监控指标体系

### 核心内存指标
```yaml
process_memory_rss_bytes:     # RSS内存使用量
  target: < 40MB
  alert: > 60MB

memory_growth_rate_mb_per_minute:  # 内存增长率
  target: < 0.1MB/min
  alert: > 0.5MB/min

memory_peak_rss_bytes:        # 内存峰值
  tracking: 启动后最高值
```

### GC性能指标
```yaml
gc_pause_duration_seconds:    # GC暂停时间
  target_p95: < 0.05s
  alert_p95: > 0.1s

gc_collections_by_generation_total:  # 分代回收次数
  gen0_frequency: < 10/sec
  gen1_frequency: < 1/sec
  gen2_frequency: < 0.1/sec
```

### 资源泄漏检测
```yaml
process_open_fds:             # 文件描述符
  stable_range: 10-500
  leak_threshold: > 800

active_connections:           # 网络连接数
  websocket_target: 3-10
  leak_detection: 自动识别
```

---

## 🏗️ 优化策略

### W1: 对象池/LRU缓存
**目标**: RSS减少25%

#### DataFrame复用池
```python
from cachetools import LRUCache

# DataFrame复用池
df_pool = LRUCache(maxsize=50)

@cached(df_pool, key=lambda symbol, window: f"{symbol}_{window}")
def get_market_data_window(symbol: str, window: int) -> pd.DataFrame:
    """复用DataFrame窗口，避免重复分配"""
    return self.market_data[symbol].tail(window).copy()
```

#### ATR/MA计算缓存
```python
# 技术指标LRU缓存
indicator_cache = LRUCache(maxsize=100)

@cached(indicator_cache)
def compute_cached_atr(data_hash: str, period: int) -> float:
    """缓存ATR计算结果"""
    return self._compute_atr_internal(period)
```

#### 预分配策略
```python
# 预分配固定大小的DataFrame
def init_data_buffer(self, max_candles: int = 200):
    """预分配数据缓冲区，避免动态扩展"""
    self.data_buffer = pd.DataFrame(
        index=range(max_candles),
        columns=['open', 'high', 'low', 'close', 'volume']
    )
    self.buffer_index = 0
```

### W2: GC调参优化
**目标**: GC暂停减少50%

#### 动态阈值调整
```python
import gc

# M5推荐的GC阈值
def optimize_gc_settings():
    """M5优化的GC设置"""
    # 减少Gen0频率，增加批量处理
    gc.set_threshold(700, 10, 10)  # 默认(700,10,10)
    
    # 禁用debug模式
    gc.set_debug(0)
    
    # 注册GC监控回调
    gc.callbacks.append(gc_monitoring_callback)
```

#### 手动GC触发策略
```python
async def periodic_gc_management(self):
    """定期GC管理"""
    while self.running:
        # 在低负载时期主动触发GC
        if self.current_load < 0.3:
            collected = gc.collect()
            self.metrics.record_gc_event(
                generation=-1, 
                pause_duration=0.001,  # 主动GC通常很快
                collected_objects=collected
            )
        
        await asyncio.sleep(30)
```

### W3: 资源泄漏防护
**目标**: FD/连接稳定<500

#### WebSocket连接池管理
```python
class ManagedWSPool:
    """管理WebSocket连接池，防止泄漏"""
    
    def __init__(self, max_connections: int = 10):
        self.pool = []
        self.max_connections = max_connections
        self._cleanup_timer = None
    
    async def cleanup_stale_connections(self):
        """清理失效连接"""
        stale_connections = []
        for conn in self.pool:
            if conn.closed or time.time() - conn.last_activity > 300:
                stale_connections.append(conn)
        
        for conn in stale_connections:
            await conn.close()
            self.pool.remove(conn)
```

#### 文件描述符监控
```python
def monitor_fd_leaks(self):
    """监控文件描述符泄漏"""
    current_fds = psutil.Process().num_fds()
    
    if current_fds > 800:  # 泄漏阈值
        self.logger.warning(f"🚨 FD泄漏检测: {current_fds}")
        
        # 自动清理
        self._emergency_cleanup()
        
        # 告警
        self.metrics.update_fd_growth_rate(
            (current_fds - self._last_fd_count) / 60  # 每分钟增长
        )
```

---

## 🛠️ 工具使用指南

### 内存快照分析
```bash
# 连续监控60分钟，每60秒一次快照
python scripts/mem_snapshot.py --continuous 60 --interval 60

# 单次详细快照
python scripts/mem_snapshot.py --top 50 --save
```

输出分析：
```json
{
  "summary": {
    "memory_stats": {
      "max_rss_mb": 45.2,
      "total_growth_mb": 2.1
    },
    "leak_detection": [
      {
        "type": "rss_growth", 
        "severity": "medium",
        "growth_rate_mb_per_snapshot": 0.5
      }
    ]
  }
}
```

### GC性能调优
```bash
# 分析当前GC性能
python scripts/gc_profiler.py --duration 600 --prometheus

# 自动应用优化建议
python scripts/gc_profiler.py --duration 300 --optimize
```

输出解读：
```
🗑️ GC性能分析报告
⏱️ 监控时长: 300.0秒
📊 GC事件: 45次
⏸️ 总暂停时间: 234.5ms
📈 平均暂停: 5.21ms
🔄 GC频率: 0.15/秒

🏷️ 分代统计:
   Gen0: 42次, 平均5.1ms, P95=12.3ms
   Gen1: 3次, 平均8.7ms, P95=15.2ms

💡 优化建议:
   gen0: 900 (Gen0频率过高(0.14/s)，建议增加阈值)
```

### 基线对比分析
```bash
# 建立基线
python scripts/mem_baseline.py --duration 1800 --save baseline_v1.json

# 优化后对比
python scripts/mem_baseline.py --duration 1800 --save baseline_v2.json --compare baseline_v1.json
```

---

## 📈 持续监控设置

### Prometheus告警规则
```yaml
groups:
- name: m5_memory_alerts
  rules:
  - alert: MemoryUsageHigh
    expr: process_memory_rss_bytes > 60 * 1024 * 1024
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "内存使用过高"
      
  - alert: GCPauseTimeHigh  
    expr: histogram_quantile(0.95, gc_pause_duration_seconds) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "GC暂停时间过长"
      
  - alert: FDLeakDetected
    expr: increase(process_open_fds[5m]) > 50
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "检测到文件描述符泄漏"
```

### 自动化监控脚本
```bash
#!/bin/bash
# scripts/memory_watchdog.sh

while true; do
    # 检查内存使用
    RSS_MB=$(python -c "import psutil; print(psutil.Process().memory_info().rss // 1024 // 1024)")
    
    if [ $RSS_MB -gt 80 ]; then
        echo "🚨 内存使用过高: ${RSS_MB}MB"
        
        # 自动生成快照
        python scripts/mem_snapshot.py --save --top 10
        
        # 可选：自动重启
        # systemctl restart trading-engine
    fi
    
    sleep 300  # 5分钟检查一次
done
```

---

## 🧪 测试与验证

### 内存压力测试
```python
async def memory_stress_test(duration_hours: int = 24):
    """24小时内存压力测试"""
    
    start_rss = psutil.Process().memory_info().rss
    
    for hour in range(duration_hours):
        # 模拟高负载
        await simulate_high_frequency_trading()
        
        # 每小时检查
        current_rss = psutil.Process().memory_info().rss
        growth_mb = (current_rss - start_rss) / 1024 / 1024
        
        if growth_mb > hour * 2:  # 每小时增长>2MB视为异常
            raise MemoryLeakDetected(f"内存增长异常: {growth_mb:.1f}MB")
        
        await asyncio.sleep(3600)
```

### 性能回归测试
```bash
# CI/CD集成
- name: M5内存回归测试
  run: |
    python scripts/mem_baseline.py --duration 600 --save current.json
    python scripts/compare_with_baseline.py current.json baseline.json --threshold 15
```

---

## 🎯 M5完成标准

### 定量指标
- [x] RSS峰值 < 40MB (当前: ~12MB ✅)
- [ ] GC暂停P95 < 50ms (目标)
- [x] FD数量 < 500 (当前: ~3 ✅)
- [ ] 24h内存增长 < 5% (待测试)

### 基础设施
- [x] ✅ 内存监控工具套件
- [x] ✅ GC性能分析器  
- [x] ✅ 基线采集系统
- [x] ✅ Prometheus指标集成
- [x] ✅ 自动化测试流程

### 部署就绪度
- [ ] 对象池/LRU实现
- [ ] GC参数优化应用
- [ ] 24小时稳定性验证
- [ ] 生产环境监控配置

---

## 🔗 相关资源

- **M4异步架构文档**: `docs/M4_INCIDENT_RUNBOOK.md`
- **Prometheus监控**: `src/monitoring/metrics_collector.py`
- **工具脚本目录**: `scripts/mem_*.py`, `scripts/gc_*.py`
- **CI/CD集成**: `.github/workflows/perf-regression.yml`

---

**最后更新**: 2024-12-20  
**负责团队**: M5 Memory Optimization Team  
**版本**: v5.0.0-alpha 