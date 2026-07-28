"""
Live Positions — reads the manually-uploaded holdings sheet, keeps only
OPEN rows, and fetches a fresh live price for each ticker (the sheet's own
"Live Price" column is only as fresh as the last time it was uploaded).
"""
import logging
import math
import os

import pandas as pd

import config
from fetch_market_data import _quote  # reuse the same retrying yfinance fetch

log = logging.getLogger("market_monitor.holdings")


def load_holdings() -> list:
    """
    Returns a list of dicts, one per OPEN position, or [] if no file has
    been uploaded yet / it can't be parsed. Never raises — a missing or
    malformed holdings file should degrade the page, not break the run.
    """
    path = config.HOLDINGS_XLSX_PATH
    if not os.path.exists(path):
        log.info("No holdings file at %s — Live Positions will show as empty.", path)
        return []

    try:
        df = pd.read_excel(path, sheet_name=0)
    except Exception as exc:
        log.warning("Could not read holdings file %s: %s", path, exc)
        return []

    df.columns = [str(c).strip() for c in df.columns]
    if "Status" not in df.columns or "Ticker" not in df.columns:
        log.warning(
            "Holdings file missing expected columns (Status/Ticker). Found: %s",
            list(df.columns),
        )
        return []

    open_rows = df[df["Status"].astype(str).str.strip().str.upper() == "OPEN"]

    positions = []
    for _, row in open_rows.iterrows():
        ticker = str(row.get("Ticker", "")).strip()
        if not ticker or ticker.lower() == "nan":
            continue

        entry_price = _safe_float(row.get("Entry Price"))
        qty = _safe_float(row.get("Qty"))
        live_price, live_pct = _quote(f"{ticker}.NS")

        # Fall back to the sheet's own Live Price if a fresh fetch fails
        # (delisted ticker, symbol mismatch, etc.) rather than showing blank.
        if live_price is None:
            live_price = _safe_float(row.get("Live Price"))
            live_pct = _safe_float(row.get("Change%"))
            stale = True
        else:
            stale = False

        pnl = pnl_pct = None
        if entry_price and qty and live_price is not None:
            pnl = round((live_price - entry_price) * qty, 0)
            pnl_pct = round((live_price - entry_price) / entry_price * 100, 2)

        positions.append({
            "ticker": ticker,
            "strategy": str(row.get("Strategy", "")).strip(),
            "entry_date": str(row.get("Entry Date", "")).strip(),
            "qty": qty,
            "entry_price": entry_price,
            "stop_loss": _safe_float(row.get("Stop Loss")),
            "take_profit": _safe_float(row.get("Take Profit")),
            "live_price": live_price,
            "live_pct": live_pct,
            "stale_price": stale,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "risk_status": str(row.get("Risk Status", "")).strip(),
        })

    log.info("Loaded %d open position(s) from %s", len(positions), path)
    return positions


def _safe_float(v):
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def match_news_to_holdings(positions: list, news_pool: list, max_per_ticker: int = 2) -> dict:
    """
    news_pool: the broader (pre-truncation) list of fetched headlines.
    Returns {ticker: [news_item, ...]} — matches by ticker symbol appearing
    in the headline or summary. This is a substring match, so it'll miss
    articles that reference the company by name rather than ticker; a
    ticker-to-company-name mapping would improve recall if this proves
    too sparse in practice.
    """
    result = {}
    for pos in positions:
        ticker = pos["ticker"]
        matches = []
        for item in news_pool:
            haystack = (item.get("title", "") + " " + item.get("summary", "")).upper()
            if ticker.upper() in haystack:
                matches.append(item)
            if len(matches) >= max_per_ticker:
                break
        result[ticker] = matches
    return result
