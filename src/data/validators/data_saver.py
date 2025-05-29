"""
数据保存器模块 (Data Saver Module)

提供数据保存和导出功能，包括：
- 多格式数据保存
- 数据验证
- 批量处理
- 备份管理
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


class DataSaver:
    """数据保存器类"""

    def __init__(self, base_output_dir: Optional[Union[str, Path]] = None):
        """
        初始化数据保存器

        参数:
            base_output_dir: 基础输出目录
        """
        self.base_output_dir = Path(base_output_dir) if base_output_dir else Path("output")
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

    def save_data(
        self,
        df: pd.DataFrame,
        filename: str,
        file_format: str = "csv",
        subdirectory: Optional[str] = None,
        create_backup: bool = False,
        **kwargs,
    ) -> bool:
        """
        保存数据到文件

        参数:
            df: 要保存的DataFrame
            filename: 文件名
            file_format: 文件格式 ('csv', 'parquet', 'pickle', 'json', 'excel')
            subdirectory: 子目录名
            create_backup: 是否创建备份
            **kwargs: 保存方法的额外参数

        返回:
            bool: 保存是否成功
        """
        try:
            # 构建完整路径
            if subdirectory:
                output_dir = self.base_output_dir / subdirectory
                output_dir.mkdir(parents=True, exist_ok=True)
            else:
                output_dir = self.base_output_dir

            # 提取特殊参数
            add_timestamp = kwargs.pop("add_timestamp", False)
            save_metadata = kwargs.pop("save_metadata", True)

            # 添加时间戳到文件名(如果需要)
            if add_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{timestamp}{ext}"

            file_path = output_dir / filename

            # 创建备份
            if create_backup and file_path.exists():
                self._create_backup(file_path)

            # 根据格式保存数据
            success = self._save_by_format(df, file_path, file_format, **kwargs)

            if success:
                print(f"✅ 数据已成功保存到: {file_path}")

                # 保存元数据
                if save_metadata:
                    self._save_metadata(df, file_path)

                return True
            else:
                return False

        except Exception as e:
            print(f"❌ 保存数据时出错: {str(e)}")
            return False

    def _save_by_format(
        self, df: pd.DataFrame, file_path: Path, file_format: str, **kwargs
    ) -> bool:
        """
        根据格式保存数据

        参数:
            df: DataFrame
            file_path: 文件路径
            file_format: 文件格式
            **kwargs: 额外参数

        返回:
            bool: 是否成功
        """
        try:
            format_lower = file_format.lower()

            if not self._is_supported_format(format_lower):
                print(f"❌ 不支持的文件格式: {file_format}")
                return False

            self._execute_save_operation(df, file_path, format_lower, **kwargs)
            return True

        except Exception as e:
            print(f"❌ 保存格式 {file_format} 时出错: {str(e)}")
            return False

    def _is_supported_format(self, format_lower: str) -> bool:
        """检查是否支持该格式"""
        supported_formats = ["csv", "parquet", "pickle", "json", "excel", "xlsx", "hdf5"]
        return format_lower in supported_formats

    def _execute_save_operation(
        self, df: pd.DataFrame, file_path: Path, format_lower: str, **kwargs
    ):
        """执行具体的保存操作"""
        if format_lower == "csv":
            df.to_csv(file_path, **kwargs)
        elif format_lower == "parquet":
            df.to_parquet(file_path, **kwargs)
        elif format_lower == "pickle":
            df.to_pickle(file_path, **kwargs)
        elif format_lower == "json":
            df.to_json(file_path, **kwargs)
        elif format_lower in ["excel", "xlsx"]:
            df.to_excel(file_path, **kwargs)
        elif format_lower == "hdf5":
            store_key = kwargs.pop("key", "data")
            df.to_hdf(file_path, key=store_key, **kwargs)

    def _create_backup(self, file_path: Path) -> None:
        """
        创建文件备份

        参数:
            file_path: 原文件路径
        """
        try:
            backup_dir = file_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name

            # 复制文件
            import shutil

            shutil.copy2(file_path, backup_path)
            print(f"📁 备份已创建: {backup_path}")

        except Exception as e:
            print(f"⚠️ 创建备份失败: {str(e)}")

    def _save_metadata(self, df: pd.DataFrame, file_path: Path) -> None:
        """
        保存数据元信息

        参数:
            df: DataFrame
            file_path: 数据文件路径
        """
        try:
            metadata = {
                "filename": file_path.name,
                "created_at": datetime.now().isoformat(),
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
                "null_counts": df.isnull().sum().to_dict(),
                "index_type": str(type(df.index).__name__),
            }

            # 数值列统计
            numeric_cols = df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) > 0:
                metadata["numeric_summary"] = df[numeric_cols].describe().to_dict()

            # 保存元数据文件
            metadata_path = file_path.with_suffix(".metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️ 保存元数据失败: {str(e)}")

    def save_multiple_formats(
        self,
        df: pd.DataFrame,
        base_filename: str,
        formats: List[str],
        subdirectory: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        将数据保存为多种格式

        参数:
            df: 要保存的DataFrame
            base_filename: 基础文件名（无扩展名）
            formats: 格式列表
            subdirectory: 子目录

        返回:
            Dict[str, bool]: 各格式的保存结果
        """
        results = {}

        for fmt in formats:
            # 构建文件名
            if fmt.lower() == "excel":
                filename = f"{base_filename}.xlsx"
            else:
                filename = f"{base_filename}.{fmt.lower()}"

            # 保存
            success = self.save_data(df, filename, fmt, subdirectory)
            results[fmt] = success

        return results

    def batch_save(
        self,
        dataframes: Dict[str, pd.DataFrame],
        file_format: str = "csv",
        subdirectory: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        批量保存多个DataFrame

        参数:
            dataframes: {文件名: DataFrame} 字典
            file_format: 文件格式
            subdirectory: 子目录

        返回:
            Dict[str, bool]: 各文件的保存结果
        """
        results = {}

        for filename, df in dataframes.items():
            # 确保文件名有正确扩展名
            if not filename.endswith(f".{file_format}"):
                filename = f"{filename}.{file_format}"

            success = self.save_data(df, filename, file_format, subdirectory)
            results[filename] = success

        return results

    def get_saved_files_info(self, subdirectory: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取已保存文件的信息

        参数:
            subdirectory: 子目录

        返回:
            List[Dict]: 文件信息列表
        """
        search_dir = self.base_output_dir
        if subdirectory:
            search_dir = search_dir / subdirectory

        if not search_dir.exists():
            return []

        files_info = []

        for file_path in search_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith("."):
                try:
                    stat = file_path.stat()
                    info = {
                        "filename": file_path.name,
                        "path": str(file_path),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "extension": file_path.suffix,
                    }

                    # 尝试加载元数据
                    metadata_path = file_path.with_suffix(f"{file_path.suffix}.metadata.json")
                    if metadata_path.exists():
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            info["metadata"] = metadata

                    files_info.append(info)

                except Exception as e:
                    print(f"⚠️ 获取文件信息失败 {file_path}: {e}")

        return sorted(files_info, key=lambda x: x["modified"], reverse=True)

    def cleanup_old_files(
        self, subdirectory: Optional[str] = None, days_old: int = 30, file_pattern: str = "*"
    ) -> int:
        """
        清理旧文件

        参数:
            subdirectory: 子目录
            days_old: 保留天数
            file_pattern: 文件模式

        返回:
            int: 清理的文件数量
        """
        search_dir = self._get_search_directory(subdirectory)
        if not search_dir.exists():
            return 0

        cutoff_time = self._calculate_cutoff_time(days_old)

        try:
            cleaned_count = self._remove_old_files(search_dir, file_pattern, cutoff_time)
            print(f"✅ 清理完成，删除了 {cleaned_count} 个文件")
            return cleaned_count

        except Exception as e:
            print(f"❌ 清理文件时出错: {str(e)}")
            return 0

    def _get_search_directory(self, subdirectory: Optional[str]) -> Path:
        """获取搜索目录"""
        search_dir = self.base_output_dir
        if subdirectory:
            search_dir = search_dir / subdirectory
        return search_dir

    def _calculate_cutoff_time(self, days_old: int) -> float:
        """计算截止时间"""
        import time

        return time.time() - (days_old * 24 * 60 * 60)

    def _remove_old_files(self, search_dir: Path, file_pattern: str, cutoff_time: float) -> int:
        """移除旧文件"""
        cleaned_count = 0

        for file_path in search_dir.glob(file_pattern):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                self._delete_file_and_metadata(file_path)
                cleaned_count += 1
                print(f"🗑️ 已删除旧文件: {file_path.name}")

        return cleaned_count

    def _delete_file_and_metadata(self, file_path: Path):
        """删除文件及其元数据"""
        file_path.unlink()

        # 删除对应的元数据文件
        metadata_path = file_path.with_suffix(f"{file_path.suffix}.metadata.json")
        if metadata_path.exists():
            metadata_path.unlink()


class ProcessedDataExporter:
    """处理后数据导出器"""

    def __init__(self, data_saver: Optional[DataSaver] = None):
        """
        初始化导出器

        参数:
            data_saver: 数据保存器实例
        """
        self.data_saver = data_saver or DataSaver()

    def export_ohlcv_data(
        self, df: pd.DataFrame, symbol: str, timeframe: str = "1h", include_indicators: bool = True
    ) -> bool:
        """
        导出OHLCV数据

        参数:
            df: OHLCV数据
            symbol: 交易对
            timeframe: 时间框架
            include_indicators: 是否包含技术指标

        返回:
            bool: 是否成功
        """
        filename = f"{symbol}_{timeframe}_ohlcv"
        if include_indicators:
            filename += "_with_indicators"

        return self.data_saver.save_data(
            df, f"{filename}.csv", subdirectory="ohlcv_data", add_timestamp=True
        )

    def export_signals_data(self, df: pd.DataFrame, strategy_name: str) -> bool:
        """
        导出交易信号数据

        参数:
            df: 信号数据
            strategy_name: 策略名称

        返回:
            bool: 是否成功
        """
        filename = f"{strategy_name}_signals"

        return self.data_saver.save_data(
            df, f"{filename}.csv", subdirectory="signals", add_timestamp=True
        )

    def export_backtest_results(self, results: Dict[str, Any], strategy_name: str) -> bool:
        """
        导出回测结果

        参数:
            results: 回测结果字典
            strategy_name: 策略名称

        返回:
            bool: 是否成功
        """
        try:
            # 保存为JSON格式
            filename = f"{strategy_name}_backtest_results.json"

            output_dir = self.data_saver.base_output_dir / "backtest_results"
            output_dir.mkdir(exist_ok=True)

            file_path = output_dir / filename

            # 确保数据可序列化
            serializable_results = self._make_serializable(results)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)

            print(f"✅ 回测结果已保存到: {file_path}")
            return True

        except Exception as e:
            print(f"❌ 导出回测结果失败: {str(e)}")
            return False

    def _make_serializable(self, data: Any) -> Any:
        """
        使数据可序列化

        参数:
            data: 输入数据

        返回:
            可序列化的数据
        """
        if isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, (pd.Series, pd.DataFrame)):
            return data.to_dict()
        elif isinstance(data, (pd.Timestamp, datetime)):
            return data.isoformat()
        elif isinstance(data, (int, float, str, bool)) or data is None:
            return data
        else:
            return str(data)


# 便捷函数
def save_processed_data(
    df: pd.DataFrame, output_path: str, file_format: str = "csv", **kwargs
) -> bool:
    """
    便捷函数：保存处理后的数据

    参数:
        df: 要保存的DataFrame
        output_path: 输出路径
        file_format: 文件格式
        **kwargs: 其他参数

    返回:
        bool: 保存是否成功
    """
    try:
        # 创建目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 根据文件格式保存数据
        if file_format.lower() == "csv":
            df.to_csv(output_path, **kwargs)
        elif file_format.lower() == "pickle":
            df.to_pickle(output_path, **kwargs)
        elif file_format.lower() == "parquet":
            df.to_parquet(output_path, **kwargs)
        else:
            print(f"❌ 不支持的文件格式: {file_format}")
            return False

        print(f"✅ 数据已成功保存到 {output_path}")
        return True

    except Exception as e:
        print(f"❌ 保存数据时出错: {str(e)}")
        return False
