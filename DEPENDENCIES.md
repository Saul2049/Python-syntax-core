# 项目依赖管理

本项目使用两个不同的依赖文件管理运行时依赖和开发依赖，确保安装过程简单高效。

## 依赖文件

1. **requirements.txt** - 仅包含运行应用所需的依赖
   - pandas, numpy, matplotlib 等核心计算和可视化库
   - requests 用于API调用
   - 其他必要的运行时依赖

2. **dev-requirements.txt** - 包含开发和测试所需的所有工具
   - 自动包含 requirements.txt (通过 `-r requirements.txt`)
   - pytest 和相关插件用于测试
   - black, isort, flake8, mypy 用于代码质量控制
   - pre-commit 用于Git提交前检查

## 安装指南

### 仅运行项目（生产环境）

```bash
pip install -r requirements.txt
```

### 开发环境（包含所有工具）

```bash
pip install -r dev-requirements.txt
```

### 安装为包（可编辑模式）

```bash
pip install -e .
```

## CI/CD 集成

GitHub Actions 工作流配置为使用 `dev-requirements.txt`，确保测试环境包含所有必要的工具。

## 依赖版本更新

当需要更新依赖版本时，请同时更新以下文件：

1. requirements.txt
2. setup.py 中的 install_requires
3. pyproject.toml (如果使用)

这样确保无论哪种安装方式都能获得一致的依赖版本。 