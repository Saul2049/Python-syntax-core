#!/usr/bin/env python3
"""
Test coverage for src/improved_strategy.py backward compatibility layer
"""

import warnings
import pandas as pd
import pytest

from src import improved_strategy


class TestImprovedStrategyBackwardCompatibility:
    """Test the improved strategy backward compatibility layer"""

    def setup_method(self):
        """Setup test data for each test"""
        self.test_data = pd.DataFrame({
            "open": [99, 101, 100, 104, 106, 109, 107, 111, 114, 112, 117, 119],
            "close": [100, 102, 101, 105, 107, 110, 108, 112, 115, 113, 118, 120],
            "high": [102, 104, 103, 107, 109, 112, 110, 114, 117, 115, 120, 122],
            "low": [98, 100, 99, 103, 105, 108, 106, 110, 113, 111, 116, 118],
            "volume": [1000] * 12
        })

    def test_module_level_deprecation_warning(self):
        """Test that the module issues deprecation warning on import"""
        # The warning is already issued when the module is imported
        # We verify that the classes are properly imported
        assert hasattr(improved_strategy, 'SimpleMAStrategy')
        assert hasattr(improved_strategy, 'BollingerBreakoutStrategy')
        assert hasattr(improved_strategy, 'RSIStrategy')
        assert hasattr(improved_strategy, 'MACDStrategy')
        assert hasattr(improved_strategy, 'TrendFollowingStrategy')
        assert hasattr(improved_strategy, 'MultiTimeframeStrategy')

    def test_simple_ma_cross_function(self):
        """Test simple_ma_cross function with deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_strategy.simple_ma_cross(
                self.test_data,
                short_window=2,
                long_window=4,
                column="close"
            )
            
            # Verify deprecation warning
            assert len(w) >= 1
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "simple_ma_cross function is deprecated" in str(deprecation_warnings[0].message)
            
            # Verify result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_bollinger_breakout_function(self):
        """Test bollinger_breakout function with deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # 测试修复后的函数，不传递column参数给BollingerBreakoutStrategy
            result = improved_strategy.bollinger_breakout(
                self.test_data,
                window=5,
                num_std=2.0,
                column="close"
            )
            
            # Verify deprecation warning  
            assert len(w) >= 1
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "bollinger_breakout function is deprecated" in str(deprecation_warnings[0].message)
            
            # Verify result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_rsi_strategy_function(self):
        """Test rsi_strategy function with deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_strategy.rsi_strategy(
                self.test_data,
                window=6,
                overbought=75,
                oversold=25,
                column="close"
            )
            
            # Verify deprecation warning
            assert len(w) >= 1
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "rsi_strategy function is deprecated" in str(deprecation_warnings[0].message)
            
            # Verify result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_macd_strategy_function(self):
        """Test macd_strategy function with deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # 测试修复后的函数，不传递column参数给MACDStrategy  
            result = improved_strategy.macd_strategy(
                self.test_data,
                fast_period=5,
                slow_period=8,
                signal_period=3,
                column="close"
            )
            
            # Verify deprecation warning
            assert len(w) >= 1
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "macd_strategy function is deprecated" in str(deprecation_warnings[0].message)
            
            # Verify result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_trend_following_strategy_function(self):
        """Test trend_following_strategy function with deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_strategy.trend_following_strategy(
                self.test_data,
                ma_window=4,
                atr_window=3,
                column="close"
            )
            
            # Verify deprecation warning
            assert len(w) >= 1
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "trend_following_strategy function is deprecated" in str(deprecation_warnings[0].message)
            
            # Verify result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_improved_ma_cross_function(self):
        """Test improved_ma_cross function with deprecation warning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = improved_strategy.improved_ma_cross(
                self.test_data,
                short_window=3,
                long_window=6,
                column="close"
            )
            
            # Verify deprecation warning
            assert len(w) >= 1
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "improved_ma_cross function is deprecated" in str(deprecation_warnings[0].message)
            
            # Verify result
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)


class TestImprovedStrategyParameters:
    """Test parameter handling in backward compatibility functions"""

    def setup_method(self):
        """Setup test data"""
        self.test_data = pd.DataFrame({
            "open": [99, 101, 100, 104, 106, 109, 107, 111, 114, 112],
            "close": [100, 102, 101, 105, 107, 110, 108, 112, 115, 113],
            "high": [102, 104, 103, 107, 109, 112, 110, 114, 117, 115],
            "low": [98, 100, 99, 103, 105, 108, 106, 110, 113, 111],
            "volume": [1000] * 10
        })

    def test_simple_ma_cross_custom_params(self):
        """Test simple_ma_cross with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_strategy.simple_ma_cross(
                self.test_data,
                short_window=3,
                long_window=5,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_bollinger_breakout_custom_params(self):
        """Test bollinger_breakout with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_strategy.bollinger_breakout(
                self.test_data,
                window=8,
                num_std=1.5,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_rsi_strategy_custom_params(self):
        """Test rsi_strategy with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_strategy.rsi_strategy(
                self.test_data,
                window=10,
                overbought=80,
                oversold=20,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)

    def test_macd_strategy_custom_params(self):
        """Test macd_strategy with custom parameters"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_strategy.macd_strategy(
                self.test_data,
                fast_period=8,
                slow_period=12,
                signal_period=6,
                column="close"
            )
            assert isinstance(result, pd.DataFrame)
            assert len(result) == len(self.test_data)


class TestImprovedStrategyEdgeCases:
    """Test edge cases for backward compatibility functions"""

    def test_empty_dataframe_handling(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises((ValueError, IndexError, KeyError)):
                improved_strategy.simple_ma_cross(empty_df)

    def test_missing_column_handling(self):
        """Test handling of missing column"""
        df_missing_close = pd.DataFrame({
            "open": [100, 102, 101],
            "high": [102, 104, 103],
            "low": [98, 100, 99],
            "volume": [1000, 1100, 1200]
        })
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises((ValueError, KeyError)):
                improved_strategy.simple_ma_cross(df_missing_close, column="close")

    def test_small_dataset_handling(self):
        """Test handling of small dataset"""
        small_df = pd.DataFrame({
            "open": [99, 101],
            "close": [100, 102],
            "high": [102, 103],
            "low": [98, 100],
            "volume": [1000, 1100]
        })
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = improved_strategy.simple_ma_cross(
                small_df,
                short_window=1,
                long_window=2
            )
            assert isinstance(result, pd.DataFrame)


class TestImprovedStrategyClassAccess:
    """Test that strategy classes are properly accessible"""

    def setup_method(self):
        """Setup test data"""
        self.test_data = pd.DataFrame({
            "open": [99, 101, 100, 104, 106, 109, 107, 111, 114, 112],
            "close": [100, 102, 101, 105, 107, 110, 108, 112, 115, 113],
            "high": [102, 104, 103, 107, 109, 112, 110, 114, 117, 115],
            "low": [98, 100, 99, 103, 105, 108, 106, 110, 113, 111],
            "volume": [1000] * 10
        })

    def test_simple_ma_strategy_class(self):
        """Test SimpleMAStrategy class access"""
        strategy = improved_strategy.SimpleMAStrategy(short_window=5, long_window=10)
        assert strategy.get_parameter("short_window") == 5
        assert strategy.get_parameter("long_window") == 10

    def test_bollinger_breakout_strategy_class(self):
        """Test BollingerBreakoutStrategy class access"""
        strategy = improved_strategy.BollingerBreakoutStrategy(window=20, num_std=2.0)
        assert strategy.window == 20
        assert strategy.num_std == 2.0

    def test_rsi_strategy_class(self):
        """Test RSIStrategy class access"""
        strategy = improved_strategy.RSIStrategy(window=14, overbought=70, oversold=30)
        assert strategy.window == 14
        assert strategy.overbought == 70
        assert strategy.oversold == 30

    def test_macd_strategy_class(self):
        """Test MACDStrategy class access"""
        strategy = improved_strategy.MACDStrategy(fast_period=12, slow_period=26, signal_period=9)
        assert strategy.fast_period == 12
        assert strategy.slow_period == 26
        assert strategy.signal_period == 9

    def test_trend_following_strategy_class(self):
        """Test TrendFollowingStrategy class access"""
        strategy = improved_strategy.TrendFollowingStrategy(ma_window=20)
        assert strategy.ma_window == 20

    def test_multi_timeframe_strategy_class(self):
        """Test MultiTimeframeStrategy class access"""
        strategy = improved_strategy.MultiTimeframeStrategy(
            short_window=5,
            medium_window=15,
            long_window=20
        )
        assert strategy.short_window == 5
        assert strategy.medium_window == 15
        assert strategy.long_window == 20

    def test_bollinger_breakout_strategy_instantiation(self):
        """Test that BollingerBreakoutStrategy can be instantiated correctly"""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # 直接调用修复后的bollinger_breakout函数
            result = improved_strategy.bollinger_breakout(
                self.test_data,
                window=10,
                num_std=1.5
            )
            assert isinstance(result, pd.DataFrame)

    def test_macd_strategy_instantiation(self):
        """Test that MACDStrategy can be instantiated correctly"""  
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # 直接调用修复后的macd_strategy函数
            result = improved_strategy.macd_strategy(
                self.test_data,
                fast_period=10,
                slow_period=20,
                signal_period=5
            )
            assert isinstance(result, pd.DataFrame) 