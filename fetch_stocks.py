"""
ดึงราคาหุ้นกลุ่มเทคโนโลยี (สหรัฐฯ + ไทย) ผ่าน Yahoo Finance (ไลบรารี yfinance)
ใช้ประกอบเว็บข่าวเทค อัปเดตพร้อมกับรอบดึงข่าวทุกครั้ง

หมายเหตุ: SpaceX (SPCX) ยังไม่ได้เข้าตลาดหุ้น (บริษัทเอกชน) จึงใช้ AAPL แทนในลิสต์นี้
"""

STOCKS = [
    {"symbol": "NVDA", "name": "Nvidia", "market": "US"},
    {"symbol": "TSLA", "name": "Tesla", "market": "US"},
    {"symbol": "GOOGL", "name": "Alphabet", "market": "US"},
    {"symbol": "MSFT", "name": "Microsoft", "market": "US"},
    {"symbol": "AAPL", "name": "Apple", "market": "US"},
    {"symbol": "AMZN", "name": "Amazon", "market": "US"},
    {"symbol": "META", "name": "Meta", "market": "US"},
    {"symbol": "DELTA.BK", "name": "Delta Electronics", "market": "TH"},
]


def fetch_indices() -> list:
    """ดึงราคาปิดล่าสุดและเปอร์เซ็นต์เปลี่ยนแปลงของหุ้นแต่ละตัวใน STOCKS
    ถ้าตัวไหนดึงไม่สำเร็จจะข้ามไปเฉยๆ ไม่ทำให้ทั้งสคริปต์พัง
    (ชื่อฟังก์ชันคงเดิมว่า fetch_indices เพื่อให้ build_feed.py เรียกใช้ได้โดยไม่ต้องแก้)"""
    import yfinance as yf

    results = []
    for stock in STOCKS:
        try:
            ticker = yf.Ticker(stock["symbol"])
            hist = ticker.history(period="5d")
            if hist.empty or len(hist) < 2:
                print(f"  [เตือน] ไม่มีข้อมูลพอสำหรับ {stock['name']} ({stock['symbol']})")
                continue

            last_close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            change = last_close - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0.0

            results.append({
                "symbol": stock["symbol"],
                "name": stock["name"],
                "market": stock["market"],
                "price": round(last_close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            })
        except Exception as e:
            print(f"  [เตือน] ดึงข้อมูล {stock['name']} ({stock['symbol']}) ไม่สำเร็จ: {e}")

    return results


if __name__ == "__main__":
    for r in fetch_indices():
        arrow = "▲" if r["change"] >= 0 else "▼"
        print(f"{r['name']:20} {r['price']:>10}  {arrow} {r['change']:+.2f} ({r['change_pct']:+.2f}%)")
