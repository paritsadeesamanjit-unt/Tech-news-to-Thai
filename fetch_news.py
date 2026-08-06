"""
ดึงข่าวเทคโนโลยี/AI จาก RSS feed ของสำนักข่าวต่างประเทศ
ปรับรายชื่อ feed หรือหมวดหมู่ได้ที่ FEEDS ด้านล่าง
"""

import re
import html
import feedparser

# name      = ชื่อสำนักข่าว (แสดงบนเว็บ)
# url       = ที่อยู่ RSS feed
# category  = ต้องตรงกับหมวดที่หน้าเว็บใช้กรอง: ai, robot, startup, chip, software
FEEDS = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "startup"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "software"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "category": "software"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "ai"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "category": "ai"},
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "category": "chip"},
    {"name": "IEEE Spectrum", "url": "https://spectrum.ieee.org/rss/fulltext", "category": "robot"},
]

MAX_ITEMS_PER_FEED = 5

# คำที่ใช้กรองเฉพาะข่าวที่เกี่ยวกับ AI/เทค/นวัตกรรม (กันข่าวหมวดอื่นที่หลุดเข้ามาจาก feed กว้างๆ)
KEYWORDS = [
    "ai", "artificial intelligence", "robot", "chip", "semiconductor",
    "startup", "software", "app", "machine learning", "model", "tech",
    "data", "cloud", "quantum", "automation", "hardware", "innovation",
]


def clean_html(raw: str) -> str:
    """ตัดแท็ก HTML และช่องว่างเกินออกจากข้อความ RSS"""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_relevant(title: str, summary: str) -> bool:
    combined = f"{title} {summary}".lower()
    return any(kw in combined for kw in KEYWORDS)


def fetch_all(max_per_feed: int = MAX_ITEMS_PER_FEED, filter_keywords: bool = True):
    """ดึงข่าวจากทุก feed ใน FEEDS แล้วคืนค่าเป็น list ของ dict (ยังเป็นภาษาอังกฤษ/ต้นฉบับ)"""
    items = []
    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        if parsed.bozo and not parsed.entries:
            print(f"  [เตือน] ดึง feed ไม่สำเร็จ: {feed['name']} ({feed['url']})")
            continue

        count = 0
        for entry in parsed.entries:
            if count >= max_per_feed:
                break
            title = clean_html(getattr(entry, "title", ""))
            summary = clean_html(getattr(entry, "summary", "") or getattr(entry, "description", ""))
            summary = summary[:500]

            if filter_keywords and not is_relevant(title, summary):
                continue

            items.append({
                "source": feed["name"],
                "flag": "",  # เติมทีหลังใน build_feed.py ถ้าต้องการ
                "category": feed["category"],
                "title_en": title,
                "summary_en": summary,
                "link": getattr(entry, "link", ""),
                "published": getattr(entry, "published", ""),
            })
            count += 1
    return items


if __name__ == "__main__":
    results = fetch_all()
    print(f"ดึงข่าวได้ทั้งหมด {len(results)} ชิ้น")
    for r in results[:5]:
        print(f"- [{r['source']}] {r['title_en']}")
