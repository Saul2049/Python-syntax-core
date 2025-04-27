import pandas as pd
import numpy as np

def cagr(equity: pd.Series) -> float:
    """
    Calculate Compound Annual Growth Rate from equity curve.
    
    Parameters
    ----------
    equity : pd.Series
        Equity curve indexed by date
        
    Returns
    -------
    float
        CAGR as a decimal (e.g., 0.15 for 15%)
    """
    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25
    return (equity.iloc[-1] / equity.iloc[0]) ** (1/years) - 1

def max_drawdown(equity: pd.Series) -> float:
    """
    Calculate maximum drawdown from peak as a percentage.
    
    Parameters
    ----------
    equity : pd.Series
        Equity curve indexed by date
        
    Returns
    -------
    float
        Max drawdown as a decimal (e.g., -0.35 for -35%)
    """
    return (equity / equity.cummax() - 1).min()

def sharpe(returns: pd.Series, rfr: float = 0.0, periods: int = 252) -> float:
    """
    Calculate annualized Sharpe ratio.
    
    Parameters
    ----------
    returns : pd.Series
        Series of returns (not prices)
    rfr : float, optional
        Risk-free rate, by default 0.0
    periods : int, optional
        Number of periods per year, by default 252 (trading days)
        
    Returns
    -------
    float
        Annualized Sharpe ratio
    """
    if isinstance(returns, pd.Series) and returns.index.inferred_type.startswith('datetime'):
        # If a price series is passed instead of returns, convert it
        returns = returns.pct_change().dropna()
    
    excess_returns = returns - rfr / periods
    return excess_returns.mean() / excess_returns.std() * np.sqrt(periods)
