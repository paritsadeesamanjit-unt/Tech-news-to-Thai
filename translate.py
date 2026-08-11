"""
โมดูลแปลภาษา รองรับ 2 แบบ:

1. "google"  - ใช้ deep-translator (ฟรี ไม่ต้องมี API key) แปลตรงตัว เหมาะไว้ทดสอบ/ใช้ฟรี
2. "claude"  - ใช้ Claude API แปลแบบเกลาให้อ่านลื่นเป็นข่าวไทย คุณภาพดีกว่าแต่มีค่าใช้จ่าย
               ต้องตั้งค่า ANTHROPIC_API_KEY เป็น environment variable ก่อน

เลือกได้ผ่าน build_feed.py --backend google|claude
"""

import os
import json
import time

# ข้อความที่มักหลุดมาตอน Google Translate โดน rate limit / บล็อกชั่วคราว
# (ไลบรารีฟรีตัวนี้บางทีไม่ raise exception แต่คืนหน้า error กลับมาแทนคำแปลเฉยๆ)
_BAD_SIGNATURES = [
    "error 500", "server error", "that's all we know", "error 404",
    "<!doctype", "<html", "bad request", "too many requests",
    "we're sorry", "service unavailable",
]


def _looks_broken(text: str) -> bool:
    if not text or not text.strip():
        return True
    lowered = text.lower()
    return any(sig in lowered for sig in _BAD_SIGNATURES)


def translate_google(title_en: str, summary_en: str, max_retries: int = 3) -> dict:
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source="auto", target="th")

    def _safe_translate(text: str) -> str:
        if not text:
            return ""
        for attempt in range(max_retries):
            try:
                result = translator.translate(text)
            except Exception:
                result = None
            if result and not _looks_broken(result):
                return result
            time.sleep(1.5 * (attempt + 1))  # รอนานขึ้นเรื่อยๆ ก่อนลองใหม่
        # แปลไม่สำเร็จจริงๆ หลังลองครบทุกครั้ง — เก็บข้อความอังกฤษเดิมไว้ดีกว่าเอาข้อความ error มาโชว์
        return text

    title_th = _safe_translate(title_en)
    time.sleep(0.6)  # เว้นจังหวะระหว่างแปลหัวข้อกับสรุป กันยิงรัวเกินไป
    summary_th = _safe_translate(summary_en)
    return {"title_th": title_th, "summary_th": summary_th}


def translate_claude(title_en: str, summary_en: str, model: str = "claude-sonnet-4-6") -> dict:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ไม่พบ ANTHROPIC_API_KEY กรุณาตั้งค่า environment variable ก่อนใช้ backend='claude'\n"
            "เช่น: export ANTHROPIC_API_KEY=sk-ant-...\n"
            "หรือใช้ backend='google' แทนถ้าไม่ต้องการใช้ API key"
        )

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""แปลข่าวเทคโนโลยีต่อไปนี้เป็นภาษาไทยสำหรับเว็บข่าวเทค เขียนให้อ่านลื่นแบบข่าวไทย ไม่ใช่แปลตรงตัวคำต่อคำ
ใช้ข้อมูลเท่าที่ให้มาเท่านั้น ห้ามเติมข้อเท็จจริง ตัวเลข หรือรายละเอียดที่ไม่มีในต้นฉบับ

หัวข้อข่าว (อังกฤษ): {title_en}
สรุปเนื้อหา (อังกฤษ): {summary_en}

ตอบกลับเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายอื่น รูปแบบตรงนี้เป๊ะๆ:
{{"title_th": "หัวข้อภาษาไทย กระชับ ดึงดูด", "summary_th": "สรุปภาษาไทยจากเนื้อหาที่ให้มา เขียนให้อ่านลื่นเป็นธรรมชาติ ยาวเท่าที่เนื้อหาต้นฉบับมีพอจะสรุปได้"}}"""

    resp = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = resp.content[0].text.strip()

    # กันกรณีโมเดลห่อ JSON ด้วย ```json ... ```
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_text)
        return {"title_th": parsed.get("title_th", ""), "summary_th": parsed.get("summary_th", "")}
    except json.JSONDecodeError:
        return {"title_th": title_en, "summary_th": summary_en}


def translate_item(item: dict, backend: str = "google") -> dict:
    """แปล item เดียว คืนค่า item เดิมพร้อมฟิลด์ title_th / summary_th เพิ่มเข้ามา"""
    if backend == "claude":
        result = translate_claude(item["title_en"], item["summary_en"])
    else:
        result = translate_google(item["title_en"], item["summary_en"])

    item = dict(item)
    item["title_th"] = result["title_th"]
    item["summary_th"] = result["summary_th"]
    return item


def translate_title(title: str, backend: str = "google") -> str:
    """แปลเฉพาะหัวข้อสั้นๆ (ใช้กับหัวข้อวิดีโอรีวิวจาก YouTube)
    ถ้าเป็นภาษาไทยอยู่แล้วจะคืนค่าเดิมไปเลย ไม่แปลซ้ำ"""
    if not title:
        return ""
    if any("\u0e00" <= ch <= "\u0e7f" for ch in title):
        return title
    if backend == "claude":
        result = translate_claude(title, "")
        return result.get("title_th") or title
    result = translate_google(title, "")
    return result.get("title_th") or title


def translate_all(items: list, backend: str = "google", delay_seconds: float = 1.2) -> list:
    """แปลข่าวทั้งหมดทีละชิ้น พร้อมหน่วงเวลาให้พอกันโดน rate limit"""
    translated = []
    for i, item in enumerate(items, 1):
        print(f"  แปล [{i}/{len(items)}] {item['title_en'][:60]}...")
        try:
            translated.append(translate_item(item, backend=backend))
        except Exception as e:
            print(f"    [เตือน] แปลไม่สำเร็จ: {e} — ใช้ข้อความอังกฤษแทนไปก่อน")
            fallback = dict(item)
            fallback["title_th"] = item["title_en"]
            fallback["summary_th"] = item["summary_en"]
            translated.append(fallback)
        time.sleep(delay_seconds)
    return translated
