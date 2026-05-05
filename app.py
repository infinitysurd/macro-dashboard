import streamlit as st
import yfinance as yf
import pandas as pd
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

# ── Colour palette ────────────────────────────────────────────────────────────
BG        = "#1e1e1e"   # main background  (dark charcoal)
SURFACE   = "#252526"   # cards / sidebar
SURFACE2  = "#2d2d30"   # raised elements
BORDER    = "#3e3e42"   # borders
TXT       = "#d4d4d4"   # primary text
TXT_MUTED = "#858585"   # captions / labels
ACCENT    = "#f0b429"   # amber-gold (labels, active tabs)
UP        = "#00cc66"   # positive / green
DOWN      = "#f44747"   # negative / red

# ── Dark-grey CSS ─────────────────────────────────────────────────────────────
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
/* header */
.dash-header {{
    background: linear-gradient(90deg, {SURFACE} 0%, {SURFACE2} 50%, {SURFACE} 100%);
    border-bottom: 2px solid {ACCENT};
    padding: 12px 24px 10px;
    margin-bottom: 14px;
    border-radius: 0 0 4px 4px;
}}
.dash-header h1 {{
    color: {ACCENT};
    margin: 0;
    font-size: 1.25rem;
    letter-spacing: 3px;
    font-weight: 700;
    font-family: 'Segoe UI', monospace;
}}
.dash-header small {{ color: {TXT_MUTED}; font-size: 0.72rem; letter-spacing: 1px; }}

/* metric cards */
[data-testid="stMetric"] {{
    background-color: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
}}
[data-testid="stMetricLabel"] {{
    color: {TXT_MUTED} !important;
    font-size: 0.68rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}}
[data-testid="stMetricValue"] {{
    color: {TXT} !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] svg {{ display: none !important; }}
[data-testid="stMetricDelta"][data-direction="up"]   {{ color: {UP}   !important; }}
[data-testid="stMetricDelta"][data-direction="down"] {{ color: {DOWN} !important; }}

/* tabs */
[data-testid="stTabs"] button {{
    color: {TXT_MUTED} !important;
    font-size: 0.78rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid transparent !important;
    padding: 8px 16px !important;
}}
[data-testid="stTabs"] button[aria-selected="true"] {{
    color: {ACCENT} !important;
    border-bottom: 2px solid {ACCENT} !important;
    background: transparent !important;
}}
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 1px solid {BORDER} !important;
}}

/* section labels */
.sec {{
    color: {ACCENT};
    font-size: 0.68rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-weight: 600;
    border-bottom: 1px solid {BORDER};
    padding-bottom: 5px;
    margin: 16px 0 10px 0;
}}

/* risk badges */
.badge-on  {{ background:#0d2b1f; color:{UP};   border:1px solid {UP};   padding:3px 12px; border-radius:4px; font-size:0.75rem; letter-spacing:1px; font-weight:600; }}
.badge-off {{ background:#2b0d0d; color:{DOWN}; border:1px solid {DOWN}; padding:3px 12px; border-radius:4px; font-size:0.75rem; letter-spacing:1px; font-weight:600; }}
.badge-neu {{ background:#2b2400; color:#ffcc00; border:1px solid #ffcc00; padding:3px 12px; border-radius:4px; font-size:0.75rem; letter-spacing:1px; font-weight:600; }}

/* text area */
textarea, [data-baseweb="textarea"] textarea {{
    background-color: {SURFACE} !important;
    color: {TXT} !important;
    font-size: 0.82rem !important;
    border: 1px solid {BORDER} !important;
    border-radius: 4px !important;
}}

/* dataframe */
[data-testid="stDataFrame"] {{ border: 1px solid {BORDER} !important; border-radius: 4px; }}

/* scrollbar */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}

/* divider */
hr {{ border-color: {BORDER} !important; margin: 8px 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ── Plotly theme (matches grey palette) ───────────────────────────────────────
PT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=SURFACE,
    font=dict(color=TXT_MUTED, family="Segoe UI, sans-serif", size=11),
    xaxis=dict(gridcolor=SURFACE2, linecolor=BORDER, showgrid=True, zeroline=False),
    yaxis=dict(gridcolor=SURFACE2, linecolor=BORDER, showgrid=True, zeroline=False),
    margin=dict(l=48, r=16, t=40, b=32),
)

# ── Ticker universe ───────────────────────────────────────────────────────────
BASE_TICKERS = {
    "Rates": {
        "2Y":  "^IRX",
        "5Y":  "^FVX",
        "10Y": "^TNX",
        "30Y": "^TYX",
    },
    "Equities": {
        "S&P 500":      "^GSPC",
        "Dow":          "^DJI",
        "Nasdaq":       "^IXIC",
        "Russell 2000": "^RUT",
        "VIX":          "^VIX",
    },
    "FX": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CAD": "CAD=X",
        "AUD/USD": "AUDUSD=X",
        "USD/INR": "INR=X",
    },
    "Crypto": {
        "BTC":  "BTC-USD",
        "ETH":  "ETH-USD",
        "IBIT": "IBIT",
    },
}

FOCUS_TICKERS = {
    "TLT":     "TLT",
    "MDI":     "MDI.TO",
    "CAR.UN":  "CAR-UN.TO",
    "IBIT":    "IBIT",
    "BTC":     "BTC-USD",
    "USD/INR": "INR=X",
    "10Y":     "^TNX",
    "30Y":     "^TYX",
    "VIX":     "^VIX",
}

YIELD_CURVE = {"2Y": ("^IRX", 2), "5Y": ("^FVX", 5), "10Y": ("^TNX", 10), "30Y": ("^TYX", 30)}

# ── Utility ───────────────────────────────────────────────────────────────────
def hex_rgba(hex_color: str, alpha: float = 0.12) -> str:
    """Convert #rrggbb to rgba(r,g,b,a)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def sec(label: str):
    st.markdown(f'<div class="sec">▸ {label}</div>', unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def latest_metrics(df: pd.DataFrame):
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
            if len(df) > 21:
                m1 = ((df["Close"].iloc[-1] / df["Close"].iloc[-22]) - 1) * 100
            if len(df) > 63:
                m3 = ((df["Close"].iloc[-1] / df["Close"].iloc[-64]) - 1) * 100
        rows.append({
            "Name":    name,
            "Ticker":  symbol,
            "Last":    round(last, 4) if last  is not None else None,
            "Day Chg": round(chg,  4) if chg   is not None else None,
            "Day %":   round(pct,  2) if pct   is not None else None,
            "1M %":    round(m1,   2) if m1    is not None else None,
            "3M %":    round(m3,   2) if m3    is not None else None,
        })
    return pd.DataFrame(rows)


def render_table(df: pd.DataFrame):
    col_cfg = {}
    for c in df.columns:
        if "%" in c:
            col_cfg[c] = st.column_config.NumberColumn(c, format="%.2f %%")
        elif c == "Last":
            col_cfg[c] = st.column_config.NumberColumn("Last", format="%.4f")
        elif c == "Day Chg":
            col_cfg[c] = st.column_config.NumberColumn("Day Chg", format="%.4f")
    st.dataframe(df, use_container_width=True, hide_index=True, column_config=col_cfg)


def metric_strip(df: pd.DataFrame):
    cols = st.columns(len(df))
    for col, (_, row) in zip(cols, df.iterrows()):
        last = row.get("Last")
        pct  = row.get("Day %")
        val  = "—" if (last is None or (isinstance(last, float) and pd.isna(last))) else f"{last:,.2f}"
        d    = None if (pct  is None or (isinstance(pct,  float) and pd.isna(pct)))  else f"{pct:+.2f}%"
        col.metric(row["Name"], val, d)


# ── Chart helpers ─────────────────────────────────────────────────────────────
def _no_data(title: str):
    st.markdown(
        f'<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:6px;'
        f'padding:24px;text-align:center;color:{TXT_MUTED};font-size:0.8rem;">'
        f'No data available — {title}</div>',
        unsafe_allow_html=True,
    )


def plotly_line(symbol: str, title: str, color: str = ACCENT, height: int = 300):
    df = load_history(symbol)
    if df is None or df.empty:
        _no_data(title)
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=hex_rgba(color, 0.08),
        name=title,
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>%{y:.4f}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=ACCENT, size=12), x=0),
        height=height,
        showlegend=False,
        **PT,
    )
    st.plotly_chart(fig, use_container_width=True)


def plotly_candle(symbol: str, title: str, period: str = "3mo", height: int = 360):
    df = load_history(symbol, period=period)
    if df is None or df.empty:
        _no_data(title)
        return

    has_volume = "Volume" in df.columns and df["Volume"].sum() > 0
    rows_cfg = [0.78, 0.22] if has_volume else [1.0]
    n_rows   = 2 if has_volume else 1

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        row_heights=rows_cfg,
        vertical_spacing=0.03,
    )
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing=dict(line=dict(color=UP),   fillcolor=hex_rgba(UP,   0.6)),
        decreasing=dict(line=dict(color=DOWN),  fillcolor=hex_rgba(DOWN, 0.6)),
        name=title,
        hoverlabel=dict(bgcolor=SURFACE2),
    ), row=1, col=1)

    if has_volume:
        vol_colors = [UP if c >= o else DOWN
                      for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=[hex_rgba(c, 0.7) for c in vol_colors],
            name="Volume",
            showlegend=False,
        ), row=2, col=1)

    fig.update_layout(
        title=dict(text=title, font=dict(color=ACCENT, size=12), x=0),
        height=height,
        xaxis_rangeslider_visible=False,
        showlegend=False,
        **PT,
    )
    fig.update_yaxes(gridcolor=SURFACE2, linecolor=BORDER)
    st.plotly_chart(fig, use_container_width=True)


def plotly_yield_curve():
    tenors, yields = [], []
    for label, (sym, tenor) in YIELD_CURVE.items():
        df = load_history(sym)
        if df is not None and not df.empty:
            tenors.append(tenor)
            yields.append(float(df["Close"].iloc[-1]))
    if not tenors:
        _no_data("Yield Curve")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenors, y=yields,
        mode="lines+markers+text",
        text=[f"{y:.2f}%" for y in yields],
        textposition="top center",
        textfont=dict(color=ACCENT, size=11, family="Segoe UI"),
        line=dict(color=ACCENT, width=2.5),
        marker=dict(color=ACCENT, size=9, line=dict(color=BG, width=2)),
        fill="tozeroy",
        fillcolor=hex_rgba(ACCENT, 0.07),
        hovertemplate="<b>%{x}Y</b>: %{y:.3f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="U.S. Treasury Yield Curve", font=dict(color=ACCENT, size=12), x=0),
        xaxis=dict(tickvals=tenors, ticktext=[f"{t}Y" for t in tenors], gridcolor=SURFACE2),
        yaxis=dict(tickformat=".2f", ticksuffix="%", gridcolor=SURFACE2),
        height=300,
        **PT,
    )
    st.plotly_chart(fig, use_container_width=True)


def plotly_multi_line(series_map: dict, title: str, height: int = 320, pct_base: bool = True):
    """Overlay multiple tickers. series_map = {label: (symbol, color)}"""
    fig = go.Figure()
    for label, (sym, color) in series_map.items():
        df = load_history(sym)
        if df is None or df.empty:
            continue
        y = df["Close"]
        if pct_base:
            y = (y / y.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=y,
            mode="lines", name=label,
            line=dict(color=color, width=1.8),
            hovertemplate=f"<b>{label}</b>: %{{y:.2f}}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=ACCENT, size=12), x=0),
        height=height,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            bgcolor="rgba(0,0,0,0)", font=dict(size=10),
        ),
        **PT,
    )
    if pct_base:
        fig.update_yaxes(ticksuffix="%")
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
    "Executive Summary": "📋", "Rates Market": "📈", "Equities": "🏦",
    "Crypto": "₿", "FX": "💱", "Gamma & Positioning": "⚡",
    "Risk Sentiment Dashboard": "🚦", "What to Watch Today": "👁",
}

def parse_brief(text: str) -> dict:
    out = {}
    for name, pat in SECTION_RE.items():
        m = re.search(pat, text, re.DOTALL)
        if m:
            out[name] = m.group(1).strip()
    return out or ({"Full Brief": text.strip()} if text.strip() else {})


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<div style="color:{ACCENT};font-size:0.95rem;letter-spacing:3px;'
        f'font-weight:700;padding:4px 0 8px;">MACRO TERMINAL</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**Tabs**")
    st.markdown("""
- **Market Base** — broad cross-asset tape
- **Rates** — curve + spreads
- **FX** — six-pair dashboard
- **Macro Focus** — daily brief names
- **Brief Sync** — paste & parse brief
- **Cross-Asset Risk** — regime dashboard
""")
    st.markdown("---")
    st.markdown("**Watchlist**")
    st.caption("TLT · MDI.TO · CAR.UN · IBIT · BTC · USD/INR · 10Y · 30Y · VIX")
    st.markdown("---")
    if st.button("⟳  Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Loaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("Source: Yahoo Finance · 5-min cache")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="dash-header">
      <h1>MACRO MARKET DASHBOARD</h1>
      <small>MARKET BASE &nbsp;·&nbsp; RATES &nbsp;·&nbsp; FX &nbsp;·&nbsp;
      MACRO FOCUS &nbsp;·&nbsp; BRIEF SYNC &nbsp;·&nbsp; CROSS-ASSET RISK
      &nbsp;|&nbsp; {datetime.now().strftime("%Y-%m-%d %H:%M")} ET</small>
    </div>""",
    unsafe_allow_html=True,
)

# ── Top-line strip ────────────────────────────────────────────────────────────
_top = build_table({
    "S&P 500": "^GSPC",
    "10Y Yld": "^TNX",
    "VIX":     "^VIX",
    "BTC":     "BTC-USD",
    "DXY":     "DX=F",
    "Gold":    "GC=F",
})
metric_strip(_top)
st.markdown("<hr>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
base_tab, rates_tab, fx_tab, focus_tab, brief_tab, risk_tab = st.tabs([
    "📊 Market Base", "📈 Rates", "💱 FX",
    "🎯 Macro Focus", "📋 Brief Sync", "🚦 Cross-Asset Risk",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET BASE
# ═══════════════════════════════════════════════════════════════════════════════
with base_tab:
    for section_name, tickers in BASE_TICKERS.items():
        sec(section_name)
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
with rates_tab:
    sec("Treasury Yields")
    rates_df = build_table(BASE_TICKERS["Rates"])
    metric_strip(rates_df)
    render_table(rates_df)

    st.markdown("")
    rmap = {r["Name"]: r["Last"] for _, r in rates_df.iterrows() if pd.notna(r["Last"])}
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("2s5s (bp)",   f"{(rmap['5Y']  - rmap['2Y'])  * 100:.1f}" if rmap.get("2Y")  and rmap.get("5Y")  else "—")
    s2.metric("5s10s (bp)",  f"{(rmap['10Y'] - rmap['5Y'])  * 100:.1f}" if rmap.get("5Y")  and rmap.get("10Y") else "—")
    s3.metric("10s30s (bp)", f"{(rmap['30Y'] - rmap['10Y']) * 100:.1f}" if rmap.get("10Y") and rmap.get("30Y") else "—")
    s4.metric("2s30s (bp)",  f"{(rmap['30Y'] - rmap['2Y'])  * 100:.1f}" if rmap.get("2Y")  and rmap.get("30Y") else "—")

    sec("Yield Curve Snapshot")
    plotly_yield_curve()

    sec("Individual Yield Trends")
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
with fx_tab:
    sec("FX Snapshot")
    fx_df = build_table(BASE_TICKERS["FX"])
    metric_strip(fx_df)
    render_table(fx_df)

    sec("G3 Pairs — 6-Month % Return")
    plotly_multi_line({
        "EUR/USD": ("EURUSD=X", "#3399ff"),
        "GBP/USD": ("GBPUSD=X", UP),
        "AUD/USD": ("AUDUSD=X", "#ffcc00"),
        "USD/CAD": ("CAD=X",    "#cc66ff"),
    }, "G4 FX vs USD — 6M % Return", height=340)

    sec("Pair Charts")
    cl, cr = st.columns(2)
    with cl:
        plotly_line("INR=X",    "USD/INR  (EM Stress Barometer)", color=ACCENT,    height=300)
        plotly_line("JPY=X",    "USD/JPY  (Rate-Beta Express)",    color="#3399ff", height=300)
    with cr:
        plotly_line("CAD=X",    "USD/CAD  (Commodity Carry)",      color="#cc66ff", height=300)
        plotly_line("EURUSD=X", "EUR/USD",                         color=UP,        height=300)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DAILY MACRO FOCUS
# ═══════════════════════════════════════════════════════════════════════════════
with focus_tab:
    sec("Daily Brief Watchlist — Live Tape")
    st.caption("Aligned to the morning brief · TLT · MDI (TSX) · CAR.UN · IBIT · BTC · USD/INR · 10Y · 30Y · VIX")
    focus_df = build_table(FOCUS_TICKERS)
    metric_strip(focus_df)
    render_table(focus_df)

    sec("Charts")
    c1, c2, c3 = st.columns(3)
    with c1:
        plotly_candle("TLT",   "TLT",         height=380)
        plotly_line("^VIX",    "VIX",          color=DOWN,  height=280)
    with c2:
        plotly_candle("MDI.TO",    "MDI — TSX Major Drilling",  height=380)
        plotly_candle("CAR-UN.TO", "CAR.UN — Cdn Apt REIT",     height=380)
    with c3:
        plotly_candle("IBIT",      "IBIT — iShares Bitcoin Trust", height=380)
        plotly_candle("BTC-USD",   "Bitcoin (BTC-USD)",             height=380)

    sec("60-Day Return Correlation Matrix")
    corr_syms = {"BTC": "BTC-USD", "IBIT": "IBIT", "TLT": "TLT",
                 "SPX": "^GSPC",   "VIX":  "^VIX", "10Y": "^TNX"}
    frames = {}
    for name, sym in corr_syms.items():
        d = load_history(sym)
        if d is not None and not d.empty:
            frames[name] = d["Close"].rename(name)
    if len(frames) >= 3:
        combined = pd.concat(frames.values(), axis=1).dropna()
        if len(combined) > 10:
            corr_m = combined.pct_change().dropna().tail(60).corr()
            fig_c = px.imshow(
                corr_m,
                color_continuous_scale=[[0, DOWN], [0.5, SURFACE2], [1, UP]],
                zmin=-1, zmax=1,
                text_auto=".2f",
                title="60-Day Return Correlation",
            )
            fig_c.update_layout(height=360, coloraxis_showscale=True, **PT)
            fig_c.update_traces(textfont_size=12)
            st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.info("Not enough data for correlation matrix.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BRIEF SYNC
# ═══════════════════════════════════════════════════════════════════════════════
with brief_tab:
    sec("Morning Brief — Paste & Parse")
    st.caption("Paste the full Perplexity macro brief below. Sections are auto-detected by ## headings.")

    brief_text = st.text_area(
        "brief_input",
        height=260,
        placeholder=(
            "## Executive Summary\n"
            "- Paste the full brief here...\n\n"
            "## Rates Market\n...\n\n"
            "## Equities\n..."
        ),
        label_visibility="collapsed",
    )

    if brief_text.strip():
        sections = parse_brief(brief_text)
        if sections:
            st.markdown("")
            col_brief, col_live = st.columns([3, 2])
            with col_brief:
                sec("Parsed Sections")
                for title, body in sections.items():
                    icon = SECTION_ICONS.get(title, "•")
                    with st.expander(f"{icon}  {title}", expanded=(title == "Executive Summary")):
                        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
                        st.markdown(cleaned)
            with col_live:
                sec("Live Data")
                _live = build_table({
                    "10Y": "^TNX", "30Y": "^TYX",
                    "SPX": "^GSPC", "VIX": "^VIX",
                    "BTC": "BTC-USD", "TLT": "TLT",
                    "INR": "INR=X",   "JPY": "JPY=X",
                })
                metric_strip(_live.head(4))
                render_table(_live)
                st.markdown("")
                plotly_line("^TNX",    "10Y Yield",  color=ACCENT,    height=200)
                plotly_line("^GSPC",   "S&P 500",    color=UP,        height=200)
                plotly_line("BTC-USD", "BTC",        color="#f7931a", height=200)
        else:
            st.info("No sections detected — displaying as plain text.")
            st.markdown(brief_text)
    else:
        st.markdown(
            f"""<div style="background:{SURFACE};border:1px solid {BORDER};border-radius:6px;
            padding:28px;text-align:center;color:{TXT_MUTED};">
            <div style="font-size:2rem;margin-bottom:8px;">📋</div>
            <div style="font-size:0.9rem;">Paste the Perplexity morning brief above.</div>
            <div style="font-size:0.75rem;margin-top:6px;color:{TXT_MUTED};">
            Sections parsed: Executive Summary · Rates · Equities · Crypto · FX · Gamma · Risk · Watch
            </div></div>""",
            unsafe_allow_html=True,
        )
        st.markdown("")
        sec("Live Snapshot")
        _snap = build_table({
            "10Y Yld": "^TNX", "30Y Yld": "^TYX", "VIX": "^VIX",
            "S&P 500": "^GSPC", "BTC": "BTC-USD",
            "IBIT": "IBIT", "TLT": "TLT", "USD/INR": "INR=X",
        })
        metric_strip(_snap.head(4))
        render_table(_snap)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CROSS-ASSET RISK
# ═══════════════════════════════════════════════════════════════════════════════
with risk_tab:
    sec("Cross-Asset Risk Dashboard")

    vix_df  = load_history("^VIX")
    spx_df  = load_history("^GSPC")
    tlt_df  = load_history("TLT")
    btc_df  = load_history("BTC-USD")
    hy_df   = load_history("HYG")
    ig_df   = load_history("LQD")
    dxy_df  = load_history("DX=F")
    gold_df = load_history("GC=F")

    def _last(df): return float(df["Close"].iloc[-1]) if df is not None and not df.empty else None
    def _dpct(df):
        if df is None or df.empty or len(df) < 2: return None
        return (float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-2]) - 1) * 100

    vix_v  = _last(vix_df);  vix_c  = _dpct(vix_df)
    spx_v  = _last(spx_df);  spx_c  = _dpct(spx_df)
    hy_v   = _last(hy_df);   hy_c   = _dpct(hy_df)
    btc_v  = _last(btc_df);  btc_c  = _dpct(btc_df)
    tlt_v  = _last(tlt_df)
    dxy_v  = _last(dxy_df)
    gold_v = _last(gold_df)
    ig_v   = _last(ig_df)

    # Regime badge
    if vix_v is not None:
        if   vix_v < 15:  badge = f'<span class="badge-on">RISK-ON</span>';            rc = UP
        elif vix_v < 25:  badge = f'<span class="badge-neu">CAUTIOUS NEUTRAL</span>'; rc = "#ffcc00"
        elif vix_v < 35:  badge = f'<span class="badge-off">RISK-OFF</span>';          rc = DOWN
        else:             badge = f'<span class="badge-off">STRESS / CRISIS</span>';   rc = DOWN
    else:
        badge = f'<span class="badge-neu">UNKNOWN</span>'; rc = TXT_MUTED

    st.markdown(f"**Regime:** {badge} &nbsp;&nbsp; VIX: **{vix_v:.2f}**" if vix_v else f"**Regime:** {badge}", unsafe_allow_html=True)
    st.markdown("")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("VIX",          f"{vix_v:.2f}"   if vix_v  else "—", f"{vix_c:+.2f}%"  if vix_c  else None)
    r2.metric("S&P 500",      f"{spx_v:,.0f}"  if spx_v  else "—", f"{spx_c:+.2f}%"  if spx_c  else None)
    r3.metric("HYG (HY ETF)", f"{hy_v:.2f}"    if hy_v   else "—", f"{hy_c:+.2f}%"   if hy_c   else None)
    r4.metric("BTC",          f"{btc_v:,.0f}"  if btc_v  else "—", f"{btc_c:+.2f}%"  if btc_c  else None)

    r5, r6, r7, r8 = st.columns(4)
    r5.metric("TLT",          f"{tlt_v:.2f}"   if tlt_v  else "—")
    r6.metric("DXY",          f"{dxy_v:.2f}"   if dxy_v  else "—")
    r7.metric("Gold",         f"{gold_v:,.1f}" if gold_v else "—")
    r8.metric("LQD (IG ETF)", f"{ig_v:.2f}"    if ig_v   else "—")

    sec("VIX Regime History")
    if vix_df is not None and not vix_df.empty:
        fig_v = go.Figure()
        for y0, y1, col in [(0,15,UP),(15,25,"#ffcc00"),(25,35,DOWN),(35,80,DOWN)]:
            fig_v.add_hrect(y0=y0, y1=y1, fillcolor=hex_rgba(col, 0.05), line_width=0)
        for lvl, col, lbl in [(15,UP,"Risk-On <15"),(25,"#ffcc00","Elevated 15-25"),(35,DOWN,"Stress >35")]:
            fig_v.add_hline(y=lvl, line_dash="dot", line_color=col, line_width=1,
                            annotation_text=lbl, annotation_font_color=col,
                            annotation_position="right")
        fig_v.add_trace(go.Scatter(
            x=vix_df.index, y=vix_df["Close"],
            mode="lines", line=dict(color=DOWN, width=2),
            fill="tozeroy", fillcolor=hex_rgba(DOWN, 0.08),
            hovertemplate="<b>%{x|%b %d}</b>  VIX %{y:.2f}<extra></extra>",
        ))
        fig_v.update_layout(height=320, showlegend=False, **PT)
        st.plotly_chart(fig_v, use_container_width=True)

    sec("Cross-Asset 6-Month % Return")
    plotly_multi_line({
        "S&P 500": ("^GSPC",   UP),
        "TLT":     ("TLT",     ACCENT),
        "HYG":     ("HYG",     "#3399ff"),
        "Gold":    ("GC=F",    "#ffcc00"),
        "BTC":     ("BTC-USD", "#f7931a"),
        "DXY":     ("DX=F",    "#cc66ff"),
    }, "Cross-Asset 6-Month % Return", height=380)

    sec("Gamma / Positioning Framework")
    st.markdown(f"""
| Signal | Threshold | Implication |
|--------|-----------|-------------|
| **VIX** | <15 risk-on · 15-25 neutral · >25 risk-off · >35 stress | Regime classification |
| **0DTE Flow** | Break of dominant OI cluster | Can accelerate realised vol rapidly |
| **TLT price action** | Sustained selling | Bear-steepener pressure on duration |
| **SPX Pinning** | Near large open-interest strikes | Dealer buy-low/sell-high damps moves |
| **BTC β** | Rises with liquidity / falls with real yields | High DXY + high real yield = headwind |
| **Positive γ regime** | Spot near max OI strike | Mean-reversion, vol suppression |
| **Negative γ regime** | Spot through major strike | Trend-following, vol expansion |

> Live GEX requires SpotGamma / Tier1Alpha. The above is the structural decision framework.
""")
