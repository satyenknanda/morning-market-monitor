"""
Market Monitor — configuration
Edit the paths/tickers below to match your actual setup.
"""

# ---------------------------------------------------------------------------
# Yahoo Finance tickers for the top strip + Global Cues panel.
# ---------------------------------------------------------------------------
INDEX_TICKERS = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    # Confirmed valid on finance.yahoo.com (as "NIFTY MIDSML 400") — needed
    # the longer-period retry in fetch_market_data._quote() to actually
    # return bars, not a different symbol.
    "NIFTY MIDSMALLCAP 400": "NIFTYMIDSML400.NS",
}

# Kept as a fallback path — unused unless a future index proves as
# stubborn as this one was, in which case NSE's own live-indices API
# (fetch_market_data.fetch_nse_indices()) is the alternative to reach for.
NSE_DIRECT_INDICES = {}

FX_COMMODITY_TICKERS = {
    "USD/INR": "INR=X",
    "GOLD (COMEX, $/OZ)": "GC=F",
}

GLOBAL_CUES_TICKERS = {
    "S&P 500": "^GSPC",
    "QQQ": "QQQ",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "Shanghai Composite": "000001.SS",
    "KOSPI": "^KS11",
}

# ---------------------------------------------------------------------------
# NSE full-equity list used for breadth (advance/decline, SMA%, new hi/lo).
# This CSV is NSE's own master list of listed equities.
# If you already maintain a universe file for the pre-market scanner,
# point UNIVERSE_CSV_PATH at that instead — it'll be faster and consistent
# with your other tools.
# ---------------------------------------------------------------------------
NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
UNIVERSE_CSV_PATH = None   # e.g. "/path/to/premarket-scanner/universe.csv"
UNIVERSE_CACHE = "docs/_cache/universe.csv"

# How many days of history to pull per ticker for SMA/new-hi-lo calcs.
# 260 trading days ≈ covers 200SMA with buffer.
HISTORY_LOOKBACK_DAYS = 280

# Momentum-mover thresholds (used in Ticker Thrust footer chips)
FIVE_DAY_MOVER_PCT = 20.0     # "+20% in 5D · N stocks"
VOL_MOVE_PCT = 4.0            # "4% vol moves · X▲ / Y▼" (single-day % move)

# ---------------------------------------------------------------------------
# FII/DII provisional cash-market data (NSE).
# NSE requires session cookies from a prior homepage hit before the API
# will respond — see fetch_fii_dii.py.
# ---------------------------------------------------------------------------
NSE_HOME_URL = "https://www.nseindia.com"
NSE_ALL_INDICES_URL = "https://www.nseindia.com/api/allIndices"
NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# News RSS feeds for the "Live Intelligence Feed" panel.
# ---------------------------------------------------------------------------
NEWS_FEEDS = {
    "Livemint Markets": "https://www.livemint.com/rss/markets",
    "Economic Times Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/latestnews.xml",
}
NEWS_ITEMS_LIMIT = 12          # total headlines shown in the feed panel
NEWS_PER_FEED_LIMIT = 10        # how many entries to pull from each RSS feed before ranking
NEWS_SUMMARY_CHARS = 420        # snippet length per headline (was 220 — this is the "deeper" ask)

# Keyword → tag mapping for the feed (first match wins, else "MARKETS")
NEWS_TAGS = {
    "BREAKING": ["breaking", "war", "ceasefire", "crash", "surge", "record low", "record high"],
    "DEALS":    ["ipo", "acquire", "acquisition", "stake", "merger", "raises", "funding"],
    "EARNINGS": ["q1 results", "q2 results", "q3 results", "q4 results", "earnings", "profit", "net loss"],
    "COMMODITY": ["crude", "brent", "gold", "oil", "opec"],
    "POLICY":   ["rbi", "fed", "sebi", "budget", "tariff", "trade deal"],
}

# LOAD-BEARING: main.py runs with working-directory: scripts in the GitHub
# Actions workflow, so this path is relative to scripts/, not the repo root.
# It must stay "../docs" to land in the docs/ folder git actually tracks —
# this has been silently reverted to "docs" twice already. Do not "fix" it
# back without checking .github/workflows/market-monitor.yml first.
OUTPUT_DIR = "../docs"
