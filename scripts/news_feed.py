"""Fetch and tag headlines for the Live Intelligence Feed panel."""
import logging
import re
from datetime import datetime, timezone

import feedparser

import config

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text or "").replace("&nbsp;", " ").strip()

log = logging.getLogger("market_monitor.news_feed")


def _tag_for(text: str) -> str:
    text_lower = text.lower()
    for tag, keywords in config.NEWS_TAGS.items():
        if any(kw in text_lower for kw in keywords):
            return tag
    return "MARKETS"


def _time_ago(published_parsed) -> str:
    if not published_parsed:
        return ""
    published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - published
    mins = int(delta.total_seconds() // 60)
    if mins < 60:
        return f"{max(mins, 1)}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def fetch_feed_items() -> list[dict]:
    items = []
    per_feed_limit = getattr(config, "NEWS_PER_FEED_LIMIT", 6)
    summary_chars = getattr(config, "NEWS_SUMMARY_CHARS", 220)

    for source, url in config.NEWS_FEEDS.items():
        try:
            parsed = feedparser.parse(url)
            n_entries = len(parsed.entries)
            bozo = getattr(parsed, "bozo", 0)
            if n_entries == 0:
                log.warning(
                    "Feed for %s (%s) returned 0 entries — bozo=%s, bozo_exception=%s, status=%s",
                    source, url, bozo, getattr(parsed, "bozo_exception", None),
                    getattr(parsed, "status", "n/a"),
                )
            else:
                log.info("Feed for %s returned %d entries", source, n_entries)
            for entry in parsed.entries[:per_feed_limit]:
                title = _strip_html(entry.get("title", ""))
                raw_summary = _strip_html(entry.get("summary", "") or entry.get("description", ""))
                truncated = len(raw_summary) > summary_chars
                summary = raw_summary[:summary_chars].strip()
                items.append({
                    "source": source,
                    "tag": _tag_for(title + " " + raw_summary),
                    "time_ago": _time_ago(entry.get("published_parsed")),
                    "published_parsed": entry.get("published_parsed"),
                    "title": title,
                    "summary": summary,
                    "truncated": truncated,
                    "link": entry.get("link", ""),
                })
        except Exception as exc:
            log.warning("Feed fetch failed for %s: %s", source, exc)

    items.sort(key=lambda x: x["published_parsed"] or 0, reverse=True)
    return _select_with_source_floor(items, config.NEWS_ITEMS_LIMIT, min_per_source=2)


def _select_with_source_floor(items: list, limit: int, min_per_source: int) -> list:
    """
    Take the top `limit` items by recency, but first guarantee up to
    `min_per_source` slots for every source present — otherwise a feed
    that's simply updated less often (fewer very-recent items) can get
    crowded out of the panel entirely by a busier feed's backlog.
    """
    by_source = {}
    for item in items:
        by_source.setdefault(item["source"], []).append(item)

    guaranteed = []
    for source_items in by_source.values():
        guaranteed.extend(source_items[:min_per_source])
    guaranteed = guaranteed[:limit]  # in case sources * min_per_source exceeds limit

    guaranteed_ids = {id(x) for x in guaranteed}
    remainder = [x for x in items if id(x) not in guaranteed_ids]

    remaining_slots = max(limit - len(guaranteed), 0)
    combined = guaranteed + remainder[:remaining_slots]
    combined.sort(key=lambda x: x["published_parsed"] or 0, reverse=True)
    return combined


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for it in fetch_feed_items():
        print(it["tag"], it["time_ago"], "-", it["title"])
