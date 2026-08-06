# สัญญาณ — เว็บข่าวเทคต่างประเทศแปลไทย

เว็บไซต์สถิต (static site) ธรรมดา ไม่ต้องมีเซิร์ฟเวอร์แยก — hosting ฟรีด้วย GitHub Pages
ข่าวอัปเดตอัตโนมัติด้วย GitHub Actions ที่รันทุกไม่กี่ชั่วโมง

## โครงสร้างไฟล์
- `index.html` — หน้าเว็บ อ่านข่าวจาก `news.json` ในโฟลเดอร์เดียวกัน
- `news.json` — ข่าวที่แปลแล้ว (มีข้อมูลตัวอย่างให้ก่อน จะถูกแทนที่ด้วยข่าวจริงตอนรันจริง)
- `fetch_news.py` — ดึงข่าวจาก RSS feed (TechCrunch, The Verge, Ars Technica, Wired, MIT Tech Review, Engadget, IEEE Spectrum)
- `translate.py` — แปลภาษา เลือกได้ Google Translate (ฟรี) หรือ Claude API (คุณภาพดีกว่า)
- `build_feed.py` — สคริปต์หลัก รวมขั้นตอนดึง+แปล แล้วเซฟเป็น `news.json`
- `.github/workflows/update-news.yml` — ตั้งให้ GitHub รันดึงข่าวอัตโนมัติทุก 3 ชั่วโมง

## ขั้นตอน Deploy (ทำครั้งเดียว)

### 1. สร้าง repo บน GitHub แล้ว push โค้ดขึ้นไป
```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

### 2. เปิดสิทธิ์ให้ GitHub Actions เขียนไฟล์กลับ repo ได้
ไปที่ repo → **Settings** → **Actions** → **General** → เลื่อนลงหา **Workflow permissions**
→ เลือก **Read and write permissions** → กด Save
(ถ้าไม่ทำขั้นนี้ workflow จะ push `news.json` กลับเข้า repo ไม่ได้)

### 3. เปิดใช้งาน GitHub Pages
ไปที่ repo → **Settings** → **Pages** → ในหัวข้อ **Build and deployment**:
- Source: **Deploy from a branch**
- Branch: **main** / โฟลเดอร์ **/ (root)**
- กด **Save**

รอสัก 1-2 นาที เว็บจะขึ้นออนไลน์ที่ `https://<username>.github.io/<repo-name>/`

### 4. ปล่อยให้ระบบอัปเดตข่าวเอง
Workflow ใน `.github/workflows/update-news.yml` จะรันดึง+แปลข่าวทุก 3 ชั่วโมง แล้ว commit
`news.json` ใหม่กลับเข้า repo อัตโนมัติ — พอ commit เข้า `main` เว็บบน GitHub Pages จะอัปเดตตาม
ภายในไม่กี่นาที ไม่ต้องทำอะไรเพิ่ม

อยากรันทันทีโดยไม่ต้องรอ: ไปที่แท็บ **Actions** บน repo → เลือก workflow "Update Thai Tech News"
→ กด **Run workflow**

## ถ้าอยากใช้ Claude API แทน Google Translate
คุณภาพการแปลจะลื่นกว่าแบบตรงตัว แต่มีค่าใช้จ่ายตาม API usage
1. repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   ตั้งชื่อ `ANTHROPIC_API_KEY` ใส่ API key ของตัวเอง
2. แก้ `.github/workflows/update-news.yml`: เอาคอมเมนต์ 3 บรรทัดที่มี `--backend claude` และ
   `env:` ออก แล้วคอมเมนต์บรรทัด `--backend google` แทน

## รันดูบนเครื่องตัวเองก่อน push ก็ได้
```bash
pip install -r requirements.txt
python build_feed.py            # ดึง+แปลข่าวจริง เขียนทับ news.json
python -m http.server 8000      # เปิดเซิร์ฟเวอร์เล็กๆ ดูผลก่อน deploy
```
แล้วเปิด http://localhost:8000 (ต้องรันเซิร์ฟเวอร์ก่อน เพราะเบราว์เซอร์บล็อก fetch() บนไฟล์ที่
เปิดตรงๆ แบบ file://)

## ปรับแต่งเพิ่มเติม
- เพิ่ม/ลบสำนักข่าว: แก้ list `FEEDS` ใน `fetch_news.py`
- ปรับคำกรองข่าวที่เกี่ยวข้อง: แก้ `KEYWORDS` ใน `fetch_news.py`
- ปิดการกรองคำสำคัญ: `python build_feed.py --no-filter`
- ปรับความถี่การอัปเดต: แก้บรรทัด `cron:` ใน `.github/workflows/update-news.yml`
  (เวลาที่ใส่เป็น UTC — เวลาไทย = UTC+7)
