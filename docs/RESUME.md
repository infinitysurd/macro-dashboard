# Resume Point — Macro Dashboard
**Last session:** 2026-05-05  
**Status:** Local dev working · Streamlit Community Cloud deploy still pending

---

## Where We Are

The app runs cleanly at `http://localhost:8501`.  
Start it with:
```bash
cd "C:/Users/Manav/Downloads/AI Test Folder/MacroDashboard"
streamlit run app.py
```

**GitHub:** https://github.com/infinitysurd/macro-dashboard  
**Branch:** `main` · **Entrypoint:** `app.py`  
**Last commit:** `c42cbcd` — light-grey theme

---

## App Structure (7 tabs)

| Tab | Purpose |
|-----|---------|
| 📊 Market Base | Cross-asset tables + 6M return overlays |
| 📈 Rates | Yield curve snapshot, spreads (2s5s/5s10s/10s30s/2s30s), TLT candle |
| 💱 FX | Six-pair table + individual trend charts |
| 🎯 Macro Focus | Brief watchlist: TLT, MDI.TO, CAR.UN, IBIT, BTC, 10Y, 30Y, VIX |
| 📋 Brief Sync | Paste Perplexity brief → auto-parsed by `##` section into expandable panels + live data |
| 🚦 Cross-Asset Risk | VIX regime badge + cross-asset overlay + gamma framework table |
| 📡 Market Intel | Ticker lookup, market movers bar chart, INTEL scorecard (RSI/MA/52W/mom) |

**Top strip** (always visible): S&P 500 · 10Y Yld · VIX · BTC · DXY · Gold  
**Sidebar:** workflow notes + manual refresh button

---

## Tech Stack

```
streamlit>=1.35.0
pandas>=2.0.0
numpy>=1.26.0
yfinance>=0.2.40
plotly>=5.22.0
requests>=2.31.0
jinja2>=3.1.0
```

Python env: **miniforge3** (Windows)  
jinja2 must be installed in miniforge3, not another venv.

---

## Theme

Light-grey palette — edit the 9 colour constants at the top of `app.py`:

```python
BG        = "#f0f2f5"   # page background
SURFACE   = "#ffffff"   # cards
SURFACE2  = "#e4e6ea"   # alt rows
BORDER    = "#ced0d4"
TXT       = "#1c1e21"
TXT_MUTED = "#606770"
ACCENT    = "#b8860b"   # dark amber
UP        = "#0a7a3c"
DOWN      = "#cc1f1f"
```

To go darker: swap BG→`#2b2b2b`, SURFACE→`#333`, TXT→`#d4d4d4`, ACCENT→`#f0b429`.

---

## Known Issues (to review on large display)

- [ ] Minor errors still showing in some tabs (noted but deferred)
- [ ] Chart proportions / spacing not fully validated on large monitor
- [ ] Line chart axis labels may need font-size tuning at wider viewport
- [ ] MDI.TO / CAR.UN candlesticks show "No data" outside TSX hours — expected, not a bug
- [ ] Streamlit Community Cloud deploy not yet done (see below)

---

## Next Session: Streamlit Community Cloud Deploy

Manual steps (takes ~2 min):
1. Go to https://share.streamlit.io/ → sign in as `infinitysurd`
2. **Create app** → repo `infinitysurd/macro-dashboard` · branch `main` · file `app.py`
3. Deploy → URL format: `https://infinitysurd-macro-dashboard-app-XXXX.streamlit.app`
4. Run through 7-tab checklist once live

---

## Next Session: Visual Polish (large display)

Things to eyeball and tweak:
- Chart heights per tab (current defaults: lines 300px, candles 380px, 3-col 380px)
- Metric strip card widths at wide viewport
- Table column widths — consider `column_config` width hints
- Brief Sync layout ratio (currently 3:2 col split)
- Consider adding a live price ticker scrollbar at the very top
- Consider adding date-range selector to charts (1W / 1M / 3M / 6M / 1Y)

---

## Morning Brief Format (Perplexity)

The Brief Sync tab expects these `##` headings (in order):
```
## Executive Summary
## Rates Market
## Equities
## Crypto
## FX
## Gamma & Positioning
## Risk Sentiment Dashboard
## What to Watch Today
```
Paste the full Perplexity output — parser strips citation links automatically.

---

## Key Design Decisions (don't undo without reason)

| Decision | Why |
|----------|-----|
| `DX=F` for DXY | `DX-Y.NYB` is unreliable on yfinance |
| `MDI.TO` for MDI | TSX ticker; `MDI` alone returns nothing |
| `PT_BASE` + `update_xaxes/yaxes` separately | Passing `xaxis=` in both `PT` and `update_layout` caused `TypeError: multiple values` |
| No `pandas.DataFrame.style` | Requires jinja2 in the same env; use `column_config` instead |
| `@st.cache_data(ttl=300)` on `load_history` | 5-min cache prevents hammering Yahoo Finance |
