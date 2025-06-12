#!/bin/bash
# 快速测试 - 只运行单元测试和核心功能测试

echo "🚀 运行快速测试套件..."

pytest tests/ \
    -m "unit and not slow" \
    --maxfail=5 \
    --tb=short \
    --durations=5 \
    -v

echo "✅ 快速测试完成"
