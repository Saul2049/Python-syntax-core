---
title: 监控系统运维手册
description: M5内存优化阶段的完整监控运维手册
version: v5.0
status: active
last_updated: 2024-12-19
category: guide
---

# 🔍 监控系统运维手册 (M5 Monitoring Operations Runbook)

## 📋 概述 (Overview)

本文档是M5内存优化阶段的完整监控运维手册，涵盖系统健康检查、告警处理和故障排查。

**系统架构**: Prometheus + Grafana + 自动化告警
**监控范围**: 业务指标 + 系统指标 + M5内存优化指标

---

## 📊 **关键指标一览** (Key Metrics Dashboard)

### 🎯 **业务关键指标**
| 指标名 | 类型 | 说明 | 目标阈值 | 告警条件 |
|--------|------|------|---------|----------|
| `signal_latency_seconds_p95` | histogram | 信号计算延迟P95 | < 0.005s | > 0.0055s |
| `trading_trade_count_total` | counter | 交易计数 | — | 速率异常 |
| `trading_error_count_total` | counter | 错误计数 | — | > 5/10min |
| `trading_heartbeat_age_seconds` | gauge | 心跳年龄 | < 60s | > 180s |

### 🧠 **M5内存优化指标**
| 指标名 | 类型 | 说明 | 目标阈值 | 告警条件 |
|--------|------|------|---------|----------|
| `process_memory_rss_bytes` | gauge | RSS内存使用 | < 40MB | > 60MB |
| `process_memory_vms_bytes` | gauge | VMS内存使用 | < 80MB | > 120MB |
| `gc_pause_duration_seconds` | histogram | GC暂停时间 | P95 < 0.05s | P95 > 0.05s |
| `gc_collections_by_generation_total` | counter | 分代GC计数 | — | 频率异常 |
| `memory_growth_rate_mb_per_minute` | gauge | 内存增长率 | < 1MB/min | > 2MB/min |
| `fd_growth_rate_per_minute` | gauge | FD增长率 | < 1/min | > 5/min |
| `leaked_objects_total` | counter | 泄漏对象计数 | 0 | > 0 |
| `clean_hours_counter` | counter | 无泄漏小时数 | ≥ 6h | < 6h |

### 📈 **系统资源指标**
| 指标名 | 类型 | 说明 | 目标阈值 | 告警条件 |
|--------|------|------|---------|----------|
| `process_open_fds` | gauge | 打开的文件描述符 | < 500 | > 800 |
| `process_cpu_seconds_total` | counter | CPU使用时间 | — | 利用率>80% |
| `data_source_status` | gauge | 数据源状态 | 1 (active) | 0 (inactive) |

---

## 🚨 **告警规则配置** (Alert Rules)

### 📄 **Prometheus告警规则文件**: `monitoring/alerts.yml`

```yaml
groups:
  - name: trading_system_alerts
    rules:
      # 高延迟告警
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(signal_latency_seconds_bucket[5m])) > 0.0055
        for: 3m
        labels:
          severity: warning
          component: latency
        annotations:
          summary: "Trading signal latency too high"
          description: "P95 latency {{ $value }}s exceeds 5.5ms threshold"

      # 内存泄漏告警
      - alert: MemoryLeak
        expr: increase(process_memory_rss_bytes[30m]) > 62914560  # 60MB
        for: 5m
        labels:
          severity: critical
          component: memory
        annotations:
          summary: "Memory leak detected"
          description: "RSS memory increased by {{ $value | humanize1024 }} in 30 minutes"

      # GC性能告警
      - alert: GCPerformanceDegraded
        expr: histogram_quantile(0.95, rate(gc_pause_duration_seconds_bucket[10m])) > 0.05
        for: 5m
        labels:
          severity: warning
          component: gc
        annotations:
          summary: "GC pause time too high"
          description: "GC P95 pause time {{ $value }}s exceeds 50ms threshold"

      # 文件描述符泄漏
      - alert: FileDescriptorLeak
        expr: process_open_fds > 800
        for: 3m
        labels:
          severity: warning
          component: system
        annotations:
          summary: "File descriptor count too high"
          description: "Open FDs: {{ $value }} > 800 threshold"

      # 数据源断线
      - alert: DataSourceDown
        expr: data_source_status == 0
        for: 1m
        labels:
          severity: critical
          component: data_source
        annotations:
          summary: "Data source unavailable"
          description: "Data source {{ $labels.source_name }} is down"

      # 错误率激增
      - alert: HighErrorRate
        expr: increase(trading_error_count_total[10m]) > 5
        for: 2m
        labels:
          severity: warning
          component: errors
        annotations:
          summary: "High error rate detected"
          description: "{{ $value }} errors in last 10 minutes"
```

### 📱 **告警通知配置** (Alertmanager)

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'component']
```

---

## 🔧 **快速健康检查** (Health Check Commands)

### 💻 **命令行健康检查**

```bash
# 综合系统健康检查
make health

# 内存专项检查
make mem-health

# Prometheus指标检查
make prometheus-check

# Canary状态检查
make canary-status

# M5基础设施完成度
make m5-completion
```

### 🎯 **自动化验收测试**

```bash
# M5自动化断言验证
python scripts/assert_p95.py --quick

# W1 缓存优化验证
make w1-cache-test

# 完整M5验收流程
make m5-full-validation
```

---

## 🏥 **故障排查流程** (Troubleshooting Procedures)

### 🚨 **故障场景1: 高延迟告警 (HighLatency)**

**症状**: P95延迟 > 5.5ms
**排查步骤**:
1. 检查Grafana Dashboard "Trading-Overview"
2. 分析延迟分布: `histogram_quantile(0.95, rate(signal_latency_seconds_bucket[5m]))`
3. 检查资源使用: CPU、内存、GC暂停
4. 检查数据源连接状态
5. 如果是WebSocket问题: `make restart-ws`
6. 如果持续，回退到REST模式: `make fallback-rest`

**恢复SOP**:
```bash
# 1. 确认问题
curl -s http://localhost:8000/metrics | grep signal_latency

# 2. 重启WebSocket连接
make restart-ws

# 3. 监控恢复
watch "curl -s http://localhost:8000/metrics | grep signal_latency"
```

### 🧠 **故障场景2: 内存泄漏 (MemoryLeak)**

**症状**: RSS增长 > 60MB 或增长率 > 2MB/min
**排查步骤**:
1. 立即拍摄内存快照: `make mem-snapshot`
2. 检查内存增长趋势: `rate(process_memory_rss_bytes[30m])`
3. 分析对象泄漏: `python scripts/mem_snapshot.py --continuous --duration 300`
4. 检查缓存命中率: 缓存可能失效导致内存堆积
5. 必要时重启服务释放内存

**恢复SOP**:
```bash
# 1. 紧急内存快照
make mem-snapshot

# 2. 分析泄漏源
python scripts/mem_snapshot.py --top 50 --save

# 3. 启动泄漏哨兵
python scripts/w3_leak_sentinel.py --target-hours 1

# 4. 如果泄漏严重，准备重启
# 注意：重启会中断交易，仅在紧急情况下执行
```

### 🗑️ **故障场景3: GC性能恶化 (GCPerformanceDegraded)**

**症状**: GC P95暂停 > 50ms
**排查步骤**:
1. 启动GC profiler: `make gc-profile`
2. 检查各代GC频率: `rate(gc_collections_by_generation_total[10m])`
3. 分析内存分配模式
4. 检查大对象创建
5. 调优GC参数

**恢复SOP**:
```bash
# 1. GC性能分析
make gc-profile

# 2. 应用优化配置
make w2-gc-optimize

# 3. 验证改善效果
python scripts/gc_profiler.py --duration 300
```

### 🔗 **故障场景4: 文件描述符泄漏 (FileDescriptorLeak)**

**症状**: 打开FD > 800
**排查步骤**:
1. 检查当前FD状态: `lsof -p $(pgrep python)`
2. 分析FD类型分布: socket、文件、管道
3. 检查WebSocket连接是否正常关闭
4. 检查日志文件是否正常轮转

**恢复SOP**:
```bash
# 1. 检查FD使用情况
lsof -p $(pgrep -f "python.*trading") | head -50

# 2. 重启WebSocket连接
make restart-ws

# 3. 监控FD恢复
watch "lsof -p $(pgrep -f \"python.*trading\") | wc -l"
```

---

## 📈 **Grafana仪表板配置** (Dashboard Setup)

### 🖥️ **主要仪表板**

1. **Trading System Overview**
   - 信号延迟时间序列
   - 交易计数和错误率
   - 心跳和数据源状态

2. **M5 Memory Optimization**
   - RSS/VMS内存使用趋势
   - GC暂停时间分布
   - 内存增长率和FD使用

3. **System Resources**
   - CPU利用率
   - 文件描述符计数
   - 网络连接状态

### 🎨 **关键面板配置**

**延迟监控面板**:
```
Query: histogram_quantile(0.95, rate(signal_latency_seconds_bucket[5m]))
Visualization: Time series
Thresholds: 0.005 (green), 0.0055 (red)
```

**内存使用面板**:
```
Query: process_memory_rss_bytes / 1024 / 1024
Visualization: Gauge
Thresholds: 40MB (green), 60MB (red)
```

---

## 🤖 **自动化监控配置** (Automated Monitoring)

### ⏰ **定时健康检查脚本**

创建 `scripts/daily_health_check.py`:

```python
#!/usr/bin/env python3
"""
每日自动健康检查脚本
"""
import subprocess
import json
import requests
from datetime import datetime

def run_health_check():
    """运行综合健康检查"""
    timestamp = datetime.now().isoformat()
    
    # 运行Makefile健康检查
    result = subprocess.run(['make', 'health'], 
                          capture_output=True, text=True)
    
    # 收集关键指标
    metrics = collect_prometheus_metrics()
    
    # 生成报告
    report = {
        'timestamp': timestamp,
        'health_check_output': result.stdout,
        'return_code': result.returncode,
        'metrics': metrics,
        'status': 'healthy' if result.returncode == 0 else 'unhealthy'
    }
    
    # 保存报告
    with open(f'output/daily_health_{timestamp[:10]}.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def collect_prometheus_metrics():
    """收集Prometheus关键指标"""
    try:
        response = requests.get('http://localhost:8000/metrics', timeout=5)
        # 解析关键指标
        return parse_key_metrics(response.text)
    except:
        return {'error': 'prometheus_unavailable'}

if __name__ == "__main__":
    report = run_health_check()
    print(f"Health check completed: {report['status']}")
```

---

## 📋 **监控检查清单** (Monitoring Checklist)

### ✅ **日常检查项**
- [ ] 系统健康检查: `make health`
- [ ] Prometheus指标正常: `make prometheus-check`
- [ ] Grafana仪表板无告警
- [ ] 内存使用在阈值内: < 40MB RSS
- [ ] GC性能正常: P95 < 50ms
- [ ] 文件描述符正常: < 500 FDs
- [ ] 数据源连接稳定

### 🚨 **告警响应检查项**
- [ ] 确认告警真实性
- [ ] 执行对应故障排查SOP
- [ ] 记录问题和解决方案
- [ ] 更新监控阈值(如需要)
- [ ] 确认告警恢复

### 📊 **周度审查项**
- [ ] 审查告警历史和误报率
- [ ] 分析性能趋势
- [ ] 更新监控阈值
- [ ] 优化仪表板布局
- [ ] 更新运维文档

---

## 🔗 **相关资源链接** (Related Resources)

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
- **Metrics Endpoint**: http://localhost:8000/metrics
- **M4 Incident Runbook**: [docs/M4_INCIDENT_RUNBOOK.md](M4_INCIDENT_RUNBOOK.md)
- **M5 Memory Guide**: [docs/M5_MEMORY_OPTIMIZATION_GUIDE.md](M5_MEMORY_OPTIMIZATION_GUIDE.md)

---

## 📞 **支持联系方式** (Support Contacts)

- **监控系统问题**: 参考本文档故障排查流程
- **告警静噪**: 修改 `monitoring/alerts.yml`
- **仪表板问题**: 检查Grafana配置
- **性能问题**: 运行 `make perf-benchmark`

---

**文档版本**: M5.1.0  
**最后更新**: 2024-12-20  
**维护责任**: DevOps团队 