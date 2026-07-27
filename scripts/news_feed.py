"""Fetch and tag headlines for the Live Intelligence Feed panel."""
import logging
from datetime import datetime, timezone

import feedparser

import config

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
    for source, url in config.NEWS_FEEDS.items():
        try:
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:6]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                items.append({
                    "source": source,
                    "tag": _tag_for(title + " " + summary),
                    "time_ago": _time_ago(entry.get("published_parsed")),
                    "published_parsed": entry.get("published_parsed"),
                    "title": title,
                    "summary": summary[:220].strip(),
                })
        except Exception as exc:
            log.warning("Feed fetch failed for %s: %s", source, exc)

    items.sort(key=lambda x: x["published_parsed"] or 0, reverse=True)
    return items[: config.NEWS_ITEMS_LIMIT]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for it in fetch_feed_items():
        print(it["tag"], it["time_ago"], "-", it["title"])
