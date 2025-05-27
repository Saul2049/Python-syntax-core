# 📚 Python交易框架文档中心

> **版本**: v5.0 | **状态**: 活跃维护 | **最后更新**: 2024年12月

欢迎来到Python交易框架的文档中心！这里提供完整的技术文档、使用指南和参考资料。

## 🚀 快速开始

- [📖 README](../README.md) - 项目概览和快速安装
- [🔧 安装指南](guides/MONITORING.md) - 详细安装和配置步骤
- [🌅 晨间指南](guides/morning_guide.md) - 日常操作指南

## 📋 文档导航

### 📖 使用指南 (Guides)
> 面向使用者的实用指南和操作手册

- [📊 监控系统指南](guides/MONITORING.md) - 系统监控和告警配置
- [🔧 快速开始推送指南](guides/QUICK_START_PUSH_GUIDE.md) - 5分钟掌握推送前检查
- [🛠️ Git推送最佳实践](guides/GIT_PUSH_BEST_PRACTICES.md) - 推送前完整检查清单
- [🧠 内存优化指南](guides/M5_MEMORY_OPTIMIZATION_GUIDE.md) - M5阶段内存优化实践
- [🚨 事件处理手册](guides/M4_INCIDENT_RUNBOOK.md) - M4事件响应和故障排除
- [💾 内存优化实践](guides/MEMORY_OPTIM.md) - 内存管理最佳实践
- [🌅 日常操作指南](guides/morning_guide.md) - 每日维护和检查流程

### 🏗️ 设计文档 (Design)
> 架构设计、决策记录和发展规划

- [🏛️ 系统架构](design/ARCHITECTURE.md) - 整体架构设计和组件关系
- [📋 项目阶段规划](design/PROJECT_PHASES.md) - 开发阶段和里程碑
- [🗺️ 开发路线图](design/DEVELOPMENT_ROADMAP.md) - 未来发展计划
- [📈 专业交易改进计划](design/PROFESSIONAL_TRADING_IMPROVEMENT_PLAN.md) - 交易系统专业化升级
- [🔧 项目结构优化计划](design/PROJECT_STRUCTURE_OPTIMIZATION_PLAN.md) - 代码结构重构规划

### 📚 参考文档 (References)
> API文档、配置参考和技术规范

- [🔌 API文档](references/API_DOCUMENTATION.md) - 完整的API接口文档
- [🐳 Docker部署](references/DOCKER_DEPLOYMENT.md) - 容器化部署指南
- [⚙️ CI/CD配置](references/CI_CD.md) - 持续集成和部署配置
- [📡 数据源配置](references/DATA_SOURCES.md) - 数据源接入和配置

### 🎯 发布记录 (Releases)
> 版本发布记录和重要里程碑

- [✅ 代码质量完成报告](releases/FINAL_CODE_QUALITY_COMPLETION_REPORT.md) - 最新代码质量优化成果

## 📦 项目结构概览

```
Python Trading Framework/
├── src/                    # 核心源代码
│   ├── core/              # 核心交易引擎
│   ├── strategies/        # 交易策略
│   ├── monitoring/        # 监控系统
│   └── brokers/          # 经纪商接口
├── tests/                 # 测试套件
├── docs/                  # 📚 文档中心 (当前位置)
├── scripts/              # 工具脚本
└── examples/             # 示例代码
```

## 🔍 文档搜索和导航

### 按主题查找
- **🚀 快速上手**: [README](../README.md) → [快速推送指南](guides/QUICK_START_PUSH_GUIDE.md)
- **🏗️ 架构理解**: [系统架构](design/ARCHITECTURE.md) → [项目阶段](design/PROJECT_PHASES.md)
- **🔧 开发配置**: [推送指南](guides/GIT_PUSH_BEST_PRACTICES.md) → [CI/CD](references/CI_CD.md)
- **📊 监控运维**: [监控指南](guides/MONITORING.md) → [事件手册](guides/M4_INCIDENT_RUNBOOK.md)

### 按角色查找
- **👨‍💻 开发者**: [架构文档](design/ARCHITECTURE.md) + [API文档](references/API_DOCUMENTATION.md)
- **🔧 运维人员**: [监控指南](guides/MONITORING.md) + [事件手册](guides/M4_INCIDENT_RUNBOOK.md)
- **📈 交易员**: [专业交易计划](design/PROFESSIONAL_TRADING_IMPROVEMENT_PLAN.md)
- **🆕 新用户**: [README](../README.md) + [晨间指南](guides/morning_guide.md)

## 📈 版本信息

| 组件 | 版本 | 状态 | 文档覆盖率 |
|------|------|------|-----------|
| 核心引擎 | v5.0 | ✅ 稳定 | 95% |
| 监控系统 | v4.0 | ✅ 稳定 | 90% |
| 策略模块 | v3.0 | ✅ 稳定 | 85% |
| API接口 | v2.0 | ✅ 稳定 | 100% |

## 🗂️ 历史文档归档

历史版本和已完成项目的文档已移至 [归档目录](archives/2024-legacy/)，包括：
- 各阶段优化完成报告
- 历史版本的技术文档
- 已废弃的配置和指南

## 🤝 贡献指南

- 📝 文档更新请遵循 [代码风格指南](../CODE_STYLE.md)
- 🔄 重大变更需要更新相应的设计文档
- ✅ 新功能需要同步更新API文档和使用指南

## 📞 支持和反馈

- 🐛 问题报告: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 讨论交流: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 直接联系: [项目维护者](mailto:maintainer@example.com)

---

**📅 最后更新**: 2024年12月19日  
**📝 维护者**: Python交易框架团队  
**�� 许可证**: MIT License 