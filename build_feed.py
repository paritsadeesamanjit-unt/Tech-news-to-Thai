"""
สคริปต์หลัก: ดึงข่าว -> แปลไทย -> เซฟเป็น news.json
รันมือหรือให้ GitHub Actions รันอัตโนมัติก็ได้ (ดูใน .github/workflows/update-news.yml)

วิธีใช้:
  python build_feed.py                      # ใช้ Google Translate (ฟรี)
  python build_feed.py --backend claude      # ใช้ Claude API (ต้องมี ANTHROPIC_API_KEY)
  python build_feed.py --max-per-feed 3      # จำกัดข่าวต่อสำนักข่าว
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fetch_news import fetch_all
from translate import translate_all, translate_title
from fetch_stocks import fetch_indices
from fetch_youtube import fetch_reviews

FLAGS = {
    "TechCrunch": "US", "The Verge": "US", "Ars Technica": "US",
    "Wired": "US", "MIT Technology Review": "US", "Engadget": "US",
    "IEEE Spectrum": "US",
}

OUTPUT_PATH = Path(__file__).parent / "news.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["google", "claude"], default="google",
                         help="ตัวแปลภาษา: google (ฟรี) หรือ claude (คุณภาพดีกว่า ต้องมี API key)")
    parser.add_argument("--max-per-feed", type=int, default=5, help="จำนวนข่าวสูงสุดต่อ feed")
    parser.add_argument("--no-filter", action="store_true", help="ปิดการกรองด้วยคำสำคัญ")
    parser.add_argument("--no-stocks", action="store_true", help="ข้ามการดึงดัชนีหุ้น")
    parser.add_argument("--no-reviews", action="store_true", help="ข้ามการดึงวิดีโอรีวิวจาก YouTube")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="ที่อยู่ไฟล์ผลลัพธ์ json")
    args = parser.parse_args()

    print("[1/5] กำลังดึงข่าวจาก RSS feed ...")
    items = fetch_all(max_per_feed=args.max_per_feed, filter_keywords=not args.no_filter)
    print(f"      ดึงได้ {len(items)} ข่าว")

    for item in items:
        item["flag"] = FLAGS.get(item["source"], "")

    print(f"[2/5] กำลังแปลเป็นไทย (backend={args.backend}) ...")
    translated = translate_all(items, backend=args.backend)

    indices = []
    if not args.no_stocks:
        print("[3/5] กำลังดึงดัชนีหุ้นไทย/สหรัฐฯ ...")
        indices = fetch_indices()
        print(f"      ดึงได้ {len(indices)} ดัชนี")
    else:
        print("[3/5] ข้ามการดึงดัชนีหุ้น (--no-stocks)")

    reviews = []
    if not args.no_reviews:
        print("[4/5] กำลังดึงวิดีโอรีวิวจาก YouTube ...")
        raw_reviews = fetch_reviews()
        for v in raw_reviews:
            v["title_th"] = translate_title(v["title_en"], backend=args.backend)
        reviews = raw_reviews
        print(f"      ดึงได้ {len(reviews)} วิดีโอ")
    else:
        print("[4/5] ข้ามการดึงวิดีโอรีวิว (--no-reviews)")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(translated),
        "articles": translated,
        "indices": indices,
        "reviews": reviews,
    }

    print(f"[5/5] บันทึกผลลง {args.output}")
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print("เสร็จแล้ว")


if __name__ == "__main__":
    main()
