"""
Morning Market Monitor — orchestrator.
Fetches data, computes breadth/scores, writes docs/index.html and
docs/winning-edge.html for GitHub Pages.

Run locally:   python scripts/main.py
Run in CI:     see .github/workflows/market-monitor.yml
"""
import logging
import os
from datetime import datetime

import config
import fetch_market_data
import fetch_fii_dii
import breadth_engine
import news_feed
import render

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("market_monitor.main")


def main():
    generated_at = datetime.now()

    log.info("Fetching indices / FX / commodities / global cues...")
    indices = fetch_market_data.fetch_group(config.INDEX_TICKERS)
    fx_commodity = fetch_market_data.fetch_group(config.FX_COMMODITY_TICKERS)
    global_cues = fetch_market_data.fetch_group(config.GLOBAL_CUES_TICKERS)

    log.info("Fetching FII/DII flows...")
    fii_dii = fetch_fii_dii.fetch_fii_dii()

    log.info("Fetching news feed...")
    news_items = news_feed.fetch_feed_items()

    log.info("Loading NSE universe...")
    universe = breadth_engine.load_universe()
    log.info("Universe size: %d", len(universe))

    if universe:
        log.info("Downloading history for breadth calc (this can take a few minutes for the full universe)...")
        history = breadth_engine.download_history(universe)
        log.info("Got usable history for %d/%d tickers", len(history), len(universe))
        breadth = breadth_engine.compute_breadth(history)
    else:
        log.warning("Empty universe — breadth panel will show placeholders.")
        breadth = {
            "tape": 0, "advances": 0, "declines": 0, "pct_advancing": None,
            "pct_above_sma": {20: None, 50: None, 200: None},
            "net_new_hilo_today": 0, "net_new_hilo_5ago": 0,
            "movers_5d_20pct": 0, "vol_moves_up": 0, "vol_moves_down": 0,
            "avg_adv_dec_10d": None,
        }

    scores = breadth_engine.score_tale_of_tape(breadth)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    mm_html = render.render_market_monitor(indices, fx_commodity, fii_dii, global_cues, news_items, generated_at)
    we_html = render.render_winning_edge(breadth, scores, generated_at)

    with open(os.path.join(config.OUTPUT_DIR, "index.html"), "w") as f:
        f.write(mm_html)
    with open(os.path.join(config.OUTPUT_DIR, "winning-edge.html"), "w") as f:
        f.write(we_html)

    log.info("Wrote %s/index.html and %s/winning-edge.html", config.OUTPUT_DIR, config.OUTPUT_DIR)


if __name__ == "__main__":
    main()
