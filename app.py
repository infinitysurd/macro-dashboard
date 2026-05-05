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

# ── Colour palette — light grey ───────────────────────────────────────────────
BG        = "#f0f2f5"   # page background   (light grey)
SURFACE   = "#ffffff"   # cards / panels     (white)
SURFACE2  = "#e4e6ea"   # raised / alt rows  (mid grey)
BORDER    = "#ced0d4"   # borders
TXT       = "#1c1e21"   # primary text       (near black)
TXT_MUTED = "#606770"   # captions / labels
ACCENT    = "#b8860b"   # dark-amber gold    (readable on white)
UP        = "#0a7a3c"   # green
DOWN      = "#cc1f1f"   # red

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
/* header */
.dash-header {{
    background: linear-gradient(90deg, {SURFACE2} 0%, {SURFACE} 60%, {SURFACE2} 100%);
    border-bottom: 2px solid {ACCENT};
    padding: 12px 24px 10px;
    margin-bottom: 14px;
    border-radius: 0 0 4px 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}}
.dash-header h1 {{ color:{ACCENT}; margin:0; font-size:1.2rem; letter-spacing:3px; font-weight:700; }}
.dash-header small {{ color:{TXT_MUTED}; font-size:0.7rem; letter-spacing:1px; }}
/* metric cards */
[data-testid="stMetric"] {{
    background-color:{SURFACE} !important;
    border:1px solid {BORDER} !important;
    border-radius:6px !important;
    padding:10px 14px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}}
[data-testid="stMetricLabel"]  {{ color:{TXT_MUTED}!important; font-size:0.67rem!important; letter-spacing:1px!important; text-transform:uppercase!important; }}
[data-testid="stMetricValue"]  {{ color:{TXT}!important; font-size:1.05rem!important; font-weight:700!important; }}
[data-testid="stMetricDelta"] svg {{ display:none!important; }}
[data-testid="stMetricDelta"][data-direction="up"]   {{ color:{UP}!important; font-weight:600!important; }}
[data-testid="stMetricDelta"][data-direction="down"] {{ color:{DOWN}!important; font-weight:600!important; }}
/* tabs */
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
/* section labels */
.sec {{
    color:{ACCENT}; font-size:0.67rem; letter-spacing:2px; text-transform:uppercase;
    font-weight:700; border-bottom:1px solid {BORDER}; padding-bottom:5px; margin:16px 0 10px 0;
}}
/* risk badges */
.badge-on  {{ background:#d4f4e2; color:{UP};   border:1px solid {UP};   padding:3px 12px; border-radius:4px; font-size:0.74rem; font-weight:700; }}
.badge-off {{ background:#fde8e8; color:{DOWN}; border:1px solid {DOWN}; padding:3px 12px; border-radius:4px; font-size:0.74rem; font-weight:700; }}
.badge-neu {{ background:#fef9e7; color:#7d6608; border:1px solid #c8a416; padding:3px 12px; border-radius:4px; font-size:0.74rem; font-weight:700; }}
/* inputs */
textarea, [data-baseweb="textarea"] textarea {{
    background-color:{SURFACE}!important; color:{TXT}!important;
    font-size:0.82rem!important; border:1px solid {BORDER}!important; border-radius:4px!important;
}}
input, [data-baseweb="input"] input {{
    background-color:{SURFACE}!important; color:{TXT}!important;
    border:1px solid {BORDER}!important;
}}
/* dataframe */
[data-testid="stDataFrame"] {{ border:1px solid {BORDER}!important; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.05); }}
/* divider */
hr {{ border-color:{BORDER}!important; margin:8px 0!important; }}
/* scrollbar */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:{BG}; }}
::-webkit-scrollbar-thumb {{ background:{BORDER}; border-radius:3px; }}
</style>
""", unsafe_allow_html=True)

# ── Plotly base theme (NO xaxis/yaxis — apply those separately) ───────────────
PT_BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=SURFACE,
    font=dict(color=TXT_MUTED, family="Segoe UI, sans-serif", size=11),
    margin=dict(l=52, r=20, t=44, b=36),
)
XAXIS_STYLE = dict(gridcolor=SURFACE2, linecolor=BORDER, showgrid=True, zeroline=False,
                   tickfont=dict(size=10, color=TXT_MUTED))
YAXIS_STYLE = dict(gridcolor=SURFACE2, linecolor=BORDER, showgrid=True, zeroline=False,
                   tickfont=dict(size=10, color=TXT_MUTED))

def theme(fig, height: int = 320, title: str = ""):
    """Apply standard dark-grey theme to any figure."""
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
    "FX":       {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"JPY=X","USD/CAD":"CAD=X","AUD/USD":"AUDUSD=X","USD/INR":"INR=X"},
    "Crypto":   {"BTC":"BTC-USD","ETH":"ETH-USD","IBIT":"IBIT"},
}
FOCUS_TICKERS = {
    "TLT":"TLT","MDI":"MDI.TO","CAR.UN":"CAR-UN.TO",
    "IBIT":"IBIT","BTC":"BTC-USD","USD/INR":"INR=X",
    "10Y":"^TNX","30Y":"^TYX","VIX":"^VIX",
}
YIELD_CURVE   = {"2Y":("^IRX",2),"5Y":("^FVX",5),"10Y":("^TNX",10),"30Y":("^TYX",30)}

# Broad watchlist for market movers
MOVERS_UNIVERSE = {
    "SPY":"^GSPC","QQQ":"^IXIC","IWM":"^RUT","DIA":"^DJI",
    "TLT":"TLT","HYG":"HYG","LQD":"LQD","GLD":"GC=F",
    "BTC":"BTC-USD","ETH":"ETH-USD","IBIT":"IBIT",
    "MDI":"MDI.TO","CAR.UN":"CAR-UN.TO",
    "EUR":"EURUSD=X","JPY":"JPY=X","INR":"INR=X",
    "VIX":"^VIX","DXY":"DX=F",
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
        f'⚠ No data available — {label}</div>',
        unsafe_allow_html=True)

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

def build_table(tickers: dict) -> pd.DataFrame:
    rows = []
    for name, symbol in tickers.items():
        df = load_history(symbol)
        last, chg, pct = latest_metrics(df)
        m1 = m3 = None
        if df is not None and not df.empty:
            if len(df) > 21: m1 = ((df["Close"].iloc[-1]/df["Close"].iloc[-22])-1)*100
            if len(df) > 63: m3 = ((df["Close"].iloc[-1]/df["Close"].iloc[-64])-1)*100
        rows.append({"Name":name,"Ticker":symbol,
                     "Last":round(last,4) if last is not None else None,
                     "Day Chg":round(chg,4) if chg is not None else None,
                     "Day %":round(pct,2) if pct is not None else None,
                     "1M %":round(m1,2) if m1 is not None else None,
                     "3M %":round(m3,2) if m3 is not None else None})
    return pd.DataFrame(rows)

def render_table(df: pd.DataFrame):
    cfg = {}
    for c in df.columns:
        if "%" in c: cfg[c] = st.column_config.NumberColumn(c, format="%.2f %%")
        elif c == "Last":    cfg[c] = st.column_config.NumberColumn("Last",    format="%.4f")
        elif c == "Day Chg": cfg[c] = st.column_config.NumberColumn("Day Chg", format="%.4f")
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
    """Return a dict of technical signals for a ticker."""
    df = load_history(symbol, period="1y")
    if df is None or df.empty or len(df) < 20:
        return {}
    c = df["Close"]
    rsi = compute_rsi(c).iloc[-1]
    ma50  = c.rolling(50).mean().iloc[-1]  if len(c) >= 50  else None
    ma200 = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else None
    hi52  = c.rolling(252).max().iloc[-1]  if len(c) >= 252 else c.max()
    lo52  = c.rolling(252).min().iloc[-1]  if len(c) >= 252 else c.min()
    price = c.iloc[-1]
    rng_pct = ((price - lo52) / (hi52 - lo52) * 100) if (hi52 - lo52) > 0 else None
    mom5d = ((price / c.iloc[-6]) - 1) * 100 if len(c) >= 6 else None
    return {
        "price": price, "rsi": rsi,
        "vs_50ma":  ((price/ma50  - 1)*100) if ma50  else None,
        "vs_200ma": ((price/ma200 - 1)*100) if ma200 else None,
        "52w_range_pct": rng_pct,
        "mom_5d": mom5d,
    }

# ── Chart helpers ─────────────────────────────────────────────────────────────
def plotly_line(symbol: str, title: str = "", color: str = ACCENT, height: int = 300):
    df = load_history(symbol)
    if df is None or df.empty:
        no_data(title or symbol); return
    fig = go.Figure(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
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
        vcols = [hex_rgba(UP if c>=o else DOWN, 0.6)
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
            tenors.append(tenor); yields.append(float(df["Close"].iloc[-1]))
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
                      title=dict(text="U.S. Treasury Yield Curve", font=dict(color=ACCENT,size=12), x=0.01))
    fig.update_xaxes(tickvals=tenors, ticktext=[f"{t}Y" for t in tenors], **XAXIS_STYLE)
    fig.update_yaxes(tickformat=".2f", ticksuffix="%", **YAXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)


def plotly_multi_line(series_map: dict, title: str, height: int = 340, pct_base: bool = True):
    fig = go.Figure()
    for label, (sym, color) in series_map.items():
        df = load_history(sym)
        if df is None or df.empty: continue
        y = df["Close"]
        if pct_base: y = (y / y.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(x=df.index, y=y, mode="lines", name=label,
                                 line=dict(color=color, width=1.8),
                                 hovertemplate=f"<b>{label}</b>: %{{y:.2f}}<extra></extra>"))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=10, color=TXT_MUTED)),
        **PT_BASE, height=height,
        title=dict(text=title, font=dict(color=ACCENT, size=12), x=0.01),
    )
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(ticksuffix="%" if pct_base else "", **YAXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)


def plotly_rsi(symbol: str, height: int = 200):
    df = load_history(symbol, period="6mo")
    if df is None or df.empty: return
    rsi = compute_rsi(df["Close"])
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor=hex_rgba(DOWN, 0.07), line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor=hex_rgba(UP,   0.07), line_width=0)
    fig.add_hline(y=70, line_dash="dot", line_color=DOWN, line_width=1)
    fig.add_hline(y=30, line_dash="dot", line_color=UP,   line_width=1)
    fig.add_hline(y=50, line_dash="dot", line_color=BORDER, line_width=1)
    fig.add_trace(go.Scatter(x=df.index, y=rsi, mode="lines",
                             line=dict(color=ACCENT, width=1.8),
                             hovertemplate="RSI: %{y:.1f}<extra></extra>"))
    fig.update_layout(**PT_BASE, height=height,
                      title=dict(text="RSI (14)", font=dict(color=ACCENT, size=11), x=0.01))
    fig.update_xaxes(**XAXIS_STYLE)
    fig.update_yaxes(range=[0, 100], tickvals=[30,50,70], **YAXIS_STYLE)
    st.plotly_chart(fig, use_container_width=True)


# ── Brief parser ──────────────────────────────────────────────────────────────
SECTION_RE = {
    "Executive Summary":        r"(?i)##\s*executive summary(.*?)(?=##|\Z)",
    "Rates Market":             r"(?i)##\s*rates market(.*?)(?=##|\Z)",
    "Equities":                 r"(?i)##\s*equities(.*?)(?=##|\Z)",
    "Crypto":                   r"(?i)##\s*crypto(.*?)(?=##|\Z)",
    "FX":                       r"(?i)##\s*fx(.*?)(?=##|\Z)",
    "Gamma & Positioning":      r"(?i)##\s*gamma.*?positioning(.*?)(?=##|\Z)",
    "Risk Sentiment Dashboard": r"(?i)##\s*risk sentiment(.*?)(?=##|\Z)",
    "What to Watch Today":      r"(?i)##\s*what to watch(.*?)(?=##|\Z)",
}
SECTION_ICONS = {
    "Executive Summary":"📋","Rates Market":"📈","Equities":"🏦","Crypto":"₿",
    "FX":"💱","Gamma & Positioning":"⚡","Risk Sentiment Dashboard":"🚦","What to Watch Today":"👁",
}

def parse_brief(text: str) -> dict:
    out = {n: m.group(1).strip() for n, p in SECTION_RE.items()
           if (m := re.search(p, text, re.DOTALL))}
    return out or ({"Full Brief": text.strip()} if text.strip() else {})

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="color:{ACCENT};font-size:0.9rem;letter-spacing:3px;font-weight:700;padding:4px 0 8px;">MACRO TERMINAL</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Tabs**")
    st.markdown(f"""
- **Market Base** — broad cross-asset tape
- **Rates** — curve, spreads, TLT
- **FX** — six-pair dashboard
- **Macro Focus** — brief names + charts
- **Brief Sync** — paste & parse brief
- **Cross-Asset Risk** — regime overview
- **Market Intel** — movers, scorecard, lookup
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
    <h1>MACRO MARKET DASHBOARD</h1>
    <small>MARKET BASE &nbsp;·&nbsp; RATES &nbsp;·&nbsp; FX &nbsp;·&nbsp; MACRO FOCUS
    &nbsp;·&nbsp; BRIEF SYNC &nbsp;·&nbsp; CROSS-ASSET RISK &nbsp;·&nbsp; MARKET INTEL
    &nbsp;|&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")} ET</small>
    </div>""", unsafe_allow_html=True)

# Top-line strip
_top = build_table({"S&P 500":"^GSPC","10Y Yld":"^TNX","VIX":"^VIX","BTC":"BTC-USD","DXY":"DX=F","Gold":"GC=F"})
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
    for sname, tickers in BASE_TICKERS.items():
        sec(sname)
        df = build_table(tickers)
        metric_strip(df)
        render_table(df)
        st.markdown("")

    sec("Relative Performance — 6-Month % Return")
    c1, c2 = st.columns(2)
    with c1:
        plotly_multi_line({
            "S&P 500": ("^GSPC", UP),
            "Nasdaq":  ("^IXIC", "#3399ff"),
            "Russell": ("^RUT",  ACCENT),
            "Dow":     ("^DJI",  "#cc66ff"),
        }, "U.S. Equities — 6M % Return", height=340)
    with c2:
        plotly_multi_line({
            "BTC":  ("BTC-USD", "#f7931a"),
            "IBIT": ("IBIT",    "#3399ff"),
            "TLT":  ("TLT",     ACCENT),
            "VIX":  ("^VIX",    DOWN),
        }, "BTC · IBIT · TLT · VIX — 6M % Return", height=340)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RATES
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    sec("Treasury Yields")
    rates_df = build_table(BASE_TICKERS["Rates"])
    metric_strip(rates_df)
    render_table(rates_df)

    st.markdown("")
    rmap = {r["Name"]: r["Last"] for _, r in rates_df.iterrows() if pd.notna(r.get("Last") or float("nan"))}
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("2s5s (bp)",   f"{(rmap['5Y'] -rmap['2Y']) *100:.1f}" if rmap.get("2Y")  and rmap.get("5Y")  else "—")
    s2.metric("5s10s (bp)",  f"{(rmap['10Y']-rmap['5Y']) *100:.1f}" if rmap.get("5Y")  and rmap.get("10Y") else "—")
    s3.metric("10s30s (bp)", f"{(rmap['30Y']-rmap['10Y'])*100:.1f}" if rmap.get("10Y") and rmap.get("30Y") else "—")
    s4.metric("2s30s (bp)",  f"{(rmap['30Y']-rmap['2Y']) *100:.1f}" if rmap.get("2Y")  and rmap.get("30Y") else "—")

    sec("Yield Curve Snapshot")
    plotly_yield_curve()

    sec("Individual Yield Trends — 6 Months")
    cl, cr = st.columns(2)
    with cl:
        plotly_line("^TNX", "10Y Treasury Yield",  color=ACCENT,    height=300)
        plotly_line("^IRX", "2Y Treasury Yield",   color="#3399ff", height=300)
    with cr:
        plotly_line("^TYX", "30Y Treasury Yield",  color="#cc66ff", height=300)
        plotly_line("^FVX", "5Y Treasury Yield",   color=UP,        height=300)

    sec("TLT — iShares 20+ Year Treasury ETF")
    plotly_candle("TLT", "TLT — 20+ Year Treasury Bond ETF", height=420)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FX
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    sec("FX Snapshot")
    fx_df = build_table(BASE_TICKERS["FX"])
    metric_strip(fx_df)
    render_table(fx_df)

    sec("G4 Pairs — 6-Month % Return")
    plotly_multi_line({
        "EUR/USD": ("EURUSD=X", "#3399ff"),
        "GBP/USD": ("GBPUSD=X", UP),
        "AUD/USD": ("AUDUSD=X", "#ffcc00"),
        "USD/CAD": ("CAD=X",    "#cc66ff"),
    }, "G4 FX — 6M % Return", height=340)

    sec("Pair Charts")
    cl, cr = st.columns(2)
    with cl:
        plotly_line("INR=X",    "USD/INR — EM Stress Barometer", color=ACCENT,    height=300)
        plotly_line("JPY=X",    "USD/JPY — Rate Beta Express",   color="#3399ff", height=300)
    with cr:
        plotly_line("CAD=X",    "USD/CAD — Commodity Carry",     color="#cc66ff", height=300)
        plotly_line("EURUSD=X", "EUR/USD",                       color=UP,        height=300)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MACRO FOCUS
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    sec("Daily Brief Watchlist — Live Tape")
    st.caption("TLT · MDI (TSX) · CAR.UN · IBIT · BTC · USD/INR · 10Y · 30Y · VIX")
    focus_df = build_table(FOCUS_TICKERS)
    metric_strip(focus_df)
    render_table(focus_df)

    sec("Charts — 3-Month Price Action")
    c1, c2, c3 = st.columns(3)
    with c1:
        plotly_candle("TLT",   "TLT",                    height=380)
        plotly_line("^VIX",    "VIX",   color=DOWN,      height=260)
    with c2:
        plotly_candle("MDI.TO",    "MDI — TSX Major Drilling",  height=380)
        plotly_candle("CAR-UN.TO", "CAR.UN — Cdn Apt REIT",     height=380)
    with c3:
        plotly_candle("IBIT",    "IBIT — iShares Bitcoin Trust", height=380)
        plotly_candle("BTC-USD", "Bitcoin (BTC-USD)",             height=380)

    sec("60-Day Return Correlation Matrix")
    corr_syms = {"BTC":"BTC-USD","IBIT":"IBIT","TLT":"TLT","SPX":"^GSPC","VIX":"^VIX","10Y":"^TNX"}
    frames = {n: load_history(s)["Close"].rename(n) for n, s in corr_syms.items()
              if (d := load_history(s)) is not None and not d.empty}
    if len(frames) >= 3:
        combined = pd.concat(frames.values(), axis=1).dropna()
        if len(combined) > 10:
            corr_m = combined.pct_change().dropna().tail(60).corr()
            fig_c  = px.imshow(corr_m,
                               color_continuous_scale=[[0,DOWN],[0.5,SURFACE2],[1,UP]],
                               zmin=-1, zmax=1, text_auto=".2f",
                               title="60-Day Return Correlation")
            fig_c.update_layout(**PT_BASE, height=360, coloraxis_showscale=True,
                                title=dict(text="60-Day Return Correlation", font=dict(color=ACCENT,size=12), x=0.01))
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
    st.caption("Paste the full Perplexity macro brief. Sections are auto-detected by ## headings.")
    brief_text = st.text_area("brief_input", height=240,
        placeholder="## Executive Summary\n- paste brief here...\n\n## Rates Market\n...",
        label_visibility="collapsed")

    if brief_text.strip():
        sections = parse_brief(brief_text)
        if sections:
            col_brief, col_live = st.columns([3, 2])
            with col_brief:
                sec("Parsed Sections")
                for title, body in sections.items():
                    icon = SECTION_ICONS.get(title, "•")
                    with st.expander(f"{icon}  {title}", expanded=(title == "Executive Summary")):
                        st.markdown(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body))
            with col_live:
                sec("Live Data")
                _live = build_table({"10Y":"^TNX","30Y":"^TYX","SPX":"^GSPC","VIX":"^VIX",
                                     "BTC":"BTC-USD","TLT":"TLT","INR":"INR=X","JPY":"JPY=X"})
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
            f'<div style="font-size:0.9rem;">Paste the Perplexity morning brief above.</div>'
            f'<div style="font-size:0.74rem;margin-top:6px;">Sections: Executive Summary · Rates · '
            f'Equities · Crypto · FX · Gamma · Risk · Watch</div></div>',
            unsafe_allow_html=True)
        st.markdown("")
        sec("Live Snapshot")
        _snap = build_table({"10Y Yld":"^TNX","30Y Yld":"^TYX","VIX":"^VIX",
                              "S&P 500":"^GSPC","BTC":"BTC-USD","IBIT":"IBIT","TLT":"TLT","USD/INR":"INR=X"})
        metric_strip(_snap.head(4))
        render_table(_snap)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CROSS-ASSET RISK
# ═══════════════════════════════════════════════════════════════════════════════
with tab6:
    sec("Cross-Asset Risk Dashboard")

    def _last(df): return float(df["Close"].iloc[-1]) if df is not None and not df.empty else None
    def _dpct(df):
        if df is None or df.empty or len(df)<2: return None
        return (float(df["Close"].iloc[-1])/float(df["Close"].iloc[-2])-1)*100

    vix_df  = load_history("^VIX");   spx_df  = load_history("^GSPC")
    tlt_df  = load_history("TLT");    btc_df  = load_history("BTC-USD")
    hy_df   = load_history("HYG");    ig_df   = load_history("LQD")
    dxy_df  = load_history("DX=F");   gold_df = load_history("GC=F")

    vix_v=_last(vix_df); vix_c=_dpct(vix_df)
    spx_v=_last(spx_df); spx_c=_dpct(spx_df)
    hy_v =_last(hy_df);  hy_c =_dpct(hy_df)
    btc_v=_last(btc_df); btc_c=_dpct(btc_df)
    tlt_v=_last(tlt_df); dxy_v=_last(dxy_df)
    gold_v=_last(gold_df); ig_v=_last(ig_df)

    if   vix_v and vix_v < 15: badge=f'<span class="badge-on">RISK-ON</span>'
    elif vix_v and vix_v < 25: badge=f'<span class="badge-neu">CAUTIOUS NEUTRAL</span>'
    elif vix_v and vix_v < 35: badge=f'<span class="badge-off">RISK-OFF</span>'
    elif vix_v:                 badge=f'<span class="badge-off">STRESS / CRISIS</span>'
    else:                       badge=f'<span class="badge-neu">UNKNOWN</span>'

    vix_str = f" &nbsp;·&nbsp; VIX <b>{vix_v:.2f}</b>" if vix_v else ""
    st.markdown(f"**Regime:** {badge}{vix_str}", unsafe_allow_html=True)
    st.markdown("")

    r1,r2,r3,r4 = st.columns(4)
    r1.metric("VIX",          f"{vix_v:.2f}"   if vix_v  else "—", f"{vix_c:+.2f}%"  if vix_c  else None)
    r2.metric("S&P 500",      f"{spx_v:,.0f}"  if spx_v  else "—", f"{spx_c:+.2f}%"  if spx_c  else None)
    r3.metric("HYG (HY ETF)", f"{hy_v:.2f}"    if hy_v   else "—", f"{hy_c:+.2f}%"   if hy_c   else None)
    r4.metric("BTC",          f"{btc_v:,.0f}"  if btc_v  else "—", f"{btc_c:+.2f}%"  if btc_c  else None)
    r5,r6,r7,r8 = st.columns(4)
    r5.metric("TLT",          f"{tlt_v:.2f}"   if tlt_v  else "—")
    r6.metric("DXY",          f"{dxy_v:.2f}"   if dxy_v  else "—")
    r7.metric("Gold",         f"{gold_v:,.1f}" if gold_v else "—")
    r8.metric("LQD (IG ETF)", f"{ig_v:.2f}"    if ig_v   else "—")

    sec("VIX Regime History")
    if vix_df is not None and not vix_df.empty:
        fig_v = go.Figure()
        for y0,y1,col in [(0,15,UP),(15,25,"#ffcc00"),(25,35,DOWN),(35,80,DOWN)]:
            fig_v.add_hrect(y0=y0,y1=y1,fillcolor=hex_rgba(col,0.05),line_width=0)
        for lvl,col,lbl in [(15,UP,"<15 Risk-On"),(25,"#ffcc00","15-25 Neutral"),(35,DOWN,">35 Stress")]:
            fig_v.add_hline(y=lvl,line_dash="dot",line_color=col,line_width=1,
                            annotation_text=lbl,annotation_font_color=col,annotation_position="right")
        fig_v.add_trace(go.Scatter(x=vix_df.index,y=vix_df["Close"],mode="lines",
                                   line=dict(color=DOWN,width=2),
                                   fill="tozeroy",fillcolor=hex_rgba(DOWN,0.08),
                                   hovertemplate="<b>%{x|%b %d}</b>  VIX %{y:.2f}<extra></extra>"))
        fig_v.update_layout(**PT_BASE,height=300,showlegend=False,
                            title=dict(text="VIX — 6 Months",font=dict(color=ACCENT,size=12),x=0.01))
        fig_v.update_xaxes(**XAXIS_STYLE)
        fig_v.update_yaxes(**YAXIS_STYLE)
        st.plotly_chart(fig_v,use_container_width=True)

    sec("Cross-Asset 6-Month % Return")
    plotly_multi_line({
        "S&P 500":("^GSPC",UP),"TLT":("TLT",ACCENT),"HYG":("HYG","#3399ff"),
        "Gold":("GC=F","#ffcc00"),"BTC":("BTC-USD","#f7931a"),"DXY":("DX=F","#cc66ff"),
    }, "Cross-Asset 6-Month % Return", height=360)

    sec("Gamma / Positioning Framework")
    st.markdown("""
| Signal | Threshold | Implication |
|--------|-----------|-------------|
| **VIX** | <15 / 15-25 / >25 / >35 | Risk-On / Neutral / Risk-Off / Stress |
| **0DTE Flow** | Break of dominant OI cluster | Accelerates realised vol |
| **TLT price action** | Sustained selling | Bear-steepener pressure |
| **SPX Pinning** | Near large open-interest strikes | Dealer hedging damps moves |
| **BTC β** | High DXY + high real yield | BTC headwind |
| **Positive γ** | Spot near max OI strike | Vol suppression, mean reversion |
| **Negative γ** | Spot through major strike | Vol expansion, trending |

> Live GEX: SpotGamma / Tier1Alpha. The above is the structural decision framework.
""")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 7 — MARKET INTEL  (BB-Terminal inspired)
# ═══════════════════════════════════════════════════════════════════════════════
with tab7:
    # ── Ticker Lookup ──────────────────────────────────────────────────────────
    sec("Ticker Lookup")
    col_in, col_per = st.columns([2, 1])
    with col_in:
        lookup_sym = st.text_input("Enter any ticker (e.g. AAPL, MDI.TO, BTC-USD, ^TNX)",
                                   value="", placeholder="AAPL", label_visibility="collapsed")
    with col_per:
        lookup_per = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y"], index=2,
                                  label_visibility="collapsed")

    if lookup_sym.strip():
        sym = lookup_sym.strip().upper()
        ldf = load_history(sym, period=lookup_per)
        if ldf is not None and not ldf.empty:
            last, chg, pct = latest_metrics(ldf)
            hi = float(ldf["High"].max()); lo = float(ldf["Low"].min())
            avg_vol = ldf["Volume"].replace(0, np.nan).mean() if "Volume" in ldf.columns else None
            lc1,lc2,lc3,lc4,lc5 = st.columns(5)
            lc1.metric("Last",       f"{last:,.4f}" if last else "—", f"{pct:+.2f}%" if pct else None)
            lc2.metric("Day Chg",    f"{chg:+.4f}"  if chg  else "—")
            lc3.metric(f"Period Hi", f"{hi:,.4f}")
            lc4.metric(f"Period Lo", f"{lo:,.4f}")
            lc5.metric("Avg Vol",    f"{avg_vol:,.0f}" if avg_vol and not np.isnan(avg_vol) else "N/A")
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
        gainers = movers_df.head(5)[["Name","Ticker","Last","Day %","1M %"]].reset_index(drop=True)
        render_table(gainers)
    with mc2:
        sec("Top Losers")
        losers  = movers_df.tail(5).iloc[::-1][["Name","Ticker","Last","Day %","1M %"]].reset_index(drop=True)
        render_table(losers)

    # Movers bar chart
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
        fig_m.update_layout(**PT_BASE, height=280,
                            title=dict(text="Watchlist — Day % Change", font=dict(color=ACCENT,size=12), x=0.01))
        fig_m.update_xaxes(tickangle=-30, **XAXIS_STYLE)
        fig_m.update_yaxes(ticksuffix="%", zeroline=True, zerolinecolor=BORDER, zerolinewidth=1, **YAXIS_STYLE)
        st.plotly_chart(fig_m, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── INTEL Scorecard ────────────────────────────────────────────────────────
    sec("INTEL Scorecard — Technical Signals")
    st.caption("RSI(14) · Price vs 50/200-day MA · 52-Week Range Position · 5-Day Momentum")

    scorecard_tickers = {
        "TLT":"TLT","MDI":"MDI.TO","IBIT":"IBIT","BTC":"BTC-USD",
        "SPX":"^GSPC","VIX":"^VIX","10Y":"^TNX","DXY":"DX=F",
    }
    score_rows = []
    for name, sym in scorecard_tickers.items():
        sc = intel_scorecard(sym)
        if not sc: continue
        rsi_val  = sc.get("rsi")
        rsi_sig  = ("🔴 OB" if rsi_val and rsi_val > 70 else
                    "🟢 OS" if rsi_val and rsi_val < 30 else "⚪ Neutral") if rsi_val else "—"
        ma50_sig = ("▲ Above" if sc.get("vs_50ma") and sc["vs_50ma"] > 0 else
                    "▼ Below") if sc.get("vs_50ma") is not None else "—"
        ma200_sig= ("▲ Above" if sc.get("vs_200ma") and sc["vs_200ma"] > 0 else
                    "▼ Below") if sc.get("vs_200ma") is not None else "—"
        rng      = sc.get("52w_range_pct")
        mom      = sc.get("mom_5d")
        score_rows.append({
            "Name":      name,
            "RSI(14)":   f"{rsi_val:.1f}" if rsi_val else "—",
            "RSI Signal":rsi_sig,
            "vs 50MA":   f"{sc['vs_50ma']:+.1f}%" if sc.get("vs_50ma") is not None else "—",
            "50MA Signal":ma50_sig,
            "vs 200MA":  f"{sc['vs_200ma']:+.1f}%" if sc.get("vs_200ma") is not None else "—",
            "200MA Sig": ma200_sig,
            "52W Range": f"{rng:.0f}%" if rng is not None else "—",
            "5D Mom":    f"{mom:+.2f}%" if mom is not None else "—",
        })

    if score_rows:
        sc_df = pd.DataFrame(score_rows)
        st.dataframe(sc_df, use_container_width=True, hide_index=True)

        # 52-week range bar chart
        rng_data = [(r["Name"], float(r["52W Range"].replace("%","")))
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
            fig_r.update_layout(**PT_BASE, height=260,
                                title=dict(text="52-Week Range Position (0% = 52W Low · 100% = 52W High)",
                                           font=dict(color=ACCENT, size=12), x=0.01))
            fig_r.update_xaxes(**XAXIS_STYLE)
            fig_r.update_yaxes(range=[0,110], ticksuffix="%", **YAXIS_STYLE)
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("Scorecard data loading…")
