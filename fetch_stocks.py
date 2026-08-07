"""
ดึงข้อมูลดัชนีหุ้นไทยและสหรัฐฯ ผ่าน Yahoo Finance (ไลบรารี yfinance)
ใช้ประกอบเว็บข่าวเทค อัปเดตพร้อมกับรอบดึงข่าวทุกครั้ง
"""

INDICES = [
    {"symbol": "^SET.BK", "name": "SET Index", "market": "TH"},
    {"symbol": "^GSPC", "name": "S&P 500", "market": "US"},
    {"symbol": "^DJI", "name": "Dow Jones", "market": "US"},
    {"symbol": "^IXIC", "name": "Nasdaq", "market": "US"},
]


def fetch_indices() -> list:
    """ดึงราคาปิดล่าสุดและเปอร์เซ็นต์เปลี่ยนแปลงของแต่ละดัชนี
    ถ้าดัชนีไหนดึงไม่สำเร็จจะข้ามไปเฉยๆ ไม่ทำให้ทั้งสคริปต์พัง"""
    import yfinance as yf

    results = []
    for idx in INDICES:
        try:
            ticker = yf.Ticker(idx["symbol"])
            hist = ticker.history(period="5d")
            if hist.empty or len(hist) < 2:
                print(f"  [เตือน] ไม่มีข้อมูลพอสำหรับ {idx['name']} ({idx['symbol']})")
                continue

            last_close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[-2])
            change = last_close - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0.0

            results.append({
                "symbol": idx["symbol"],
                "name": idx["name"],
                "market": idx["market"],
                "price": round(last_close, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            })
        except Exception as e:
            print(f"  [เตือน] ดึงข้อมูล {idx['name']} ({idx['symbol']}) ไม่สำเร็จ: {e}")

    return results


if __name__ == "__main__":
    for r in fetch_indices():
        arrow = "▲" if r["change"] >= 0 else "▼"
        print(f"{r['name']:12} {r['price']:>10}  {arrow} {r['change']:+.2f} ({r['change_pct']:+.2f}%)")
