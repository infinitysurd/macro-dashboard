# data.py — shared data layer for the Macro Market Dashboard

"""
This module provides reusable helpers for:
- Fetching price history from yfinance for tickers in the dashboard.
- Computing daily change, 1-month and 3-month returns.
- Supporting ETF flow panels, catalyst calendars, and watchlist notes
  (placeholders and examples for future extensions).
"""

from typing import Optional, Tuple, Dict, List

import yfinance as yf
import pandas as pd


def get_ticker_history(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d"
) -> pd.DataFrame:
    """
    Download historical price data for a ticker from Yahoo Finance.

    Parameters
    ----------
    symbol : str
        Ticker symbol, e.g. "TLT", "MDI.TO", "BTC-USD", "INR=X".
    period : str
        History period passed to yfinance.history(), e.g. "6mo", "1mo", "1y".
    interval : str
        Interval, e.g. "1d", "1wk".

    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV data. Empty if the request fails or symbol is invalid.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=False)
        if df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def compute_returns(
    df: pd.DataFrame
) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Compute latest price, daily change, daily % change, 1-month % change, and 3-month % change.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with at least a "Close" column and recent rows.

    Returns
    -------
    (last_close, daily_change, daily_pct, one_month_pct, three_month_pct)
        Values are floats or None if not computable.
    """
    if df is None or df.empty or "Close" not in df.columns or len(df) < 2:
        return None, None, None, None, None

    last_close = df["Close"].iloc[-1]
    prev_close = df["Close"].iloc[-2]

    daily_change = last_close - prev_close if pd.notna(prev_close) else None
    daily_pct = (daily_change / prev_close) * 100 if daily_change is not None and prev_close not in (0, None) else None

    # 1-month: ~21 trading days
    idx_1m = -22
    # 3-month: ~63 trading days
    idx_3m = -64

    last = df["Close"].iloc[-1]

    if len(df) >= abs(idx_1m):
        close_1m_ago = df["Close"].iloc[idx_1m]
        one_month_pct = ((last / close_1m_ago) - 1) * 100 if pd.notna(close_1m_ago) and close_1m_ago != 0 else None
    else:
        one_month_pct = None

    if len(df) >= abs(idx_3m):
        close_3m_ago = df["Close"].iloc[idx_3m]
        three_month_pct = ((last / close_3m_ago) - 1) * 100 if pd.notna(close_3m_ago) and close_3m_ago != 0 else None
    else:
        three_month_pct = None

    return float(last_close), float(daily_change) if daily_change is not None else None, (
        float(daily_pct) if daily_pct is not None else None
    ), (
        float(one_month_pct) if one_month_pct is not None else None
    ), (
        float(three_month_pct) if three_month_pct is not None else None
    )


def build_ticker_summary(
    tickers: Dict[str, str],
    period: str = "6mo"
) -> pd.DataFrame:
    """
    Build a summary DataFrame of price and returns for a dict of name -> symbol.

    Parameters
    ----------
    tickers : dict
        {"Name": "SYMBOL", ...}
    period : str
        History period for yfinance.

    Returns
    -------
    pd.DataFrame
        Columns: Name, Symbol, Last, Day_Chg, Day_% , 1M_%, 3M_%
    """
    rows = []
    for name, symbol in tickers.items():
        df = get_ticker_history(symbol, period=period)
        last, chg, pct, m1, m3 = compute_returns(df)
        rows.append({
            "Name": name,
            "Symbol": symbol,
            "Last": round(last, 4) if last is not None else None,
            "Day_Chg": round(chg, 4) if chg is not None else None,
            "Day_%": round(pct, 2) if pct is not None else None,
            "1M_%": round(m1, 2) if m1 is not None else None,
            "3M_%": round(m3, 2) if m3 is not None else None,
        })
    return pd.DataFrame(rows)


#
# Placeholders for future flow / catalyst extensions
# ---

def get_etf_flow_stats(
    etf_symbols: List[str],
    days: int = 5
) -> pd.DataFrame:
    """
    Placeholder for ETF flow statistics.

    For now, returns an empty DataFrame with the expected schema.
    Future implementations can integrate with external flow providers or APIs.

    Returns
    -------
    pd.DataFrame
        Columns: Symbol, Date, Net_Flow, Volume, Price
    """
    df = pd.DataFrame(columns=["Symbol", "Date", "Net_Flow", "Volume", "Price"])
    # Future: wire up to a real data source.
    return df


def get_catalyst_list() -> pd.DataFrame:
    """
    Placeholder for a catalyst calendar (earnings, data, auction schedule, etc.).

    Returns
    -------
    pd.DataFrame
        Columns: Date, Event, Tickers, Impact
    """
    df = pd.DataFrame(columns=["Date", "Event", "Tickers", "Impact"])
    # Future: integrate with an economic calendar or earnings calendar API.
    return df


def get_watchlist_notes() -> pd.DataFrame:
    """
    Placeholder for watchlist notes (MDI, CAR.UN, BTC, etc.).

    Returns
    -------
    pd.DataFrame
        Columns: Ticker, Note, Source, Last_Updated
    """
    df = pd.DataFrame(columns=["Ticker", "Note", "Source", "Last_Updated"])
    # Future: store notes in a local file (CSV/JSON) or small database.
    return df
