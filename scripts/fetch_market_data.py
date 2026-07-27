"""
Fetch index / FX / commodity / global-cue quotes via yfinance.
Runs on GitHub Actions (unrestricted network) — not testable from a
sandboxed dev environment with domain allowlisting.
"""
import logging
import math
import requests
import yfinance as yf

import config

log = logging.getLogger("market_monitor.fetch_market_data")


def _quote(ticker: str):
    """Return (last_price, pct_change) for a ticker, or (None, None) on failure."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")
        if hist.empty or len(hist) < 2:
            log.warning("No/insufficient history for %s", ticker)
            return None, None
        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        if math.isnan(last) or math.isnan(prev) or prev == 0:
            log.warning("NaN/zero close price for %s", ticker)
            return None, None
        pct = (last - prev) / prev * 100
        if math.isnan(pct):
            pct = None
        return round(last, 2), round(pct, 2) if pct is not None else None
    except Exception as exc:
        log.warning("Failed to fetch %s: %s", ticker, exc)
        return None, None


def fetch_group(ticker_map: dict) -> dict:
    """ticker_map: {label: yahoo_ticker} -> {label: {"value": x, "pct": y}}"""
    out = {}
    for label, ticker in ticker_map.items():
        value, pct = _quote(ticker)
        out[label] = {"value": value, "pct": pct, "ticker": ticker}
    return out


def fetch_nse_indices(name_match_map: dict) -> dict:
    """
    name_match_map: {label: substring_to_match_in_NSE_indexName}
    Fetches NSE's own live-indices API and matches rows by substring —
    for sub-indices Yahoo Finance doesn't reliably carry.
    Returns {label: {"value": x, "pct": y}}, with (None, None) per label on failure.
    """
    out = {label: {"value": None, "pct": None} for label in name_match_map}
    try:
        session = requests.Session()
        session.headers.update(config.NSE_HEADERS)
        session.get(config.NSE_HOME_URL, timeout=10)
        resp = session.get(config.NSE_ALL_INDICES_URL, timeout=10)
        resp.raise_for_status()
        rows = resp.json().get("data", [])
        for label, needle in name_match_map.items():
            needle_up = needle.upper()
            match = next(
                (r for r in rows if needle_up in str(r.get("indexName", "")).upper()),
                None,
            )
            if match is None:
                log.warning("No NSE index row matched %r for %s", needle, label)
                continue
            try:
                out[label] = {
                    "value": round(float(match["last"]), 2),
                    "pct": round(float(match["percentChange"]), 2),
                }
            except (KeyError, TypeError, ValueError) as exc:
                log.warning("Bad NSE index row for %s: %s (%s)", label, match, exc)
    except Exception as exc:
        log.warning("NSE allIndices fetch failed: %s", exc)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_group(config.INDEX_TICKERS))
    print(fetch_group(config.FX_COMMODITY_TICKERS))
    print(fetch_group(config.GLOBAL_CUES_TICKERS))
