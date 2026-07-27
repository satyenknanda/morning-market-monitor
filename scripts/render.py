"""Render the Market Monitor and Winning Edge HTML pages."""
import math
from datetime import datetime
from zoneinfo import ZoneInfo

SHARED_CSS = """
:root {
  --navy: #2c4a6e; --navy-dark: #1e3550; --ink: #1a2433; --muted: #6b7686;
  --green: #1a9c5c; --red: #d63a3a; --amber: #b8862c; --card-bg: #ffffff;
  --page-bg: #f4f6f9; --border: #e4e8ee;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  background: var(--page-bg); color: var(--ink);
}
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 32px; background: #fff; border-bottom: 1px solid var(--border);
}
.topbar .brand { font-weight: 700; font-size: 15px; }
.topbar nav { display: flex; gap: 10px; }
.topbar nav a {
  padding: 8px 16px; border-radius: 20px; border: 1px solid var(--border);
  color: var(--ink); text-decoration: none; font-size: 13px; font-weight: 600;
}
.topbar nav a.active { background: var(--navy); color: #fff; border-color: var(--navy); }
.topbar .timestamp { font-size: 12px; color: var(--muted); }
.hero {
  background: linear-gradient(135deg, var(--navy) 0%, var(--navy-dark) 100%);
  color: #fff; text-align: center; padding: 44px 20px 36px;
}
.hero .ticker-line { font-size: 12px; opacity: .85; margin-bottom: 18px; }
.hero h1 { font-size: 54px; margin: 0; letter-spacing: 2px; font-weight: 800; }
.hero .tagline { font-size: 12px; letter-spacing: 3px; opacity: .8; margin: 14px 0 6px; text-transform: uppercase; }
.hero .meta { font-size: 13px; opacity: .9; }
.metric-strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1px; background: var(--border); margin: 24px 32px; border-radius: 10px; overflow: hidden;
}
.metric-card { background: #fff; padding: 20px 18px; text-align: center; }
.metric-label {
  display: inline-block; background: var(--navy); color: #fff; font-size: 11px;
  font-weight: 700; letter-spacing: .5px; padding: 4px 12px; border-radius: 6px; margin-bottom: 12px;
}
.metric-value { font-size: 24px; font-weight: 700; }
.metric-pct { font-size: 13px; font-weight: 600; margin-top: 4px; }
.pct-up { color: var(--green); } .pct-down { color: var(--red); } .pct-flat { color: var(--muted); }
.grid-2 { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; margin: 0 32px 32px; }
.panel { background: #fff; border-radius: 10px; border: 1px solid var(--border); padding: 22px 24px; }
.panel h2 { font-size: 13px; letter-spacing: .5px; color: var(--navy); margin: 0 0 16px; }
.feed-item {
  display: block; padding: 14px 0; border-bottom: 1px solid var(--border);
  color: inherit; text-decoration: none; cursor: pointer;
}
.feed-item:last-child { border-bottom: none; }
.feed-item:hover .feed-title { color: var(--navy); text-decoration: underline; }
.feed-source { font-size: 10.5px; color: var(--muted); margin-left: 4px; }
.feed-readmore { font-size: 11px; color: var(--navy); font-weight: 600; }
.feed-tag {
  display: inline-block; font-size: 10px; font-weight: 700; color: #fff;
  padding: 2px 8px; border-radius: 4px; margin-right: 8px; background: var(--muted);
}
.tag-BREAKING { background: var(--red); } .tag-DEALS { background: #8a4fd6; }
.tag-EARNINGS { background: var(--green); } .tag-COMMODITY { background: var(--amber); }
.tag-POLICY { background: #3a6fd6; } .tag-MARKETS { background: var(--muted); }
.feed-time { font-size: 11px; color: var(--muted); }
.feed-title { font-weight: 600; font-size: 14px; margin: 6px 0 4px; }
.feed-summary { font-size: 12.5px; color: var(--muted); line-height: 1.4; }
.cue-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 12px 0; border-bottom: 1px solid var(--border);
}
.cue-row:last-child { border-bottom: none; }
.cue-name { font-size: 13.5px; font-weight: 500; }
.cue-vals { text-align: right; }
.cue-value { font-size: 14px; font-weight: 700; }
.cue-pct { font-size: 11.5px; }
.gauge-wrap { text-align: center; }
.gauge-value { font-size: 42px; font-weight: 800; margin-top: -18px; }
.gauge-caption { font-size: 12px; color: var(--muted); letter-spacing: .5px; }
.adv-dec-bar {
  height: 10px; border-radius: 6px; overflow: hidden; display: flex; margin: 14px 0 8px;
}
.chips { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.chip { background: var(--page-bg); border: 1px solid var(--border); border-radius: 16px; padding: 6px 12px; font-size: 12px; }
.footer-note { background: #eaf6ee; color: var(--green); font-size: 13px; padding: 10px 16px; border-radius: 8px; margin-top: 14px; }
.score-badge {
  display: inline-flex; align-items: center; gap: 10px; margin-bottom: 4px;
}
.score-pill {
  background: var(--amber); color: #fff; font-weight: 700; font-size: 11px;
  padding: 4px 10px; border-radius: 4px;
}
.score-num { font-size: 20px; font-weight: 800; }
.score-desc { color: var(--amber); font-weight: 600; font-size: 13px; }
.factor-block { margin-top: 18px; }
.factor-block h3 { font-size: 12px; color: var(--navy); margin: 0 0 6px; letter-spacing: .3px; }
.factor-block ul { margin: 0; padding-left: 18px; font-size: 13px; color: #333; line-height: 1.55; }
"""


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and v != v)  # NaN != NaN


def _pct_class(pct):
    if _is_missing(pct):
        return "pct-flat"
    return "pct-up" if pct > 0 else ("pct-down" if pct < 0 else "pct-flat")


def _fmt_pct(pct):
    if _is_missing(pct):
        return "—"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct:.2f}%"


def _fmt_val(v, decimals=2):
    if _is_missing(v):
        return "—"
    return f"{v:,.{decimals}f}"


def _nav(active: str) -> str:
    tabs = [
        ("Market Monitor", "index.html"),
        ("Winning Edge", "winning-edge.html"),
        ("Live Positions", "#"),
        ("KPIs", "#"),
    ]
    links = "".join(
        f'<a href="{href}" class="{"active" if label == active else ""}">{label} →</a>'
        for label, href in tabs
    )
    return f'''<div class="topbar">
      <div class="brand">The Market Monitor</div>
      <nav>{links}<a href="#">● Connect Kite</a></nav>
      <div class="timestamp">{datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%A, %d %B %Y · %I:%M %p IST")}</div>
    </div>'''


def render_market_monitor(indices, fx_commodity, fii_dii, global_cues, news_items, generated_at) -> str:
    metric_cards = ""
    for label, d in {**indices, **fx_commodity}.items():
        if label == "FII/DII FLOWS":
            continue
        metric_cards += f'''<div class="metric-card">
          <span class="metric-label">{label}</span><br>
          <div class="metric-value">{_fmt_val(d["value"])}</div>
          <div class="metric-pct {_pct_class(d["pct"])}">{_fmt_pct(d["pct"])}</div>
        </div>'''

    fii_val = fii_dii.get("fii_net_cr") if fii_dii else None
    dii_val = fii_dii.get("dii_net_cr") if fii_dii else None
    if fii_val is not None or dii_val is not None:
        fii_text = f"FII {fii_val:+,.0f} cr" if fii_val is not None else "FII —"
        dii_text = f"DII {dii_val:+,.0f} cr" if dii_val is not None else "DII —"
        metric_cards += f'''<div class="metric-card">
          <span class="metric-label">FII / DII FLOWS</span><br>
          <div class="metric-value {_pct_class(fii_val)}">{fii_text}</div>
          <div class="metric-pct {_pct_class(dii_val)}">{dii_text}</div>
        </div>'''
    else:
        metric_cards += '''<div class="metric-card">
          <span class="metric-label">FII / DII FLOWS</span><br>
          <div class="metric-value">—</div><div class="metric-pct pct-flat">data unavailable</div>
        </div>'''

    feed_html = ""
    for item in news_items:
        link = item.get("link") or "#"
        ellipsis = "…" if item.get("truncated") else ""
        tag_href = f'href="{link}" target="_blank" rel="noopener noreferrer"' if link != "#" else 'href="#"'
        feed_html += f'''<a class="feed-item" {tag_href}>
          <span class="feed-tag tag-{item["tag"]}">{item["tag"]}</span>
          <span class="feed-time">{item["time_ago"]}</span>
          <span class="feed-source">· {item.get("source", "")}</span>
          <div class="feed-title">{item["title"]}</div>
          <div class="feed-summary">{item["summary"]}{ellipsis}</div>
          <div class="feed-readmore">Read full article →</div>
        </a>'''
    if not feed_html:
        feed_html = '<div class="feed-item feed-summary">No headlines fetched this run.</div>'

    cues_html = ""
    for label, d in global_cues.items():
        cues_html += f'''<div class="cue-row">
          <span class="cue-name">{label}</span>
          <div class="cue-vals">
            <div class="cue-value">{_fmt_val(d["value"])}</div>
            <div class="cue-pct {_pct_class(d["pct"])}">{_fmt_pct(d["pct"])}</div>
          </div>
        </div>'''

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>The Market Monitor</title>
<style>{SHARED_CSS}</style></head>
<body>
{_nav("Market Monitor")}
<div class="hero">
  <div class="ticker-line">Daily market wire — Indian equities</div>
  <h1>MARKET MONITOR</h1>
  <div class="tagline">Daily Market Wire</div>
  <div class="meta">Indian equities · {generated_at.strftime("%A, %d %B %Y")} · generated {generated_at.strftime("%I:%M %p IST")}</div>
</div>
<div class="metric-strip">{metric_cards}</div>
<div class="grid-2">
  <div class="panel"><h2>LIVE INTELLIGENCE FEED</h2>{feed_html}</div>
  <div class="panel"><h2>GLOBAL CUES</h2>{cues_html}</div>
</div>
</body></html>"""


def render_winning_edge(breadth, scores, generated_at) -> str:
    pct = breadth["pct_advancing"] or 0
    # semicircular gauge: 0-100% mapped to 180deg arc
    angle = 180 * (pct / 100)
    radius, cx, cy = 90, 100, 100
    rad = math.radians(180 - angle)
    x = cx + radius * math.cos(rad)
    y = cy - radius * math.sin(rad)
    large_arc = 1 if angle > 180 else 0
    gauge_svg = f'''<svg viewBox="0 0 200 110" width="260">
      <path d="M 10 100 A 90 90 0 0 1 190 100" fill="none" stroke="#e4e8ee" stroke-width="16"/>
      <path d="M 10 100 A 90 90 0 {large_arc} 1 {x:.1f} {y:.1f}" fill="none" stroke="#1a9c5c" stroke-width="16" stroke-linecap="round"/>
    </svg>'''

    adv, dec, tape = breadth["advances"], breadth["declines"], breadth["tape"]
    adv_pct = (adv / tape * 100) if tape else 0

    sma = scores  # scores dict already has factor breakdown; pull raw pct from breadth
    pct_sma = breadth["pct_above_sma"]

    tale_html = f"""
    <div class="score-badge">
      <span class="score-pill">{scores['label']}</span>
      <span class="score-num">{scores['overall']}/100</span>
      <span class="score-desc">— {scores['description']}</span>
    </div>

    <div class="factor-block">
      <h3>SMA GAUGES</h3>
      <ul>
        <li>20/50/200-day % above SMA: {_fmt_pctval(pct_sma.get(20))} / {_fmt_pctval(pct_sma.get(50))} / {_fmt_pctval(pct_sma.get(200))}</li>
        <li>{_sma_commentary(pct_sma)}</li>
      </ul>
    </div>

    <div class="factor-block">
      <h3>NEW HIGHS – LOWS</h3>
      <ul>
        <li>Net new highs – lows: {breadth['net_new_hilo_today']:+d} today, vs {breadth['net_new_hilo_5ago']:+d} five sessions ago</li>
        <li>{_hilo_commentary(breadth)}</li>
      </ul>
    </div>

    <div class="factor-block">
      <h3>PRICE &amp; BREADTH TREND</h3>
      <ul>
        <li>Trend factor score: {scores['factor_trend']}/100</li>
        <li>{_trend_commentary(scores['factor_trend'])}</li>
      </ul>
    </div>

    <div class="factor-block">
      <h3>10-DAY AVG ADV/DEC</h3>
      <ul>
        <li>10-day average advance/decline ratio: {_fmt_pctval(breadth['avg_adv_dec_10d'])}</li>
        <li>{_tenday_commentary(breadth['avg_adv_dec_10d'])}</li>
      </ul>
    </div>
    """

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>The Winning Edge</title>
<style>{SHARED_CSS}</style></head>
<body>
{_nav("Winning Edge")}
<div class="hero">
  <h1>THE WINNING EDGE</h1>
  <div class="tagline">The Trend Is Your Friend</div>
  <div class="meta">Indian equities · {generated_at.strftime("%A, %d %B %Y")} · generated {generated_at.strftime("%I:%M %p IST")}</div>
</div>
<div class="grid-2">
  <div class="panel">
    <h2>TICKER THRUST</h2>
    <div class="gauge-wrap">
      {gauge_svg}
      <div class="gauge-value">{pct:.1f}%</div>
      <div class="gauge-caption">OF THE TAPE IS ADVANCING</div>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top:18px;">
      <div><span style="color:var(--green); font-weight:800; font-size:20px">{adv:,}</span> ADVANCES</div>
      <div>TAPE {tape:,}</div>
      <div><span style="color:var(--red); font-weight:800; font-size:20px">{dec:,}</span> DECLINES</div>
    </div>
    <div class="adv-dec-bar">
      <div style="background:var(--green); width:{adv_pct:.1f}%"></div>
      <div style="background:var(--red); flex:1"></div>
    </div>
    <div class="chips">
      <span class="chip">+{breadth.get('movers_5d_20pct', 0)}% in 5D · {breadth.get('movers_5d_20pct', 0)} stocks</span>
      <span class="chip">4% vol moves · {breadth.get('vol_moves_up', 0)}▲ / {breadth.get('vol_moves_down', 0)}▼</span>
    </div>
    <div class="footer-note">Advancers ahead</div>
  </div>
  <div class="panel">
    <h2>TALE OF THE TAPE <span style="font-weight:400;color:var(--muted)">— Score = equal-weighted avg of the 4 factors below</span></h2>
    {tale_html}
  </div>
</div>
</body></html>"""


def _fmt_pctval(v):
    return f"{v:.1f}%" if v is not None else "—"


def _sma_commentary(pct_sma):
    vals = [v for v in pct_sma.values() if v is not None]
    if not vals:
        return "SMA data unavailable this run."
    below_50 = sum(1 for v in vals if v < 50)
    if below_50 == len(vals):
        return "All 3 gauges are below 50 — participation is narrow, with only a thin slice of the tape holding up"
    if below_50 == 0:
        return "All 3 gauges are above 50 — broad-based participation across the tape"
    return "Mixed readings across timeframes — participation is uneven"


def _hilo_commentary(breadth):
    delta = breadth["net_new_hilo_today"] - breadth["net_new_hilo_5ago"]
    if delta > 0:
        return "The trend is improving — more stocks are breaking out, and momentum is building beneath the surface"
    if delta < 0:
        return "The trend is deteriorating — fewer stocks are breaking out than five sessions ago"
    return "No meaningful change in the new-highs/lows trend over the window"


def _trend_commentary(factor_trend):
    if factor_trend < 40:
        return "Price and breadth are confirming each other to the downside — weakness is broad-based, not just a few names"
    if factor_trend > 60:
        return "Price and breadth are confirming each other to the upside — strength is broad-based"
    return "Price and breadth are not clearly aligned this window"


def _tenday_commentary(avg):
    if avg is None:
        return "Data unavailable this run."
    if avg < 40:
        return "Weak — decliners have had the upper hand over the last 10 sessions"
    if avg > 60:
        return "Strong — advancers have had the upper hand over the last 10 sessions"
    return "Middling — no strong directional signal either way over the last 10 sessions"
