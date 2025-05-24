"""
网络模块 - 向后兼容导入
(Network Module - Backward Compatible Imports)

⚠️ 已重构提示 (Refactoring Notice):
此模块已被拆分为多个专门模块以提高代码质量。
推荐直接使用新的模块结构：

- src.core.network.retry_manager - 重试管理
- src.core.network.state_manager - 状态管理
- src.core.network.client - 网络客户端
- src.core.network.decorators - 高级装饰器

为了保持向后兼容性，此文件重新导出了重构后的功能。
"""

# 向后兼容导入 - 客户端相关
from src.core.network.client import NetworkClient

# 向后兼容导入 - 装饰器相关
from src.core.network.decorators import with_retry

# 向后兼容导入 - 重试相关
from src.core.network.retry_manager import (
    DEFAULT_RETRY_CONFIG,
    calculate_retry_delay,
)

# 向后兼容导入 - 状态管理相关
from src.core.network.state_manager import (
    load_state,
    save_state,
)

# 保持原有接口
__all__ = [
    "calculate_retry_delay",
    "DEFAULT_RETRY_CONFIG",
    "save_state",
    "load_state",
    "with_retry",
    "NetworkClient",
]

from src.core.network.client import create_simple_client as create_network_client

# 为了完全兼容，保留一些别名
# 这样原有的导入语句仍能正常工作
from src.core.network.state_manager import get_global_state_manager


# 便捷函数向后兼容
def create_default_client():
    """创建默认网络客户端 - 向后兼容"""
    return create_network_client()


def get_default_state_manager():
    """获取默认状态管理器 - 向后兼容"""
    return get_global_state_manager()
