import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import re

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Market Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈",
)

# ── Dark mode state (must initialise before any widget) ───────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
_dark = st.session_state.dark_mode

# ── Colour palette ────────────────────────────────────────────────────────────
if _dark:
    BG        = "#0e1117"
    SURFACE   = "#1a1d2e"
    SURFACE2  = "#252840"
    BORDER    = "#363a55"
    TXT       = "#e6e9f4"
    TXT_MUTED = "#8d97b8"
    ACCENT    = "#d4a820"
    UP        = "#28d980"
    DOWN      = "#ff4c4c"
else:
    BG        = "#f0f2f5"
    SURFACE   = "#ffffff"
    SURFACE2  = "#e4e6ea"
    BORDER    = "#ced0d4"
    TXT       = "#1c1e21"
    TXT_MUTED = "#606770"
    ACCENT    = "#b8860b"
    UP        = "#0a7a3c"
    DOWN      = "#cc1f1f"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="block-container"] {{
    background-color: {BG} !important;
    color: {TXT} !important;
    font-family: 'Segoe UI', 'Inter', sans-serif !important;
}}
[data-testid="stSidebar"] {{
    background-color: {SURFACE} !important;
    border-right: 1px solid {BORDER} !important;
}}
[data-testid="stSidebar"] * {{ color: {TXT} !important; }}
.dash-header {{
    background: linear-gradient(90deg, {SURFACE2} 0%, {SURFACE} 60%, {SURFACE2} 100%);
    border-bottom: 2px solid {ACCENT};
    padding: 12px 24px 10px;
    margin-bottom: 14px;
    border-radius: 0 0 4px 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.10);
}}
.dash-header h1 {{ color:{ACCENT}; margin:0; font-size:1.2rem; letter-spacing:3px; font-weight:700; }}
.dash-header small {{ color:{TXT_MUTED}; font-size:0.7rem; letter-spacing:1px; }}
[data-testid="stMetric"] {{
    background-color:{SURFACE} !important;
    border:1px solid {BORDER} !important;
    border-radius:6px !important;
    padding:10px 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
[data-testid="stMetricLabel"]  {{ color:{TXT_MUTED}!important; font-size:0.67rem!important;
    letter-spacing:1px!important; text-transform:uppercase!important; }}
[data-testid="stMetricValue"]  {{ color:{TXT}!important; font-size:1.05rem!important; font-weight:700!important; }}
[data-testid="stMetricDelta"] svg {{ display:none!important; }}
[data-testid="stMetricDelta"][data-direction="up"]   {{ color:{UP}!important; font-weight:600!important; }}
[data-testid="stMetricDelta"][data-direction="down"] {{ color:{DOWN}!important; font-weight:600!important; }}
[data-testid="stTabs"] button {{
    color:{TXT_MUTED}!important; font-size:0.75rem!important;
    letter-spacing:1px!important; text-transform:uppercase!important;
    border-bottom:2px solid transparent!important; padding:8px 16px!important;
}}
[data-testid="stTabs"] button[aria-selected="true"] {{
    color:{ACCENT}!important; border-bottom:2px solid {ACCENT}!important;
    background:transparent!important; font-weight:700!important;
}}
[data-testid="stTabs"] [role="tablist"] {{ border-bottom:1px solid {BORDER}!important; }}
.sec {{
    color:{ACCENT}; font-size:0.67rem; letter-spacing:2px; text-transform:uppercase;
    font-weight:700; border-bottom:1px solid {BORDER}; padding-bottom:5px; margin:16px 0 10px 0;
}}
.badge-on  {{ background:#d4f4e2; color:{UP};   border:1px solid {UP};
    padding:3px 12px; border-radius:4px; font-size:0.74rem; font-weight:700; }}
.badge-off {{ background:#fde8e8; color:{DOWN}; border:1px solid {DOWN};
    padding:3px 12px; border-radius:4px; font-size:0.74rem; font-weight:700; }}
.badge-neu {{ background:#fef9e7; color:#7d6608; border:1px solid #c8a416;
    padding:3px 12px; border-radius:4px; font-size:0.74rem; font-weight:700; }}
.rate-box {{
    background:{SURFACE}; border:1px solid {BORDER}; border-radius:6px;
    padding:12px 16px; margin:4px 0; font-size:0.82rem; color:{TXT};
}}
.rate-box strong {{ color:{ACCENT}; }}
textarea, [data-baseweb="textarea"] textarea {{
    background-color:{SURFACE}!important; color:{TXT}!important;
    font-size:0.82rem!important; border:1px solid {BORDER}!important; border-radius:4px!important;
}}
input, [data-baseweb="input"] input {{
    background-color:{SURFACE}!important; color:{TXT}!important;
    border:1px solid {BORDER}!important;
}}
[data-testid="stDataFrame"] {{ border:1px solid {BORDER}!important;
    border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.05); }}
hr {{ border-color:{BORDER}!important; margin:8px 0!important; }}
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:{BG}; }}
::-webkit-scrollbar-thumb {{ background:{BORDER}; border-radius:3px; }}
</style>
""", unsafe_allow_html=True)

# ── Plotly base theme ─────────────────────────────────────────────────────────
PT_BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=SURFACE,
    font=dict(color=TXT_MUTED, family="Segoe UI, sans-serif", size=11),
    margin=dict(l=52, r=20, t=54, b=40),
)
XAXIS_STYLE = dict(gridcolor=SURFACE2, linecolor=BORDER, showgrid=True, zeroline=False,
                   tickfont=dict(size=10, color=TXT_MUTED))
YAXIS_STYLE = dict(gridcolor=SURFACE2, linecolor=BORDER, showgrid=True, zeroline=False,
                   tickfont=dict(size=10, color=TXT_MUTED))

def yax(**overrides):
    """Return YAXIS_STYLE merged with overrides — avoids duplicate-kwarg TypeError."""
    return {**YAXIS_STYLE, **overrides}

def xax(**overrides):
    return {**XAXIS_STYLE, **overrides}

LEGEND_H = dict(
    orientation="h", yanchor="top", y=-0.18,
    xanchor="center", x=0.5,
    bgcolor="rgba(0,0,0,0)",
    font=dict(size=10, color=TXT_MUTED),
)

def theme(fig, height: int = 320, title: str = ""):
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(color=ACCENT, size=12), x=0.01, xanchor="left"),
        showlegend=False,
        **PT_BASE,
    )
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(**YAXIS_STYLE)
    return fig

# ── Ticker universe ───────────────────────────────────────────────────────────
BASE_TICKERS = {
    "Rates":    {"2Y":"^IRX","5Y":"^FVX","10Y":"^TNX","30Y":"^TYX"},
    "Equities": {"S&P 500":"^GSPC","Dow":"^DJI","Nasdaq":"^IXIC","Russell 2000":"^RUT","VIX":"^VIX"},
    "FX":       {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"JPY=X",
                 "USD/CAD":"CAD=X","AUD/USD":"AUDUSD=X","USD/INR":"INR=X"},
    "Crypto":   {"BTC":"BTC-USD","ETH":"ETH-USD","IBIT":"IBIT"},
}
FOCUS_TICKERS = {
    "TLT":"TLT","MDI":"MDI.TO","CAR.UN":"CAR-UN.TO",
    "IBIT":"IBIT","BTC":"BTC-USD","USD/INR":"INR=X",
    "10Y":"^TNX","30Y":"^TYX","VIX":"^VIX",
}
YIELD_CURVE = {"2Y":("^IRX",2),"5Y":("^FVX",5),"10Y":("^TNX",10),"30Y":("^TYX",30)}

MOVERS_UNIVERSE = {
    "S&P 500":"^GSPC","Nasdaq":"^IXIC","Russell":"^RUT","Dow":"^DJI",
    "TLT":"TLT","HYG":"HYG","LQD":"LQD","Gold":"GC=F",
    "BTC":"BTC-USD","ETH":"ETH-USD","IBIT":"IBIT",
    "MDI":"MDI.TO","CAR.UN":"CAR-UN.TO",
    "EUR":"EURUSD=X","JPY":"JPY=X","INR":"INR=X",
    "VIX":"^VIX",
}

# Timeframe map → (yfinance period, bars to tail or None)
TF_MAP = {
    "3D":  ("5d",   3),
    "7D":  ("1mo",  7),
    "15D": ("1mo",  15),
    "1M":  ("1mo",  None),
    "3M":  ("3mo",  None),
    "6M":  ("6mo",  None),
    "1Y":  ("1y",   None),
}

# ── Utilities ─────────────────────────────────────────────────────────────────
def hex_rgba(hex_c: str, alpha: float = 0.12) -> str:
    h = hex_c.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def sec(label: str):
    st.markdown(f'<div class="sec">▸ {label}</div>', unsafe_allow_html=True)

def no_data(label: str):
    st.markdown(
        f'<div style="background:{SURFACE2};border:1px solid {BORDER};border-radius:6px;'
        f'padding:20px;text-align:center;color:{TXT_MUTED};font-size:0.8rem;">'
        f'⚠ No data — {label}</div>', unsafe_allow_html=True)

def pct_color(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return TXT_MUTED
    return UP if v >= 0 else DOWN

# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def latest_metrics(df):
    if df is None or df.empty or len(df) < 2:
        return None, None, None
    last = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])
    chg  = last - prev
    pct  = (chg / prev) * 100 if prev else None
    return last, chg, pct

def _pct_n(series: pd.Series, n: int):
    """Return % change over last n bars; None if insufficient data."""
    if series is None or len(series) <= n:
        return None
    v = ((series.iloc[-1] / series.iloc[-(n+1)]) - 1) * 100
    return round(float(v), 2)

def build_table(tickers: dict) -> pd.DataFrame:
    rows = []
    for name, symbol in tickers.items():
        df = load_history(symbol)
        last, chg, pct = latest_metrics(df)
        d3 = d7 = d15 = m1 = m3 = m6 = None
        if df is not None and not df.empty:
            c = df["Close"]
            d3  = _pct_n(c, 3)
            d7  = _pct_n(c, 7)
            d15 = _pct_n(c, 15)
            m1  = _pct_n(c, 21)
            m3  = _pct_n(c, 63)
            m6  = _pct_n(c, 126)
        rows.append({
            "Name":    name,
            "Ticker":  symbol,
            "Last":    round(last, 4) if last is not None else None,
            "Day Chg": round(chg,  4) if chg  is not None else None,
            "Day %":   round(pct,  2) if pct  is not None else None,
            "3D %":    d3,
            "7D %":    d7,
            "15D %":   d15,
            "1M %":    m1,
            "3M %":    m3,
            "6M %":    m6,
        })
    return pd.DataFrame(rows)

def render_table(df: pd.DataFrame):
    cfg = {}
    for c in df.columns:
        if "%" in c:
            cfg[c] = st.column_config.NumberColumn(c, format="%.2f %%")
        elif c == "Last":
            cfg[c] = st.column_config.NumberColumn("Last",    format="%.4f")
        elif c == "Day Chg":
            cfg[c] = st.column_config.NumberColumn("Day Chg", format="%.4f")
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=cfg)

def metric_strip(df: pd.DataFrame):
    cols = st.columns(len(df))
    for col, (_, row) in zip(cols, df.iterrows()):
        last = row.get("Last"); pct = row.get("Day %")
        val = "—" if (last is None or pd.isna(last)) else f"{last:,.2f}"
        d   = None if (pct  is None or pd.isna(pct))  else f"{pct:+.2f}%"
        col.metric(row["Name"], val, d)

# ── Technical indicators ──────────────────────────────────────────────────────
def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def intel_scorecard(symbol: str) -> dict:
    df = load_history(symbol, period="1y")
    if df is None or df.empty or len(df) < 20:
        return {}
    c = df["Close"]
    rsi   = compute_rsi(c).iloc[-1]
    ma50  = c.rolling(50).mean().iloc[-1]  if len(c) >= 50  else None
    ma200 = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else None
    hi52  = c.rolling(252).max().iloc[-1]  if len(c) >= 252 else c.max()
    lo52  = c.rolling(252).min().iloc[-1]  if len(c) >= 252 else c.min()
    price = c.iloc[-1]
    rng_pct = ((price - lo52) / (hi52 - lo52) * 100) if (hi52 - lo52) > 0 else None
    mom5d   = ((price / c.iloc[-6]) - 1) * 100 if len(c) >= 6 else None
    return {
        "price": price, "rsi": rsi,
        "vs_50ma":       ((price/ma50  - 1)*100) if ma50  else None,
        "vs_200ma":      ((price/ma200 - 1)*100) if ma200 else None,
        "52w_range_pct": rng_pct,
        "mom_5d":        mom5d,
    }

# ── Chart helpers ─────────────────────────────────────────────────────────────
def plotly_line(symbol: str, title: str = "", color: str = ACCENT, height: int = 300,
                period: str = "6mo"):
    df = load_history(symbol, period=period)
    if df is None or df.empty:
        no_data(title or symbol); return
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["Close"], mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=hex_rgba(color, 0.08),
        hovertemplate="<b>%{x|%b %d %Y}</b><br>%{y:,.4f}<extra></extra>",
    ))
    theme(fig, height=height, title=title)
    st.plotly_chart(fig, use_container_width=True)


def plotly_candle(symbol: str, title: str = "", period: str = "3mo", height: int = 380):
    df = load_history(symbol, period=period)
    if df is None or df.empty:
        no_data(title or symbol); return
    has_vol = "Volume" in df.columns and df["Volume"].fillna(0).sum() > 0
    fig = make_subplots(rows=2 if has_vol else 1, cols=1,
                        shared_xaxes=True,
                        row_heights=[0.77, 0.23] if has_vol else [1.0],
                        vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing=dict(line=dict(color=UP, width=1),   fillcolor=hex_rgba(UP,   0.7)),
        decreasing=dict(line=dict(color=DOWN, width=1), fillcolor=hex_rgba(DOWN, 0.7)),
        name=title, hoverlabel=dict(bgcolor=SURFACE2),
    ), row=1, col=1)
    if has_vol:
        vcols = [hex_rgba(UP if c >= o else DOWN, 0.6)
                 for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"],
                             marker_color=vcols, showlegend=False), row=2, col=1)
    fig.update_layout(xaxis_rangeslider_visible=False, **PT_BASE, height=height,
                      title=dict(text=title, font=dict(color=ACCENT, size=12), x=0.01))
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(**YAXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)


def plotly_yield_curve():
    tenors, yields = [], []
    for _, (sym, tenor) in YIELD_CURVE.items():
        df = load_history(sym)
        if df is not None and not df.empty:
            tenors.append(tenor)
            yields.append(float(df["Close"].iloc[-1]))
    if not tenors:
        no_data("Yield Curve"); return
    fig = go.Figure(go.Scatter(
        x=tenors, y=yields, mode="lines+markers+text",
        text=[f"{y:.2f}%" for y in yields],
        textposition="top center",
        textfont=dict(color=ACCENT, size=11),
        line=dict(color=ACCENT, width=2.5),
        marker=dict(color=ACCENT, size=9, line=dict(color=BG, width=2)),
        fill="tozeroy", fillcolor=hex_rgba(ACCENT, 0.07),
        hovertemplate="<b>%{x}Y Treasury</b>: %{y:.3f}%<extra></extra>",
    ))
    fig.update_layout(**PT_BASE, height=300,
                      title=dict(text="U.S. Treasury Yield Curve — Snapshot",
                                 font=dict(color=ACCENT, size=12), x=0.01))
    fig.update_xaxes(tickvals=tenors, ticktext=[f"{t}Y" for t in tenors], **XAXIS_STYLE)
    fig.update_yaxes(**yax(tickformat=".2f", ticksuffix="%"))
    st.plotly_chart(fig, use_container_width=True)


def plotly_multi_line(series_map: dict, title: str, height: int = 360,
                      pct_base: bool = True, tf_label: str = "6M"):
    """Multi-line chart with configurable timeframe and clean legend below chart."""
    yf_period, tail_bars = TF_MAP.get(tf_label, ("6mo", None))
    fig = go.Figure()
    for label, (sym, color) in series_map.items():
        df = load_history(sym, period=yf_period)
        if df is None or df.empty:
            continue
        if tail_bars:
            df = df.tail(tail_bars + 1)
        y = df["Close"]
        if pct_base:
            y = (y / y.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=y, mode="lines", name=label,
            line=dict(color=color, width=1.8),
            hovertemplate=f"<b>{label}</b>: %{{y:.2f}}{'%' if pct_base else ''}<extra></extra>",
        ))
    suffix = "% Return" if pct_base else ""
    fig.update_layout(
        legend=LEGEND_H,
        showlegend=True,
        **{**PT_BASE, "margin": dict(l=52, r=20, t=54, b=80)},
        height=height,
        title=dict(text=f"{title} — {tf_label}", font=dict(color=ACCENT, size=12), x=0.01),
    )
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(**yax(ticksuffix="%" if pct_base else ""))
    st.plotly_chart(fig, use_container_width=True)


def plotly_rsi(symbol: str, height: int = 200):
    df = load_history(symbol, period="6mo")
    if df is None or df.empty:
        return
    rsi = compute_rsi(df["Close"])
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor=hex_rgba(DOWN, 0.07), line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor=hex_rgba(UP,   0.07), line_width=0)
    for lvl, col in [(70, DOWN), (30, UP), (50, BORDER)]:
        fig.add_hline(y=lvl, line_dash="dot", line_color=col, line_width=1)
    fig.add_trace(go.Scatter(x=df.index, y=rsi, mode="lines",
                             line=dict(color=ACCENT, width=1.8),
                             hovertemplate="RSI: %{y:.1f}<extra></extra>"))
    fig.update_layout(**PT_BASE, height=height,
                      title=dict(text="RSI (14)", font=dict(color=ACCENT, size=11), x=0.01))
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(**yax(range=[0, 100], tickvals=[30, 50, 70]))
    st.plotly_chart(fig, use_container_width=True)


# ── Duration vs Yield — Rate Effect Chart ─────────────────────────────────────
def plotly_duration_yield(tf_label: str = "6M"):
    """TLT actual return vs theoretical rate effect and 10Y yield — dual axis."""
    yf_period, tail_bars = TF_MAP.get(tf_label, ("6mo", None))
    tlt_df = load_history("TLT",  period=yf_period)
    tny_df = load_history("^TNX", period=yf_period)

    if tlt_df is None or tlt_df.empty or tny_df is None or tny_df.empty:
        no_data("Duration vs Yield"); return

    if tail_bars:
        tlt_df = tlt_df.tail(tail_bars + 1)
        tny_df = tny_df.tail(tail_bars + 1)

    MOD_DUR = 16.5  # TLT approximate modified duration

    combined = pd.concat([
        tlt_df["Close"].rename("TLT"),
        tny_df["Close"].rename("Yield10Y"),
    ], axis=1).dropna()

    if len(combined) < 3:
        no_data("Duration vs Yield (insufficient data)"); return

    tlt_ret    = (combined["TLT"] / combined["TLT"].iloc[0] - 1) * 100
    yield_chg  = combined["Yield10Y"] - combined["Yield10Y"].iloc[0]   # in % points
    rate_effect = -MOD_DUR * (yield_chg / 100) * 100                   # convert: Δyield in decimal × dur → % price

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(
        x=combined.index, y=tlt_ret, name="TLT Actual Return (%)",
        line=dict(color=ACCENT, width=2.2),
        hovertemplate="<b>TLT Return</b>: %{y:.2f}%<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=combined.index, y=rate_effect, name=f"Rate Effect (−{MOD_DUR}× Δyield)",
        line=dict(color="#3399ff", width=1.6, dash="dash"),
        hovertemplate="<b>Rate Effect</b>: %{y:.2f}%<extra></extra>",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=combined.index, y=combined["Yield10Y"], name="10Y Yield (%)",
        line=dict(color=DOWN, width=1.4),
        fill="tozeroy", fillcolor=hex_rgba(DOWN, 0.05),
        hovertemplate="<b>10Y Yield</b>: %{y:.3f}%<extra></extra>",
    ), secondary_y=True)

    cur_yield = combined["Yield10Y"].iloc[-1]
    cur_tlt   = tlt_ret.iloc[-1]

    fig.update_layout(
        **{**PT_BASE, "margin": dict(l=52, r=60, t=54, b=90)},
        height=400,
        title=dict(
            text=f"TLT vs 10Y Yield — Duration Rate Effect (ModDur ≈ {MOD_DUR}yr)  |  {tf_label}",
            font=dict(color=ACCENT, size=12), x=0.01),
        legend=LEGEND_H,
        showlegend=True,
    )
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(**yax(ticksuffix="%", title_text="% Return"), secondary_y=False)
    fig.update_yaxes(**yax(ticksuffix="%", title_text="Yield (%)", showgrid=False),
                     secondary_y=True)

    # Sensitivity callout box
    bp25_impact = -MOD_DUR * 0.0025 * 100
    bp50_cut    = +MOD_DUR * 0.005  * 100
    fig.add_annotation(
        x=0.99, y=0.04, xref="paper", yref="paper",
        text=(f"<b>Rate Sensitivity</b><br>"
              f"ModDur: {MOD_DUR}yr  |  1bp ≈ {MOD_DUR/100:.2f}%<br>"
              f"+25bp hike → TLT {bp25_impact:+.1f}%<br>"
              f"−50bp cut  → TLT {bp50_cut:+.1f}%<br>"
              f"10Y now: {cur_yield:.3f}%  |  TLT: {cur_tlt:+.1f}%"),
        font=dict(size=9, color=TXT_MUTED), align="right",
        xanchor="right", yanchor="bottom", showarrow=False,
        bgcolor=SURFACE2, bordercolor=BORDER, borderwidth=1,
    )
    st.plotly_chart(fig, use_container_width=True)


# ── FX — INR Currency Exposure Chart ─────────────────────────────────────────
def plotly_inr_exposure():
    """INR vs USD and CAD performance across 1M, 3M, 6M, 1Y timeframes."""
    inr_df = load_history("INR=X", period="1y")   # USD/INR
    cad_df = load_history("CAD=X", period="1y")   # USD/CAD

    if inr_df is None or inr_df.empty:
        no_data("INR/USD data"); return
    if cad_df is None or cad_df.empty:
        no_data("USD/CAD data"); return

    combined = pd.concat([
        inr_df["Close"].rename("USDINR"),
        cad_df["Close"].rename("USDCAD"),
    ], axis=1).dropna()

    if len(combined) < 22:
        no_data("INR data — insufficient history"); return

    # CAD/INR cross: how many INR per 1 CAD = USDINR / USDCAD
    combined["CADINR"] = combined["USDINR"] / combined["USDCAD"]

    period_bars = {"1M": 21, "3M": 63, "6M": 126, "1Y": 251}

    rows = []
    for label, n in period_bars.items():
        if len(combined) <= n:
            continue
        usdinr_pct = ((combined["USDINR"].iloc[-1] / combined["USDINR"].iloc[-(n+1)]) - 1) * 100
        cadinr_pct = ((combined["CADINR"].iloc[-1] / combined["CADINR"].iloc[-(n+1)]) - 1) * 100
        usdcad_pct = ((combined["USDCAD"].iloc[-1] / combined["USDCAD"].iloc[-(n+1)]) - 1) * 100
        rows.append({
            "Period":    label,
            "INR vs USD": round(-usdinr_pct, 2),   # positive = INR gained vs USD
            "INR vs CAD": round(-cadinr_pct, 2),   # positive = INR gained vs CAD
            "USD vs CAD": round(usdcad_pct,  2),   # reference benchmark
        })

    if not rows:
        no_data("Insufficient history for INR exposure"); return

    perf_df = pd.DataFrame(rows)

    # ── Metric strip ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    def _m(df, period, col):
        r = df[df["Period"] == period]
        return r[col].values[0] if not r.empty else None

    for col_w, period in zip([c1, c2, c3, c4], ["1M", "3M", "6M", "1Y"]):
        v_usd = _m(perf_df, period, "INR vs USD")
        v_cad = _m(perf_df, period, "INR vs CAD")
        if v_usd is not None:
            col_w.metric(f"INR/USD ({period})", f"{v_usd:+.2f}%",
                         delta_color="normal" if v_usd >= 0 else "inverse")
        if v_cad is not None:
            col_w.metric(f"INR/CAD ({period})", f"{v_cad:+.2f}%",
                         delta_color="normal" if v_cad >= 0 else "inverse")

    st.markdown("")

    # ── Grouped bar chart ─────────────────────────────────────────────────────
    # Three clearly distinct colours: orange / teal / purple
    palette = {
        "INR vs USD": "#f7931a",   # orange  — warm, stands out
        "INR vs CAD": "#00c4aa",   # teal    — cool, clearly different
        "USD vs CAD": "#9c27b0",   # purple  — benchmark reference
    }
    fig = go.Figure()
    for series, color in palette.items():
        values = perf_df[series].tolist()
        # Positive bar = full opacity, negative = 60% opacity of same colour
        bar_clrs = [color if v >= 0 else hex_rgba(color, 0.55) for v in values]
        fig.add_trace(go.Bar(
            name=series, x=perf_df["Period"], y=values,
            marker_color=bar_clrs,
            marker_line=dict(width=1, color=color),
            text=[f"{v:+.2f}%" for v in values],
            textposition="outside",
            textfont=dict(size=9, color=TXT_MUTED),
            hovertemplate=f"<b>{series}</b>  %{{x}}: %{{y:+.2f}}%<extra></extra>",
        ))

    fig.update_layout(
        barmode="group",
        **{**PT_BASE, "margin": dict(l=52, r=20, t=54, b=90)},
        height=380,
        title=dict(
            text="INR Performance vs USD & CAD (positive = INR gained)",
            font=dict(color=ACCENT, size=12), x=0.01),
        legend=LEGEND_H,
        showlegend=True,
    )
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(**yax(ticksuffix="%", zeroline=True, zerolinecolor=BORDER, zerolinewidth=1))
    fig.add_hline(y=0, line_color=BORDER, line_width=1)
    st.plotly_chart(fig, use_container_width=True)

    # ── Indexed line chart (1Y) ────────────────────────────────────────────────
    fig2 = go.Figure()
    inr_usd_idx  = (combined["USDINR"].iloc[0] / combined["USDINR"]) * 100   # up = INR stronger
    inr_cad_idx  = (combined["CADINR"].iloc[0] / combined["CADINR"]) * 100   # up = INR stronger vs CAD
    usdcad_idx   = (combined["USDCAD"] / combined["USDCAD"].iloc[0]) * 100   # benchmark

    for y_data, lbl, clr in [
        (inr_usd_idx, "INR vs USD (idx 100)",   "#f7931a"),
        (inr_cad_idx, "INR vs CAD (idx 100)",   "#00c4aa"),
        (usdcad_idx,  "USD vs CAD (benchmark)",  "#9c27b0"),
    ]:
        fig2.add_trace(go.Scatter(
            x=combined.index, y=y_data, mode="lines", name=lbl,
            line=dict(color=clr, width=1.8),
            hovertemplate=f"<b>{lbl}</b>: %{{y:.2f}}<extra></extra>",
        ))

    fig2.add_hline(y=100, line_dash="dot", line_color=BORDER, line_width=1,
                   annotation_text="Base 100", annotation_font_color=TXT_MUTED,
                   annotation_position="right")

    fig2.update_layout(
        **{**PT_BASE, "margin": dict(l=52, r=20, t=54, b=90)},
        height=320,
        title=dict(text="INR Relative Strength — Indexed to 100 at Period Start (1Y)",
                   font=dict(color=ACCENT, size=12), x=0.01),
        legend=LEGEND_H,
        showlegend=True,
    )
    fig2.update_xaxes(**XAXIS_STYLE)
    fig2.update_yaxes(**YAXIS_STYLE)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Summary performance table ─────────────────────────────────────────────
    st.caption("Summary: positive = INR appreciated. 'USD vs CAD' is shown as reference benchmark.")
    render_table(perf_df)


# ── Brief parser ──────────────────────────────────────────────────────────────
SECTION_RE = {
    "Executive Summary":        r"(?i)#{1,4}\s*executive summary(.*?)(?=#{1,4}\s|\Z)",
    "Rates Market":             r"(?i)#{1,4}\s*rates?\s*market(.*?)(?=#{1,4}\s|\Z)",
    "Equities":                 r"(?i)#{1,4}\s*equities(.*?)(?=#{1,4}\s|\Z)",
    "Crypto":                   r"(?i)#{1,4}\s*crypto(.*?)(?=#{1,4}\s|\Z)",
    "FX":                       r"(?i)#{1,4}\s*fx\b(.*?)(?=#{1,4}\s|\Z)",
    "Gamma & Positioning":      r"(?i)#{1,4}\s*gamma.*?positioning(.*?)(?=#{1,4}\s|\Z)",
    "Risk Sentiment Dashboard": r"(?i)#{1,4}\s*risk\s*sentiment(.*?)(?=#{1,4}\s|\Z)",
    "What to Watch Today":      r"(?i)#{1,4}\s*what\s*to\s*watch(.*?)(?=#{1,4}\s|\Z)",
    "Commodities":              r"(?i)#{1,4}\s*commodit(.*?)(?=#{1,4}\s|\Z)",
    "Macro Outlook":            r"(?i)#{1,4}\s*macro\s*outlook(.*?)(?=#{1,4}\s|\Z)",
    "Technical":                r"(?i)#{1,4}\s*technical(.*?)(?=#{1,4}\s|\Z)",
}
SECTION_ICONS = {
    "Executive Summary":"📋","Rates Market":"📈","Equities":"🏦","Crypto":"₿",
    "FX":"💱","Gamma & Positioning":"⚡","Risk Sentiment Dashboard":"🚦",
    "What to Watch Today":"👁","Commodities":"🛢","Macro Outlook":"🌐","Technical":"📐",
}

def parse_brief(text: str) -> dict:
    out = {}
    for n, p in SECTION_RE.items():
        m = re.search(p, text, re.DOTALL)
        if m:
            out[n] = m.group(1).strip()

    # Auto-detect any remaining ## headings not already matched
    if len(out) < 3:
        found_headings = re.findall(r"(?m)^#{1,4}\s+(.+?)$", text)
        for heading in found_headings:
            clean = heading.strip()
            if any(clean.lower() in k.lower() or k.lower() in clean.lower() for k in out):
                continue
            esc = re.escape(clean)
            pat = rf"(?i)#{{{1,4}}}\s*{esc}(.*?)(?=#{{{1,4}}}\s|\Z)"
            m = re.search(pat, text, re.DOTALL)
            if m:
                out[clean] = m.group(1).strip()

    return out or ({"Full Brief": text.strip()} if text.strip() else {})


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Dark mode toggle — at top of sidebar so it re-inits colours on rerun
    new_dark = st.toggle("🌙  Dark Mode", value=st.session_state.dark_mode)
    if new_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = new_dark
        st.rerun()

    st.markdown(f'<div style="color:{ACCENT};font-size:0.9rem;letter-spacing:3px;'
                f'font-weight:700;padding:8px 0 8px;">MACRO TERMINAL</div>',
                unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Tabs**")
    st.markdown("""
- **Market Base** — broad cross-asset tape
- **Rates** — curve, duration, TLT
- **FX** — pairs + INR exposure
- **Macro Focus** — watchlist + charts
- **Brief Sync** — paste & parse brief
- **Cross-Asset Risk** — regime overview
- **Market Intel** — movers, scorecard
""")
    st.markdown("---")
    st.markdown("**Watchlist**")
    st.caption("TLT · MDI.TO · CAR.UN · IBIT · BTC · USD/INR · 10Y · 30Y · VIX")
    st.markdown("---")
    if st.button("⟳  Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Loaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("Yahoo Finance · 5-min cache")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="dash-header">
    <h1>MACRO MARKET DASHBOARD ◈</h1>
    <small>MARKET BASE &nbsp;·&nbsp; RATES &nbsp;·&nbsp; FX &nbsp;·&nbsp; MACRO FOCUS
    &nbsp;·&nbsp; BRIEF SYNC &nbsp;·&nbsp; CROSS-ASSET RISK &nbsp;·&nbsp; MARKET INTEL
    &nbsp;|&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")} ET</small>
    </div>""", unsafe_allow_html=True)

# ── Top-line strip — Nasdaq added, DXY dropped (data unreliable) ─────────────
_top = build_table({
    "S&P 500": "^GSPC",
    "Nasdaq":  "^IXIC",
    "10Y Yld": "^TNX",
    "VIX":     "^VIX",
    "BTC":     "BTC-USD",
    "Gold":    "GC=F",
})
metric_strip(_top)
st.markdown("<hr>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Market Base", "📈 Rates", "💱 FX",
    "🎯 Macro Focus", "📋 Brief Sync", "🚦 Cross-Asset Risk", "📡 Market Intel",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET BASE
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    # Timeframe selector
    tf1 = st.radio("Chart Timeframe", list(TF_MAP.keys()), index=5,
                   horizontal=True, label_visibility="collapsed",
                   key="tf_tab1")

    for sname, tickers in BASE_TICKERS.items():
        sec(sname)
        df = build_table(tickers)
        metric_strip(df)
        render_table(df)
        st.markdown("")

    sec(f"Relative Performance — {tf1} % Return")
    c1, c2 = st.columns(2)
    with c1:
        plotly_multi_line({
            "S&P 500": ("^GSPC", UP),
            "Nasdaq":  ("^IXIC", "#3399ff"),
            "Russell": ("^RUT",  ACCENT),
            "Dow":     ("^DJI",  "#cc66ff"),
        }, "U.S. Equities", height=380, tf_label=tf1)
    with c2:
        plotly_multi_line({
            "BTC":  ("BTC-USD", "#f7931a"),
            "IBIT": ("IBIT",    "#3399ff"),
            "TLT":  ("TLT",     ACCENT),
            "VIX":  ("^VIX",    DOWN),
        }, "BTC · IBIT · TLT · VIX", height=380, tf_label=tf1)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RATES
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    tf2 = st.radio("Chart Timeframe", list(TF_MAP.keys()), index=5,
                   horizontal=True, label_visibility="collapsed",
                   key="tf_tab2")

    sec("Treasury Yields")
    rates_df = build_table(BASE_TICKERS["Rates"])
    metric_strip(rates_df)
    render_table(rates_df)

    st.markdown("")
    rmap = {r["Name"]: r["Last"] for _, r in rates_df.iterrows()
            if pd.notna(r.get("Last") or float("nan"))}
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("2s5s (bp)",   f"{(rmap['5Y']-rmap['2Y'])*100:.1f}"   if rmap.get("2Y")  and rmap.get("5Y")  else "—")
    s2.metric("5s10s (bp)",  f"{(rmap['10Y']-rmap['5Y'])*100:.1f}"  if rmap.get("5Y")  and rmap.get("10Y") else "—")
    s3.metric("10s30s (bp)", f"{(rmap['30Y']-rmap['10Y'])*100:.1f}" if rmap.get("10Y") and rmap.get("30Y") else "—")
    s4.metric("2s30s (bp)",  f"{(rmap['30Y']-rmap['2Y'])*100:.1f}"  if rmap.get("2Y")  and rmap.get("30Y") else "—")

    sec("Yield Curve Snapshot")
    plotly_yield_curve()

    sec(f"TLT Duration vs 10Y Yield — Rate Effect  [{tf2}]")
    st.caption(
        f"TLT Modified Duration ≈ 16.5yr. "
        f"Solid line = actual TLT return. Dashed = theoretical rate-effect estimate (−ModDur × Δyield). "
        f"Right axis = 10Y yield level. Divergence = credit/vol/other factors.")
    plotly_duration_yield(tf_label=tf2)

    sec(f"Individual Yield Trends — {tf2}")
    yf_period2, _ = TF_MAP.get(tf2, ("6mo", None))
    cl, cr = st.columns(2)
    with cl:
        plotly_line("^TNX", "10Y Treasury Yield",  color=ACCENT,    height=280, period=yf_period2)
        plotly_line("^IRX", "2Y Treasury Yield",   color="#3399ff", height=280, period=yf_period2)
    with cr:
        plotly_line("^TYX", "30Y Treasury Yield",  color="#cc66ff", height=280, period=yf_period2)
        plotly_line("^FVX", "5Y Treasury Yield",   color=UP,        height=280, period=yf_period2)

    sec("TLT — iShares 20+ Year Treasury ETF")
    plotly_candle("TLT", "TLT — 20+ Year Treasury Bond ETF",
                  period=yf_period2, height=420)

    sec("Relative Performance vs Treasury Curve")
    plotly_multi_line({
        "TLT":   ("TLT",    ACCENT),
        "10Y":   ("^TNX",   DOWN),
        "30Y":   ("^TYX",   "#cc66ff"),
        "2Y":    ("^IRX",   "#3399ff"),
    }, "TLT & Treasury Yields", height=340, tf_label=tf2)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FX
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    tf3 = st.radio("Chart Timeframe", list(TF_MAP.keys()), index=5,
                   horizontal=True, label_visibility="collapsed",
                   key="tf_tab3")
    yf_period3, _ = TF_MAP.get(tf3, ("6mo", None))

    sec("FX Snapshot")
    fx_df = build_table(BASE_TICKERS["FX"])
    metric_strip(fx_df)
    render_table(fx_df)

    sec(f"G4 Pairs — {tf3} % Return")
    plotly_multi_line({
        "EUR/USD": ("EURUSD=X", "#3399ff"),
        "GBP/USD": ("GBPUSD=X", UP),
        "AUD/USD": ("AUDUSD=X", "#ffcc00"),
        "USD/CAD": ("CAD=X",    "#cc66ff"),
    }, "G4 FX", height=360, tf_label=tf3)

    # ── INR Currency Exposure ────────────────────────────────────────────────
    sec("INR Currency Exposure — USD & CAD Benchmark")
    st.caption(
        "Inverse performance: positive = INR appreciated vs that currency. "
        "3 currencies tracked: INR, USD, CAD.")
    plotly_inr_exposure()

    sec(f"Pair Charts — {tf3}")
    cl, cr = st.columns(2)
    with cl:
        plotly_line("INR=X",    "USD/INR — EM Stress Barometer", color=ACCENT,    height=280, period=yf_period3)
        plotly_line("JPY=X",    "USD/JPY — Rate Beta Express",   color="#3399ff", height=280, period=yf_period3)
    with cr:
        plotly_line("CAD=X",    "USD/CAD — Commodity Carry",     color="#cc66ff", height=280, period=yf_period3)
        plotly_line("EURUSD=X", "EUR/USD",                       color=UP,        height=280, period=yf_period3)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MACRO FOCUS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    tf4 = st.radio("Chart Timeframe", list(TF_MAP.keys()), index=4,
                   horizontal=True, label_visibility="collapsed",
                   key="tf_tab4")
    yf_period4, _ = TF_MAP.get(tf4, ("3mo", None))

    sec("Daily Brief Watchlist — Live Tape")
    st.caption("TLT · MDI (TSX) · CAR.UN · IBIT · BTC · USD/INR · 10Y · 30Y · VIX")
    focus_df = build_table(FOCUS_TICKERS)
    metric_strip(focus_df)
    render_table(focus_df)

    # Nasdaq top-line addition
    sec("Nasdaq Performance")
    qqq_df = build_table({"Nasdaq (^IXIC)": "^IXIC", "QQQ": "QQQ"})
    metric_strip(qqq_df)
    plotly_line("^IXIC", f"Nasdaq Composite — {tf4}", color="#3399ff",
                height=260, period=yf_period4)

    sec(f"Charts — {tf4} Price Action")
    c1, c2, c3 = st.columns(3)
    with c1:
        plotly_candle("TLT",   "TLT",               period=yf_period4, height=360)
        plotly_line("^VIX",    "VIX", color=DOWN,    height=240, period=yf_period4)
    with c2:
        plotly_candle("MDI.TO",    "MDI — TSX Major Drilling", period=yf_period4, height=360)
        plotly_candle("CAR-UN.TO", "CAR.UN — Cdn Apt REIT",    period=yf_period4, height=360)
    with c3:
        plotly_candle("IBIT",    "IBIT — iShares Bitcoin Trust", period=yf_period4, height=360)
        plotly_candle("BTC-USD", "Bitcoin (BTC-USD)",             period=yf_period4, height=360)

    sec("60-Day Return Correlation Matrix")
    corr_syms = {"BTC":"BTC-USD","IBIT":"IBIT","TLT":"TLT",
                 "SPX":"^GSPC","VIX":"^VIX","10Y":"^TNX","Nasdaq":"^IXIC"}
    frames = {}
    for n, s in corr_syms.items():
        d = load_history(s)
        if d is not None and not d.empty:
            frames[n] = d["Close"].rename(n)

    if len(frames) >= 3:
        combined_c = pd.concat(frames.values(), axis=1).dropna()
        if len(combined_c) > 10:
            corr_m = combined_c.pct_change().dropna().tail(60).corr()
            fig_c  = px.imshow(corr_m,
                               color_continuous_scale=[[0, DOWN],[0.5, SURFACE2],[1, UP]],
                               zmin=-1, zmax=1, text_auto=".2f",
                               title="60-Day Return Correlation")
            fig_c.update_layout(**PT_BASE, height=380, coloraxis_showscale=True,
                                title=dict(text="60-Day Return Correlation",
                                           font=dict(color=ACCENT, size=12), x=0.01))
            fig_c.update_xaxes(tickfont=dict(size=11, color=TXT_MUTED))
            fig_c.update_yaxes(tickfont=dict(size=11, color=TXT_MUTED))
            fig_c.update_traces(textfont_size=12)
            st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.info("Not enough data for correlation matrix.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BRIEF SYNC
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    sec("Morning Brief — Paste & Parse")
    st.caption("Paste the full morning brief. Sections auto-detected by # / ## / ### headings.")
    brief_text = st.text_area(
        "brief_input", height=240,
        placeholder=("## Executive Summary\n- paste brief here...\n\n"
                     "## Rates Market\n...\n\n## Equities\n...\n\n## FX\n..."),
        label_visibility="collapsed")

    if brief_text.strip():
        sections = parse_brief(brief_text)
        if sections:
            col_brief, col_live = st.columns([3, 2])
            with col_brief:
                sec(f"Parsed Sections ({len(sections)} found)")
                for title, body in sections.items():
                    icon = SECTION_ICONS.get(title, "•")
                    with st.expander(f"{icon}  {title}", expanded=(title == "Executive Summary")):
                        st.markdown(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body))
            with col_live:
                sec("Live Data")
                _live = build_table({
                    "10Y": "^TNX", "30Y": "^TYX", "SPX": "^GSPC", "Nasdaq": "^IXIC",
                    "VIX": "^VIX", "BTC": "BTC-USD", "TLT": "TLT",
                    "INR": "INR=X", "JPY": "JPY=X",
                })
                metric_strip(_live.head(4))
                render_table(_live)
                st.markdown("")
                plotly_line("^TNX",    "10Y Yield",  color=ACCENT,    height=190)
                plotly_line("^GSPC",   "S&P 500",    color=UP,        height=190)
                plotly_line("BTC-USD", "BTC",        color="#f7931a", height=190)
        else:
            st.info("No sections detected — displaying as plain text.")
            st.markdown(brief_text)
    else:
        st.markdown(
            f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:6px;'
            f'padding:28px;text-align:center;color:{TXT_MUTED};">'
            f'<div style="font-size:2rem;margin-bottom:8px;">📋</div>'
            f'<div style="font-size:0.9rem;">Paste the morning brief above to auto-parse sections.</div>'
            f'<div style="font-size:0.74rem;margin-top:6px;">Sections detected: Executive Summary · Rates · '
            f'Equities · Crypto · FX · Gamma · Risk · Watch · Commodities · Macro Outlook</div></div>',
            unsafe_allow_html=True)
        st.markdown("")
        sec("Live Snapshot")
        _snap = build_table({
            "10Y Yld": "^TNX", "30Y Yld": "^TYX", "VIX": "^VIX",
            "S&P 500": "^GSPC", "Nasdaq": "^IXIC", "BTC": "BTC-USD",
            "IBIT": "IBIT", "TLT": "TLT", "USD/INR": "INR=X",
        })
        metric_strip(_snap.head(4))
        render_table(_snap)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CROSS-ASSET RISK
# ═══════════════════════════════════════════════════════════════════════════════
with tab6:
    tf6 = st.radio("Chart Timeframe", list(TF_MAP.keys()), index=5,
                   horizontal=True, label_visibility="collapsed",
                   key="tf_tab6")

    sec("Cross-Asset Risk Dashboard")

    def _last(df): return float(df["Close"].iloc[-1]) if df is not None and not df.empty else None
    def _dpct(df):
        if df is None or df.empty or len(df) < 2: return None
        return (float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-2]) - 1) * 100

    vix_df  = load_history("^VIX");   spx_df  = load_history("^GSPC")
    tlt_df  = load_history("TLT");    btc_df  = load_history("BTC-USD")
    hy_df   = load_history("HYG");    ig_df   = load_history("LQD")
    gold_df = load_history("GC=F");   qqq_df  = load_history("^IXIC")

    vix_v=_last(vix_df); vix_c=_dpct(vix_df)
    spx_v=_last(spx_df); spx_c=_dpct(spx_df)
    hy_v =_last(hy_df);  hy_c =_dpct(hy_df)
    btc_v=_last(btc_df); btc_c=_dpct(btc_df)
    tlt_v=_last(tlt_df); gold_v=_last(gold_df)
    ig_v =_last(ig_df);  qqq_v=_last(qqq_df); qqq_c=_dpct(qqq_df)

    if   vix_v and vix_v < 15: badge = f'<span class="badge-on">RISK-ON</span>'
    elif vix_v and vix_v < 25: badge = f'<span class="badge-neu">CAUTIOUS NEUTRAL</span>'
    elif vix_v and vix_v < 35: badge = f'<span class="badge-off">RISK-OFF</span>'
    elif vix_v:                  badge = f'<span class="badge-off">STRESS / CRISIS</span>'
    else:                        badge = f'<span class="badge-neu">UNKNOWN</span>'

    vix_str = f" &nbsp;·&nbsp; VIX <b>{vix_v:.2f}</b>" if vix_v else ""
    st.markdown(f"**Regime:** {badge}{vix_str}", unsafe_allow_html=True)
    st.markdown("")

    r1,r2,r3,r4 = st.columns(4)
    r1.metric("VIX",          f"{vix_v:.2f}"   if vix_v  else "—", f"{vix_c:+.2f}%"  if vix_c  else None)
    r2.metric("S&P 500",      f"{spx_v:,.0f}"  if spx_v  else "—", f"{spx_c:+.2f}%"  if spx_c  else None)
    r3.metric("Nasdaq",       f"{qqq_v:,.0f}"  if qqq_v  else "—", f"{qqq_c:+.2f}%"  if qqq_c  else None)
    r4.metric("BTC",          f"{btc_v:,.0f}"  if btc_v  else "—", f"{btc_c:+.2f}%"  if btc_c  else None)
    r5,r6,r7,r8 = st.columns(4)
    r5.metric("TLT",          f"{tlt_v:.2f}"   if tlt_v  else "—")
    r6.metric("HYG (HY ETF)", f"{hy_v:.2f}"    if hy_v   else "—", f"{hy_c:+.2f}%"   if hy_c   else None)
    r7.metric("Gold",         f"{gold_v:,.1f}" if gold_v else "—")
    r8.metric("LQD (IG ETF)", f"{ig_v:.2f}"    if ig_v   else "—")

    sec("VIX Regime History")
    if vix_df is not None and not vix_df.empty:
        fig_v = go.Figure()
        for y0,y1,col in [(0,15,UP),(15,25,"#ffcc00"),(25,35,DOWN),(35,80,DOWN)]:
            fig_v.add_hrect(y0=y0, y1=y1, fillcolor=hex_rgba(col,0.05), line_width=0)
        for lvl, col, lbl in [(15,UP,"<15 Risk-On"),(25,"#ffcc00","15-25 Neutral"),(35,DOWN,">35 Stress")]:
            fig_v.add_hline(y=lvl, line_dash="dot", line_color=col, line_width=1,
                            annotation_text=lbl, annotation_font_color=col,
                            annotation_position="right")
        fig_v.add_trace(go.Scatter(
            x=vix_df.index, y=vix_df["Close"], mode="lines",
            line=dict(color=DOWN, width=2),
            fill="tozeroy", fillcolor=hex_rgba(DOWN, 0.08),
            hovertemplate="<b>%{x|%b %d}</b>  VIX %{y:.2f}<extra></extra>"))
        fig_v.update_layout(**PT_BASE, height=300, showlegend=False,
                            title=dict(text=f"VIX — {tf6}",
                                       font=dict(color=ACCENT, size=12), x=0.01))
        fig_v.update_xaxes(**XAXIS_STYLE)
        fig_v.update_yaxes(**YAXIS_STYLE)
        st.plotly_chart(fig_v, use_container_width=True)

    sec(f"Cross-Asset {tf6} % Return")
    plotly_multi_line({
        "S&P 500": ("^GSPC",   UP),
        "Nasdaq":  ("^IXIC",   "#3399ff"),
        "TLT":     ("TLT",     ACCENT),
        "HYG":     ("HYG",     "#26c6da"),
        "Gold":    ("GC=F",    "#ffcc00"),
        "BTC":     ("BTC-USD", "#f7931a"),
    }, "Cross-Asset % Return", height=400, tf_label=tf6)

    sec("Gamma / Positioning Framework")
    st.markdown("""
| Signal | Threshold | Implication |
|--------|-----------|-------------|
| **VIX** | <15 / 15-25 / >25 / >35 | Risk-On / Neutral / Risk-Off / Stress |
| **0DTE Flow** | Break of dominant OI cluster | Accelerates realised vol |
| **TLT price action** | Sustained selling | Bear-steepener pressure |
| **SPX Pinning** | Near large open-interest strikes | Dealer hedging damps moves |
| **BTC β** | High real yield | BTC headwind |
| **Positive γ** | Spot near max OI strike | Vol suppression, mean reversion |
| **Negative γ** | Spot through major strike | Vol expansion, trending |

> Live GEX: SpotGamma / Tier1Alpha. The above is the structural decision framework.
""")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — MARKET INTEL
# ═══════════════════════════════════════════════════════════════════════════════
with tab7:
    # ── Ticker Lookup ──────────────────────────────────────────────────────────
    sec("Ticker Lookup")
    col_in, col_per = st.columns([2, 1])
    with col_in:
        lookup_sym = st.text_input(
            "Enter any ticker (e.g. AAPL, MDI.TO, BTC-USD, ^TNX)",
            value="", placeholder="AAPL", label_visibility="collapsed")
    with col_per:
        lookup_per = st.selectbox("Period",
                                  ["3d","5d","1mo","3mo","6mo","1y","2y"],
                                  index=4, label_visibility="collapsed")

    if lookup_sym.strip():
        sym = lookup_sym.strip().upper()
        ldf = load_history(sym, period=lookup_per)
        if ldf is not None and not ldf.empty:
            last, chg, pct = latest_metrics(ldf)
            hi = float(ldf["High"].max()); lo = float(ldf["Low"].min())
            avg_vol = ldf["Volume"].replace(0, np.nan).mean() if "Volume" in ldf.columns else None
            lc1,lc2,lc3,lc4,lc5 = st.columns(5)
            lc1.metric("Last",     f"{last:,.4f}" if last else "—",  f"{pct:+.2f}%" if pct else None)
            lc2.metric("Day Chg",  f"{chg:+.4f}"  if chg  else "—")
            lc3.metric("Period Hi", f"{hi:,.4f}")
            lc4.metric("Period Lo", f"{lo:,.4f}")
            lc5.metric("Avg Vol",  f"{avg_vol:,.0f}" if avg_vol and not np.isnan(avg_vol) else "N/A")
            plotly_candle(sym, f"{sym} — {lookup_per}", period=lookup_per, height=400)
            plotly_rsi(sym, height=200)
        else:
            st.warning(f"No data found for **{sym}**. Check the ticker and try again.")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Market Movers ──────────────────────────────────────────────────────────
    sec("Market Movers — Watchlist")
    movers_df = build_table(MOVERS_UNIVERSE)
    movers_df = movers_df.dropna(subset=["Day %"]).sort_values("Day %", ascending=False)

    mc1, mc2 = st.columns(2)
    with mc1:
        sec("Top Gainers")
        gainers = movers_df.head(5)[["Name","Ticker","Last","Day %","1M %","3M %"]].reset_index(drop=True)
        render_table(gainers)
    with mc2:
        sec("Top Losers")
        losers  = movers_df.tail(5).iloc[::-1][["Name","Ticker","Last","Day %","1M %","3M %"]].reset_index(drop=True)
        render_table(losers)

    # Movers bar chart — FIXED (no duplicate zeroline kwarg)
    movers_plot = movers_df.dropna(subset=["Day %"]).copy()
    if not movers_plot.empty:
        fig_m = go.Figure(go.Bar(
            x=movers_plot["Name"], y=movers_plot["Day %"],
            marker_color=[UP if v >= 0 else DOWN for v in movers_plot["Day %"]],
            text=[f"{v:+.2f}%" for v in movers_plot["Day %"]],
            textposition="outside",
            textfont=dict(size=10, color=TXT_MUTED),
            hovertemplate="<b>%{x}</b><br>Day %{y:+.2f}%<extra></extra>",
        ))
        fig_m.update_layout(**PT_BASE, height=300,
                            title=dict(text="Watchlist — Day % Change",
                                       font=dict(color=ACCENT, size=12), x=0.01))
        fig_m.update_xaxes(**xax(tickangle=-30))
        # Use yax() helper to safely merge zeroline override
        fig_m.update_yaxes(**yax(ticksuffix="%", zeroline=True,
                                 zerolinecolor=BORDER, zerolinewidth=1))
        st.plotly_chart(fig_m, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── INTEL Scorecard ────────────────────────────────────────────────────────
    sec("INTEL Scorecard — Technical Signals")
    st.caption("RSI(14) · Price vs 50/200-day MA · 52-Week Range Position · 5-Day Momentum")

    scorecard_tickers = {
        "TLT":"TLT","MDI":"MDI.TO","IBIT":"IBIT","BTC":"BTC-USD",
        "SPX":"^GSPC","Nasdaq":"^IXIC","VIX":"^VIX","10Y":"^TNX",
    }
    score_rows = []
    for name, sym in scorecard_tickers.items():
        sc = intel_scorecard(sym)
        if not sc:
            continue
        rsi_val  = sc.get("rsi")
        rsi_sig  = ("🔴 OB" if rsi_val and rsi_val > 70 else
                    "🟢 OS" if rsi_val and rsi_val < 30 else "⚪ Neutral") if rsi_val else "—"
        ma50_sig = ("▲ Above" if sc.get("vs_50ma") and sc["vs_50ma"] > 0 else "▼ Below") \
                   if sc.get("vs_50ma") is not None else "—"
        ma200_sig= ("▲ Above" if sc.get("vs_200ma") and sc["vs_200ma"] > 0 else "▼ Below") \
                   if sc.get("vs_200ma") is not None else "—"
        rng = sc.get("52w_range_pct")
        mom = sc.get("mom_5d")
        score_rows.append({
            "Name":       name,
            "RSI(14)":    f"{rsi_val:.1f}" if rsi_val else "—",
            "RSI Signal": rsi_sig,
            "vs 50MA":    f"{sc['vs_50ma']:+.1f}%" if sc.get("vs_50ma") is not None else "—",
            "50MA Sig":   ma50_sig,
            "vs 200MA":   f"{sc['vs_200ma']:+.1f}%" if sc.get("vs_200ma") is not None else "—",
            "200MA Sig":  ma200_sig,
            "52W Range":  f"{rng:.0f}%" if rng is not None else "—",
            "5D Mom":     f"{mom:+.2f}%" if mom is not None else "—",
        })

    if score_rows:
        sc_df = pd.DataFrame(score_rows)
        st.dataframe(sc_df, use_container_width=True, hide_index=True)

        rng_data = [(r["Name"], float(r["52W Range"].replace("%", "")))
                    for r in score_rows if r["52W Range"] != "—"]
        if rng_data:
            names_r, vals_r = zip(*rng_data)
            fig_r = go.Figure(go.Bar(
                x=list(names_r), y=list(vals_r),
                marker_color=[UP if v > 50 else ACCENT for v in vals_r],
                text=[f"{v:.0f}%" for v in vals_r],
                textposition="outside",
                textfont=dict(size=10, color=TXT_MUTED),
                hovertemplate="<b>%{x}</b><br>52W Position: %{y:.1f}%<extra></extra>",
            ))
            fig_r.add_hline(y=50, line_dash="dot", line_color=BORDER, line_width=1)
            fig_r.update_layout(
                **PT_BASE, height=280,
                title=dict(text="52-Week Range Position (0% = 52W Low · 100% = 52W High)",
                           font=dict(color=ACCENT, size=12), x=0.01))
            fig_r.update_xaxes(**XAXIS_STYLE)
            fig_r.update_yaxes(**yax(range=[0, 115], ticksuffix="%"))
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("Scorecard data loading…")
