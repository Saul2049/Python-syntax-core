import os
from datetime import datetime
from pathlib import Path


def get_trades_dir(base_dir: str = None) -> Path:
    """
    获取交易数据存储目录。
    Get trades data storage directory.

    参数 (Parameters):
        base_dir: 基础目录路径 (Base directory path)
                 如果为None，使用环境变量TRADES_DIR或默认值
                 If None, use TRADES_DIR env var or default value

    返回 (Returns):
        Path: 交易数据目录路径 (Trades directory path)

    说明 (Notes):
        - 生产环境建议使用 ~/trades/YYYY/ 格式
        - 开发环境可以使用项目目录下的trades/
        - 所有交易数据文件都会被git忽略
    """
    if base_dir is None:
        base_dir = os.getenv("TRADES_DIR", "./trades")

    # 如果是生产环境，使用 ~/trades/YYYY/ 格式
    if base_dir.startswith("~"):
        base_dir = os.path.expanduser(base_dir)
        year = datetime.now().year
        trades_dir = Path(base_dir) / str(year)
    else:
        trades_dir = Path(base_dir)

    # 确保目录存在
    trades_dir.mkdir(parents=True, exist_ok=True)
    return trades_dir


def get_trades_file(symbol: str, base_dir: str = None) -> Path:
    """
    获取指定交易对的交易数据文件路径。
    Get trades data file path for specified symbol.

    参数 (Parameters):
        symbol: 交易对 (Trading pair)
        base_dir: 基础目录路径 (Base directory path)

    返回 (Returns):
        Path: 交易数据文件路径 (Trades data file path)
    """
    trades_dir = get_trades_dir(base_dir)
    return trades_dir / f"{symbol.lower()}_trades.csv"
