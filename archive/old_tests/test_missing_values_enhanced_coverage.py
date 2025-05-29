#!/usr/bin/env python3
"""
Enhanced coverage tests for src/data/transformers/missing_values.py
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.data.transformers.missing_values import MissingValueHandler


class TestMissingValueHandlerComprehensive:
    """Comprehensive tests for MissingValueHandler class"""

    def test_fill_missing_values_forward(self):
        """Test forward fill method"""
        data = pd.DataFrame(
            {"price": [100, np.nan, 102, np.nan, 104], "volume": [1000, 1100, np.nan, 1200, np.nan]}
        )

        result = MissingValueHandler.fill_missing_values(data, method="forward")
        expected_price = [100, 100, 102, 102, 104]
        expected_volume = [1000, 1100, 1100, 1200, 1200]

        assert result["price"].tolist() == expected_price
        assert result["volume"].tolist() == expected_volume

    def test_fill_missing_values_backward(self):
        """Test backward fill method"""
        data = pd.DataFrame(
            {"price": [100, np.nan, 102, np.nan, 104], "volume": [np.nan, 1100, np.nan, 1200, 1300]}
        )

        result = MissingValueHandler.fill_missing_values(data, method="backward")
        # Test that backward fill works correctly
        assert not pd.isna(result["price"].iloc[1])  # Should be filled
        assert not pd.isna(result["volume"].iloc[0])  # Should be filled

    def test_fill_missing_values_mean(self):
        """Test mean imputation method"""
        data = pd.DataFrame(
            {"price": [100, np.nan, 102, np.nan, 104], "volume": [1000, np.nan, 1200, np.nan, 1400]}
        )

        result = MissingValueHandler.fill_missing_values(data, method="mean")
        # Check that mean values are used for imputation
        assert not result.isna().any().any()
        # Check that imputed values are reasonable (around mean)
        assert 100 <= result["price"].iloc[1] <= 104
        assert 1000 <= result["volume"].iloc[1] <= 1400

    def test_fill_missing_values_median(self):
        """Test median imputation method"""
        data = pd.DataFrame(
            {"price": [100, np.nan, 102, np.nan, 108], "volume": [1000, np.nan, 1200, np.nan, 1600]}
        )

        result = MissingValueHandler.fill_missing_values(data, method="median")
        # Check that median values are used
        assert not result.isna().any().any()
        # Median of [100, 102, 108] should be 102
        assert result["price"].iloc[1] == 102

    def test_fill_missing_values_mode(self):
        """Test mode imputation method"""
        data = pd.DataFrame(
            {
                "category": ["A", np.nan, "A", np.nan, "B", "A"],
                "status": [1, np.nan, 1, np.nan, 2, 1],
            }
        )

        result = MissingValueHandler.fill_missing_values(data, method="mode")
        # Check that mode values are used
        assert not result.isna().any().any()
        # Mode of ['A', 'A', 'B', 'A'] should be 'A'
        assert result["category"].iloc[1] == "A"

    def test_fill_missing_values_zero(self):
        """Test zero fill method"""
        data = pd.DataFrame(
            {"price": [100, np.nan, 102, np.nan], "volume": [1000, np.nan, 1200, 1300]}
        )

        result = MissingValueHandler.fill_missing_values(data, method="zero")
        # Check that zeros are used for filling
        assert result["price"].iloc[1] == 0
        assert result["volume"].iloc[1] == 0

    def test_fill_missing_values_with_columns(self):
        """Test specifying specific columns to handle"""
        data = pd.DataFrame({"price": [100, np.nan, 102], "volume": [1000, np.nan, 1200]})

        result = MissingValueHandler.fill_missing_values(
            data, method="forward", columns=["price"]  # Only handle price column
        )
        # Price should be filled, volume should remain NaN
        assert not pd.isna(result["price"].iloc[1])
        assert pd.isna(result["volume"].iloc[1])

    def test_fill_missing_values_invalid_method(self):
        """Test error handling for invalid method"""
        data = pd.DataFrame({"price": [1, np.nan, 3]})

        with pytest.raises(ValueError, match="不支持的填充方法"):
            MissingValueHandler.fill_missing_values(data, method="invalid_method")

    def test_fill_missing_values_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame()
        result = MissingValueHandler.fill_missing_values(empty_df)
        assert len(result) == 0

    def test_fill_missing_values_no_missing(self):
        """Test handling when there are no missing values"""
        data = pd.DataFrame({"price": [100, 101, 102, 103], "volume": [1000, 1100, 1200, 1300]})

        result = MissingValueHandler.fill_missing_values(data, method="forward")
        pd.testing.assert_frame_equal(result, data)

    def test_fill_missing_values_nonexistent_columns(self):
        """Test handling of nonexistent columns"""
        data = pd.DataFrame({"price": [1, np.nan, 3]})

        result = MissingValueHandler.fill_missing_values(
            data, method="forward", columns=["nonexistent_column"]
        )
        # Should return original data unchanged
        pd.testing.assert_frame_equal(result, data)


class TestMissingValueHandlerInterpolation:
    """Test interpolation methods"""

    def test_interpolate_missing_values_linear(self):
        """Test linear interpolation"""
        data = pd.DataFrame(
            {"price": [100, np.nan, np.nan, 106, 108], "volume": [1000, np.nan, 1200, np.nan, 1400]}
        )

        result = MissingValueHandler.interpolate_missing_values(data, method="linear")
        # Check that interpolation fills values reasonably
        assert not pd.isna(result["price"].iloc[1])
        assert not pd.isna(result["price"].iloc[2])
        assert not pd.isna(result["volume"].iloc[1])
        assert not pd.isna(result["volume"].iloc[3])

    def test_interpolate_missing_values_time(self):
        """Test time interpolation with datetime index"""
        dates = pd.date_range("2023-01-01", periods=5, freq="D")
        data = pd.DataFrame({"price": [100, np.nan, np.nan, 104, 105]}, index=dates)

        result = MissingValueHandler.interpolate_missing_values(data, method="time")
        assert not result.isna().any().any()

    def test_interpolate_missing_values_spline(self):
        """Test spline interpolation"""
        data = pd.DataFrame({"price": [100, np.nan, np.nan, 104, 105, 106]})

        result = MissingValueHandler.interpolate_missing_values(data, method="spline")
        assert not result.isna().any().any()

    def test_interpolate_missing_values_polynomial(self):
        """Test polynomial interpolation"""
        data = pd.DataFrame({"price": [100, np.nan, np.nan, 104, 105]})

        result = MissingValueHandler.interpolate_missing_values(data, method="polynomial")
        assert not result.isna().any().any()

    def test_interpolate_with_columns_parameter(self):
        """Test interpolation with specific columns"""
        data = pd.DataFrame(
            {
                "price": [100, np.nan, 102],
                "volume": [1000, np.nan, 1200],
                "category": ["A", np.nan, "C"],  # Non-numeric column
            }
        )

        result = MissingValueHandler.interpolate_missing_values(
            data, method="linear", columns=["price"]
        )
        # Only price should be interpolated
        assert not pd.isna(result["price"].iloc[1])
        assert pd.isna(result["volume"].iloc[1])
        assert pd.isna(result["category"].iloc[1])

    def test_interpolate_invalid_method(self):
        """Test error handling for invalid interpolation method"""
        data = pd.DataFrame({"price": [1, np.nan, 3]})

        with pytest.raises(ValueError, match="不支持的插值方法"):
            MissingValueHandler.interpolate_missing_values(data, method="invalid_method")

    def test_interpolate_non_numeric_columns_skipped(self):
        """Test that non-numeric columns are skipped in interpolation"""
        data = pd.DataFrame({"price": [100, np.nan, 102], "category": ["A", np.nan, "C"]})

        result = MissingValueHandler.interpolate_missing_values(data, method="linear")
        # Price should be interpolated, category should remain NaN
        assert not pd.isna(result["price"].iloc[1])
        assert pd.isna(result["category"].iloc[1])


class TestMissingValueHandlerPatternDetection:
    """Test missing value pattern detection"""

    def test_detect_missing_patterns(self):
        """Test detection of missing value patterns"""
        data = pd.DataFrame(
            {
                "price": [100, np.nan, 102, np.nan, 104],
                "volume": [1000, 1100, np.nan, np.nan, 1400],
                "good_col": [1, 2, 3, 4, 5],
            }
        )

        patterns = MissingValueHandler.detect_missing_patterns(data)

        # Should return DataFrame with missing value statistics
        assert isinstance(patterns, pd.DataFrame)
        assert len(patterns) == 3  # Three columns
        assert "column" in patterns.columns
        assert "missing_count" in patterns.columns
        assert "missing_percent" in patterns.columns
        assert "data_type" in patterns.columns

        # Check that patterns are sorted by missing_percent
        assert patterns["missing_percent"].iloc[0] >= patterns["missing_percent"].iloc[1]

    def test_detect_missing_patterns_empty_dataframe(self):
        """Test pattern detection with empty DataFrame"""
        empty_df = pd.DataFrame()
        patterns = MissingValueHandler.detect_missing_patterns(empty_df)
        assert isinstance(patterns, pd.DataFrame)
        assert len(patterns) == 0

    def test_detect_missing_patterns_no_missing_values(self):
        """Test pattern detection with no missing values"""
        data = pd.DataFrame({"price": [100, 101, 102], "volume": [1000, 1100, 1200]})

        patterns = MissingValueHandler.detect_missing_patterns(data)
        assert all(patterns["missing_count"] == 0)
        assert all(patterns["missing_percent"] == 0)


class TestMissingValueHandlerRowRemoval:
    """Test row removal methods"""

    def test_remove_missing_rows_default_threshold(self):
        """Test removing rows with default threshold"""
        data = pd.DataFrame(
            {"a": [1, np.nan, 3, np.nan], "b": [np.nan, 2, 3, np.nan], "c": [1, 2, np.nan, np.nan]}
        )

        result = MissingValueHandler.remove_missing_rows(data, threshold=0.5)
        # Rows with >50% missing should be removed
        assert len(result) < len(data)

    def test_remove_missing_rows_custom_threshold(self):
        """Test removing rows with custom threshold"""
        data = pd.DataFrame({"a": [1, np.nan, 3], "b": [2, np.nan, 3], "c": [3, 2, np.nan]})

        result = MissingValueHandler.remove_missing_rows(data, threshold=0.3)
        # With 30% threshold, row with 2/3 missing should be removed
        assert len(result) <= len(data)

    def test_remove_missing_rows_with_columns_parameter(self):
        """Test removing rows considering only specific columns"""
        data = pd.DataFrame(
            {
                "important": [1, np.nan, 3, 4],
                "also_important": [2, np.nan, 3, 4],
                "not_important": [np.nan, np.nan, np.nan, np.nan],
            }
        )

        result = MissingValueHandler.remove_missing_rows(
            data, threshold=0.5, columns=["important", "also_important"]
        )
        # Should only consider important columns for threshold calculation
        assert len(result) < len(data)

    def test_remove_missing_rows_no_missing(self):
        """Test removing rows when there are no missing values"""
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        result = MissingValueHandler.remove_missing_rows(data)
        pd.testing.assert_frame_equal(result, data)


class TestMissingValueHandlerColumnRemoval:
    """Test column removal methods"""

    def test_remove_missing_columns_default_threshold(self):
        """Test removing columns with default threshold"""
        data = pd.DataFrame(
            {
                "good_col": [1, 2, 3, 4, 5],  # 0% missing
                "bad_col": [1, np.nan, np.nan, np.nan, 5],  # 60% missing
                "ok_col": [1, np.nan, 3, 4, 5],  # 20% missing
            }
        )

        result = MissingValueHandler.remove_missing_columns(data, threshold=0.5)
        assert "good_col" in result.columns
        assert "ok_col" in result.columns
        assert "bad_col" not in result.columns

    def test_remove_missing_columns_strict_threshold(self):
        """Test removing columns with strict threshold"""
        data = pd.DataFrame({"perfect_col": [1, 2, 3, 4], "one_missing": [1, np.nan, 3, 4]})

        result = MissingValueHandler.remove_missing_columns(data, threshold=0.1)
        assert "perfect_col" in result.columns
        assert "one_missing" not in result.columns

    def test_remove_missing_columns_no_removal(self):
        """Test when no columns should be removed"""
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        result = MissingValueHandler.remove_missing_columns(data)
        pd.testing.assert_frame_equal(result, data)


class TestMissingValueHandlerGroupFill:
    """Test group-based fill methods"""

    def test_fill_with_groups_mean(self):
        """Test group-based mean filling"""
        data = pd.DataFrame(
            {"group": ["A", "A", "B", "B", "A"], "value": [10, np.nan, 20, np.nan, 30]}
        )

        result = MissingValueHandler.fill_with_groups(
            data, group_columns=["group"], target_columns=["value"], method="mean"
        )

        # Check that NaN values are filled with group means
        assert not result.isna().any().any()
        # Group A mean should be (10 + 30) / 2 = 20
        assert result[result["group"] == "A"]["value"].iloc[1] == 20

    def test_fill_with_groups_median(self):
        """Test group-based median filling"""
        data = pd.DataFrame(
            {"category": ["X", "X", "Y", "Y", "X"], "score": [10, np.nan, 50, np.nan, 30]}
        )

        result = MissingValueHandler.fill_with_groups(
            data, group_columns=["category"], target_columns=["score"], method="median"
        )

        assert not result.isna().any().any()

    def test_fill_with_groups_multiple_columns(self):
        """Test group filling with multiple target columns"""
        data = pd.DataFrame(
            {
                "group": ["A", "A", "B", "B"],
                "value1": [10, np.nan, 20, np.nan],
                "value2": [100, np.nan, 200, np.nan],
            }
        )

        result = MissingValueHandler.fill_with_groups(
            data, group_columns=["group"], target_columns=["value1", "value2"], method="mean"
        )

        assert not result.isna().any().any()


class TestMissingValueHandlerSummary:
    """Test missing value summary methods"""

    def test_get_missing_summary(self):
        """Test getting missing value summary"""
        data = pd.DataFrame(
            {
                "price": [100, np.nan, 102, np.nan, 104],
                "volume": [1000, 1100, np.nan, 1200, 1300],
                "complete": [1, 2, 3, 4, 5],
            }
        )

        summary = MissingValueHandler.get_missing_summary(data)

        # Should return dictionary with summary statistics
        assert isinstance(summary, dict)
        assert "total_missing" in summary
        assert "missing_percentage" in summary
        assert "columns_with_missing" in summary

        # Check values
        assert summary["total_missing"] == 3  # 2 in price + 1 in volume
        assert summary["missing_percentage"] == (3 / 15) * 100  # 3 missing out of 15 total values
        assert "price" in summary["columns_with_missing"]
        assert "volume" in summary["columns_with_missing"]
        assert "complete" not in summary["columns_with_missing"]

    def test_get_missing_summary_no_missing(self):
        """Test summary when there are no missing values"""
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

        summary = MissingValueHandler.get_missing_summary(data)
        assert summary["total_missing"] == 0
        assert summary["missing_percentage"] == 0.0
        assert len(summary["columns_with_missing"]) == 0

    def test_get_missing_summary_empty_dataframe(self):
        """Test summary with empty DataFrame"""
        empty_df = pd.DataFrame()
        summary = MissingValueHandler.get_missing_summary(empty_df)

        assert summary["total_missing"] == 0
        assert summary["missing_percentage"] == 0.0
        assert len(summary["columns_with_missing"]) == 0


class TestMissingValueHandlerEdgeCases:
    """Test edge cases and error conditions"""

    def test_single_row_dataframe(self):
        """Test with single row DataFrame"""
        data = pd.DataFrame({"price": [np.nan]})

        result = MissingValueHandler.fill_missing_values(data, method="forward")
        # Forward fill can't fill the first NaN
        assert pd.isna(result["price"].iloc[0])

    def test_single_column_dataframe(self):
        """Test with single column DataFrame"""
        data = pd.DataFrame({"price": [100, np.nan, 102]})

        result = MissingValueHandler.fill_missing_values(data, method="mean")
        assert not result.isna().any().any()
        assert result["price"].iloc[1] == 101  # Mean of 100 and 102

    def test_all_nan_column(self):
        """Test with column that is all NaN"""
        data = pd.DataFrame({"all_nan": [np.nan, np.nan, np.nan], "good": [1, 2, 3]})

        result = MissingValueHandler.fill_missing_values(data, method="mean")
        # All NaN column should remain NaN, good column unchanged
        assert pd.isna(result["all_nan"]).all()
        assert not pd.isna(result["good"]).any()

    def test_mixed_data_types(self):
        """Test with mixed data types"""
        data = pd.DataFrame(
            {
                "numeric": [1.5, np.nan, 2.5],
                "integer": [1, 2, 3],
                "string": ["a", np.nan, "c"],
                "boolean": [True, False, True],
            }
        )

        result = MissingValueHandler.fill_missing_values(data, method="forward")
        assert result["numeric"].iloc[1] == 1.5
        assert result["string"].iloc[1] == "a"

    def test_datetime_index_preservation(self):
        """Test that datetime index is preserved"""
        dates = pd.date_range("2023-01-01", periods=3, freq="D")
        data = pd.DataFrame({"price": [100, np.nan, 102]}, index=dates)

        result = MissingValueHandler.fill_missing_values(data, method="forward")
        assert isinstance(result.index, pd.DatetimeIndex)
        assert (result.index == dates).all()

    def test_multiindex_handling(self):
        """Test with MultiIndex DataFrame"""
        arrays = [["A", "A", "B", "B"], [1, 2, 1, 2]]
        index = pd.MultiIndex.from_arrays(arrays, names=["first", "second"])
        data = pd.DataFrame({"price": [100, np.nan, 102, np.nan]}, index=index)

        result = MissingValueHandler.fill_missing_values(data, method="forward")
        assert result["price"].iloc[1] == 100
