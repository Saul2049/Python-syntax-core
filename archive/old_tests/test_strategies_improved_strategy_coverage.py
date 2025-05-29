#!/usr/bin/env python3
"""
Enhanced test coverage for src/strategies/improved_strategy.py

目标：从41%覆盖率提升到85%+，专注于三个策略函数和主程序块
"""

import os
import subprocess
import sys
from unittest.mock import Mock, MagicMock, patch
import warnings

import numpy as np
import pandas as pd
import pytest
from matplotlib import pyplot as plt

from src.strategies.improved_strategy import buy_and_hold, trend_following, improved_ma_cross


class TestBuyAndHoldStrategy:
    """Test buy and hold strategy comprehensive coverage"""

    def test_buy_and_hold_basic(self):
        """Test basic buy and hold functionality"""
        price = pd.Series([100, 105, 110, 115, 120], name="price")
        result = buy_and_hold(price, init_equity=10000)

        # Expected: 10000 + (120-100) * (10000/100) = 10000 + 20*100 = 12000
        expected_final = 10000 + (120 - 100) * (10000 / 100)
        assert abs(result.iloc[-1] - expected_final) < 0.01
        assert len(result) == len(price)
        assert isinstance(result, pd.Series)

    def test_buy_and_hold_with_price_decline(self):
        """Test buy and hold with declining prices"""
        price = pd.Series([100, 95, 90, 85, 80])
        result = buy_and_hold(price, init_equity=10000)

        # Expected: 10000 + (80-100) * (10000/100) = 10000 - 20*100 = 8000
        expected_final = 10000 + (80 - 100) * (10000 / 100)
        assert abs(result.iloc[-1] - expected_final) < 0.01

    def test_buy_and_hold_with_zero_initial_price(self):
        """Test buy and hold with zero initial price (edge case)"""
        price = pd.Series([0, 10, 20, 30])
        result = buy_and_hold(price, init_equity=10000)

        # Division by zero should result in inf position size and NaN equity curve
        assert len(result) == len(price)
        # Division by zero creates NaN or inf values
        assert np.isnan(result.iloc[0]) or np.isinf(result.iloc[0]) or result.iloc[0] == 10000

    def test_buy_and_hold_with_negative_prices(self):
        """Test buy and hold with negative prices"""
        price = pd.Series([-10, -5, 0, 5])
        result = buy_and_hold(price, init_equity=10000)

        assert len(result) == len(price)
        assert isinstance(result, pd.Series)

    def test_buy_and_hold_single_price(self):
        """Test buy and hold with single price point"""
        price = pd.Series([100])
        result = buy_and_hold(price, init_equity=5000)

        assert len(result) == 1
        assert result.iloc[0] == 5000  # No change in price

    def test_buy_and_hold_custom_equity(self):
        """Test buy and hold with different initial equity amounts"""
        price = pd.Series([50, 60, 70])

        # Test with different equity amounts
        result_small = buy_and_hold(price, init_equity=1000)
        result_large = buy_and_hold(price, init_equity=100000)

        # Both should have same length
        assert len(result_small) == len(result_large) == len(price)

        # Large equity should have proportionally larger final value
        ratio = result_large.iloc[-1] / result_small.iloc[-1]
        assert abs(ratio - 100) < 0.01  # 100000/1000 = 100


class TestTrendFollowingStrategy:
    """Test trend following strategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data for trend following tests"""
        # Create trending price data
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=250, freq="D")
        trend = np.linspace(100, 150, 250)
        noise = np.random.normal(0, 2, 250)
        self.price_data = pd.Series(trend + noise, index=dates, name="price")

        # Create sideways price data
        sideways = 100 + np.random.normal(0, 1, 250)
        self.sideways_data = pd.Series(sideways, index=dates, name="price")

    def test_trend_following_basic(self):
        """Test basic trend following functionality"""
        result = trend_following(self.price_data, long_win=50, atr_win=20, init_equity=10000)

        assert isinstance(result, pd.Series)
        assert len(result) <= len(self.price_data)
        assert result.iloc[0] == 10000  # Should start with initial equity

    def test_trend_following_with_trailing_stop(self):
        """Test trend following with trailing stop enabled"""
        result_with_trailing = trend_following(
            self.price_data, use_trailing_stop=True, init_equity=10000
        )

        result_without_trailing = trend_following(
            self.price_data, use_trailing_stop=False, init_equity=10000
        )

        assert isinstance(result_with_trailing, pd.Series)
        assert isinstance(result_without_trailing, pd.Series)
        # Results should be different
        assert not result_with_trailing.equals(result_without_trailing)

    def test_trend_following_different_parameters(self):
        """Test trend following with different parameter combinations"""
        # Test with short long_win
        result_short = trend_following(
            self.price_data, long_win=20, atr_win=10, risk_frac=0.01, init_equity=5000
        )

        # Test with long long_win
        result_long = trend_following(
            self.price_data, long_win=100, atr_win=30, risk_frac=0.03, init_equity=15000
        )

        assert isinstance(result_short, pd.Series)
        assert isinstance(result_long, pd.Series)
        assert result_short.iloc[0] == 5000
        assert result_long.iloc[0] == 15000

    def test_trend_following_sideways_market(self):
        """Test trend following in sideways market"""
        result = trend_following(self.sideways_data, long_win=50, atr_win=20, init_equity=10000)

        assert isinstance(result, pd.Series)
        assert len(result) <= len(self.sideways_data)

    def test_trend_following_short_data(self):
        """Test trend following with insufficient data"""
        short_data = self.price_data[:10]  # Only 10 days
        result = trend_following(
            short_data, long_win=20, atr_win=5, init_equity=10000  # Longer than data
        )

        assert isinstance(result, pd.Series)
        assert len(result) == len(short_data)
        # Should mostly stay at initial equity due to insufficient data
        assert result.iloc[0] == 10000

    def test_trend_following_edge_case_parameters(self):
        """Test trend following with edge case parameters"""
        # Very high risk fraction
        result_high_risk = trend_following(
            self.price_data, risk_frac=0.5, init_equity=10000  # 50% risk
        )

        # Very low risk fraction
        result_low_risk = trend_following(
            self.price_data, risk_frac=0.001, init_equity=10000  # 0.1% risk
        )

        assert isinstance(result_high_risk, pd.Series)
        assert isinstance(result_low_risk, pd.Series)

    @patch("src.broker.compute_trailing_stop")
    @patch("src.broker.compute_position_size")
    @patch("src.broker.compute_stop_price")
    def test_trend_following_broker_integration(self, mock_stop, mock_size, mock_trailing):
        """Test trend following integration with broker functions"""
        # Mock broker functions
        mock_size.return_value = 100  # Fixed position size
        mock_stop.return_value = 95  # Fixed stop price
        mock_trailing.return_value = 98  # Fixed trailing stop

        result = trend_following(
            self.price_data[:50],  # Shorter data for faster test
            long_win=20,
            atr_win=10,
            use_trailing_stop=True,
            init_equity=10000,
        )

        assert isinstance(result, pd.Series)
        # Verify broker functions were called
        assert mock_size.called
        assert mock_stop.called


class TestImprovedMACrossStrategy:
    """Test improved MA cross strategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data for MA cross tests"""
        np.random.seed(123)
        dates = pd.date_range("2020-01-01", periods=300, freq="D")
        trend = np.linspace(100, 200, 300)
        noise = np.random.normal(0, 5, 300)
        self.price_data = pd.Series(trend + noise, index=dates, name="price")

    def test_improved_ma_cross_basic(self):
        """Test basic improved MA cross functionality"""
        result = improved_ma_cross(self.price_data, fast_win=20, slow_win=50, init_equity=10000)

        assert isinstance(result, pd.Series)
        assert len(result) <= len(self.price_data)
        assert result.iloc[0] == 10000

    @patch("src.broker.backtest_single")
    def test_improved_ma_cross_delegates_to_broker(self, mock_backtest):
        """Test that improved_ma_cross properly delegates to broker.backtest_single"""
        expected_result = pd.Series([10000, 10500, 11000])
        mock_backtest.return_value = expected_result

        result = improved_ma_cross(
            self.price_data,
            fast_win=30,
            slow_win=60,
            atr_win=15,
            risk_frac=0.025,
            init_equity=15000,
            use_trailing_stop=False,
        )

        # Verify the result is what broker returned
        assert result.equals(expected_result)

        # Verify broker.backtest_single was called with correct parameters
        mock_backtest.assert_called_once_with(
            self.price_data,
            fast_win=30,
            slow_win=60,
            atr_win=15,
            risk_frac=0.025,
            init_equity=15000,
            use_trailing_stop=False,
        )

    def test_improved_ma_cross_different_parameters(self):
        """Test improved MA cross with various parameter combinations"""
        # Test different window combinations
        result1 = improved_ma_cross(
            self.price_data, fast_win=10, slow_win=30, atr_win=14, init_equity=5000
        )

        result2 = improved_ma_cross(
            self.price_data, fast_win=50, slow_win=200, atr_win=20, init_equity=20000
        )

        assert isinstance(result1, pd.Series)
        assert isinstance(result2, pd.Series)

    def test_improved_ma_cross_edge_parameters(self):
        """Test improved MA cross with edge case parameters"""
        # Very short windows
        result_short = improved_ma_cross(
            self.price_data, fast_win=2, slow_win=5, atr_win=3, risk_frac=0.1, init_equity=1000
        )

        # Very long windows
        result_long = improved_ma_cross(
            self.price_data,
            fast_win=100,
            slow_win=250,
            atr_win=50,
            risk_frac=0.005,
            init_equity=50000,
        )

        assert isinstance(result_short, pd.Series)
        assert isinstance(result_long, pd.Series)


class TestMainBlockExecution:
    """Test the main block execution (__name__ == '__main__')"""

    @patch("pandas.read_csv")
    @patch("matplotlib.pyplot.show")
    @patch("matplotlib.pyplot.savefig")
    def test_main_block_with_valid_data(self, mock_savefig, mock_show, mock_read_csv):
        """Test main block execution with valid data"""
        # Mock the CSV data
        dates = pd.date_range("2020-01-01", periods=100, freq="D")
        prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        mock_df = pd.DataFrame(
            {"btc": prices, "eth": prices * 0.8}, index=dates  # ETH roughly 80% of BTC
        )
        mock_read_csv.return_value = mock_df

        # Execute main block
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys
sys.path.insert(0, ".")

from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Mock the data
dates = pd.date_range("2020-01-01", periods=100, freq="D")
prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
mock_df = pd.DataFrame({
    "btc": prices,
    "eth": prices * 0.8
}, index=dates)

with patch("pandas.read_csv", return_value=mock_df), \\
     patch("matplotlib.pyplot.show"), \\
     patch("matplotlib.pyplot.savefig"):
    exec(open("src/strategies/improved_strategy.py").read())
""",
            ],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # Should execute without errors
        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
        assert result.returncode == 0

    @patch("pandas.read_csv")
    def test_main_block_with_missing_file(self, mock_read_csv):
        """Test main block execution when CSV file is missing"""
        # Mock read_csv to raise FileNotFoundError
        mock_read_csv.side_effect = FileNotFoundError("btc_eth.csv not found")

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys
sys.path.insert(0, ".")

from unittest.mock import patch
with patch("pandas.read_csv", side_effect=FileNotFoundError("btc_eth.csv not found")):
    try:
        exec(open("src/strategies/improved_strategy.py").read())
    except FileNotFoundError as e:
        print(f"Expected error: {e}")
""",
            ],
            capture_output=True,
            text=True,
            cwd=".",
        )

        # Should handle the error (may not be success depending on implementation)
        assert "Expected error" in result.stdout or result.returncode != 0

    def test_main_block_import_coverage(self):
        """Test that main block covers import statements"""
        # Execute just the import part
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                """
import sys
sys.path.insert(0, ".")

# Test individual imports
try:
    from src.strategies.improved_strategy import buy_and_hold, trend_following, improved_ma_cross
    print("IMPORTS_SUCCESS")
except ImportError as e:
    print(f"IMPORT_ERROR: {e}")
""",
            ],
            capture_output=True,
            text=True,
            cwd=".",
        )

        assert "IMPORTS_SUCCESS" in result.stdout


class TestStrategiesIntegration:
    """Test integration between all strategies"""

    def setup_method(self):
        """Setup comprehensive test data"""
        np.random.seed(456)
        dates = pd.date_range("2020-01-01", periods=200, freq="D")

        # Create various market conditions
        trend_up = np.linspace(100, 150, 200)
        trend_down = np.linspace(150, 100, 200)
        sideways = 125 + np.random.normal(0, 2, 200)
        volatile = 125 + np.random.normal(0, 10, 200)

        noise = np.random.normal(0, 1, 200)

        self.trending_up = pd.Series(trend_up + noise, index=dates)
        self.trending_down = pd.Series(trend_down + noise, index=dates)
        self.sideways = pd.Series(sideways, index=dates)
        self.volatile = pd.Series(volatile, index=dates)

    def test_all_strategies_with_different_markets(self):
        """Test all strategies work with different market conditions"""
        markets = {
            "trending_up": self.trending_up,
            "trending_down": self.trending_down,
            "sideways": self.sideways,
            "volatile": self.volatile,
        }

        for market_name, market_data in markets.items():
            # Test buy_and_hold
            bnh_result = buy_and_hold(market_data, init_equity=10000)
            assert isinstance(bnh_result, pd.Series)
            assert len(bnh_result) == len(market_data)

            # Test trend_following
            tf_result = trend_following(market_data, long_win=30, init_equity=10000)
            assert isinstance(tf_result, pd.Series)
            assert len(tf_result) <= len(market_data)

            # Test improved_ma_cross
            with patch("src.broker.backtest_single") as mock_backtest:
                mock_backtest.return_value = pd.Series([10000] * len(market_data))
                ma_result = improved_ma_cross(market_data, init_equity=10000)
                assert isinstance(ma_result, pd.Series)

    def test_strategies_return_different_results(self):
        """Test that different strategies return different results"""
        # Use trending up market
        bnh_result = buy_and_hold(self.trending_up, init_equity=10000)

        tf_result = trend_following(
            self.trending_up, long_win=50, use_trailing_stop=False, init_equity=10000
        )

        # Results should be different (strategies behave differently)
        assert not bnh_result.equals(tf_result)
        assert len(bnh_result) == len(self.trending_up)

    def test_strategies_performance_comparison(self):
        """Test relative performance characteristics"""
        # In trending up market, buy and hold should generally perform well
        bnh_result = buy_and_hold(self.trending_up, init_equity=10000)

        # Final value should be higher than initial for uptrending market
        assert bnh_result.iloc[-1] > bnh_result.iloc[0]

        # Test trend following in trending market
        tf_result = trend_following(self.trending_up, long_win=30, init_equity=10000)

        # Should at least maintain initial equity (modulo strategy logic)
        assert tf_result.iloc[0] == 10000


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling"""

    def test_empty_price_series(self):
        """Test behavior with empty price series"""
        empty_series = pd.Series([], dtype=float)

        # buy_and_hold should handle empty series
        with pytest.raises((IndexError, ValueError)):
            buy_and_hold(empty_series)

    def test_single_price_point(self):
        """Test behavior with single price point"""
        single_price = pd.Series([100.0])

        # buy_and_hold should work with single point
        result = buy_and_hold(single_price, init_equity=1000)
        assert len(result) == 1
        assert result.iloc[0] == 1000  # No change in price

    def test_nan_values_in_price(self):
        """Test behavior with NaN values in price series"""
        price_with_nan = pd.Series([100, np.nan, 105, 110, np.nan])

        # Functions should handle NaN gracefully or raise appropriate errors
        try:
            result = buy_and_hold(price_with_nan, init_equity=1000)
            # If it doesn't raise an error, result should be a valid series
            assert isinstance(result, pd.Series)
        except (ValueError, TypeError):
            # It's acceptable to raise an error for invalid data
            pass

    def test_extreme_parameter_values(self):
        """Test with extreme parameter values"""
        normal_price = pd.Series([100, 105, 110, 115, 120])

        # Test with very large initial equity
        result_large = buy_and_hold(normal_price, init_equity=1e12)
        assert isinstance(result_large, pd.Series)

        # Test with very small initial equity
        result_small = buy_and_hold(normal_price, init_equity=0.01)
        assert isinstance(result_small, pd.Series)

    def test_inf_values_handling(self):
        """Test handling of infinite values"""
        price_with_inf = pd.Series([100, np.inf, 105])

        try:
            result = buy_and_hold(price_with_inf, init_equity=1000)
            assert isinstance(result, pd.Series)
        except (ValueError, OverflowError):
            # It's acceptable to raise errors for infinite values
            pass


class TestImportsAndModularity:
    """Test import behavior and module structure"""

    def test_required_imports_available(self):
        """Test that all required imports are available"""
        # Test that we can import required modules
        try:
            from src import broker, metrics, signals
            from math import isfinite
            import matplotlib.pyplot as plt
            import pandas as pd

            assert True  # All imports successful
        except ImportError as e:
            pytest.fail(f"Required import failed: {e}")

    def test_function_signatures(self):
        """Test function signatures are as expected"""
        import inspect

        # Test buy_and_hold signature
        sig = inspect.signature(buy_and_hold)
        params = list(sig.parameters.keys())
        assert "price" in params
        assert "init_equity" in params

        # Test trend_following signature
        sig = inspect.signature(trend_following)
        params = list(sig.parameters.keys())
        assert "price" in params
        assert "long_win" in params
        assert "atr_win" in params
        assert "risk_frac" in params
        assert "init_equity" in params
        assert "use_trailing_stop" in params

        # Test improved_ma_cross signature
        sig = inspect.signature(improved_ma_cross)
        params = list(sig.parameters.keys())
        assert "price" in params
        assert "fast_win" in params
        assert "slow_win" in params
        assert "atr_win" in params
        assert "risk_frac" in params
        assert "init_equity" in params
        assert "use_trailing_stop" in params

    def test_docstring_presence(self):
        """Test that all functions have proper docstrings"""
        assert buy_and_hold.__doc__ is not None
        assert len(buy_and_hold.__doc__.strip()) > 0
        assert "买入持有策略" in buy_and_hold.__doc__

        assert trend_following.__doc__ is not None
        assert len(trend_following.__doc__.strip()) > 0
        assert "趋势跟踪策略" in trend_following.__doc__

        assert improved_ma_cross.__doc__ is not None
        assert len(improved_ma_cross.__doc__.strip()) > 0
        assert "MA交叉策略" in improved_ma_cross.__doc__
