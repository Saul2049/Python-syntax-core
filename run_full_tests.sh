#!/bin/bash
# 完整测试 - 包含所有测试

echo "🧪 运行完整测试套件..."

pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term-missing \
    --durations=10 \
    -v

echo "✅ 完整测试完成"
