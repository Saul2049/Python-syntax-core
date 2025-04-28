import pandas as pd
import requests


def load_csv(path: str = "btc_eth.csv") -> pd.DataFrame:
    """
    Load price data from a CSV with 'date' index and 'btc', 'eth' columns.
    """
    df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    return df


def fetch_klines(
    symbol: str, interval: str = "1d", limit: int = 100
) -> pd.Series:
    """
    Fetch historical klines for a given symbol from Binance API and return the closing price series.
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    # build DataFrame
    df = pd.DataFrame(
        data,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "num_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    series = df["close"].astype(float)
    series.index.name = "date"
    series.name = symbol.replace("USDT", "").lower()
    return series
