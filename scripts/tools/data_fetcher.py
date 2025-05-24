#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Fetcher Tool (数据获取工具)

Unified interface for fetching market data from various sources
"""

import sys
import os
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.config import get_config
from src.brokers import BinanceClient

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Unified data fetcher for market data (统一市场数据获取器)
    
    Supports multiple data sources and provides consistent interface
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize data fetcher
        
        Args:
            config_path: Path to configuration file
        """
        self.config = get_config(config_path)
        self.logger = logging.getLogger(f"{__name__}.DataFetcher")
        
        # Initialize clients
        self._binance_client = None
        
    def _get_binance_client(self):
        """Get or create Binance client"""
        if self._binance_client is None:
            api_key, api_secret = self.config.get_api_credentials()
            self._binance_client = BinanceClient(
                api_key=api_key,
                api_secret=api_secret,
                testnet=self.config.use_binance_testnet()
            )
        return self._binance_client
    
    def fetch_historical_data(
        self,
        symbol: str,
        interval: str = "1d",
        days: int = 365,
        source: str = "binance"
    ) -> pd.DataFrame:
        """
        Fetch historical market data
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval ('1m', '5m', '1h', '1d', etc.)
            days: Number of days to fetch
            source: Data source ('binance', 'yahoo', etc.)
            
        Returns:
            DataFrame with OHLCV data
        """
        self.logger.info(f"Fetching {days} days of {interval} data for {symbol} from {source}")
        
        try:
            if source.lower() == "binance":
                return self._fetch_binance_data(symbol, interval, days)
            elif source.lower() == "yahoo":
                return self._fetch_yahoo_data(symbol, interval, days)
            else:
                raise ValueError(f"Unsupported data source: {source}")
                
        except Exception as e:
            self.logger.error(f"Failed to fetch data: {e}")
            raise
    
    def _fetch_binance_data(self, symbol: str, interval: str, days: int) -> pd.DataFrame:
        """Fetch data from Binance"""
        client = self._get_binance_client()
        
        # Calculate start time
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Fetch klines
        klines = client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_time.strftime("%d %b %Y"),
            end_str=end_time.strftime("%d %b %Y")
        )
        
        if not klines:
            raise ValueError(f"No data returned for {symbol}")
        
        # Convert to DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Clean and format data
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # Convert to numeric
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Keep only OHLCV columns
        return df[numeric_columns]
    
    def _fetch_yahoo_data(self, symbol: str, interval: str, days: int) -> pd.DataFrame:
        """Fetch data from Yahoo Finance"""
        try:
            import yfinance as yf
            
            # Map intervals to Yahoo format
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '1d': '1d', '1wk': '1wk', '1mo': '1mo'
            }
            
            yf_interval = interval_map.get(interval, '1d')
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=f"{days}d", interval=yf_interval)
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            df.index.name = 'timestamp'
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except ImportError:
            raise ImportError("yfinance package required for Yahoo Finance data")
    
    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        interval: str = "1d",
        days: int = 365,
        source: str = "binance"
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols
        
        Args:
            symbols: List of trading symbols
            interval: Time interval
            days: Number of days to fetch
            source: Data source
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        results = {}
        
        for symbol in symbols:
            try:
                self.logger.info(f"Fetching data for {symbol}")
                data = self.fetch_historical_data(symbol, interval, days, source)
                results[symbol] = data
                self.logger.info(f"Successfully fetched {len(data)} records for {symbol}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch data for {symbol}: {e}")
                results[symbol] = pd.DataFrame()  # Empty DataFrame for failed fetches
        
        return results
    
    def save_data(self, data: pd.DataFrame, filepath: str, format: str = "csv"):
        """
        Save data to file
        
        Args:
            data: DataFrame to save
            filepath: Output file path
            format: File format ('csv', 'parquet', 'json')
        """
        try:
            if format.lower() == "csv":
                data.to_csv(filepath)
            elif format.lower() == "parquet":
                data.to_parquet(filepath)
            elif format.lower() == "json":
                data.to_json(filepath, date_format='iso')
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Data saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to save data: {e}")
            raise


def main():
    """Command line interface for data fetcher"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch market data")
    parser.add_argument("--symbol", "-s", default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--interval", "-i", default="1d", help="Time interval")
    parser.add_argument("--days", "-d", type=int, default=365, help="Number of days")
    parser.add_argument("--source", default="binance", help="Data source")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", "-f", default="csv", help="Output format")
    parser.add_argument("--multiple", "-m", nargs="+", help="Multiple symbols")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Create fetcher
    fetcher = DataFetcher()
    
    try:
        if args.multiple:
            # Fetch multiple symbols
            data_dict = fetcher.fetch_multiple_symbols(
                args.multiple, args.interval, args.days, args.source
            )
            
            for symbol, data in data_dict.items():
                if not data.empty:
                    output_path = args.output or f"{symbol}_{args.interval}_{args.days}d.{args.format}"
                    fetcher.save_data(data, output_path, args.format)
                    print(f"Saved {symbol} data to {output_path}")
        else:
            # Fetch single symbol
            data = fetcher.fetch_historical_data(
                args.symbol, args.interval, args.days, args.source
            )
            
            if args.output:
                fetcher.save_data(data, args.output, args.format)
                print(f"Data saved to {args.output}")
            else:
                print(data.head())
                print(f"\nFetched {len(data)} records for {args.symbol}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 