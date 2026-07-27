"""
Fetch index / FX / commodity / global-cue quotes via yfinance.
Runs on GitHub Actions (unrestricted network) — not testable from a
sandboxed dev environment with domain allowlisting.
"""
import logging
import yfinance as yf

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
        pct = (last - prev) / prev * 100 if prev else None
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


if __name__ == "__main__":
    import config
    logging.basicConfig(level=logging.INFO)
    print(fetch_group(config.INDEX_TICKERS))
    print(fetch_group(config.FX_COMMODITY_TICKERS))
    print(fetch_group(config.GLOBAL_CUES_TICKERS))
