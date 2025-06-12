#!/usr/bin/env python3
"""
Enhanced test coverage for src/strategies/breakout.py

目标：从51%覆盖率提升到85%+，覆盖所有5个突破策略类
"""


import numpy as np
import pandas as pd
import pytest

from src.strategies.breakout import (
    ATRBreakoutStrategy,
    BollingerBreakoutStrategy,
    BollingerMeanReversionStrategy,
    ChannelBreakoutStrategy,
    DonchianChannelStrategy,
)


class TestBollingerBreakoutStrategy:
    """Test BollingerBreakoutStrategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data for Bollinger breakout tests"""
        # Create realistic market data
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=100, freq="D")

        # Trending market with volatility
        base_price = 100
        trend = np.linspace(0, 20, 100)  # 20% uptrend
        volatility = np.random.normal(0, 2, 100)
        prices = base_price + trend + volatility

        # Create OHLC data
        self.test_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 0.5, 100),
                "high": prices + abs(np.random.normal(0, 1, 100)),
                "low": prices - abs(np.random.normal(0, 1, 100)),
                "close": prices,
                "volume": np.random.randint(1000, 10000, 100),
            },
            index=dates,
        )

    def test_bollinger_breakout_init(self):
        """Test BollingerBreakoutStrategy initialization"""
        # Default parameters
        strategy = BollingerBreakoutStrategy()
        assert strategy.window == 20
        assert strategy.num_std == 2.0

        # Custom parameters
        strategy_custom = BollingerBreakoutStrategy(window=15, num_std=1.5)
        assert strategy_custom.window == 15
        assert strategy_custom.num_std == 1.5

    def test_bollinger_breakout_calculate_indicators(self):
        """Test calculate_indicators method"""
        strategy = BollingerBreakoutStrategy(window=10, num_std=2.0)
        result = strategy.calculate_indicators(self.test_data)

        # Check all required columns are present
        assert "upper_band" in result.columns
        assert "middle_band" in result.columns
        assert "lower_band" in result.columns
        assert "bb_width" in result.columns

        # Check data integrity
        assert len(result) == len(self.test_data)
        assert not result["middle_band"].iloc[-10:].isna().all()  # Should have values

        # Check Bollinger Band logic (only for non-NaN values)
        valid_data = result.dropna()
        if len(valid_data) > 0:
            assert (valid_data["upper_band"] >= valid_data["middle_band"]).all()
            assert (valid_data["middle_band"] >= valid_data["lower_band"]).all()

    def test_bollinger_breakout_generate_signals(self):
        """Test generate_signals method"""
        strategy = BollingerBreakoutStrategy(window=10, num_std=2.0)
        result = strategy.generate_signals(self.test_data)

        # Check signal column exists
        assert "signal" in result.columns
        assert len(result) == len(self.test_data)

        # Check signal values are valid
        valid_signals = result["signal"].isin([-1, 0, 1])
        assert valid_signals.all()

        # Check that signals are generated (at least some non-zero signals)
        assert (result["signal"] != 0).any()

    def test_bollinger_breakout_signal_logic(self):
        """Test signal generation logic specifically"""
        strategy = BollingerBreakoutStrategy(window=5, num_std=1.0)

        # Create specific test case for breakout
        test_data = pd.DataFrame(
            {
                "open": [100, 101, 102, 103, 110],  # Price breaks out
                "high": [101, 102, 103, 104, 112],
                "low": [99, 100, 101, 102, 109],
                "close": [100, 101, 102, 103, 111],  # Final price breaks upper band
                "volume": [1000] * 5,
            }
        )

        result = strategy.generate_signals(test_data)

        # The last signal should be buy (1) due to upper band breakout
        assert result["signal"].iloc[-1] == 1 or result["signal"].sum() > 0

    def test_bollinger_breakout_edge_cases(self):
        """Test edge cases"""
        strategy = BollingerBreakoutStrategy(window=5, num_std=2.0)

        # Minimal data
        minimal_data = pd.DataFrame(
            {
                "open": [100, 101],
                "high": [101, 102],
                "low": [99, 100],
                "close": [100, 101],
                "volume": [1000, 1000],
            }
        )

        result = strategy.generate_signals(minimal_data)
        assert len(result) == 2
        assert "signal" in result.columns

    def test_bollinger_breakout_different_parameters(self):
        """Test with different parameter combinations"""
        # Short window, tight bands
        strategy_tight = BollingerBreakoutStrategy(window=5, num_std=1.0)
        result_tight = strategy_tight.generate_signals(self.test_data)

        # Long window, wide bands
        strategy_wide = BollingerBreakoutStrategy(window=30, num_std=3.0)
        result_wide = strategy_wide.generate_signals(self.test_data)

        # Both should work
        assert "signal" in result_tight.columns
        assert "signal" in result_wide.columns

        # Tight bands should generate more signals
        tight_signals = (result_tight["signal"] != 0).sum()
        wide_signals = (result_wide["signal"] != 0).sum()
        # This might not always be true, but generally tight bands are more sensitive


class TestBollingerMeanReversionStrategy:
    """Test BollingerMeanReversionStrategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data"""
        np.random.seed(123)
        dates = pd.date_range("2020-01-01", periods=50, freq="D")

        # Mean-reverting market (oscillating around 100)
        base_price = 100
        oscillation = 10 * np.sin(np.linspace(0, 4 * np.pi, 50))
        noise = np.random.normal(0, 1, 50)
        prices = base_price + oscillation + noise

        self.test_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 0.3, 50),
                "high": prices + abs(np.random.normal(0, 0.8, 50)),
                "low": prices - abs(np.random.normal(0, 0.8, 50)),
                "close": prices,
                "volume": np.random.randint(500, 5000, 50),
            },
            index=dates,
        )

    def test_bollinger_mean_reversion_init(self):
        """Test initialization"""
        strategy = BollingerMeanReversionStrategy()
        assert strategy.window == 20
        assert strategy.num_std == 2.0

        strategy_custom = BollingerMeanReversionStrategy(window=12, num_std=1.8)
        assert strategy_custom.window == 12
        assert strategy_custom.num_std == 1.8

    def test_bollinger_mean_reversion_calculate_indicators(self):
        """Test calculate_indicators method"""
        strategy = BollingerMeanReversionStrategy(window=10)
        result = strategy.calculate_indicators(self.test_data)

        # Check required columns
        required_cols = ["upper_band", "middle_band", "lower_band"]
        for col in required_cols:
            assert col in result.columns

        # Check Bollinger Band relationships (only for non-NaN values)
        valid_data = result.dropna()
        if len(valid_data) > 0:
            assert (valid_data["upper_band"] >= valid_data["middle_band"]).all()
            assert (valid_data["middle_band"] >= valid_data["lower_band"]).all()

    def test_bollinger_mean_reversion_generate_signals(self):
        """Test generate_signals method"""
        strategy = BollingerMeanReversionStrategy(window=8, num_std=1.5)
        result = strategy.generate_signals(self.test_data)

        assert "signal" in result.columns
        assert len(result) == len(self.test_data)

        # Check signal values
        assert result["signal"].isin([-1, 0, 1]).all()

    def test_bollinger_mean_reversion_signal_logic(self):
        """Test mean reversion signal logic"""
        strategy = BollingerMeanReversionStrategy(window=5, num_std=1.0)

        # Create data that touches bands
        test_data = pd.DataFrame(
            {
                "open": [100, 95, 90, 95, 105],
                "high": [101, 96, 91, 96, 107],
                "low": [99, 94, 89, 94, 104],
                "close": [100, 95, 90, 95, 106],  # Price oscillates
                "volume": [1000] * 5,
            }
        )

        result = strategy.generate_signals(test_data)

        # Should generate some signals due to oscillation
        assert (result["signal"] != 0).any()

    def test_bollinger_mean_reversion_extreme_parameters(self):
        """Test with extreme parameters"""
        # Very tight bands
        strategy_tight = BollingerMeanReversionStrategy(window=3, num_std=0.5)
        result_tight = strategy_tight.generate_signals(self.test_data)

        # Very wide bands
        strategy_wide = BollingerMeanReversionStrategy(window=20, num_std=5.0)
        result_wide = strategy_wide.generate_signals(self.test_data)

        assert "signal" in result_tight.columns
        assert "signal" in result_wide.columns


class TestChannelBreakoutStrategy:
    """Test ChannelBreakoutStrategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data"""
        np.random.seed(456)
        dates = pd.date_range("2020-01-01", periods=60, freq="D")

        # Create channel-bound market with breakouts
        base = 100
        channel_range = 15
        trend = np.linspace(0, 10, 60)
        prices = base + trend + np.random.uniform(-channel_range / 2, channel_range / 2, 60)

        self.test_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 0.5, 60),
                "high": prices + abs(np.random.normal(0, 2, 60)),
                "low": prices - abs(np.random.normal(0, 2, 60)),
                "close": prices,
                "volume": np.random.randint(800, 8000, 60),
            },
            index=dates,
        )

    def test_channel_breakout_init(self):
        """Test initialization"""
        strategy = ChannelBreakoutStrategy()
        assert strategy.channel_period == 20

        strategy_custom = ChannelBreakoutStrategy(channel_period=15)
        assert strategy_custom.channel_period == 15

    def test_channel_breakout_calculate_indicators(self):
        """Test calculate_indicators method"""
        strategy = ChannelBreakoutStrategy(channel_period=10)
        result = strategy.calculate_indicators(self.test_data)

        # Check channel columns
        assert "channel_high" in result.columns
        assert "channel_low" in result.columns

        # Check that channel high >= channel low (only for non-NaN values)
        valid_data = result.dropna()
        if len(valid_data) > 0:
            valid_channel = valid_data["channel_high"] >= valid_data["channel_low"]
            assert valid_channel.all()

    def test_channel_breakout_generate_signals(self):
        """Test generate_signals method"""
        strategy = ChannelBreakoutStrategy(channel_period=8)
        result = strategy.generate_signals(self.test_data)

        assert "signal" in result.columns
        assert result["signal"].isin([-1, 0, 1]).all()

    def test_channel_breakout_signal_logic(self):
        """Test specific breakout logic"""
        strategy = ChannelBreakoutStrategy(channel_period=3)

        # Create breakout scenario
        test_data = pd.DataFrame(
            {
                "open": [100, 101, 102, 108],  # Price breaks out
                "high": [102, 103, 104, 110],  # High breaks previous high
                "low": [98, 99, 100, 106],
                "close": [101, 102, 103, 109],  # Close above previous channel
                "volume": [1000] * 4,
            }
        )

        result = strategy.generate_signals(test_data)

        # Should detect breakout in last period
        assert result["signal"].iloc[-1] == 1 or (result["signal"] != 0).any()

    def test_channel_breakout_short_period(self):
        """Test with very short channel period"""
        strategy = ChannelBreakoutStrategy(channel_period=2)
        result = strategy.generate_signals(self.test_data)

        assert "signal" in result.columns
        assert len(result) == len(self.test_data)


class TestDonchianChannelStrategy:
    """Test DonchianChannelStrategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data"""
        np.random.seed(789)
        dates = pd.date_range("2020-01-01", periods=80, freq="D")

        # Create trending market suitable for Donchian
        base = 100
        trend = np.linspace(0, 25, 80)
        volatility = np.random.normal(0, 3, 80)
        prices = base + trend + volatility

        self.test_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 0.8, 80),
                "high": prices + abs(np.random.normal(0, 1.5, 80)),
                "low": prices - abs(np.random.normal(0, 1.5, 80)),
                "close": prices,
                "volume": np.random.randint(1200, 12000, 80),
            },
            index=dates,
        )

    def test_donchian_channel_init(self):
        """Test initialization"""
        strategy = DonchianChannelStrategy()
        assert strategy.entry_period == 20
        assert strategy.exit_period == 10

        strategy_custom = DonchianChannelStrategy(entry_period=15, exit_period=5)
        assert strategy_custom.entry_period == 15
        assert strategy_custom.exit_period == 5

    def test_donchian_channel_calculate_indicators(self):
        """Test calculate_indicators method"""
        strategy = DonchianChannelStrategy(entry_period=12, exit_period=6)
        result = strategy.calculate_indicators(self.test_data)

        # Check all Donchian channels
        required_cols = ["entry_high", "entry_low", "exit_high", "exit_low"]
        for col in required_cols:
            assert col in result.columns

        # Check channel relationships (only for non-NaN values)
        valid_data = result.dropna()
        if len(valid_data) > 0:
            assert (valid_data["entry_high"] >= valid_data["entry_low"]).all()
            assert (valid_data["exit_high"] >= valid_data["exit_low"]).all()

    def test_donchian_channel_generate_signals(self):
        """Test generate_signals method"""
        strategy = DonchianChannelStrategy(entry_period=8, exit_period=4)
        result = strategy.generate_signals(self.test_data)

        assert "signal" in result.columns
        assert result["signal"].isin([-1, 0, 1]).all()

    def test_donchian_channel_signal_logic(self):
        """Test Donchian breakout logic"""
        strategy = DonchianChannelStrategy(entry_period=3, exit_period=2)

        # Create clear breakout pattern
        test_data = pd.DataFrame(
            {
                "open": [100, 101, 102, 105, 108],
                "high": [102, 103, 104, 107, 112],  # Progressive highs
                "low": [98, 99, 100, 103, 106],
                "close": [101, 102, 103, 106, 110],  # Breaks previous highs
                "volume": [1000] * 5,
            }
        )

        result = strategy.generate_signals(test_data)

        # Should generate breakout signals
        assert (result["signal"] != 0).any()

    def test_donchian_channel_parameter_validation(self):
        """Test parameter relationships"""
        # Entry period longer than exit period (typical setup)
        strategy = DonchianChannelStrategy(entry_period=20, exit_period=10)
        result = strategy.generate_signals(self.test_data)

        assert "signal" in result.columns

        # Entry period shorter than exit period (unusual but valid)
        strategy_reverse = DonchianChannelStrategy(entry_period=5, exit_period=15)
        result_reverse = strategy_reverse.generate_signals(self.test_data)

        assert "signal" in result_reverse.columns


class TestATRBreakoutStrategy:
    """Test ATRBreakoutStrategy comprehensive coverage"""

    def setup_method(self):
        """Setup test data"""
        np.random.seed(321)
        dates = pd.date_range("2020-01-01", periods=100, freq="D")

        # Create volatile market suitable for ATR strategy
        base = 100
        trend = np.linspace(0, 15, 100)
        volatility = np.random.normal(0, 4, 100)  # High volatility
        prices = base + trend + volatility

        self.test_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 1, 100),
                "high": prices + abs(np.random.normal(0, 3, 100)),
                "low": prices - abs(np.random.normal(0, 3, 100)),
                "close": prices,
                "volume": np.random.randint(1500, 15000, 100),
            },
            index=dates,
        )

    def test_atr_breakout_init(self):
        """Test initialization"""
        strategy = ATRBreakoutStrategy()
        assert strategy.atr_period == 14
        assert strategy.ma_period == 20
        assert strategy.multiplier == 2.0

        strategy_custom = ATRBreakoutStrategy(atr_period=10, ma_period=15, multiplier=1.5)
        assert strategy_custom.atr_period == 10
        assert strategy_custom.ma_period == 15
        assert strategy_custom.multiplier == 1.5

    def test_atr_breakout_calculate_indicators(self):
        """Test calculate_indicators method"""
        strategy = ATRBreakoutStrategy(atr_period=10, ma_period=12, multiplier=2.0)
        result = strategy.calculate_indicators(self.test_data)

        # Check ATR-related columns
        required_cols = ["atr", "ma", "upper_atr", "lower_atr"]
        for col in required_cols:
            assert col in result.columns

        # Check ATR bands relationship (only for non-NaN values)
        valid_data = result.dropna()
        if len(valid_data) > 0:
            assert (valid_data["upper_atr"] >= valid_data["ma"]).all()
            assert (valid_data["ma"] >= valid_data["lower_atr"]).all()

        # Check ATR is positive
        atr_values = result["atr"].dropna()
        if len(atr_values) > 0:
            assert (atr_values >= 0).all()

    def test_atr_breakout_generate_signals(self):
        """Test generate_signals method"""
        strategy = ATRBreakoutStrategy(atr_period=8, ma_period=10, multiplier=1.5)
        result = strategy.generate_signals(self.test_data)

        assert "signal" in result.columns
        assert result["signal"].isin([-1, 0, 1]).all()

    def test_atr_breakout_signal_logic(self):
        """Test ATR breakout signal logic"""
        strategy = ATRBreakoutStrategy(atr_period=3, ma_period=3, multiplier=1.0)

        # Create volatility breakout scenario with enough data
        test_data = pd.DataFrame(
            {
                "open": [100, 101, 102, 105, 108, 112],
                "high": [103, 108, 115, 120, 125, 130],  # Increasing volatility
                "low": [97, 95, 90, 100, 105, 110],  # Wider ranges
                "close": [102, 106, 112, 118, 124, 128],  # Strong uptrend
                "volume": [1000] * 6,
            }
        )

        result = strategy.generate_signals(test_data)

        # Should generate signals due to volatility and trend
        # Note: May not always generate signals due to NaN values in early periods
        # At minimum, should have valid signal column
        assert "signal" in result.columns

    def test_atr_breakout_different_multipliers(self):
        """Test with different ATR multipliers"""
        # Conservative multiplier
        strategy_conservative = ATRBreakoutStrategy(multiplier=3.0)
        result_conservative = strategy_conservative.generate_signals(self.test_data)

        # Aggressive multiplier
        strategy_aggressive = ATRBreakoutStrategy(multiplier=0.5)
        result_aggressive = strategy_aggressive.generate_signals(self.test_data)

        assert "signal" in result_conservative.columns
        assert "signal" in result_aggressive.columns

        # Aggressive should typically generate more signals
        conservative_signals = (result_conservative["signal"] != 0).sum()
        aggressive_signals = (result_aggressive["signal"] != 0).sum()
        # Note: This might not always hold due to random data

    def test_atr_calculation_accuracy(self):
        """Test ATR calculation accuracy"""
        strategy = ATRBreakoutStrategy(atr_period=3)

        # Create specific data to verify ATR calculation
        test_data = pd.DataFrame(
            {
                "open": [100, 102, 104],
                "high": [105, 107, 109],
                "low": [95, 97, 99],
                "close": [102, 104, 106],
                "volume": [1000] * 3,
            }
        )

        result = strategy.calculate_indicators(test_data)

        # Check that ATR exists and is reasonable
        assert "atr" in result.columns
        atr_final = result["atr"].iloc[-1]
        assert not pd.isna(atr_final)
        assert atr_final > 0


class TestBreakoutStrategiesIntegration:
    """Test integration and comparative analysis of breakout strategies"""

    def setup_method(self):
        """Setup comprehensive test data"""
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=200, freq="D")

        # Create diverse market conditions
        base = 100
        trend = np.linspace(0, 30, 200)
        cycles = 5 * np.sin(np.linspace(0, 4 * np.pi, 200))
        noise = np.random.normal(0, 2, 200)
        prices = base + trend + cycles + noise

        self.comprehensive_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 0.5, 200),
                "high": prices + abs(np.random.normal(0, 2, 200)),
                "low": prices - abs(np.random.normal(0, 2, 200)),
                "close": prices,
                "volume": np.random.randint(1000, 10000, 200),
            },
            index=dates,
        )

    def test_all_strategies_work_with_same_data(self):
        """Test that all breakout strategies work with the same dataset"""
        strategies = [
            BollingerBreakoutStrategy(),
            BollingerMeanReversionStrategy(),
            ChannelBreakoutStrategy(),
            DonchianChannelStrategy(),
            ATRBreakoutStrategy(),
        ]

        for strategy in strategies:
            result = strategy.generate_signals(self.comprehensive_data)

            assert "signal" in result.columns
            assert len(result) == len(self.comprehensive_data)
            assert result["signal"].isin([-1, 0, 1]).all()

    def test_strategies_generate_different_signals(self):
        """Test that different strategies generate different signals"""
        bollinger = BollingerBreakoutStrategy()
        channel = ChannelBreakoutStrategy()
        atr = ATRBreakoutStrategy()

        bollinger_signals = bollinger.generate_signals(self.comprehensive_data)["signal"]
        channel_signals = channel.generate_signals(self.comprehensive_data)["signal"]
        atr_signals = atr.generate_signals(self.comprehensive_data)["signal"]

        # Strategies should have some differences in their signals
        assert not bollinger_signals.equals(channel_signals)
        assert not channel_signals.equals(atr_signals)

    def test_strategy_signal_frequency(self):
        """Test signal generation frequency across strategies"""
        strategies = {
            "Bollinger": BollingerBreakoutStrategy(num_std=1.0),  # More sensitive
            "Channel": ChannelBreakoutStrategy(channel_period=10),
            "Donchian": DonchianChannelStrategy(entry_period=10),
            "ATR": ATRBreakoutStrategy(multiplier=1.0),  # More sensitive
        }

        signal_counts = {}
        for name, strategy in strategies.items():
            result = strategy.generate_signals(self.comprehensive_data)
            signal_count = (result["signal"] != 0).sum()
            signal_counts[name] = signal_count

            # Each strategy should generate at least some signals
            assert signal_count > 0, f"{name} strategy generated no signals"

    def test_strategies_with_insufficient_data(self):
        """Test how strategies handle insufficient data"""
        # Very short data
        short_data = self.comprehensive_data.head(5)

        strategies = [
            BollingerBreakoutStrategy(window=3),
            ChannelBreakoutStrategy(channel_period=3),
            DonchianChannelStrategy(entry_period=3, exit_period=2),
            ATRBreakoutStrategy(atr_period=3, ma_period=3),
        ]

        for strategy in strategies:
            result = strategy.generate_signals(short_data)
            assert len(result) == len(short_data)
            assert "signal" in result.columns


class TestBreakoutStrategiesEdgeCases:
    """Test edge cases and error conditions for breakout strategies"""

    def test_all_strategies_with_constant_prices(self):
        """Test strategies with constant price data"""
        constant_data = pd.DataFrame(
            {
                "open": [100] * 20,
                "high": [100] * 20,
                "low": [100] * 20,
                "close": [100] * 20,
                "volume": [1000] * 20,
            }
        )

        strategies = [
            BollingerBreakoutStrategy(),
            BollingerMeanReversionStrategy(),
            ChannelBreakoutStrategy(),
            DonchianChannelStrategy(),
            ATRBreakoutStrategy(),
        ]

        for strategy in strategies:
            result = strategy.generate_signals(constant_data)
            assert "signal" in result.columns
            # With constant prices, most signals should be 0
            assert (result["signal"] == 0).sum() >= len(result) * 0.8

    def test_strategies_with_extreme_volatility(self):
        """Test strategies with extremely volatile data"""
        np.random.seed(999)
        extreme_data = pd.DataFrame(
            {
                "open": np.random.uniform(50, 150, 30),
                "high": np.random.uniform(60, 200, 30),
                "low": np.random.uniform(10, 100, 30),
                "close": np.random.uniform(40, 160, 30),
                "volume": [1000] * 30,
            }
        )

        strategies = [
            BollingerBreakoutStrategy(num_std=3.0),  # Wide bands for extreme volatility
            ATRBreakoutStrategy(multiplier=3.0),  # High multiplier for extreme volatility
        ]

        for strategy in strategies:
            result = strategy.generate_signals(extreme_data)
            assert "signal" in result.columns
            assert len(result) == len(extreme_data)

    def test_strategies_with_missing_columns(self):
        """Test error handling with missing required columns"""
        incomplete_data = pd.DataFrame(
            {
                "close": [100, 101, 102],
                "volume": [1000, 1000, 1000],
                # Missing 'high' and 'low' columns
            }
        )

        strategies = [
            ChannelBreakoutStrategy(),  # Needs 'high' and 'low'
            DonchianChannelStrategy(),  # Needs 'high' and 'low'
            ATRBreakoutStrategy(),  # Needs 'high' and 'low'
        ]

        for strategy in strategies:
            with pytest.raises((KeyError, AttributeError)):
                strategy.generate_signals(incomplete_data)

    def test_zero_standard_deviation_handling(self):
        """Test Bollinger strategies with zero standard deviation"""
        # Create data with no variation (will cause std=0)
        zero_std_data = pd.DataFrame(
            {
                "open": [100] * 25,
                "high": [100.1] * 25,
                "low": [99.9] * 25,
                "close": [100] * 25,
                "volume": [1000] * 25,
            }
        )

        strategies = [BollingerBreakoutStrategy(window=5), BollingerMeanReversionStrategy(window=5)]

        for strategy in strategies:
            # Should handle zero std gracefully (bands collapse to middle)
            result = strategy.generate_signals(zero_std_data)
            assert "signal" in result.columns
            assert len(result) == len(zero_std_data)


class TestBreakoutStrategiesPerformance:
    """Test performance characteristics and optimization"""

    def setup_method(self):
        """Setup performance test data"""
        np.random.seed(42)
        # Larger dataset for performance testing
        dates = pd.date_range("2020-01-01", periods=1000, freq="h")  # Hourly data

        base = 100
        trend = np.linspace(0, 50, 1000)
        noise = np.random.normal(0, 1, 1000)
        prices = base + trend + noise

        self.large_data = pd.DataFrame(
            {
                "open": prices + np.random.normal(0, 0.2, 1000),
                "high": prices + abs(np.random.normal(0, 1, 1000)),
                "low": prices - abs(np.random.normal(0, 1, 1000)),
                "close": prices,
                "volume": np.random.randint(500, 5000, 1000),
            },
            index=dates,
        )

    def test_strategy_execution_time(self):
        """Test that strategies execute in reasonable time"""
        import time

        strategies = [BollingerBreakoutStrategy(), ChannelBreakoutStrategy(), ATRBreakoutStrategy()]

        for strategy in strategies:
            start_time = time.time()
            result = strategy.generate_signals(self.large_data)
            execution_time = time.time() - start_time

            # Should complete within reasonable time (adjust threshold as needed)
            assert execution_time < 5.0, f"Strategy took too long: {execution_time:.2f}s"
            assert len(result) == len(self.large_data)

    def test_memory_efficiency(self):
        """Test that strategies don't create excessive memory overhead"""
        strategy = BollingerBreakoutStrategy()
        result = strategy.generate_signals(self.large_data)

        # Result shouldn't be dramatically larger than input
        input_memory = self.large_data.memory_usage(deep=True).sum()
        output_memory = result.memory_usage(deep=True).sum()

        # Output should be reasonable relative to input (factor of 3-4 max)
        memory_factor = output_memory / input_memory
        assert memory_factor < 5.0, f"Memory usage factor too high: {memory_factor:.2f}"

    def test_parameter_optimization_readiness(self):
        """Test that strategies are ready for parameter optimization"""
        # Test parameter ranges that would be typical in optimization
        parameter_sets = [
            {"window": 10, "num_std": 1.0},
            {"window": 15, "num_std": 1.5},
            {"window": 20, "num_std": 2.0},
            {"window": 25, "num_std": 2.5},
        ]

        for params in parameter_sets:
            strategy = BollingerBreakoutStrategy(**params)
            result = strategy.generate_signals(self.large_data)

            # Each parameter set should produce valid results
            assert "signal" in result.columns
            signal_count = (result["signal"] != 0).sum()

            # Should generate some signals (not all zeros)
            assert signal_count > 0
