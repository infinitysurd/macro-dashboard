import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import re

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Market Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈",
)

# ── Bloomberg-style dark theme CSS ───────────────────────────────────────────
st.markdown("""
<style>
/* ---- global dark background ---- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0d0d0d !important;
    color: #e0e0e0 !important;
    font-family: 'Consolas', 'Courier New', monospace !important;
}
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #222 !important;
}
/* ---- header bar ---- */
.main-header {
    background: linear-gradient(90deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%);
    border-bottom: 1px solid #f0b429;
    padding: 10px 20px;
    margin-bottom: 16px;
}
.main-header h1 { color: #f0b429; margin: 0; font-size: 1.4rem; letter-spacing: 2px; }
.main-header small { color: #888; font-size: 0.75rem; letter-spacing: 1px; }

/* ---- metric cards ---- */
[data-testid="stMetric"] {
    background-color: #161616 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 4px !important;
    padding: 8px 12px !important;
    margin: 2px !important;
}
[data-testid="stMetricLabel"] { color: #888 !important; font-size: 0.7rem !important; letter-spacing: 1px !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"] { color: #f0f0f0 !important; font-size: 1.1rem !important; font-weight: bold !important; }
[data-testid="stMetricDelta"] svg { display: none !important; }

/* ---- positive/negative deltas ---- */
[data-testid="stMetricDelta"][data-direction="up"]   { color: #00cc66 !important; }
[data-testid="stMetricDelta"][data-direction="down"] { color: #ff3333 !important; }

/* ---- dataframe ---- */
[data-testid="stDataFrame"] { border: 1px solid #222 !important; }
.dvn-scroller { background-color: #0d0d0d !important; }

/* ---- tabs ---- */
[data-testid="stTabs"] button {
    color: #888 !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f0b429 !important;
    border-bottom: 2px solid #f0b429 !important;
    background: transparent !important;
}

/* ---- section labels ---- */
.section-label {
    color: #f0b429;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    border-bottom: 1px solid #222;
    padding-bottom: 4px;
    margin: 12px 0 8px 0;
}

/* ---- risk badge ---- */
.badge-risk-on  { background:#003300; color:#00cc66; border:1px solid #00cc66; padding:2px 10px; border-radius:3px; font-size:0.75rem; letter-spacing:1px; }
.badge-risk-off { background:#330000; color:#ff3333; border:1px solid #ff3333; padding:2px 10px; border-radius:3px; font-size:0.75rem; letter-spacing:1px; }
.badge-neutral  { background:#1a1a00; color:#ffcc00; border:1px solid #ffcc00; padding:2px 10px; border-radius:3px; font-size:0.75rem; letter-spacing:1px; }

/* ---- text input / text area ---- */
textarea, [data-baseweb="textarea"] textarea {
    background-color: #111 !important;
    color: #ccc !important;
    font-family: monospace !important;
    font-size: 0.8rem !important;
    border: 1px solid #333 !important;
}
/* ---- scrollbar ---- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d0d0d; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── Ticker universe ───────────────────────────────────────────────────────────
BASE_TICKERS = {
    "Rates": {
        "2Y":  "^IRX",
        "5Y":  "^FVX",
        "10Y": "^TNX",
        "30Y": "^TYX",
    },
    "Equities": {
        "S&P 500":    "^GSPC",
        "Dow":        "^DJI",
        "Nasdaq":     "^IXIC",
        "Russell 2000": "^RUT",
        "VIX":        "^VIX",
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

YIELD_CURVE = {
    "2Y (^IRX)":  ("^IRX",  2),
    "5Y (^FVX)":  ("^FVX",  5),
    "10Y (^TNX)": ("^TNX", 10),
    "30Y (^TYX)": ("^TYX", 30),
}

PLOTLY_DARK = dict(
    paper_bgcolor="#0d0d0d",
    plot_bgcolor="#111111",
    font=dict(color="#aaa", family="Consolas, monospace", size=11),
    xaxis=dict(gridcolor="#1f1f1f", linecolor="#333", showgrid=True),
    yaxis=dict(gridcolor="#1f1f1f", linecolor="#333", showgrid=True),
    margin=dict(l=40, r=20, t=36, b=30),
)

# ── Data helpers ─────────────────────────────────────────────────────────────
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
            "Name":   name,
            "Ticker": symbol,
            "Last":   round(last, 4) if last is not None else None,
            "Day Chg": round(chg, 4) if chg is not None else None,
            "Day %":  round(pct, 2)  if pct is not None else None,
            "1M %":   round(m1, 2)   if m1  is not None else None,
            "3M %":   round(m3, 2)   if m3  is not None else None,
        })
    return pd.DataFrame(rows)


def styled_dataframe(df: pd.DataFrame):
    """Apply green/red colour-coding to % columns."""
    def colour_pct(val):
        if pd.isna(val):
            return "color: #555"
        return "color: #00cc66" if val >= 0 else "color: #ff3333"

    pct_cols = [c for c in df.columns if "%" in c]
    styled = df.style.applymap(colour_pct, subset=pct_cols).format(
        {c: "{:+.2f}%" for c in pct_cols},
        na_rep="—",
    ).format(
        {"Last": lambda x: f"{x:,.4f}" if pd.notna(x) else "—",
         "Day Chg": lambda x: f"{x:+.4f}" if pd.notna(x) else "—"},
        na_rep="—",
    ).set_properties(**{
        "background-color": "#111",
        "color": "#ddd",
        "font-family": "Consolas, monospace",
        "font-size": "12px",
    }).set_table_styles([
        {"selector": "th", "props": [
            ("background-color", "#1a1a1a"),
            ("color", "#f0b429"),
            ("font-size", "11px"),
            ("letter-spacing", "1px"),
            ("text-transform", "uppercase"),
            ("border-bottom", "1px solid #333"),
        ]},
        {"selector": "tr:hover td", "props": [("background-color", "#1a1a1a")]},
    ])
    return styled


def metric_strip(df: pd.DataFrame):
    cols = st.columns(len(df))
    for col, (_, row) in zip(cols, df.iterrows()):
        val = "—" if pd.isna(row["Last"]) else f"{row['Last']:,.2f}"
        d   = "—" if pd.isna(row["Day %"]) else f"{row['Day %']:+.2f}%"
        col.metric(row["Name"], val, d)


# ── Plotly chart helpers ──────────────────────────────────────────────────────
def plotly_line(symbol: str, title: str, color: str = "#f0b429", height: int = 240):
    df = load_history(symbol)
    if df is None or df.empty:
        st.warning(f"No data: {title}")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines",
        line=dict(color=color, width=1.5),
        fill="tozeroy",
        fillcolor=color.replace("#", "rgba(").rstrip(")") + ",0.07)" if color.startswith("#") else "rgba(240,180,41,0.07)",
        name=title,
        hovertemplate="%{x|%b %d}<br><b>%{y:.4f}</b><extra></extra>",
    ))
    fig.update_layout(title=dict(text=title, font=dict(color="#f0b429", size=12)),
                      height=height, showlegend=False, **PLOTLY_DARK)
    st.plotly_chart(fig, use_container_width=True)


def plotly_candle(symbol: str, title: str, period: str = "3mo", height: int = 320):
    df = load_history(symbol, period=period)
    if df is None or df.empty:
        st.warning(f"No data: {title}")
        return
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        increasing_line_color="#00cc66", decreasing_line_color="#ff3333",
        name=title,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=[
            "#00cc66" if c >= o else "#ff3333"
            for c, o in zip(df["Close"], df["Open"])
        ],
        name="Volume",
        showlegend=False,
    ), row=2, col=1)
    fig.update_layout(
        title=dict(text=title, font=dict(color="#f0b429", size=12)),
        height=height, xaxis_rangeslider_visible=False, showlegend=False,
        **PLOTLY_DARK,
    )
    fig.update_yaxes(gridcolor="#1f1f1f", linecolor="#333")
    st.plotly_chart(fig, use_container_width=True)


def plotly_yield_curve():
    """Snapshot yield curve: 2Y, 5Y, 10Y, 30Y."""
    tenors, yields, colors = [], [], []
    for label, (sym, tenor) in YIELD_CURVE.items():
        df = load_history(sym)
        if df is not None and not df.empty:
            y = float(df["Close"].iloc[-1])
            tenors.append(tenor)
            yields.append(y)
    if not tenors:
        st.warning("No yield data available")
        return
    labels = [f"{t}Y" for t in tenors]
    color  = "#f0b429"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tenors, y=yields, mode="lines+markers+text",
        text=[f"{y:.2f}%" for y in yields],
        textposition="top center",
        textfont=dict(color="#f0b429", size=11),
        line=dict(color=color, width=2),
        marker=dict(color=color, size=8),
        hovertemplate="<b>%{x}Y</b><br>%{y:.3f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="U.S. Treasury Yield Curve (Snapshot)", font=dict(color="#f0b429", size=12)),
        xaxis=dict(tickvals=tenors, ticktext=labels, gridcolor="#1f1f1f"),
        yaxis=dict(tickformat=".2f", ticksuffix="%", gridcolor="#1f1f1f"),
        height=280,
        **PLOTLY_DARK,
    )
    st.plotly_chart(fig, use_container_width=True)


def plotly_multi_line(symbols_colors: dict, title: str, height: int = 280, pct_base: bool = True):
    """Overlay multiple tickers normalised to 100 (% return basis)."""
    fig = go.Figure()
    for label, (sym, color) in symbols_colors.items():
        df = load_history(sym)
        if df is None or df.empty:
            continue
        series = df["Close"]
        if pct_base:
            series = (series / series.iloc[0] - 1) * 100
        fig.add_trace(go.Scatter(
            x=df.index, y=series,
            mode="lines", name=label,
            line=dict(color=color, width=1.5),
            hovertemplate=f"<b>{label}</b>: %{{y:.2f}}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#f0b429", size=12)),
        height=height,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
        **PLOTLY_DARK,
    )
    if pct_base:
        fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)


# ── Brief parser ──────────────────────────────────────────────────────────────
SECTION_PATTERNS = {
    "Executive Summary":       r"(?i)##\s*executive summary(.*?)(?=##|\Z)",
    "Rates Market":            r"(?i)##\s*rates market(.*?)(?=##|\Z)",
    "Equities":                r"(?i)##\s*equities(.*?)(?=##|\Z)",
    "Crypto":                  r"(?i)##\s*crypto(.*?)(?=##|\Z)",
    "FX":                      r"(?i)##\s*fx(.*?)(?=##|\Z)",
    "Gamma & Positioning":     r"(?i)##\s*gamma.*?positioning(.*?)(?=##|\Z)",
    "Risk Sentiment Dashboard":r"(?i)##\s*risk sentiment(.*?)(?=##|\Z)",
    "What to Watch Today":     r"(?i)##\s*what to watch(.*?)(?=##|\Z)",
}

SECTION_ICONS = {
    "Executive Summary":        "📋",
    "Rates Market":             "📈",
    "Equities":                 "🏦",
    "Crypto":                   "₿",
    "FX":                       "💱",
    "Gamma & Positioning":      "⚡",
    "Risk Sentiment Dashboard": "🚦",
    "What to Watch Today":      "👁",
}

def parse_brief(text: str) -> dict:
    sections = {}
    for name, pattern in SECTION_PATTERNS.items():
        m = re.search(pattern, text, re.DOTALL)
        if m:
            sections[name] = m.group(1).strip()
    if not sections and text.strip():
        sections["Full Brief"] = text.strip()
    return sections


def render_brief_section(title: str, body: str):
    icon = SECTION_ICONS.get(title, "•")
    st.markdown(
        f'<div class="section-label">{icon} {title}</div>',
        unsafe_allow_html=True,
    )
    # Strip markdown link syntax for cleaner display
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    # Bullet points → proper markdown
    st.markdown(cleaned)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="color:#f0b429;font-size:1rem;letter-spacing:2px;font-weight:bold;">⬛ MACRO TERMINAL</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**Workflow**")
    st.markdown(
        """
- **Market Base** — all-day broad tape
- **Rates** — curve structure & spreads
- **FX** — six-pair dashboard
- **Macro Focus** — daily brief alignment
- **Brief Sync** — paste & parse morning brief
- **Cross-Asset** — risk sentiment overview
""")
    st.markdown("---")
    st.markdown("**Watchlist**")
    st.markdown("TLT · MDI.TO · CAR.UN · IBIT · BTC · USD/INR · 10Y · 30Y · VIX")
    st.markdown("---")
    refresh_btn = st.button("⟳ Refresh data", use_container_width=True)
    if refresh_btn:
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("Data: Yahoo Finance · 5-min cache")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="main-header">
      <h1>MACRO MARKET DASHBOARD</h1>
      <small>BROAD MARKET BASE + DAILY MACRO FOCUS + BRIEF SYNC &nbsp;|&nbsp;
      UPDATED {datetime.now().strftime("%Y-%m-%d %H:%M")} ET</small>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Quick top-line strip ──────────────────────────────────────────────────────
_topline = {
    "S&P 500": "^GSPC",
    "10Y Yld": "^TNX",
    "VIX":     "^VIX",
    "BTC":     "BTC-USD",
    "DXY":     "DX-Y.NYB",
    "Gold":    "GC=F",
}
_top_df = build_table(_topline)
metric_strip(_top_df)
st.markdown("<hr style='border-color:#1f1f1f;margin:6px 0;'>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
(
    base_tab, rates_tab, fx_tab, focus_tab, brief_tab, risk_tab
) = st.tabs([
    "Market Base", "Rates", "FX", "Daily Macro Focus", "Brief Sync", "Cross-Asset Risk"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MARKET BASE
# ═══════════════════════════════════════════════════════════════════════════════
with base_tab:
    for section, tickers in BASE_TICKERS.items():
        st.markdown(f'<div class="section-label">▸ {section}</div>', unsafe_allow_html=True)
        df = build_table(tickers)
        metric_strip(df)
        st.dataframe(styled_dataframe(df), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-label">▸ Relative Performance (6-Month, % Return)</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        plotly_multi_line({
            "S&P 500": ("^GSPC", "#00cc66"),
            "Nasdaq":  ("^IXIC", "#3399ff"),
            "Russell": ("^RUT",  "#f0b429"),
            "Dow":     ("^DJI",  "#cc66ff"),
        }, "U.S. Equities — 6M % Return")
    with c2:
        plotly_multi_line({
            "BTC":  ("BTC-USD", "#f7931a"),
            "IBIT": ("IBIT",    "#0080ff"),
            "TLT":  ("TLT",     "#f0b429"),
            "VIX":  ("^VIX",    "#ff3333"),
        }, "BTC / IBIT / TLT / VIX — 6M % Return")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RATES
# ═══════════════════════════════════════════════════════════════════════════════
with rates_tab:
    st.markdown('<div class="section-label">▸ Treasury Yields</div>', unsafe_allow_html=True)
    rates_df = build_table(BASE_TICKERS["Rates"])
    metric_strip(rates_df)
    st.dataframe(styled_dataframe(rates_df), use_container_width=True, hide_index=True)

    # Curve spreads
    rmap = {r["Name"]: r["Last"] for _, r in rates_df.iterrows() if r["Last"] is not None}
    sc1, sc2, sc3 = st.columns(3)
    if rmap.get("2Y") and rmap.get("5Y"):
        sc1.metric("2s5s (bp)",  f"{(rmap['5Y']  - rmap['2Y'])  * 100:.1f}")
    if rmap.get("5Y") and rmap.get("10Y"):
        sc2.metric("5s10s (bp)", f"{(rmap['10Y'] - rmap['5Y'])  * 100:.1f}")
    if rmap.get("10Y") and rmap.get("30Y"):
        sc3.metric("10s30s (bp)",f"{(rmap['30Y'] - rmap['10Y']) * 100:.1f}")

    st.markdown('<div class="section-label">▸ Yield Curve Snapshot</div>', unsafe_allow_html=True)
    plotly_yield_curve()

    c_l, c_r = st.columns(2)
    with c_l:
        plotly_line("^TNX", "10Y Treasury Yield", color="#f0b429")
        plotly_line("^IRX", "2Y Treasury Yield",  color="#3399ff")
    with c_r:
        plotly_line("^TYX", "30Y Treasury Yield", color="#cc66ff")
        plotly_line("^FVX", "5Y Treasury Yield",  color="#00cc66")

    st.markdown('<div class="section-label">▸ TLT (20+ Year Treasury ETF)</div>', unsafe_allow_html=True)
    plotly_candle("TLT", "TLT — iShares 20+ Year Treasury Bond ETF")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FX
# ═══════════════════════════════════════════════════════════════════════════════
with fx_tab:
    st.markdown('<div class="section-label">▸ FX Rates</div>', unsafe_allow_html=True)
    fx_df = build_table(BASE_TICKERS["FX"])
    metric_strip(fx_df)
    st.dataframe(styled_dataframe(fx_df), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-label">▸ DXY & Key Pairs — 6-Month Trend</div>', unsafe_allow_html=True)
    plotly_multi_line({
        "EUR/USD": ("EURUSD=X", "#3399ff"),
        "GBP/USD": ("GBPUSD=X", "#00cc66"),
        "AUD/USD": ("AUDUSD=X", "#ffcc00"),
    }, "G3 FX vs USD — 6M % Return")

    c_l, c_r = st.columns(2)
    with c_l:
        plotly_line("INR=X",  "USD/INR (EM Stress Barometer)", color="#f0b429")
        plotly_line("JPY=X",  "USD/JPY (Rate-Beta Express)",   color="#3399ff")
    with c_r:
        plotly_line("CAD=X",  "USD/CAD (Commodity Carry)",     color="#cc66ff")
        plotly_line("EURUSD=X", "EUR/USD",                     color="#00cc66")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — DAILY MACRO FOCUS
# ═══════════════════════════════════════════════════════════════════════════════
with focus_tab:
    st.markdown(
        '<div class="section-label">▸ Daily Brief Watchlist — Live Tape</div>',
        unsafe_allow_html=True,
    )
    st.write("Aligned to the morning macro brief. Covers TLT, MDI (TSX), CAR.UN, IBIT, BTC, USD/INR, 10Y, 30Y, VIX.")
    focus_df = build_table(FOCUS_TICKERS)
    metric_strip(focus_df)
    st.dataframe(styled_dataframe(focus_df), use_container_width=True, hide_index=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="section-label">▸ TLT</div>', unsafe_allow_html=True)
        plotly_candle("TLT", "TLT", height=280)
        st.markdown('<div class="section-label">▸ VIX</div>', unsafe_allow_html=True)
        plotly_line("^VIX", "CBOE VIX", color="#ff3333")
    with c2:
        st.markdown('<div class="section-label">▸ MDI.TO (Major Drilling)</div>', unsafe_allow_html=True)
        plotly_candle("MDI.TO", "MDI — TSX: Major Drilling", height=280)
        st.markdown('<div class="section-label">▸ CAR.UN</div>', unsafe_allow_html=True)
        plotly_candle("CAR-UN.TO", "CAR.UN — Canadian Apt REIT", height=280)
    with c3:
        st.markdown('<div class="section-label">▸ IBIT / BTC</div>', unsafe_allow_html=True)
        plotly_candle("IBIT",    "IBIT — iShares Bitcoin Trust", height=280)
        plotly_candle("BTC-USD", "Bitcoin (BTC-USD)",             height=280)

    st.markdown('<div class="section-label">▸ Cross-Correlations (60-Day Rolling, Daily Returns)</div>', unsafe_allow_html=True)
    corr_tickers = {
        "BTC": "BTC-USD", "IBIT": "IBIT", "TLT": "TLT",
        "SPY": "^GSPC",   "VIX":  "^VIX", "10Y": "^TNX",
    }
    price_frames = {}
    for name, sym in corr_tickers.items():
        df = load_history(sym)
        if df is not None and not df.empty:
            price_frames[name] = df["Close"].rename(name)
    if price_frames:
        combined = pd.concat(price_frames.values(), axis=1).dropna()
        if len(combined) > 5:
            rets = combined.pct_change().dropna()
            corr_m = rets.tail(60).corr()
            fig_corr = px.imshow(
                corr_m,
                color_continuous_scale=[[0,"#ff3333"],[0.5,"#111111"],[1,"#00cc66"]],
                zmin=-1, zmax=1,
                text_auto=".2f",
                title="60-Day Return Correlation Matrix",
            )
            fig_corr.update_layout(
                height=340,
                coloraxis_showscale=True,
                **PLOTLY_DARK,
            )
            fig_corr.update_traces(textfont_size=11)
            st.plotly_chart(fig_corr, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BRIEF SYNC
# ═══════════════════════════════════════════════════════════════════════════════
with brief_tab:
    st.markdown('<div class="section-label">▸ Morning Brief — Paste & Analyse</div>', unsafe_allow_html=True)
    st.markdown(
        "Paste the Perplexity morning macro brief (Markdown format) below. "
        "The dashboard will parse it into sections and display live data alongside."
    )

    brief_text = st.text_area(
        "Morning Macro Brief",
        height=300,
        placeholder="## Executive Summary\n- Paste the full brief here...\n\n## Rates Market\n...",
        label_visibility="collapsed",
    )

    if brief_text.strip():
        sections = parse_brief(brief_text)

        if sections:
            st.markdown("---")
            # ── Live snapshot column alongside parsed text ──
            col_brief, col_live = st.columns([3, 2])

            with col_brief:
                st.markdown('<div class="section-label">▸ Brief Sections</div>', unsafe_allow_html=True)
                for title, body in sections.items():
                    with st.expander(f"{SECTION_ICONS.get(title, '•')} {title}", expanded=(title == "Executive Summary")):
                        render_brief_section(title, body)

            with col_live:
                st.markdown('<div class="section-label">▸ Live Data Panel</div>', unsafe_allow_html=True)
                _live = build_table({
                    "10Y Yld":  "^TNX",
                    "30Y Yld":  "^TYX",
                    "S&P 500":  "^GSPC",
                    "VIX":      "^VIX",
                    "BTC":      "BTC-USD",
                    "TLT":      "TLT",
                    "USD/INR":  "INR=X",
                    "USD/JPY":  "JPY=X",
                })
                metric_strip(_live.head(4))
                st.dataframe(styled_dataframe(_live), use_container_width=True, hide_index=True)

                st.markdown('<div class="section-label" style="margin-top:12px">▸ Key Charts</div>', unsafe_allow_html=True)
                plotly_line("^TNX",   "10Y Yield",   color="#f0b429", height=160)
                plotly_line("^GSPC",  "S&P 500",     color="#00cc66", height=160)
                plotly_line("BTC-USD","BTC",          color="#f7931a", height=160)
        else:
            st.info("Could not detect standard sections. Displaying as plain text.")
            st.markdown(brief_text)
    else:
        # Show placeholder when nothing is pasted
        st.markdown(
            """
<div style="background:#111;border:1px solid #222;border-radius:4px;padding:20px;text-align:center;color:#555;font-family:monospace;">
  <div style="font-size:2rem;">📋</div>
  <div style="margin-top:8px;">Paste the morning Perplexity brief above to unlock parsing.</div>
  <div style="font-size:0.75rem;margin-top:4px;">
    Sections detected: Executive Summary · Rates · Equities · Crypto · FX · Gamma · Risk · Watch
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        # Still show a live snapshot
        st.markdown('<div class="section-label" style="margin-top:16px">▸ Live Snapshot (while you wait for the brief)</div>', unsafe_allow_html=True)
        _snap_df = build_table({
            "10Y Yld":  "^TNX",
            "30Y Yld":  "^TYX",
            "VIX":      "^VIX",
            "S&P 500":  "^GSPC",
            "BTC":      "BTC-USD",
            "IBIT":     "IBIT",
            "TLT":      "TLT",
            "USD/INR":  "INR=X",
        })
        metric_strip(_snap_df.head(4))
        st.dataframe(styled_dataframe(_snap_df), use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CROSS-ASSET RISK
# ═══════════════════════════════════════════════════════════════════════════════
with risk_tab:
    st.markdown('<div class="section-label">▸ Cross-Asset Risk Dashboard</div>', unsafe_allow_html=True)

    # VIX regime
    vix_df  = load_history("^VIX")
    spx_df  = load_history("^GSPC")
    tlt_df  = load_history("TLT")
    btc_df  = load_history("BTC-USD")
    hy_df   = load_history("HYG")   # HY proxy
    ig_df   = load_history("LQD")   # IG proxy
    dxy_df  = load_history("DX-Y.NYB")
    gold_df = load_history("GC=F")

    def last_val(df):
        return float(df["Close"].iloc[-1]) if df is not None and not df.empty else None

    def day_pct(df):
        if df is None or df.empty or len(df) < 2:
            return None
        return (df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100

    vix_val  = last_val(vix_df)
    spx_val  = last_val(spx_df)
    tlt_val  = last_val(tlt_df)
    btc_val  = last_val(btc_df)
    hy_val   = last_val(hy_df)
    ig_val   = last_val(ig_df)
    dxy_val  = last_val(dxy_df)
    gold_val = last_val(gold_df)

    vix_chg  = day_pct(vix_df)
    spx_chg  = day_pct(spx_df)
    hy_chg   = day_pct(hy_df)
    btc_chg  = day_pct(btc_df)

    # Regime: crude VIX-based rule
    if vix_val is not None:
        if vix_val < 15:
            regime_badge = '<span class="badge-risk-on">RISK-ON</span>'
            regime_color = "#00cc66"
        elif vix_val < 25:
            regime_badge = '<span class="badge-neutral">CAUTIOUS NEUTRAL</span>'
            regime_color = "#ffcc00"
        elif vix_val < 35:
            regime_badge = '<span class="badge-risk-off">RISK-OFF</span>'
            regime_color = "#ff3333"
        else:
            regime_badge = '<span class="badge-risk-off">STRESS / CRISIS</span>'
            regime_color = "#ff0000"
    else:
        regime_badge = '<span class="badge-neutral">UNKNOWN</span>'
        regime_color = "#555"

    st.markdown(f"**Current Regime:** {regime_badge}", unsafe_allow_html=True)
    st.markdown("")

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.metric("VIX",        f"{vix_val:.2f}"  if vix_val  else "—", f"{vix_chg:+.2f}%"  if vix_chg  else None)
    r1c2.metric("S&P 500",    f"{spx_val:,.0f}" if spx_val  else "—", f"{spx_chg:+.2f}%"  if spx_chg  else None)
    r1c3.metric("HYG (HY proxy)", f"{hy_val:.2f}" if hy_val else "—", f"{hy_chg:+.2f}%"   if hy_chg   else None)
    r1c4.metric("BTC",        f"{btc_val:,.0f}" if btc_val  else "—", f"{btc_chg:+.2f}%"  if btc_chg  else None)

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.metric("TLT",  f"{tlt_val:.2f}" if tlt_val  else "—")
    r2c2.metric("DXY",  f"{dxy_val:.2f}" if dxy_val  else "—")
    r2c3.metric("Gold", f"{gold_val:,.1f}" if gold_val else "—")
    r2c4.metric("LQD (IG proxy)", f"{ig_val:.2f}" if ig_val else "—")

    st.markdown('<div class="section-label" style="margin-top:12px">▸ VIX Regime History</div>', unsafe_allow_html=True)
    if vix_df is not None and not vix_df.empty:
        fig_vix = go.Figure()
        fig_vix.add_hrect(y0=0,  y1=15, fillcolor="rgba(0,204,102,0.06)", line_width=0)
        fig_vix.add_hrect(y0=15, y1=25, fillcolor="rgba(255,204,0,0.06)",  line_width=0)
        fig_vix.add_hrect(y0=25, y1=35, fillcolor="rgba(255,51,51,0.06)",  line_width=0)
        fig_vix.add_hrect(y0=35, y1=100,fillcolor="rgba(204,0,0,0.08)",    line_width=0)
        for lvl, col, lbl in [(15,"#00cc66","Risk-On"), (25,"#ffcc00","Elevated"), (35,"#ff3333","Stress")]:
            fig_vix.add_hline(y=lvl, line_dash="dot", line_color=col,
                              annotation_text=lbl, annotation_font_color=col,
                              annotation_position="right")
        fig_vix.add_trace(go.Scatter(
            x=vix_df.index, y=vix_df["Close"],
            mode="lines", line=dict(color="#ff3333", width=1.5),
            fill="tozeroy", fillcolor="rgba(255,51,51,0.08)",
            name="VIX",
            hovertemplate="%{x|%b %d}<br>VIX <b>%{y:.2f}</b><extra></extra>",
        ))
        fig_vix.update_layout(height=280, showlegend=False, **PLOTLY_DARK)
        st.plotly_chart(fig_vix, use_container_width=True)

    st.markdown('<div class="section-label">▸ Risk Proxy Overlay (6-Month % Return)</div>', unsafe_allow_html=True)
    plotly_multi_line({
        "S&P 500":  ("^GSPC",     "#00cc66"),
        "TLT":      ("TLT",       "#f0b429"),
        "HYG":      ("HYG",       "#3399ff"),
        "Gold":     ("GC=F",      "#ffcc00"),
        "BTC":      ("BTC-USD",   "#f7931a"),
        "DXY":      ("DX-Y.NYB",  "#cc66ff"),
    }, "Cross-Asset 6-Month % Return")

    st.markdown('<div class="section-label">▸ Gamma / Positioning Commentary</div>', unsafe_allow_html=True)
    st.markdown(
        """
| Signal | Level | Implication |
|--------|-------|-------------|
| VIX (live) | ← see above | <15 = positive gamma suppression / >25 = vol expansion risk |
| 0DTE Flow | Monitor intraday | Break of dominant OI cluster can accelerate realised vol |
| TLT Put/Call | Proxy via price action | Duration selling = bear-steepener pressure |
| SPX Pinning | Near large OI strikes | Dealer buy-low/sell-high hedging damps moves |
| BTC Beta | Correlated to liquidity | High real-yield / strong DXY = BTC headwind |

> **Note:** Live GEX data requires SpotGamma / Tier1Alpha. The above is a structural framework.
> Positive gamma → mean-reversion. Negative gamma → trend-following.
"""
    )
