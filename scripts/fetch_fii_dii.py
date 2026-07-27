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

        # Real NSE schema: a list of rows, each shaped like
        # {"category": "FII/FPI", "date": "27-Jul-2026",
        #  "buyValue": "12345.67", "sellValue": "9876.54", "netValue": "2469.13"}
        fii_net = dii_net = None
        row_date = None
        for row in data:
            category = str(row.get("category", "")).upper()
            net = row.get("netValue")
            if net is None:
                continue
            try:
                net = float(net)
            except (TypeError, ValueError):
                continue
            if "FII" in category or "FPI" in category:
                fii_net = net
                row_date = row_date or row.get("date")
            elif "DII" in category:
                dii_net = net
                row_date = row_date or row.get("date")

        if fii_net is None and dii_net is None:
            log.warning("FII/DII response had no recognizable FII/DII rows: %r", data[:2])
            return None

        return {
            "date": row_date,
            "fii_net_cr": round(fii_net, 0) if fii_net is not None else None,
            "dii_net_cr": round(dii_net, 0) if dii_net is not None else None,
        }
    except Exception as exc:
        log.warning("FII/DII fetch failed: %s", exc)
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(fetch_fii_dii())
