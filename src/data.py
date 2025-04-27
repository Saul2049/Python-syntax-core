import pandas as pd

def load_csv(filepath: str = "btc_eth.csv") -> pd.DataFrame:
    """Load OHLCV CSV and return DataFrame indexed by date."""
    return pd.read_csv(filepath, parse_dates=["date"], index_col="date") 