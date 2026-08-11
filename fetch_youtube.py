"""
ดึงวิดีโอรีวิวล่าสุดจากช่อง YouTube ที่กำหนดไว้ ผ่าน RSS feed ทางการของ YouTube เอง
(https://www.youtube.com/feeds/videos.xml?channel_id=...) — ไม่มีการดาวน์โหลด, บันทึก,
หรือ transcribe เนื้อหาวิดีโอใดๆ ทั้งสิ้น ดึงมาแค่หัวข้อ/ลิงก์/ภาพปกที่ YouTube เปิดเผยต่อ
สาธารณะอยู่แล้ว (เหมือน RSS reader ทั่วไป) ฝั่งเว็บจะฝังตัวเล่นวิดีโอทางการของ YouTube
(youtube.com/embed/...) ให้กดดูบนแพลตฟอร์มของ YouTube เอง ไม่ได้เอาไฟล์วิดีโอมาเผยแพร่ต่อเอง
"""

import feedparser

# channel_id หาได้จากหน้าช่อง YouTube -> ...more -> Share channel -> Copy channel ID
CHANNELS = [
    {"channel_id": "UCBJycsmduvYEL83R_U4JriQ", "name": "MKBHD", "country": "US"},
    {"channel_id": "UCsTcErHg8oDvUnTzoqsYeNw", "name": "Unbox Therapy", "country": "US"},
    {"channel_id": "UC5P5NlgQmjinm_M4OCzbOHA", "name": "Beartai", "country": "TH"},
    {"channel_id": "UCsbSEW758I5Uow-5cCMUSow", "name": "Droidsans", "country": "TH"},
]

MAX_VIDEOS_PER_CHANNEL = 3


def fetch_reviews(max_per_channel: int = MAX_VIDEOS_PER_CHANNEL) -> list:
    """ดึงวิดีโอล่าสุดจากแต่ละช่องใน CHANNELS คืนค่าเป็น list ของ dict
    (ชื่อช่อง, หัวข้อวิดีโอ, video_id, ลิงก์, ภาพปก, วันที่เผยแพร่)"""
    videos = []
    for ch in CHANNELS:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={ch['channel_id']}"
        try:
            parsed = feedparser.parse(url)
        except Exception as e:
            print(f"  [เตือน] ดึงช่อง YouTube ไม่สำเร็จ: {ch['name']} ({e})")
            continue

        if parsed.bozo and not parsed.entries:
            print(f"  [เตือน] ดึงช่อง YouTube ไม่สำเร็จ: {ch['name']} (channel_id อาจไม่ถูกต้อง)")
            continue

        for entry in parsed.entries[:max_per_channel]:
            video_id = entry.get("yt_videoid", "")
            if not video_id:
                continue

            thumbnail = ""
            media_thumbnail = getattr(entry, "media_thumbnail", None)
            if media_thumbnail:
                thumbnail = media_thumbnail[0].get("url", "")
            if not thumbnail:
                # เผื่อ feed ไม่มี media:thumbnail มาให้ ใช้ URL ภาพปกมาตรฐานของ YouTube แทน
                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            videos.append({
                "channel": ch["name"],
                "country": ch["country"],
                "title_en": entry.get("title", ""),
                "video_id": video_id,
                "link": entry.get("link", f"https://www.youtube.com/watch?v={video_id}"),
                "thumbnail": thumbnail,
                "published": entry.get("published", ""),
            })
    return videos


if __name__ == "__main__":
    for v in fetch_reviews():
        print(f"[{v['channel']}] {v['title_en']} -> {v['link']}")
