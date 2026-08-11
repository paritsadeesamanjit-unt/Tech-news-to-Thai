"""
ดึงข่าวเทคโนโลยี/AI จาก RSS feed ของสำนักข่าวต่างประเทศ
ปรับรายชื่อ feed หรือหมวดหมู่ได้ที่ FEEDS ด้านล่าง
"""

import re
import html
import feedparser
import urllib.request
import urllib.error

# name      = ชื่อสำนักข่าว (แสดงบนเว็บ)
# url       = ที่อยู่ RSS feed
# category  = ต้องตรงกับหมวดที่หน้าเว็บใช้กรอง: ai, robot, startup, chip, software, gadget, ev, review
FEEDS = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "category": "startup"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "software"},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "category": "software"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss", "category": "ai"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "category": "ai"},
    {"name": "Engadget", "url": "https://www.engadget.com/rss.xml", "category": "chip"},
    {"name": "IEEE Spectrum", "url": "https://spectrum.ieee.org/rss/fulltext", "category": "robot"},
    # เพิ่มสาย "เปิดตัวสินค้า" (มือถือ/โน้ตบุ๊ก) และ "รถยนต์ไฟฟ้า" และ "รีวิว" โดยเฉพาะ
    {"name": "9to5Mac", "url": "https://9to5mac.com/feed/", "category": "gadget"},
    {"name": "9to5Google", "url": "https://9to5google.com/feed/", "category": "gadget"},
    {"name": "Electrek", "url": "https://electrek.co/feed/", "category": "ev"},
    {"name": "CNET Reviews", "url": "https://www.cnet.com/rss/reviews/", "category": "review"},
]

MAX_ITEMS_PER_FEED = 6

# ดึง og:image / og:description เสริมจากหน้าเว็บต้นฉบับ เมื่อ RSS ให้ข้อมูลมาไม่พอ
# (ใช้ metadata แบบเดียวกับที่ Facebook/Twitter ใช้ทำ link preview — publisher ตั้งใจ
# ใส่มาให้บุคคลที่สามแสดงตัวอย่างอยู่แล้ว ไม่ใช่การไปคัดลอกเนื้อข่าวเต็มบทความ)
FETCH_OG_METADATA = True
OG_FETCH_TIMEOUT = 6
_UA = "Mozilla/5.0 (compatible; ThaiTechNewsBot/1.0; +https://github.com/)"

# คำที่ใช้กรองเฉพาะข่าวที่เกี่ยวกับ AI/เทค/นวัตกรรม (กันข่าวหมวดอื่นที่หลุดเข้ามาจาก feed กว้างๆ)
KEYWORDS = [
    "ai", "artificial intelligence", "robot", "chip", "semiconductor",
    "startup", "software", "app", "machine learning", "model", "tech",
    "data", "cloud", "quantum", "automation", "hardware", "innovation",
    # เปิดตัวสินค้า: มือถือ/โน้ตบุ๊ก
    "smartphone", "iphone", "android", "galaxy", "pixel", "macbook",
    "laptop", "notebook", "tablet", "ipad", "wearable", "launch", "unveil",
    "unveils", "announces", "debut",
    # รถยนต์ไฟฟ้า
    "ev", "electric vehicle", "electric car", "tesla", "byd", "battery",
    "charging",
    # รีวิว
    "review", "hands-on", "hands on", "benchmark",
]


def clean_html(raw: str) -> str:
    """ตัดแท็ก HTML และช่องว่างเกินออกจากข้อความ RSS"""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_image(entry) -> str:
    """ดึง URL ภาพประกอบจาก RSS entry ถ้ามี (media:content, media:thumbnail, หรือ enclosure)
    คืนค่าว่างถ้าไม่มีภาพ"""
    media_content = getattr(entry, "media_content", None)
    if media_content:
        for m in media_content:
            url = m.get("url")
            if url:
                return url

    media_thumbnail = getattr(entry, "media_thumbnail", None)
    if media_thumbnail:
        for m in media_thumbnail:
            url = m.get("url")
            if url:
                return url

    for link in getattr(entry, "links", []) or []:
        if str(link.get("type", "")).startswith("image"):
            href = link.get("href")
            if href:
                return href

    return ""


_OG_IMAGE_PATTERNS = [
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
]
_OG_DESC_PATTERNS = [
    r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']',
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
]


def fetch_og_metadata(url: str) -> dict:
    """พยายามดึง og:image / og:description จากหน้าเว็บต้นฉบับ — ใช้ metadata ที่สำนักข่าว
    ตั้งใจใส่ไว้ให้บุคคลที่สามแสดงตัวอย่าง (แบบเดียวกับ Facebook/Twitter link preview)
    ไม่ใช่การไปโหลดเนื้อข่าวเต็มบทความมาใช้ ถ้าดึงไม่สำเร็จจะคืน dict ว่างเฉยๆ ไม่ทำให้สคริปต์พัง"""
    if not FETCH_OG_METADATA or not url:
        return {"image": "", "description": ""}

    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=OG_FETCH_TIMEOUT) as resp:
            raw = resp.read(120_000)  # อ่านแค่ช่วงต้นของหน้า พอให้เจอ <meta> ใน <head>
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return {"image": "", "description": ""}

    image = ""
    for pattern in _OG_IMAGE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            image = html.unescape(m.group(1))
            break

    description = ""
    for pattern in _OG_DESC_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            description = html.unescape(m.group(1)).strip()
            break

    return {"image": image, "description": description}


def is_relevant(title: str, summary: str) -> bool:
    combined = f"{title} {summary}".lower()
    return any(kw in combined for kw in KEYWORDS)


# ถ้าหัวข้อ/สรุปข่าวมีคำที่บ่งชี้ชัดว่าเป็นรีวิว/EV/เปิดตัวสินค้า ให้จัดหมวดตามเนื้อหาจริง
# แทนที่จะยึดตามหมวดของ feed เพียงอย่างเดียว — กันปัญหาถ้า feed เฉพาะทาง (เช่น CNET Reviews)
# ดึงไม่ได้ในบางรอบ ข่าวหมวดนั้นๆ จาก feed อื่นก็ยังโผล่มาได้
_REVIEW_HINTS = ["review", "hands-on", "hands on", "we tested", "verdict"]
_EV_HINTS = ["electric vehicle", "electric car", "tesla", "byd", "ev charging", "ev battery", " ev "]
_GADGET_HINTS = [
    "unveils", "unveil", "launch", "announces", "debut", "iphone", "macbook",
    "galaxy", "pixel", "ipad", "smartphone", "laptop", "notebook", "wearable",
]


def refine_category(title: str, summary: str, base_category: str) -> str:
    text = f" {title} {summary} ".lower()
    if any(h in text for h in _REVIEW_HINTS):
        return "review"
    if any(h in text for h in _EV_HINTS):
        return "ev"
    if any(h in text for h in _GADGET_HINTS):
        return "gadget"
    return base_category


def fetch_all(max_per_feed: int = MAX_ITEMS_PER_FEED, filter_keywords: bool = True,
              fetch_og: bool = True):
    """ดึงข่าวจากทุก feed ใน FEEDS แล้วคืนค่าเป็น list ของ dict (ยังเป็นภาษาอังกฤษ/ต้นฉบับ)
    ถ้า fetch_og=True จะพยายามเสริมภาพ/คำอธิบายจากหน้าเว็บต้นฉบับให้ข่าวที่ RSS ให้ข้อมูลมาน้อย"""
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
            summary = summary[:800]

            if filter_keywords and not is_relevant(title, summary):
                continue

            link = getattr(entry, "link", "")
            image = extract_image(entry)

            # ถ้า RSS ไม่มีภาพ หรือสรุปสั้นเกินไป (ต่ำกว่า ~120 ตัวอักษร) ลองเสริมจากหน้าเว็บต้นฉบับ
            need_image = not image
            need_more_text = len(summary) < 120
            if fetch_og and (need_image or need_more_text):
                og = fetch_og_metadata(link)
                if need_image and og["image"]:
                    image = og["image"]
                if need_more_text and og["description"] and len(og["description"]) > len(summary):
                    summary = og["description"][:800]

            items.append({
                "source": feed["name"],
                "flag": "",  # เติมทีหลังใน build_feed.py ถ้าต้องการ
                "category": refine_category(title, summary, feed["category"]),
                "title_en": title,
                "summary_en": summary,
                "image": image,
                "link": link,
                "published": getattr(entry, "published", ""),
            })
            count += 1
    return items


if __name__ == "__main__":
    results = fetch_all()
    print(f"ดึงข่าวได้ทั้งหมด {len(results)} ชิ้น")
    for r in results[:5]:
        print(f"- [{r['source']}] {r['title_en']}")
