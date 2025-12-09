#!/usr/bin/env python3
"""
Fetch latest NALCO news from:
  1) NALCO official Press Releases page
  2) Google News RSS (search: National Aluminium Company Limited NALCO)

Outputs: json/nalco_news.json
"""

import os
import json
import re
import requests
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

# ---------- CONFIG ----------
OUTPUT_PATH = os.path.join("json", "nalco_news.json")

NALCO_PRESS_URL = "https://nalcoindia.com/news-media/press-releases/"
GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?"
    "q=National+Aluminium+Company+Limited+NALCO&hl=en-IN&gl=IN&ceid=IN:en"
)


def safe_request(url, **kwargs):
    """Requests wrapper that never crashes the script."""
    try:
        resp = requests.get(url, timeout=20, **kwargs)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
        return None


# ---------- PARSE NALCO OFFICIAL PRESS RELEASES ----------

def fetch_nalco_press():
    """
    Scrape latest press releases from nalcoindia.com Press Releases listing.
    """
    print("[INFO] Fetching NALCO official press releases...")
    resp = safe_request(NALCO_PRESS_URL)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    # Find press-release headings linking to /pre-rel/
    for h3 in soup.select("h3"):
        a = h3.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        if "/pre-rel/" not in href:
            continue

        title = a.get_text(strip=True)
        url = urljoin(NALCO_PRESS_URL, href)

        # Find a dd/mm/yyyy date near this heading
        container = h3.parent
        text_block = container.get_text(" ", strip=True)
        m = re.search(r"(\d{2}/\d{2}/\d{4})", text_block)
        dt = None
        date_iso = None
        ts_iso = None

        if m:
            date_str = m.group(1)
            try:
                dt = datetime.strptime(date_str, "%d/%m/%Y")
                date_iso = dt.date().isoformat()
                ts_iso = dt.isoformat()
            except Exception:
                pass

        # Short summary from the article
        summary = ""
        detail = safe_request(url)
        if detail is not None:
            dsoup = BeautifulSoup(detail.text, "html.parser")
            p = dsoup.find("p")
            if p:
                summary = p.get_text(" ", strip=True)[:300]

        items.append({
            "source": "NALCO Press Release",
            "title": title,
            "url": url,
            "date": date_iso,
            "timestamp": ts_iso,
            "summary": summary,
        })

    print(f"[INFO] NALCO press releases found: {len(items)}")
    return items


# ---------- PARSE GOOGLE NEWS RSS ----------

def fetch_google_news():
    """
    Use Google News RSS feed for 'National Aluminium Company Limited NALCO'.
    """
    print("[INFO] Fetching Google News RSS...")
    resp = safe_request(GOOGLE_NEWS_RSS)
    if resp is None:
        return []

    items = []

    try:
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"[WARN] Failed to parse Google News RSS XML: {e}")
        return []

    channel = root.find("channel")
    if channel is None:
        return []

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = item.findtext("pubDate")
        desc_raw = item.findtext("description") or ""
        desc_clean = re.sub("<[^<]+?>", "", desc_raw)  # strip HTML tags
        desc_clean = desc_clean.replace("\xa0", " ").strip()

        dt = None
        date_iso = None
        ts_iso = None
        if pub_date_raw:
            try:
                dt = parsedate_to_datetime(pub_date_raw)
                if dt is not None:
                    date_iso = dt.date().isoformat()
                    ts_iso = dt.isoformat()
            except Exception:
                pass

        items.append({
            "source": "Google News",
            "title": title,
            "url": link,
            "date": date_iso,
            "timestamp": ts_iso,
            "summary": desc_clean[:300],
        })

    print(f"[INFO] Google News items found: {len(items)}")
    return items


# ---------- MERGE + WRITE JSON ----------

def dedupe_items(items):
    """Remove duplicates by URL."""
    seen = set()
    unique = []
    for it in items:
        key = (it.get("url") or "").strip()
        if not key:
            unique.append(it)
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)
    return unique


def main():
    all_items = []

    all_items.extend(fetch_nalco_press())
    all_items.extend(fetch_google_news())

    # Remove duplicates
    all_items = dedupe_items(all_items)

    # Sort by timestamp (most recent first)
    def sort_key(it):
        ts = it.get("timestamp")
        return ts or ""

    all_items.sort(key=sort_key, reverse=True)

    # Limit total items
    max_items = 40
    all_items = all_items[:max_items]

    data = {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(all_items),
        "items": all_items,
    }

    # Ensure json/ folder exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Wrote {len(all_items)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
