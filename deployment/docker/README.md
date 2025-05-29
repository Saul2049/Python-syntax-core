# Docker 部署指南

## 📋 概述

本目录包含用于容器化部署交易系统的Docker配置文件。

## 🗂️ 文件结构

```
deployment/docker/
├── Dockerfile              # Docker镜像构建文件
├── docker-compose.yml      # 多容器编排配置
├── validate-config.sh      # 配置验证脚本
└── README.md               # 本文档
```

## 🚀 快速开始

### 1. 验证配置

在构建之前，运行验证脚本确保所有配置正确：

```bash
# 从项目根目录运行
./deployment/docker/validate-config.sh
```

### 2. 准备配置文件

```bash
# 复制配置模板
cp scripts/config.yaml.template config.yaml

# 根据需要编辑配置
vim config.yaml
```

### 3. 构建和运行

#### 方式一：使用docker-compose（推荐）

```bash
cd deployment/docker
docker-compose up -d
```

#### 方式二：手动构建

```bash
# 构建镜像
docker build -f deployment/docker/Dockerfile -t trading-system .

# 运行容器
docker run -d \
  --name trading-system \
  -p 9090:9090 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  -v $(pwd)/logs:/app/logs \
  trading-system
```

## 🔧 配置说明

### Dockerfile 配置

- **基础镜像**: `python:3.9-slim`
- **工作目录**: `/app`
- **暴露端口**: `9090` (监控端口)
- **启动命令**: `scripts/testing/stability_test.py`

### docker-compose 服务

1. **trading-system**: 主要交易系统
2. **prometheus**: 指标收集
3. **grafana**: 监控面板

### 环境变量

- `MONITORING_PORT`: 监控端口 (默认: 9090)
- `PYTHONUNBUFFERED`: Python输出缓冲 (设为1)
- `PYTHONDONTWRITEBYTECODE`: 禁止生成.pyc文件

## 📊 监控和健康检查

### 健康检查

容器包含自动健康检查：
- **检查间隔**: 30秒
- **超时时间**: 10秒
- **重试次数**: 3次
- **启动等待**: 30秒

### 监控端点

- **应用监控**: http://localhost:9090/metrics
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)

## 🔍 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看日志
   docker-compose logs trading-system
   
   # 检查配置
   ./deployment/docker/validate-config.sh
   ```

2. **健康检查失败**
   ```bash
   # 检查容器状态
   docker ps
   
   # 测试监控端点
   curl http://localhost:9090/metrics
   ```

3. **配置文件问题**
   ```bash
   # 确保配置文件存在
   ls -la config.yaml
   
   # 检查配置语法
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

### 调试模式

运行调试版本：

```bash
# 交互式运行
docker run -it --rm \
  -v $(pwd)/config.yaml:/app/config.yaml \
  trading-system \
  python scripts/testing/stability_test.py --help
```

## 🔄 更新和维护

### 更新镜像

```bash
# 重新构建
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

### 清理资源

```bash
# 停止所有服务
docker-compose down

# 清理未使用的镜像
docker image prune -f

# 清理所有资源
docker-compose down -v --rmi all
```

## 📝 开发说明

### 本地开发

对于开发环境，建议直接运行Python脚本：

```bash
python scripts/testing/stability_test.py \
  --config-yaml config.yaml \
  --days 1 \
  --mock-only
```

### CI/CD 集成

GitHub Actions会自动：
1. 构建Docker镜像
2. 推送到GitHub Container Registry
3. 运行容器测试

## 🔐 安全注意事项

1. **生产环境**：
   - 使用非root用户运行容器
   - 限制容器资源使用
   - 定期更新基础镜像

2. **配置管理**：
   - 不要在镜像中包含敏感信息
   - 使用环境变量或secrets管理密钥
   - 定期轮换API密钥

3. **网络安全**：
   - 限制容器网络访问
   - 使用防火墙规则
   - 启用TLS加密

## 📞 支持

如果遇到问题，请：
1. 运行 `validate-config.sh` 检查配置
2. 查看容器日志
3. 检查GitHub Issues
4. 联系维护团队 