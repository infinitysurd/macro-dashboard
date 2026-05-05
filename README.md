# Macro Market Dashboard

A two-layer Streamlit dashboard for daily market work:

- **Market Base**: broad cross-asset dashboard for rates, equities, FX, crypto, and volatility.
- **Daily Macro Focus**: tighter subset aligned to the daily macro brief.

## Focus names

- TLT
- MDI (TSX: MDI / MDI.TO)
- CAR.UN (TSX: CAR-UN.TO)
- IBIT
- BTC

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy with GitHub + Streamlit Community Cloud

1. Create a GitHub repo.
2. Upload `app.py`, `requirements.txt`, and this `README.md`.
3. Go to Streamlit Community Cloud.
4. Connect the GitHub repo.
5. Deploy `app.py` from the main branch.

## Suggested workflow

- Keep **Market Base** open through the day.
- Use **Daily Macro Focus** while reading the morning note.
- Paste the latest written brief into the **Brief Sync** tab.
- Expand later with ETF flows, catalyst tables, and a manual notes panel.
