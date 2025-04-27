import pandas as pd
import numpy as np

def compute_position_size(equity: float, atr: float, risk_frac: float = 0.02) -> int:
    """Risk a fraction of equity per trade, return share size (rounded down)."""
    if atr == 0:
        return 0
    return int((equity * risk_frac) // atr)


def compute_stop_price(entry: float, atr: float, multiplier: float = 1.0) -> float:
    """Calculate stop-loss price as entry minus ATR multiplied by multiplier."""
    return entry - multiplier * atr 