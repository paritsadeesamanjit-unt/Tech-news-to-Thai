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


def translate_google(title_en: str, summary_en: str) -> dict:
    from deep_translator import GoogleTranslator

    translator = GoogleTranslator(source="auto", target="th")
    title_th = translator.translate(title_en) if title_en else ""
    summary_th = translator.translate(summary_en) if summary_en else ""
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

หัวข้อข่าว (อังกฤษ): {title_en}
สรุปเนื้อหา (อังกฤษ): {summary_en}

ตอบกลับเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายอื่น รูปแบบตรงนี้เป๊ะๆ:
{{"title_th": "หัวข้อภาษาไทย กระชับ ดึงดูด", "summary_th": "สรุปภาษาไทยแบบเต็ม 3-5 ประโยค อ่านลื่น ให้รายละเอียดครบใจความสำคัญของข่าว"}}"""

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


def translate_all(items: list, backend: str = "google", delay_seconds: float = 0.3) -> list:
    """แปลข่าวทั้งหมดทีละชิ้น พร้อมหน่วงเวลาเล็กน้อยกันโดน rate limit"""
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
