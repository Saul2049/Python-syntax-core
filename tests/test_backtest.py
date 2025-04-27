# tests/test_backtest.py
from src.backtest import run_backtest

def test_backtest_runs():
    eq = run_backtest()
    # just ensure we got a Series and final equity is finite
    assert eq.iloc[-1] > 0 