---
title: 快速开始 - Git推送指南
description: 5分钟掌握Python交易框架的推送前检查流程
version: v5.0
status: active
last_updated: 2024-12-19
category: guide
---

# ⚡ 快速开始 - Git推送指南

> **5分钟掌握推送前检查，避免CI失败和代码质量问题**

## 🚀 一键式推送检查

### 📦 完整检查 (推荐)
```bash
# 运行完整的推送前验证
make pre-push-check
```

### ⚡ 快速检查 (紧急情况)
```bash
# 最小化检查，适合紧急修复
make pre-push-quick
```

### 📚 交互式演示 (学习用)
```bash
# 查看完整的推送流程演示
make pre-push-demo

# 快速演示版本
make pre-push-demo-quick
```

---

## 🛠️ 标准推送工作流

### 1️⃣ 日常开发流程
```bash
# 开始工作前同步
git fetch origin && git rebase origin/main

# 开发完成后检查
make pre-push-check

# 提交和推送
git add .
git commit -m "feat(strategy): add new momentum indicator"
git push -u origin feature/momentum-indicator
```

### 2️⃣ 紧急修复流程
```bash
# 快速检查
make pre-push-quick

# 紧急提交
git add .
git commit -m "fix(core): critical memory leak"
git push -u origin hotfix/memory-leak
```

---

## 📋 检查项目说明

| 检查项 | 命令 | 耗时 | 说明 |
|--------|------|------|------|
| **单元测试** | `make test-quick` | 15-30s | 验证核心功能正常 |
| **代码质量** | `make lint` | 20-40s | ruff + black + isort + mypy |
| **内存健康** | `make mem-health` | 10s | 检查内存使用和GC状态 |
| **Pre-commit** | `pre-commit run --all-files` | 30-60s | 格式化和安全检查 |

---

## 🎯 分支策略

### 🔥 主分支 (`main`/`develop`)
```bash
# 必须通过所有检查
make test && make w2-validate-fast && make lint
```

### 🚀 功能分支 (`feature/*`)
```bash
# 标准检查即可
make pre-push-check
```

### 🚨 热修复分支 (`hotfix/*`)
```bash
# 快速但严格
make pre-push-quick && make health-check
```

---

## ❌ 常见问题解决

### 🧪 测试失败
```bash
# 查看详细错误
make test-quick -v

# 单独运行失败的测试
python -m pytest tests/test_specific.py::test_function -v
```

### 🎨 代码格式问题
```bash
# 自动修复格式
make format

# 重新检查
make lint
```

### 🔧 Pre-commit失败
```bash
# 重新安装钩子
pre-commit uninstall && pre-commit install

# 手动运行修复
pre-commit run --all-files
```

### 🧠 内存检查失败
```bash
# 详细内存分析
make mem-snapshot

# 快速内存优化验证
make m5-quick
```

---

## 🎓 提交信息规范

### ✅ 正确格式
```bash
git commit -m "feat(core): add RSI indicator calculation"
git commit -m "fix(monitoring): resolve memory leak in metrics collector"
git commit -m "docs(api): update trading strategy documentation"
```

### ❌ 错误格式
```bash
git commit -m "fixed bug"           # 太简单
git commit -m "Added new feature"   # 不符合规范
git commit -m "WIP stuff"           # 临时提交不应推送
```

### 🏷️ 类型标签
- `feat` - 新功能
- `fix` - 错误修复  
- `docs` - 文档更新
- `style` - 代码格式
- `refactor` - 重构
- `perf` - 性能优化
- `test` - 测试相关
- `chore` - 构建/工具

---

## 🔗 相关资源

- **完整指南**: [GIT_PUSH_BEST_PRACTICES.md](GIT_PUSH_BEST_PRACTICES.md)
- **监控指南**: [MONITORING.md](MONITORING.md)
- **M5内存优化**: [M5_MEMORY_OPTIMIZATION_GUIDE.md](M5_MEMORY_OPTIMIZATION_GUIDE.md)
- **项目架构**: [../design/ARCHITECTURE.md](../design/ARCHITECTURE.md)

---

## 💡 专业提示

1. **每日同步**: 开始工作前运行 `git fetch && git rebase`
2. **小步提交**: 每个功能点单独提交，便于回滚
3. **测试驱动**: 先写测试，再实现功能
4. **性能意识**: 关注M5内存优化指标
5. **文档同步**: 代码变更时同步更新文档

---

**📅 最后更新**: 2024年12月19日  
**🎯 适用版本**: v5.0+  
**⏱️ 阅读时间**: 5分钟 