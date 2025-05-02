# 代码风格指南
本项目使用统一的代码风格，以保持代码的可读性和一致性。

## 格式化工具

我们使用 [Black](https://github.com/psf/black) 作为Python代码的自动格式化工具，行长度设置为120字符。

## 编辑器设置

使用VS Code时，本项目已包含自动格式化设置。请确保安装Python扩展和Black。

## 手动格式化

如果自动格式化不可用，请使用命令：
```bash
black -l 120 your_file.py
```
