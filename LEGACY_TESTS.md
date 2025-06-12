# Legacy Test Suites 管理说明

| 目录 | 角色 | 默认收集 | 触发方式 |
|------|------|-----------|-----------|
| `tests/` | 主单元 / 集成测试 | ✅ | `pytest` (CI fast) |
| `tests_regression/old_20250606/` | 扩展回归测试（兼容性、边缘场景） | ❌ (已在 `pytest.ini` ignore) | 手动：`pytest tests_regression/old_20250606` |

### 清理历史
* 2025-06-11 — 移除 `archive_backup_20250106`（14 files），无独特场景。
* 2025-06-11 — 将 `archive_backup_20250606/old_tests` 迁至 `tests_regression/old_20250606`，仅在需要时执行。

### 运行示例
```bash
# 日常开发（最快）：
pytest -q

# 完整回归：
pytest -q tests tests_regression/old_20250606 -m "not slow"
``` 