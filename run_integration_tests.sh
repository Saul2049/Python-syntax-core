#!/bin/bash
# 集成测试 - 只运行集成测试

echo "🔗 运行集成测试..."

pytest tests/ \
    -m "integration" \
    --tb=short \
    -v

echo "✅ 集成测试完成"
