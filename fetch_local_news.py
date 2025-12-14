import feedparser
import json
from datetime import datetime, timezone

KEYWORDS = [
    "Damanjodi",
    "Similiguda",
    "Sunabeda",
    "Koraput",
    "Jeypore",
    "Pottangi",
    "NALCO Damanjodi",
    "HAL Sunabeda",
    "LIC Koraput",
    "Laxmipur Koraput",
    "Rayagada Odisha"
]

MAX_ITEMS = 25

all_items = {}
now = datetime.now(timezone.utc)

for key in KEYWORDS:
    url = (
        "https://news.google.com/rss/search?"
        f"q={key}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    feed = feedparser.parse(url)

    for entry in feed.entries:
        link = entry.link
        if link in all_items:
            continue

        published = (
            datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if hasattr(entry, "published_parsed")
            else now
        )

        all_items[link] = {
            "title": entry.title,
            "url": link,
            "date": published.isoformat()
        }

items = sorted(
    all_items.values(),
    key=lambda x: x["date"],
    reverse=True
)[:MAX_ITEMS]

output = {
    "items": items,
    "last_updated_utc": now.isoformat()
}

with open("json/local_news.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Local news updated: {len(items)} items")
