"""
状态管理模块 (State Manager Module)

提供状态持久化功能，包括：
- JSON状态文件操作
- 状态保存和加载
- 状态清理和管理
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src import utils

# 设置日志记录器
logger = logging.getLogger(__name__)


def save_state(state_path: Path, state_data: Dict[str, Any]) -> bool:
    """
    保存状态到JSON文件。
    Save state to JSON file.

    参数 (Parameters):
        state_path: 状态文件路径 (State file path)
        state_data: 要保存的状态数据 (State data to save)

    返回 (Returns):
        bool: 保存是否成功 (Whether save was successful)
    """
    try:
        # 确保目录存在
        state_path.parent.mkdir(parents=True, exist_ok=True)

        # 添加时间戳
        state_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 写入JSON文件
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"State saved to {state_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    从JSON文件加载状态。
    Load state from JSON file.

    参数 (Parameters):
        state_path: 状态文件路径 (State file path)

    返回 (Returns):
        Dict[str, Any]: 加载的状态数据，如果失败则返回空字典
        (Loaded state data, returns empty dict if failed)
    """
    try:
        if not state_path.exists():
            logger.debug(f"State file not found: {state_path}")
            return {}

        with open(state_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        logger.debug(f"State loaded from {state_path}")
        return state_data

    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return {}


def clear_state(state_path: Path) -> bool:
    """
    清除状态文件。
    Clear state file.

    参数 (Parameters):
        state_path: 状态文件路径 (State file path)

    返回 (Returns):
        bool: 清除是否成功 (Whether clear was successful)
    """
    try:
        if state_path.exists():
            state_path.unlink()
            logger.debug(f"State cleared: {state_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to clear state: {e}")
        return False


class StateManager:
    """状态管理器类"""

    def __init__(self, state_dir: Optional[str] = None):
        """
        初始化状态管理器

        参数:
            state_dir: 状态文件目录，默认为None (使用默认交易目录)
        """
        self.state_dir = Path(state_dir or str(utils.get_trades_dir() / "states"))

        # 确保状态目录存在
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self, operation: str) -> Path:
        """
        获取特定操作的状态文件路径

        参数:
            operation: 操作名称

        返回:
            Path: 状态文件路径
        """
        return self.state_dir / f"{operation}_state.json"

    def save_operation_state(self, operation: str, state_data: Dict[str, Any]) -> bool:
        """
        保存操作状态

        参数:
            operation: 操作名称
            state_data: 状态数据

        返回:
            bool: 保存是否成功
        """
        state_path = self.get_state_path(operation)
        return save_state(state_path, state_data)

    def load_operation_state(self, operation: str) -> Dict[str, Any]:
        """
        加载操作状态

        参数:
            operation: 操作名称

        返回:
            Dict[str, Any]: 状态数据
        """
        state_path = self.get_state_path(operation)
        return load_state(state_path)

    def clear_operation_state(self, operation: str) -> bool:
        """
        清除操作状态

        参数:
            operation: 操作名称

        返回:
            bool: 清除是否成功
        """
        state_path = self.get_state_path(operation)
        return clear_state(state_path)

    def list_operations(self) -> list[str]:
        """
        列出所有有状态的操作

        返回:
            list[str]: 操作名称列表
        """
        try:
            operations = []
            for state_file in self.state_dir.glob("*_state.json"):
                operation_name = state_file.stem.replace("_state", "")
                operations.append(operation_name)
            return operations
        except Exception as e:
            logger.error(f"Failed to list operations: {e}")
            return []

    def cleanup_old_states(self, max_age_days: int = 7) -> int:
        """
        清理旧的状态文件

        参数:
            max_age_days: 最大保留天数

        返回:
            int: 清理的文件数量
        """
        try:
            import time

            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            cleaned_count = 0

            for state_file in self.state_dir.glob("*_state.json"):
                try:
                    file_mtime = os.path.getmtime(state_file)
                    if file_mtime < cutoff_time:
                        state_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned old state file: {state_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean state file {state_file}: {e}")

            logger.info(f"Cleaned {cleaned_count} old state files")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")
            return 0

    def get_state_summary(self) -> Dict[str, Any]:
        """
        获取状态管理器摘要信息

        返回:
            Dict[str, Any]: 摘要信息
        """
        try:
            operations = self.list_operations()
            total_files = len(list(self.state_dir.glob("*.json")))

            return {
                "state_dir": str(self.state_dir),
                "total_operations": len(operations),
                "total_files": total_files,
                "operations": operations,
                "dir_exists": self.state_dir.exists(),
                "dir_writable": (
                    os.access(self.state_dir, os.W_OK) if self.state_dir.exists() else False
                ),
            }
        except Exception as e:
            logger.error(f"Failed to get state summary: {e}")
            return {"error": str(e)}


# 全局状态管理器实例
_global_state_manager: Optional[StateManager] = None


def get_global_state_manager() -> StateManager:
    """
    获取全局状态管理器实例

    返回:
        StateManager: 状态管理器实例
    """
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = StateManager()
    return _global_state_manager


def set_global_state_dir(state_dir: str) -> None:
    """
    设置全局状态目录

    参数:
        state_dir: 状态目录路径
    """
    global _global_state_manager
    _global_state_manager = StateManager(state_dir)
