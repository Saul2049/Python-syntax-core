# 📁 Archive Directory (归档目录)

⚠️ **重要说明**: 此目录包含的是**已弃用、历史文档、临时文件**等非主流程代码，仅供参考，后续将逐步删除。

## 📂 目录结构说明

### 📄 `/docs/` - 历史文档
包含项目开发过程中的历史文档和已完成的任务报告：
- `*_2024-12-20.md` - 2024年12月20日的各种状态报告
- `*_COMPLETED.md` - 已完成任务的详细报告
- `REFACTORING_PLAN.md` - 历史重构计划
- `STRUCTURE_IMPROVEMENTS_PLAN.md` - 结构改进计划

### 📊 `/coverage_reports/` - 覆盖率报告
包含代码覆盖率分析的历史文件：
- `.coverage*` - 覆盖率数据文件
- `htmlcov*/` - HTML格式的覆盖率报告
- `COVERAGE_ENHANCEMENT_REPORT.md` - 覆盖率提升报告

### 🧪 `/old_tests/` - 历史测试文件
包含已归档的大型测试文件（主要是覆盖率测试）：
- `test_*coverage*.py` - 覆盖率专用测试
- `test_*comprehensive*.py` - 综合测试文件
- `test_*enhanced*.py` - 增强测试文件
- `test_*100_percent*.py` - 100%覆盖率冲刺测试

### 📁 `/temp_files/` - 临时文件
包含开发过程中产生的临时文件：
- `tmp*.csv` - 临时CSV文件
- `grid_results.csv` - 网格搜索结果
- `position_state.json` - 仓位状态文件
- `security_report.json` - 安全报告

### 📜 `/logs/` - 历史日志
包含测试和开发过程中的日志文件：
- `stability_test.log` - 稳定性测试日志
- 其他测试日志文件

## ⚠️ 使用注意事项

1. **不要依赖这些文件**: 归档文件可能包含过时的API或已废弃的功能
2. **仅供参考**: 这些文件记录了项目的发展历程，可用于了解历史决策
3. **将被删除**: 后续版本中这些文件将被逐步清理
4. **需要功能请查看主代码**: 如需相关功能，请查看 `src/` 和 `tests/` 目录中的最新代码

## 🔗 主要目录指引

如果你是新开发者，请优先查看：
- [`../src/`](../src/) - 主要业务代码
- [`../tests/`](../tests/) - 当前测试套件
- [`../README.md`](../README.md) - 项目主要文档
- [`../docs/`](../docs/) - 当前文档

---

**创建时间**: 2024-12-20  
**目的**: 项目结构整理和开发效率提升 