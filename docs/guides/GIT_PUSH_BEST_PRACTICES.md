---
title: Git推送前最佳实践清单
description: Python交易框架项目的完整推送前检查流程
version: v5.0
status: active
last_updated: 2024-12-19
category: guide
---

# 🛠️ Git推送前最佳实践清单

> **针对 Python交易框架项目（M5内存优化 + CI/CD + 性能守护）**

## 📋 完整检查清单

| 步骤 | 命令/动作 | 目的 & 通过标准 | 预期耗时 | 必需性 |
|------|-----------|----------------|----------|--------|
| **1. 同步远端** | `git fetch origin` | 获取最新远端状态，避免冲突 | 5s | ✅ 必需 |
| **2. 变基整理** | `git rebase origin/main`<br>（或 `origin/develop`） | 保持线性历史，解决冲突<br>**禁止**产生多余merge提交 | 10-30s | ✅ 必需 |
| **3. 快速单元测试** | `make test-quick` | 核心功能验证<br>**标准**: 全部通过，耗时 ≤ 30s | 15-30s | ✅ 必需 |
| **4. 代码质量检查** | `make lint` | ruff + black + isort + mypy<br>**标准**: 0 Error, 0 Warning | 20-40s | ✅ 必需 |
| **5. M5内存快检**<br>（核心分支） | `make w2-validate-fast` | GC性能 + 内存健康<br>**标准**: P95暂停 ≤ 50ms | 60s | 🔥 主分支必需 |
| **6. 完整测试套件**<br>（可选） | `make test` | 全量测试覆盖<br>**标准**: 429+ passed, 5 skipped | 2-5min | 🟡 重要PR |
| **7. 提交信息规范** | `git commit -m "feat(core): 简述"`<br>遵循 Conventional Commits | 清晰的变更说明<br>格式: `type(scope): description` | 30s | ✅ 必需 |
| **8. Pre-commit验证** | `pre-commit run --all-files` | 自动格式化 + 代码检查<br>**标准**: 所有钩子通过 | 30-60s | ✅ 必需 |
| **9. 推送分支** | `git push -u origin <branch>` | 触发CI/CD流水线 | 10s | ✅ 必需 |
| **10. CI状态确认** | 检查GitHub Actions | **标准**: 🟢 CI + 🟢 Performance Guard | 3-5min | ✅ 必需 |

---

## 🚀 快速命令序列

### 📦 标准开发流程
```bash
# 1-4: 基础检查 (约2分钟)
git fetch origin && git rebase origin/main
make test-quick && make lint

# 5: M5内存检查 (主分支/重要PR)
make w2-validate-fast

# 6-8: 提交和验证
git add . && git commit -m "feat(strategy): add momentum indicator"
pre-commit run --all-files

# 9: 推送
git push -u origin feature/momentum-strategy
```

### ⚡ 超快验证模式 (紧急修复)
```bash
# 最小化检查 (约1分钟)
git fetch origin && git rebase origin/main
make test-quick FAST=1 && make lint
git add . && git commit -m "fix(core): critical bug fix"
git push -u origin hotfix/critical-fix
```

---

## 🎯 分支策略与检查级别

### 🔥 主分支 (`main`/`develop`)
**必需检查**: 全部10步
```bash
# 完整流程 - 不可跳过
make test && make w2-validate-fast && make lint
```

### 🚀 功能分支 (`feature/*`)
**必需检查**: 步骤1-4, 7-10
```bash
# 标准流程 - 可选M5检查
make test-quick && make lint
```

### 🚨 热修复分支 (`hotfix/*`)
**必需检查**: 步骤1-4, 7-10 + 额外验证
```bash
# 快速但严格
make test-quick && make lint && make health-check
```

---

## 🛡️ 关键约束与规则

### ❌ 严格禁止
1. **大文件推送**: >10MB 文件必须使用 Git LFS 或放入 `storage/`
2. **跳过pre-commit**: 远端CI会二次检查，本地不过远端必失败
3. **强制推送**: `git push --force` 仅限个人分支，禁止用于共享分支
4. **未测试代码**: 任何代码变更必须通过 `make test-quick`

### ⚠️ 特殊情况处理
```bash
# 仅文档更新 - 可跳过CI
git commit -m "docs: update README [skip ci]"

# 临时提交 - 后续需要squash
git commit -m "wip: temporary checkpoint"
# 推送前必须: git rebase -i HEAD~n 整理提交历史
```

---

## 🔧 工具配置验证

### 📝 Pre-commit钩子状态
```bash
# 检查pre-commit安装状态
pre-commit --version
ls -la .git/hooks/pre-commit

# 手动运行所有钩子
pre-commit run --all-files
```

### 🧪 测试环境验证
```bash
# 验证测试环境
python -m pytest --version
make test-quick --dry-run

# 验证代码质量工具
black --version && isort --version && ruff --version
```

---

## 📊 CI/CD流水线说明

### 🟢 标准CI检查 (`.github/workflows/ci.yml`)
- ✅ Python 3.11 环境
- ✅ 依赖安装验证
- ✅ 代码质量检查 (black, isort, flake8)
- ✅ 完整测试套件

### 🚀 性能回归守护 (`.github/workflows/perf-regression.yml`)
- ✅ M4性能基准测试 (120s)
- ✅ P95延迟断言 (≤ 250ms)
- ✅ CPU使用率检查
- ✅ 自动PR评论报告

### 🌙 夜间健康检查 (`.github/workflows/nightly-health.yml`)
- ✅ 完整系统健康扫描
- ✅ M5内存优化验证
- ✅ 长期稳定性测试

---

## 🎯 提交信息规范

### 📝 Conventional Commits格式
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### 🏷️ 类型标签
| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat(strategy): add RSI indicator` |
| `fix` | 错误修复 | `fix(core): resolve memory leak in signal processor` |
| `docs` | 文档更新 | `docs(api): update trading API documentation` |
| `style` | 代码格式 | `style: apply black formatting` |
| `refactor` | 重构 | `refactor(monitoring): simplify metrics collection` |
| `perf` | 性能优化 | `perf(gc): optimize garbage collection thresholds` |
| `test` | 测试相关 | `test(unit): add tests for signal validation` |
| `chore` | 构建/工具 | `chore(deps): update numpy to 1.25.2` |

### 🎯 作用域 (Scope)
- `core` - 核心交易引擎
- `strategy` - 交易策略
- `monitoring` - 监控系统
- `broker` - 经纪商接口
- `api` - API接口
- `docs` - 文档
- `test` - 测试
- `ci` - CI/CD

---

## 🚨 故障排查

### ❌ 常见问题与解决方案

#### 1. Pre-commit失败
```bash
# 重新安装pre-commit钩子
pre-commit uninstall && pre-commit install

# 跳过特定钩子 (仅紧急情况)
SKIP=black,isort git commit -m "emergency fix"
```

#### 2. 测试失败
```bash
# 详细测试输出
make test-quick -v

# 单独运行失败的测试
python -m pytest tests/test_specific.py::test_function -v
```

#### 3. 内存检查失败
```bash
# 快速内存健康检查
make mem-health

# 详细内存分析
make mem-snapshot
```

#### 4. 性能回归
```bash
# 本地性能基准
make perf-benchmark

# M5快速验证
make m5-quick
```

---

## 📈 最佳实践建议

### 🔄 日常开发工作流
1. **小步提交**: 每个功能点单独提交，便于回滚和审查
2. **分支命名**: 使用描述性名称 `feature/add-bollinger-bands`
3. **定期同步**: 每日开始前 `git fetch && git rebase`
4. **测试驱动**: 先写测试，再实现功能

### 🎯 团队协作
1. **PR模板**: 使用标准化的PR描述模板
2. **代码审查**: 重要变更必须经过代码审查
3. **文档同步**: 代码变更同步更新相关文档
4. **性能意识**: 关注性能影响，特别是M5内存优化

### 📊 质量监控
1. **覆盖率追踪**: 保持测试覆盖率 > 85%
2. **性能基线**: 定期更新性能基线数据
3. **技术债务**: 定期清理代码质量问题
4. **依赖更新**: 定期更新依赖包版本

---

## 🔗 相关资源

- **项目README**: [../README.md](../README.md)
- **监控指南**: [MONITORING.md](MONITORING.md)
- **M5内存优化**: [M5_MEMORY_OPTIMIZATION_GUIDE.md](M5_MEMORY_OPTIMIZATION_GUIDE.md)
- **架构文档**: [../design/ARCHITECTURE.md](../design/ARCHITECTURE.md)
- **CI/CD配置**: [../references/CI_CD.md](../references/CI_CD.md)

---

**📅 最后更新**: 2024年12月19日  
**📝 维护者**: DevOps团队  
**🎯 适用版本**: v5.0+  
**✅ 状态**: 活跃维护 