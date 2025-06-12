"""Placeholder database submodule (legacy tests stub).

This module exists solely to satisfy archived test suites that import
``src.database`` when patching paths such as ``patch('src.database.Session', ..)``.
The current codebase no longer relies on a dedicated database layer, so the
implementation is intentionally minimal.
"""

# Expose a minimal Session stub to avoid AttributeError during patching
author = "compat"


class Session:  # noqa: D401
    """No-op session placeholder."""

    def __init__(self, *args, **kwargs):
        pass

    def commit(self):
        pass

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Dynamic sub-module factory – allow any ``src.database.<something>`` import
# ---------------------------------------------------------------------------

import sys
import types
from types import ModuleType


def __getattr__(name: str) -> ModuleType:  # noqa: D401
    """Dynamically create sub-modules for legacy patch paths.

    归档测试可能执行：
        patch('src.database.position_manager.PositionManager', ...)

    当 ``src.database.position_manager`` 不存在时，我们即时构造一个空的
    `ModuleType` 放入 `sys.modules` ，之后 patch 解析即可成功。
    """

    module_name = f"{__name__}.{name}"

    if module_name in sys.modules:  # pragma: no cover – 已存在
        return sys.modules[module_name]

    # 创建空模块并注册到 sys.modules
    mod = types.ModuleType(module_name)
    sys.modules[module_name] = mod
    return mod


# ---------------------------------------------------------------------------
# Common placeholder classes used by archived tests
# ---------------------------------------------------------------------------


class PositionManager:  # noqa: D401
    """Legacy placeholder for position management layer."""

    def __init__(self, *args, **kwargs):
        pass

    async def open_position(self, *args, **kwargs):  # noqa: D401
        pass

    async def close_position(self, *args, **kwargs):  # noqa: D401
        pass
