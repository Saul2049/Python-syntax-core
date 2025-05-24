"""
配置工具模块 (Configuration Utils Module)

提供配置处理的通用工具函数
"""

from typing import Any, Dict


def merge_dict(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    递归合并字典，将source字典的内容合并到target字典中

    参数:
        target: 目标字典（会被修改）
        source: 源字典
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            merge_dict(target[key], value)
        else:
            # 覆盖或添加新键
            target[key] = value


def deep_merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并多个字典

    参数:
        *dicts: 要合并的字典列表

    返回:
        合并后的新字典
    """
    result = {}
    for d in dicts:
        if d:
            merge_dict(result, d)
    return result


def validate_config_keys(
    config: Dict[str, Any], required_keys: list, optional_keys: list = None
) -> bool:
    """
    验证配置字典的键

    参数:
        config: 配置字典
        required_keys: 必需的键列表
        optional_keys: 可选的键列表

    返回:
        验证是否通过
    """
    if optional_keys is None:
        optional_keys = []

    all_allowed_keys = set(required_keys + optional_keys)
    config_keys = set(config.keys())

    # 检查必需键
    missing_keys = set(required_keys) - config_keys
    if missing_keys:
        raise ValueError(f"缺少必需的配置键: {missing_keys}")

    # 检查未知键
    unknown_keys = config_keys - all_allowed_keys
    if unknown_keys:
        raise ValueError(f"未知的配置键: {unknown_keys}")

    return True


def flatten_config(config: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    扁平化嵌套配置字典

    参数:
        config: 嵌套配置字典
        separator: 键分隔符

    返回:
        扁平化的配置字典
    """

    def _flatten(obj, parent_key=""):
        items = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{separator}{k}" if parent_key else k
                items.extend(_flatten(v, new_key).items())
        else:
            return {parent_key: obj}
        return dict(items)

    return _flatten(config)


def unflatten_config(config: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
    """
    将扁平化的配置字典还原为嵌套结构

    参数:
        config: 扁平化的配置字典
        separator: 键分隔符

    返回:
        嵌套的配置字典
    """
    result = {}

    for key, value in config.items():
        keys = key.split(separator)
        current = result

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    return result


def get_nested_value(
    config: Dict[str, Any], key_path: str, default: Any = None, separator: str = "."
) -> Any:
    """
    从嵌套字典中获取值

    参数:
        config: 配置字典
        key_path: 键路径（如 "database.host"）
        default: 默认值
        separator: 路径分隔符

    返回:
        配置值或默认值
    """
    keys = key_path.split(separator)
    current = config

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def set_nested_value(
    config: Dict[str, Any], key_path: str, value: Any, separator: str = "."
) -> None:
    """
    在嵌套字典中设置值

    参数:
        config: 配置字典
        key_path: 键路径（如 "database.host"）
        value: 要设置的值
        separator: 路径分隔符
    """
    keys = key_path.split(separator)
    current = config

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def config_diff(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
    """
    比较两个配置字典的差异

    参数:
        config1: 第一个配置字典
        config2: 第二个配置字典

    返回:
        差异字典
    """
    flat1 = flatten_config(config1)
    flat2 = flatten_config(config2)

    all_keys = set(flat1.keys()) | set(flat2.keys())

    diff = {"added": {}, "removed": {}, "changed": {}, "unchanged": {}}

    for key in all_keys:
        if key in flat1 and key in flat2:
            if flat1[key] != flat2[key]:
                diff["changed"][key] = {"old": flat1[key], "new": flat2[key]}
            else:
                diff["unchanged"][key] = flat1[key]
        elif key in flat1:
            diff["removed"][key] = flat1[key]
        else:
            diff["added"][key] = flat2[key]

    return diff
