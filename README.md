# Morning Market Monitor

Two static pages, generated fresh every weekday morning by GitHub Actions:

- `docs/index.html` — **The Market Monitor**: index strip, FII/DII flows, gold, USD/INR, a live news feed, and global cues.
- `docs/winning-edge.html` — **The Winning Edge**: Ticker Thrust gauge (advance/decline) and Tale of the Tape (composite breadth score).

## First-time setup

1. Add this folder to a repo (or drop it alongside your pre-market scanner repo).
2. In repo **Settings → Pages**, set source to the `docs/` folder on your default branch (or "GitHub Actions" if you prefer the explicit deploy step in the workflow — both are wired up, pick one and drop the other from the workflow file).
3. In **Settings → Actions → General**, make sure "Read and write permissions" is enabled for the `GITHUB_TOKEN` (needed for the auto-commit step).
4. Trigger the workflow manually once via **Actions → Morning Market Monitor → Run workflow** to confirm it runs end-to-end before trusting the 8:30 AM IST schedule.

## Things to verify on the first live run

I built and unit-tested the rendering pipeline here, but this sandbox can't reach Yahoo Finance or NSE's site (network is allowlisted to a handful of package registries) — so the *data-fetching* code has to be validated on its first real run in Actions, where it'll have normal internet access. Specifically:

- **`config.INDEX_TICKERS["NIFTY SMALLCAP 100"]`** — Yahoo's symbol for this index is inconsistent; if `^CNXSC` comes back empty, try `NIFTYSMLCAP100.NS`.
- **FII/DII scrape** (`fetch_fii_dii.py`) — NSE's API needs session cookies and occasionally changes its bot-detection. It fails soft (shows "data unavailable") rather than crashing the page, but check the Action logs the first few days.
- **NSE universe** (`breadth_engine.py`) — defaults to pulling NSE's full equity list CSV directly. If you already maintain a ticker universe for the pre-market scanner, point `config.UNIVERSE_CSV_PATH` at that file instead — faster, and keeps both tools using the same universe.
- **Runtime** — a ~2,000-ticker breadth pass (280 days of history each, batched) will take a few minutes in CI. If it's too slow, drop `HISTORY_LOOKBACK_DAYS` or restrict to Nifty 500 instead of the full list.

## Tale of the Tape scoring

The 40/100 "RISK-OFF" style score is a composite you'll want to tune:

```
overall = average(
    % of stocks above 20/50/200 SMA,
    50 + net new-highs-minus-lows (clamped 0-100),
    50 + 2×(change in net new-hi-lo vs 5 sessions ago) (clamped),
    10-day average advance/decline ratio,
)
```

This is a reasonable starting rubric, not a validated one — `breadth_engine.score_tale_of_tape()` is the single place to adjust weights or normalization once you've compared a few weeks of output against your own read of the tape.

## Files

```
scripts/
  config.py           — tickers, universe source, thresholds
  fetch_market_data.py — indices/FX/commodities/global cues via yfinance
  fetch_fii_dii.py     — NSE FII/DII scrape
  breadth_engine.py    — universe load, advance/decline, SMA%, new hi/lo, scoring
  news_feed.py          — RSS headlines for the Live Intelligence Feed
  render.py             — HTML templates (shared CSS + both pages)
  main.py               — orchestrates the above, writes docs/*.html
.github/workflows/market-monitor.yml — schedule + Pages deploy
docs/                 — generated output (committed by the workflow)
```
