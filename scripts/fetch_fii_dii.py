"""
Fetch provisional FII/DII cash-market net flows from NSE.

NSE's API blocks bare requests — it needs cookies from a prior hit on the
homepage in the same session. This is the standard workaround; it can
still break if NSE changes their bot-detection, so this function fails
soft (returns None) rather than raising, and the caller should show
"data unavailable" rather than crash the whole page build.
"""
import logging
import requests
import config

log = logging.getLogger("market_monitor.fetch_fii_dii")


def fetch_fii_dii():
    session = requests.Session()
    session.headers.update(config.NSE_HEADERS)
    try:
        # Warm up session/cookies
        session.get(config.NSE_HOME_URL, timeout=10)
        resp = session.get(config.NSE_FII_DII_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        latest = data[0]  # NSE returns most-recent-first
        fii_net = float(latest.get("fiiSell", 0)) * -1 + float(latest.get("fiiBuy", 0))
        dii_net = float(latest.get("diiSell", 0)) * -1 + float(latest.get("diiBuy", 0))
        # Some NSE payload variants expose net directly — prefer that if present
        if "fiiNet" in latest:
            fii_net = float(latest["fiiNet"])
        if "diiNet" in latest:
            dii_net = float(latest["diiNet"])
        return {
            "date": latest.get("date"),
            "fii_net_cr": round(fii_net, 0),
            "dii_net_cr": round(dii_net, 0),
        }
    except Exception as exc:
        log.warning("FII/DII fetch failed: %s", exc)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_fii_dii())
