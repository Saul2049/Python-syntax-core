#!/usr/bin/env python3
"""
Enhanced test coverage for src/trading_loop.py backward compatibility layer
"""

import os
import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest

from src import trading_loop


class TestTradingLoopBackwardCompatibility:
    """Test the trading loop backward compatibility layer"""

    def test_all_imports_available(self):
        """Test that all backward compatible imports are available"""
        # Test that we can import all expected functions
        assert hasattr(trading_loop, "fetch_price_data")
        assert hasattr(trading_loop, "calculate_atr")
        assert hasattr(trading_loop, "get_trading_signals")
        assert hasattr(trading_loop, "trading_loop")
        assert hasattr(trading_loop, "TradingEngine")

        # Test that they are callable
        assert callable(trading_loop.fetch_price_data)
        assert callable(trading_loop.calculate_atr)
        assert callable(trading_loop.get_trading_signals)
        assert callable(trading_loop.trading_loop)
        assert callable(trading_loop.TradingEngine)

    def test_module_all_list(self):
        """Test that __all__ contains expected exports"""
        expected_exports = [
            "fetch_price_data",
            "calculate_atr",
            "get_trading_signals",
            "trading_loop",
            "TradingEngine",
        ]

        assert hasattr(trading_loop, "__all__")
        assert set(trading_loop.__all__) == set(expected_exports)

        # Test that all exports are actually available
        for export in expected_exports:
            assert hasattr(trading_loop, export), f"Missing export: {export}"

    def test_backward_compatibility_functions(self):
        """Test that backward compatibility functions are properly imported"""
        # Test that functions exist and are the same as their new locations
        from src.core.price_fetcher import fetch_price_data as new_fetch_price_data
        from src.core.price_fetcher import calculate_atr as new_calculate_atr
        from src.core.signal_processor import get_trading_signals as new_get_trading_signals
        from src.core.trading_engine import trading_loop as new_trading_loop
        from src.core.trading_engine import TradingEngine as NewTradingEngine

        # Test that the functions are the same objects (proper import)
        assert trading_loop.fetch_price_data is new_fetch_price_data
        assert trading_loop.calculate_atr is new_calculate_atr
        assert trading_loop.get_trading_signals is new_get_trading_signals
        assert trading_loop.trading_loop is new_trading_loop
        assert trading_loop.TradingEngine is NewTradingEngine

    def test_module_docstring(self):
        """Test that module has proper documentation"""
        assert trading_loop.__doc__ is not None
        assert "交易循环模块" in trading_loop.__doc__
        assert "Trading Loop Module" in trading_loop.__doc__
        assert "Backward Compatible" in trading_loop.__doc__


class TestTradingLoopMainBlock:
    """Test the main block execution in trading_loop.py"""

    def test_main_block_with_all_env_vars_missing(self):
        """Test main block when all environment variables are missing"""
        # Remove environment variables if they exist
        env_vars_to_remove = ["TG_TOKEN", "API_KEY", "API_SECRET"]
        original_env = {}

        for var in env_vars_to_remove:
            if var in os.environ:
                original_env[var] = os.environ[var]
                del os.environ[var]

        try:
            with patch("src.trading_loop.trading_loop") as mock_trading_loop:
                with patch("builtins.print") as mock_print:
                    # Execute the main block by running the module as script
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-c",
                            'import src.trading_loop; exec(open("src/trading_loop.py").read())',
                        ],
                        capture_output=True,
                        text=True,
                        cwd=".",
                    )

                    # Check that warnings were printed
                    assert "TG_TOKEN" in result.stdout or "未设置TG_TOKEN" in result.stdout
                    assert "API_KEY" in result.stdout or "未设置API_KEY" in result.stdout

        finally:
            # Restore original environment variables
            for var, value in original_env.items():
                os.environ[var] = value

    def test_main_block_with_missing_tg_token(self):
        """Test main block when only TG_TOKEN is missing"""
        # Ensure API keys are present, remove TG_TOKEN
        os.environ["API_KEY"] = "test_api_key"
        os.environ["API_SECRET"] = "test_api_secret"

        original_tg_token = os.environ.get("TG_TOKEN")
        if "TG_TOKEN" in os.environ:
            del os.environ["TG_TOKEN"]

        try:
            # Execute the main block
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    """
import os
import sys
sys.path.insert(0, ".")
from unittest.mock import patch

# Set up environment
os.environ["API_KEY"] = "test_api_key"
os.environ["API_SECRET"] = "test_api_secret"
if "TG_TOKEN" in os.environ:
    del os.environ["TG_TOKEN"]

# Execute main block
with patch("src.core.trading_engine.trading_loop"):
    exec(open("src/trading_loop.py").read())
""",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            # Should warn about missing TG_TOKEN but not API keys
            output = result.stdout + result.stderr
            assert any(keyword in output for keyword in ["TG_TOKEN", "未设置TG_TOKEN"])

        finally:
            # Clean up environment
            if original_tg_token:
                os.environ["TG_TOKEN"] = original_tg_token
            if "API_KEY" in os.environ:
                del os.environ["API_KEY"]
            if "API_SECRET" in os.environ:
                del os.environ["API_SECRET"]

    def test_main_block_with_missing_api_keys(self):
        """Test main block when API keys are missing"""
        # Ensure TG_TOKEN is present, remove API keys
        os.environ["TG_TOKEN"] = "test_tg_token"

        original_api_key = os.environ.get("API_KEY")
        original_api_secret = os.environ.get("API_SECRET")

        if "API_KEY" in os.environ:
            del os.environ["API_KEY"]
        if "API_SECRET" in os.environ:
            del os.environ["API_SECRET"]

        try:
            # Execute the main block
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    """
import os
import sys
sys.path.insert(0, ".")
from unittest.mock import patch

# Set up environment
os.environ["TG_TOKEN"] = "test_tg_token"
if "API_KEY" in os.environ:
    del os.environ["API_KEY"]
if "API_SECRET" in os.environ:
    del os.environ["API_SECRET"]

# Execute main block
with patch("src.core.trading_engine.trading_loop"):
    exec(open("src/trading_loop.py").read())
""",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            # Should warn about missing API keys but not TG_TOKEN
            output = result.stdout + result.stderr
            assert any(keyword in output for keyword in ["API_KEY", "未设置API_KEY", "API_SECRET"])

        finally:
            # Clean up environment
            if "TG_TOKEN" in os.environ:
                del os.environ["TG_TOKEN"]
            if original_api_key:
                os.environ["API_KEY"] = original_api_key
            if original_api_secret:
                os.environ["API_SECRET"] = original_api_secret

    def test_main_block_trading_loop_execution(self):
        """Test that trading_loop is called when running as main"""
        # Set up complete environment
        os.environ["TG_TOKEN"] = "test_tg_token"
        os.environ["API_KEY"] = "test_api_key"
        os.environ["API_SECRET"] = "test_api_secret"

        try:
            # Execute the main block with mocked trading_loop
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    """
import os
import sys
sys.path.insert(0, ".")
from unittest.mock import patch

# Set up environment
os.environ["TG_TOKEN"] = "test_tg_token"
os.environ["API_KEY"] = "test_api_key"
os.environ["API_SECRET"] = "test_api_secret"

# Track if trading_loop was called
trading_loop_called = False

def mock_trading_loop():
    global trading_loop_called
    trading_loop_called = True
    print("TRADING_LOOP_CALLED")

# Execute main block with mock
with patch("src.core.trading_engine.trading_loop", side_effect=mock_trading_loop):
    exec(open("src/trading_loop.py").read())
""",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            # Verify trading_loop was called
            assert "TRADING_LOOP_CALLED" in result.stdout

        finally:
            # Clean up environment
            for var in ["TG_TOKEN", "API_KEY", "API_SECRET"]:
                if var in os.environ:
                    del os.environ[var]


class TestTradingLoopEdgeCases:
    """Test edge cases for trading loop module"""

    def test_module_structure(self):
        """Test module structure and attributes"""
        # Test that the module has expected structure
        assert hasattr(trading_loop, "os")
        assert trading_loop.os is os

        # Test module file path
        assert trading_loop.__file__.endswith("trading_loop.py")

    def test_import_order_and_dependencies(self):
        """Test that imports work correctly and don't cause circular dependencies"""
        # Re-import to ensure no issues
        import importlib

        importlib.reload(trading_loop)

        # Test that all functions are still available after reload
        assert callable(trading_loop.fetch_price_data)
        assert callable(trading_loop.calculate_atr)
        assert callable(trading_loop.get_trading_signals)
        assert callable(trading_loop.trading_loop)
        assert callable(trading_loop.TradingEngine)

    def test_documentation_completeness(self):
        """Test that documentation is complete and helpful"""
        doc = trading_loop.__doc__

        # Check for key documentation elements
        required_elements = [
            "交易循环模块",  # Chinese description
            "Trading Loop Module",  # English description
            "Backward Compatible",  # Compatibility notice
            "Refactoring Notice",  # Refactoring information
            "src.core.trading_engine",  # New module reference
            "src.core.price_fetcher",  # New module reference
            "src.core.signal_processor",  # New module reference
        ]

        for element in required_elements:
            assert element in doc, f"Missing documentation element: {element}"

    def test_all_exports_functionality(self):
        """Test that all exported functions maintain expected signatures"""
        # Test that exported functions have reasonable signatures
        import inspect

        # Get signatures of exported functions
        signatures = {}
        for export in trading_loop.__all__:
            obj = getattr(trading_loop, export)
            if callable(obj) and not inspect.isclass(obj):
                signatures[export] = inspect.signature(obj)

        # Verify signatures exist (basic check)
        assert len(signatures) >= 3  # At least 3 callable functions

        # Test TradingEngine class
        assert inspect.isclass(trading_loop.TradingEngine)
        assert hasattr(trading_loop.TradingEngine, "__init__")
