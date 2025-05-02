# 监控系统文档

本文档介绍如何使用系统的Prometheus监控功能和Grafana可视化仪表板。

## 概述

交易系统集成了Prometheus监控功能，可以收集以下关键指标：

1. **trade_count** - 交易计数器，按交易对和操作类型（买/卖）分类
2. **error_count** - 错误计数器，按错误类型分类
3. **heartbeat_age** - 心跳年龄，记录自上次心跳以来的秒数
4. **data_source_status** - 数据源状态，表示数据源是否活跃
5. **memory_usage** - 内存使用量，以MB为单位
6. **price** - 交易对的当前价格

## 配置

### YAML配置

在`config.yaml`中配置监控设置：

```yaml
# 监控配置
monitoring:
  # 是否启用监控
  enabled: true
  # Prometheus导出器端口
  port: 9090
  # 是否启用告警
  alerts_enabled: true
  # 心跳超时(秒)
  heartbeat_timeout: 180
```

### 命令行参数

通过命令行参数设置监控端口：

```bash
python scripts/stability_test.py --monitoring-port 9090
```

或使用运行脚本：

```bash
./scripts/run_stability_test.sh --monitoring-port 9090
```

## Prometheus设置

### 安装Prometheus

1. 下载Prometheus：[https://prometheus.io/download/](https://prometheus.io/download/)
2. 创建Prometheus配置文件`prometheus.yml`：

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'trading_system'
    static_configs:
      - targets: ['localhost:9090']
```

3. 启动Prometheus：

```bash
./prometheus --config.file=prometheus.yml
```

Prometheus控制台通常在：http://localhost:9090

## Grafana设置

### 安装Grafana

1. 下载Grafana：[https://grafana.com/grafana/download](https://grafana.com/grafana/download)
2. 启动Grafana服务
3. 访问Grafana：http://localhost:3000（默认用户名和密码：admin/admin）

### 配置Prometheus数据源

1. 登录Grafana
2. 进入"Configuration" > "Data sources"
3. 点击"Add data source"
4. 选择"Prometheus"
5. 设置URL为Prometheus服务器地址：`http://localhost:9090`
6. 点击"Save & Test"确保连接成功

### 创建仪表板

1. 点击"Create" > "Dashboard"
2. 点击"Add new panel"
3. 添加以下面板：

#### 交易计数面板

- 选择"Graph"类型
- 查询：`sum(trading_trade_count_total) by (symbol, action)`
- 标题：交易计数
- 说明：显示每个交易对的买/卖交易数量

#### 错误计数面板

- 选择"Stat"类型
- 查询：`sum(trading_error_count_total)`
- 标题：错误总数
- 阈值：
  - 0-5: green
  - 5-20: orange
  - >20: red

#### 心跳监控面板

- 选择"Gauge"类型
- 查询：`trading_heartbeat_age_seconds`
- 标题：心跳（秒）
- 阈值：
  - 0-60: green
  - 60-180: orange
  - >180: red

#### 数据源状态面板

- 选择"Status map"类型（需要安装Status Panel插件）
- 查询：`trading_data_source_status`
- 标题：数据源状态
- 映射：
  - 1: OK (绿色)
  - 0: Error (红色)

#### 内存使用量面板

- 选择"Gauge"类型
- 查询：`trading_memory_usage_mb`
- 标题：内存使用量(MB)
- 阈值：
  - 0-500: green
  - 500-1000: orange
  - >1000: red

#### 价格跟踪面板

- 选择"Graph"类型
- 查询：`trading_price{symbol="BTC/USDT"}`
- 标题：BTC/USDT价格
- 重复此面板为其他交易对创建类似图表

## 设置告警

Grafana告警可以在各个面板中配置：

1. 编辑面板
2. 进入"Alert"选项卡
3. 点击"Create Alert"
4. 配置告警条件

### 常用告警示例

#### 心跳超时告警

- 名称：心跳超时
- 条件：当`trading_heartbeat_age_seconds > 180`持续3分钟时
- 通知消息：交易系统心跳超时，请检查服务是否正常运行

#### 错误计数告警

- 名称：错误过多
- 条件：当`sum(increase(trading_error_count_total[10m])) > 5`时
- 通知消息：10分钟内检测到超过5个错误，请检查系统日志

#### 数据源告警

- 名称：数据源不可用
- 条件：当`trading_data_source_status{source_name="BinanceTestnet"} == 0`持续5分钟时
- 通知消息：币安测试网数据源不可用，已切换到备用数据源

## 查看Prometheus指标

可以直接访问导出器的metrics端点查看原始指标：

```
http://localhost:9090/metrics
```

交易系统指标以`trading_`前缀开头。

## 监控接入方式

监控系统作为独立的HTTP服务运行，可以与多种监控系统集成：

- Prometheus + Grafana (推荐)
- Datadog (需要配置Datadog Agent)
- Zabbix (需要配置自定义脚本)
- CloudWatch (需要使用代理转发)

## 常见问题

### 无法访问指标

1. 确认监控服务已启动（检查日志中的"监控系统已启动"消息）
2. 确认端口未被占用
3. 检查防火墙设置

### 指标不更新

1. 检查交易系统是否正常运行
2. 检查心跳指标是否正常更新
3. 重启监控服务

## 监控最佳实践

1. 设置合理的告警阈值，避免过多误报
2. 为关键指标配置告警通知
3. 定期备份Grafana仪表板配置
4. 保留历史指标数据用于趋势分析 