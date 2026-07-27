"""
Market-breadth computations for the Ticker Thrust and Tale of the Tape panels.

Known gotcha (carried over from the pre-market scanner): recent yfinance
versions return multi-level tuple column names on batched downloads —
always flatten columns before indexing.
"""
import io
import logging
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import yfinance as yf

import config

log = logging.getLogger("market_monitor.breadth_engine")

# Exchanges/series to exclude — NSE's EQUITY_L.csv includes non-EQ series
# (rights, partly-paid, etc.) that will look like delisted/broken tickers.
VALID_SERIES = {"EQ"}


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------
def load_universe() -> list[str]:
    """Return a list of Yahoo-format tickers (SYMBOL.NS)."""
    if config.UNIVERSE_CSV_PATH:
        df = pd.read_csv(config.UNIVERSE_CSV_PATH)
        col = "SYMBOL" if "SYMBOL" in df.columns else df.columns[0]
        symbols = df[col].astype(str).str.strip().tolist()
    else:
        symbols = _download_nse_equity_list()
    return [f"{s}.NS" for s in symbols if s and s.upper() != "SYMBOL"]


def _download_nse_equity_list() -> list[str]:
    try:
        headers = {"User-Agent": config.NSE_HEADERS["User-Agent"]}
        resp = requests.get(config.NSE_EQUITY_LIST_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        df.columns = [c.strip() for c in df.columns]
        if "SERIES" in df.columns:
            df = df[df["SERIES"].str.strip().isin(VALID_SERIES)]
        return df["SYMBOL"].astype(str).str.strip().tolist()
    except Exception as exc:
        log.warning("Could not fetch NSE equity list (%s) — falling back to empty universe", exc)
        return []


# ---------------------------------------------------------------------------
# Bulk history download
# ---------------------------------------------------------------------------
def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse yfinance's MultiIndex columns from a batched download."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join([str(x) for x in col if x]) for col in df.columns]
    return df


def download_history(tickers: list[str], batch_size: int = 150) -> dict:
    """
    Returns {ticker: DataFrame[Open,High,Low,Close,Volume]} for tickers
    with usable data. Skips (and logs) tickers that error out or delist.
    """
    period_days = config.HISTORY_LOOKBACK_DAYS
    start = (datetime.utcnow() - timedelta(days=period_days)).strftime("%Y-%m-%d")
    result = {}
    skipped = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        try:
            raw = yf.download(
                batch, start=start, interval="1d",
                group_by="ticker", auto_adjust=True,
                threads=True, progress=False,
            )
        except Exception as exc:
            log.warning("Batch download failed (%s tickers): %s", len(batch), exc)
            skipped.extend(batch)
            continue

        raw = _flatten_columns(raw) if len(batch) == 1 else raw

        for tkr in batch:
            try:
                if len(batch) == 1:
                    sub = raw
                else:
                    sub = raw[tkr] if tkr in raw.columns.get_level_values(0) else None
                if sub is None or sub.empty or sub["Close"].dropna().empty:
                    skipped.append(tkr)
                    continue
                result[tkr] = sub.dropna(subset=["Close"])
            except Exception:
                skipped.append(tkr)

        time.sleep(1)  # be polite to Yahoo between batches

    if skipped:
        log.info("Skipped %d tickers with no usable data (delisted/illiquid/errors)", len(skipped))
    return result


# ---------------------------------------------------------------------------
# Per-ticker metrics
# ---------------------------------------------------------------------------
def _sma_flags(closes: pd.Series) -> dict:
    flags = {}
    for window in (20, 50, 200):
        if len(closes) >= window:
            sma = closes.rolling(window).mean().iloc[-1]
            flags[window] = bool(closes.iloc[-1] > sma) if pd.notna(sma) else None
        else:
            flags[window] = None
    return flags


def _is_new_high_low(closes: pd.Series, lookback: int = 252) -> str | None:
    window = closes.tail(lookback)
    if len(window) < 20:
        return None
    last = closes.iloc[-1]
    if last >= window.max():
        return "high"
    if last <= window.min():
        return "low"
    return None


def compute_breadth(history: dict) -> dict:
    """
    history: {ticker: DataFrame} from download_history()
    Returns the full breadth payload consumed by render.py.
    """
    advances = declines = unchanged = 0
    above_sma = {20: 0, 50: 0, 200: 0}
    counted_sma = {20: 0, 50: 0, 200: 0}
    new_highs_today = new_lows_today = 0
    new_highs_5ago = new_lows_5ago = 0
    movers_5d_20pct = 0
    up_4pct_today = down_4pct_today = 0
    adv_dec_ratio_10d = []

    for tkr, df in history.items():
        closes = df["Close"].dropna()
        if len(closes) < 2:
            continue

        chg_today = (closes.iloc[-1] - closes.iloc[-2]) / closes.iloc[-2] * 100
        if chg_today > 0:
            advances += 1
        elif chg_today < 0:
            declines += 1
        else:
            unchanged += 1

        if chg_today >= config.VOL_MOVE_PCT:
            up_4pct_today += 1
        elif chg_today <= -config.VOL_MOVE_PCT:
            down_4pct_today += 1

        if len(closes) >= 6:
            chg_5d = (closes.iloc[-1] - closes.iloc[-6]) / closes.iloc[-6] * 100
            if chg_5d >= config.FIVE_DAY_MOVER_PCT:
                movers_5d_20pct += 1

        flags = _sma_flags(closes)
        for w, is_above in flags.items():
            if is_above is not None:
                counted_sma[w] += 1
                if is_above:
                    above_sma[w] += 1

        hl_today = _is_new_high_low(closes)
        if hl_today == "high":
            new_highs_today += 1
        elif hl_today == "low":
            new_lows_today += 1

        if len(closes) >= 6:
            hl_5ago = _is_new_high_low(closes.iloc[:-5])
            if hl_5ago == "high":
                new_highs_5ago += 1
            elif hl_5ago == "low":
                new_lows_5ago += 1

        # 10-day rolling adv/dec ratio contribution
        if len(closes) >= 11:
            daily_chg = closes.diff().tail(10)
            up_days = int((daily_chg > 0).sum())
            adv_dec_ratio_10d.append(up_days / 10 * 100)

    tape = advances + declines + unchanged
    pct_advancing = round(advances / tape * 100, 1) if tape else None

    pct_above_sma = {
        w: round(above_sma[w] / counted_sma[w] * 100, 1) if counted_sma[w] else None
        for w in above_sma
    }

    avg_adv_dec_10d = round(sum(adv_dec_ratio_10d) / len(adv_dec_ratio_10d), 1) if adv_dec_ratio_10d else None

    return {
        "tape": tape,
        "advances": advances,
        "declines": declines,
        "pct_advancing": pct_advancing,
        "pct_above_sma": pct_above_sma,
        "net_new_hilo_today": new_highs_today - new_lows_today,
        "net_new_hilo_5ago": new_highs_5ago - new_lows_5ago,
        "movers_5d_20pct": movers_5d_20pct,
        "vol_moves_up": up_4pct_today,
        "vol_moves_down": down_4pct_today,
        "avg_adv_dec_10d": avg_adv_dec_10d,
    }


# ---------------------------------------------------------------------------
# Composite scoring — Tale of the Tape
# ---------------------------------------------------------------------------
def _clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))


def score_tale_of_tape(breadth: dict) -> dict:
    """
    Equal-weighted average of 4 factors, each normalized to 0-100:
      1. SMA gauges     — avg(% above 20/50/200 SMA)
      2. New hi/lo      — 50 + net_new_hilo_today, clamped
      3. Price & breadth trend — alignment of price direction vs
         %-above-50SMA direction over the 5-session window
      4. 10-day avg adv/dec ratio — used directly

    This rubric is a starting point — tune the weights/normalization
    once you've compared a few weeks of output against your own read
    of the tape.
    """
    pct_sma = breadth["pct_above_sma"]
    valid_sma = [v for v in pct_sma.values() if v is not None]
    factor_sma = sum(valid_sma) / len(valid_sma) if valid_sma else 50

    factor_hilo = _clamp(50 + breadth["net_new_hilo_today"])

    # trend alignment: compare today's %above50SMA to 5-sessions-ago proxy
    # (net_new_hilo change is used as a lightweight trend proxy here)
    hilo_delta = breadth["net_new_hilo_today"] - breadth["net_new_hilo_5ago"]
    factor_trend = _clamp(50 + hilo_delta * 2)

    factor_10d = breadth["avg_adv_dec_10d"] if breadth["avg_adv_dec_10d"] is not None else 50

    overall = round((factor_sma + factor_hilo + factor_trend + factor_10d) / 4, 1)

    if overall < 40:
        label, desc = "RISK-OFF", "weak participation, small sizes or sitout"
    elif overall < 60:
        label, desc = "NEUTRAL", "mixed signals, size normally and stay selective"
    else:
        label, desc = "RISK-ON", "broad participation, size up on your best setups"

    return {
        "overall": overall,
        "label": label,
        "description": desc,
        "factor_sma": round(factor_sma, 1),
        "factor_hilo": round(factor_hilo, 1),
        "factor_trend": round(factor_trend, 1),
        "factor_10d": round(factor_10d, 1) if breadth["avg_adv_dec_10d"] is not None else None,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    universe = load_universe()
    print(f"Universe size: {len(universe)}")
