FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装Python依赖
# 明确指定pytest版本，避免冲突
RUN pip install --no-cache-dir 'pytest>=7.4.0,<8.0.0' && \
    pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MONITORING_PORT=9090

# 创建日志目录
RUN mkdir -p /app/logs/stability_test

# 暴露监控端口
EXPOSE ${MONITORING_PORT}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${MONITORING_PORT}/metrics || exit 1

# 启动命令
CMD ["python", "scripts/testing/stability_test.py", "--monitoring-port", "9090", "--days", "30", "--config-yaml", "config.yaml"] 