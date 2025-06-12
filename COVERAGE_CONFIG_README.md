# 覆盖率配置文档

## 概述

本项目已配置完整的代码覆盖率测试，确保 `legacy/` 目录下的测试备份和回归测试文件被完全排除在覆盖率统计之外。

## 配置文件

### 1. `.coveragerc`
主要的覆盖率配置文件，包含：
- **源码目录**: `src/`
- **排除规则**: 完全排除 `legacy/` 目录及所有包含 'legacy' 的文件
- **报告格式**: 支持终端、HTML、XML 多种格式

### 2. `pyproject.toml`
现代化的 TOML 格式配置，与 `.coveragerc` 保持一致：
```toml
[tool.coverage.run]
source = ["src"]
omit = [
    "*/legacy/*",
    "legacy/*", 
    "*legacy*",
    # ... 其他排除规则
]
```

## 排除规则详解

### Legacy 目录排除
- `*/legacy/*` - 排除任何路径下的 legacy 目录
- `legacy/*` - 排除根目录下的 legacy 目录
- `*legacy*` - 排除任何包含 'legacy' 的文件/目录

### 其他排除项
- 测试文件 (`*/tests/*`, `*/test_*`)
- 构建产物 (`*/build/*`, `*/dist/*`)
- 虚拟环境 (`*/venv/*`, `*/.venv/*`)
- 包缓存 (`*/__pycache__/*`)

## 使用方法

### 本地运行
```bash
# 使用 .coveragerc 配置
python -m pytest --cov=src --cov-config=.coveragerc --cov-report=term-missing

# 生成 HTML 报告
python -m pytest --cov=src --cov-config=.coveragerc --cov-report=html:htmlcov

# 生成 XML 报告（CI 使用）
python -m pytest --cov=src --cov-config=.coveragerc --cov-report=xml:coverage.xml
```

### CI/CD 集成
GitHub Actions 自动使用配置文件：
- 运行测试时自动生成覆盖率报告
- 上传到 Codecov 进行跟踪
- 排除规则确保只统计活跃代码

## 验证排除规则

确认 `legacy/` 目录被正确排除：
```bash
# 运行覆盖率测试
python -m pytest tests/test_simple_coverage.py::TestSimpleCoverage::test_calculate_position_size_edge_cases -v --cov=src --cov-config=.coveragerc --cov-report=term-missing

# 检查报告中是否包含 legacy 文件（应该没有结果）
python -m pytest --cov=src --cov-config=.coveragerc --cov-report=term-missing | grep -i legacy
```

## 目录结构影响

### 包含在覆盖率中
- `src/` - 所有源码
- 仅活跃的、正在维护的代码

### 排除在覆盖率外
- `legacy/tests_backup_before_cleanup/` - 清理前的测试备份
- `legacy/tests_regression/` - 回归测试存档
- 所有测试文件、构建产物等

## 好处

1. **准确的覆盖率指标**: 只统计活跃代码，不被历史文件影响
2. **清洁的报告**: 覆盖率报告专注于当前需要关注的代码
3. **CI/CD 一致性**: 本地和 CI 环境使用相同的排除规则
4. **维护性**: 配置文件版本控制，团队共享一致的标准

## 维护

当项目结构变化时，更新覆盖率配置：
1. 修改 `.coveragerc` 和 `pyproject.toml` 中的排除规则
2. 本地测试验证配置正确性
3. 提交配置更改
4. 确认 CI 使用新配置 