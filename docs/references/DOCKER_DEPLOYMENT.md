# Docker部署指南

本文档介绍如何使用Docker部署交易系统，以及如何进行自动升级和维护。

## 部署架构

系统使用Docker Compose部署三个容器：

1. **trading-system** - 交易系统主服务
2. **prometheus** - 指标收集和监控
3. **grafana** - 可视化仪表板和告警

## 系统要求

- Docker 19.03+
- Docker Compose 1.27+
- 至少2GB内存
- 至少10GB磁盘空间

## 快速部署

### 1. 准备配置文件

确保在项目根目录下有一个`config.yaml`文件：

```bash
# 如果没有配置文件，从模板复制一个
cp scripts/config.yaml.template config.yaml
```

根据需要修改配置文件。

### 2. 启动服务

在项目根目录下运行：

```bash
docker-compose up -d
```

这将构建并启动所有服务。首次启动可能需要几分钟时间。

### 3. 访问服务

- 交易系统指标：http://localhost:9090/metrics
- Prometheus：http://localhost:9091
- Grafana：http://localhost:3000 (默认用户名/密码：admin/admin)

### 4. 配置Grafana

首次登录Grafana后：

1. 添加Prometheus数据源：
   - 名称：Prometheus
   - 类型：Prometheus
   - URL：http://prometheus:9090
   - 访问：Server (默认)

2. 导入仪表板：
   - 点击 + > Import
   - 上传仪表板JSON或使用ID导入

## 健康检查和自动恢复

系统配置了健康检查机制，可以自动检测和恢复故障：

1. **健康检查** - 每30秒检查一次`/metrics`端点
2. **自动重启** - 服务失败时自动重启
3. **部署策略** - 更新时先启动新实例再停止旧实例

## 升级系统

### 自动升级

使用持续集成/持续部署(CI/CD)流程可以实现自动升级：

1. 在CI/CD系统中添加构建和部署步骤
2. 触发部署时运行：

```bash
# 拉取最新代码
git pull

# 重建并启动更新后的容器
docker-compose up -d --build
```

### 手动升级

1. 拉取最新代码：

```bash
git pull
```

2. 重建并启动服务：

```bash
docker-compose up -d --build
```

Docker Compose配置了`update_config`，会先启动新版本服务，验证健康后再停止旧版本，实现零停机升级。

## 日志和监控

### 查看日志

```bash
# 查看交易系统日志
docker-compose logs -f trading-system

# 查看所有服务日志
docker-compose logs -f
```

日志文件也会挂载到宿主机的`logs`目录。

### 监控指标

关键监控指标：

1. `trading_trade_count_total` - 交易计数
2. `trading_error_count_total` - 错误计数
3. `trading_heartbeat_age_seconds` - 心跳年龄

可在Prometheus或Grafana中查看这些指标。

## 故障排除

### 容器无法启动

检查日志：

```bash
docker-compose logs trading-system
```

常见问题：

1. 端口冲突 - 修改`docker-compose.yml`中的端口映射
2. 配置错误 - 检查`config.yaml`是否正确

### 健康检查失败

检查健康状态：

```bash
docker inspect --format "{{json .State.Health }}" trading-system
```

可能的解决方法：

1. 检查监控模块是否正常运行
2. 检查端口是否正确暴露
3. 尝试手动重启容器：`docker-compose restart trading-system`

## 数据持久化

以下数据是持久化的：

1. **配置文件** - 挂载为卷
2. **日志文件** - 挂载到宿主机的`logs`目录
3. **Prometheus数据** - 存储在命名卷中
4. **Grafana数据** - 存储在命名卷中

卷数据不会在容器重启或升级时丢失。

## 生产环境最佳实践

1. **安全性** - 修改默认密码，限制网络访问
2. **备份** - 定期备份配置和数据卷
3. **资源限制** - 在`docker-compose.yml`中添加资源限制：

```yaml
trading-system:
  # ... 其他配置 ...
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

4. **监控告警** - 配置Grafana告警通知到邮件或Slack 