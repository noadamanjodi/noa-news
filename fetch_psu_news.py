import feedparser
import json
from datetime import datetime, timezone
from urllib.parse import quote_plus
from pathlib import Path

# ---------------- CONFIG ----------------
GOOGLE_FEEDS = {
    "PSU": [
        "NALCO PSU",
        "NTPC PSU",
        "SAIL PSU",
        "ONGC PSU"
    ],
    "TECH": [
        "renewable energy technology",
        "AI in power sector",
        "EV battery technology"
    ],
    "SAFETY": [
        "industrial safety India",
        "electrical safety industry"
    ],
    "INDUSTRY": [
        "mining industry India",
        "aluminium industry India"
    ]
}

OFFICIAL_RSS = {
    "PSU": [
        ("PIB", "https://pib.gov.in/RssMain.aspx")
    ],
    "INDUSTRY": [
        ("Ministry of Mines", "https://mines.gov.in/rss.xml"),
        ("Ministry of Power", "https://powermin.gov.in/rss.xml")
    ]
}

MAX_ITEMS = 40
OUTPUT_FILE = Path("json/psu_news.json")
# ----------------------------------------

all_items = {}
now = datetime.now(timezone.utc)

# 🔹 GOOGLE NEWS (MAX COVERAGE)
for category, keywords in GOOGLE_FEEDS.items():
    for key in keywords:
        url = (
            "https://news.google.com/rss/search?"
            f"q={quote_plus(key)}&hl=en-IN&gl=IN&ceid=IN:en"
        )

        feed = feedparser.parse(url)

        for entry in feed.entries:
            link = entry.link.strip()
            if link in all_items:
                continue

            published = (
                datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed
                else now
            )

            all_items[link] = {
                "title": entry.title.strip(),
                "url": link,
                "date": published.isoformat(),
                "category": category,
                "source": "Google News",
                "source_type": "google"
            }

# 🔹 OFFICIAL RSS (QUALITY)
for category, feeds in OFFICIAL_RSS.items():
    for source_name, rss_url in feeds:
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            link = entry.link.strip()
            if link in all_items:
                continue

            published = (
                datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed
                else now
            )

            all_items[link] = {
                "title": entry.title.strip(),
                "url": link,
                "date": published.isoformat(),
                "category": category,
                "source": source_name,
                "source_type": "official"
            }

# 🔹 SORT & LIMIT
items = sorted(
    all_items.values(),
    key=lambda x: x["date"],
    reverse=True
)[:MAX_ITEMS]

output = {
    "items": items,
    "last_updated_utc": now.isoformat()
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ PSU news updated: {len(items)} items")
