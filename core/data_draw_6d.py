"""
core/data_draw_6d.py
----------------------
Pengurusan data draw 6D (Sports Toto 6D): baca, tambah secara manual, dan
cuba kemas kini keputusan terkini secara automatik dari sportstoto.com.my.

Ini SATU-SATUNYA sumber data mentah yang digunakan oleh Dashboard 6D —
dikekalkan berasingan drpd data_draw.py (4D) supaya senang diselenggara.

NOTA: results_statistics_6d.asp (laman "Statistics") TIDAK sesuai sbg
sumber — ia senarai besar nombor pernah keluar SUSUN IKUT NOMBOR, bukan
ikut tarikh. Scraper ni guna results_past.asp sebaliknya, yg ada tarikh
draw sebenar bagi setiap keputusan.
"""

import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DRAW_FILE = "data/draws6d.txt"


def load_draws(file_path: str = DRAW_FILE) -> list[dict]:
    """Baca semua draw dari fail teks (format: 'YYYY-MM-DD NNNNNN' per baris)."""
    if not os.path.exists(file_path):
        return []
    draws = []
    with open(file_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2 and re.match(r"^\d{6}$", parts[1]):
                draws.append({"date": parts[0], "number": parts[1]})
    return sorted(draws, key=lambda d: d["date"])


def add_draw(date_str: str, number: str, file_path: str = DRAW_FILE) -> tuple[bool, str]:
    """Tambah satu draw secara manual. Menolak tarikh/nombor tak sah atau pendua."""
    date_str = date_str.strip()
    number = number.strip()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False, "❌ Format tarikh mesti YYYY-MM-DD."
    if not re.match(r"^\d{6}$", number):
        return False, "❌ Nombor mesti tepat 6 digit (000000–999999)."

    draws = load_draws(file_path)
    if any(d["date"] == date_str for d in draws):
        return False, f"⚠️ Draw untuk {date_str} sudah wujud."

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "a") as f:
        f.write(f"{date_str} {number}\n")
    return True, "✅ Draw berjaya ditambah."


def _parse_6d_draws_from_text(text: str) -> list[tuple[str, str]]:
    """
    Urai teks rata (BeautifulSoup.get_text()) drpd results_past.asp,
    pulangkan senarai (tarikh YYYY-MM-DD, nombor 6-digit).

    Pendekatan: cari setiap penanda "Draw Date : D/M/YYYY", ambil blok
    teks sehingga penanda tarikh SETERUSNYA, dalam blok tu cari corak
    "TOTO 6D ... 1st Prize ... NNNNNN". Cara ni tahan sikit drpd
    perubahan kecil struktur HTML sebab tak bergantung pd nama
    tag/class tertentu — tapi TETAP boleh rosak kalau susun-atur laman
    berubah besar. Kalau scrape gagal, tambah draw secara manual.
    """
    results = []
    date_matches = list(re.finditer(r"Draw Date\s*:\s*(\d{1,2})/(\d{1,2})/(\d{4})", text))
    for idx, dm in enumerate(date_matches):
        day, month, year = dm.groups()
        start = dm.end()
        end = date_matches[idx + 1].start() if idx + 1 < len(date_matches) else len(text)
        block = text[start:end]
        prize_match = re.search(r"TOTO\s*6D.*?1st\s*Prize\s*(\d{6})", block, re.S)
        if prize_match:
            try:
                date_str = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue
            results.append((date_str, prize_match.group(1)))
    return results


def scrape_latest(file_path: str = DRAW_FILE, months_back: int = 3) -> str:
    """
    Cuba tarik keputusan TOTO 6D dari sportstoto.com.my/results_past.asp,
    `months_back` bulan ke belakang drpd hari ini. Perlukan sambungan
    internet semasa aplikasi ini dijalankan (streamlit run).

    NOTA: laman ni kadang menyekat trafik automatik (bot detection).
    Kalau gagal berulang kali, tambah draw secara manual di bawah.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return "⚠️ Modul 'requests' / 'beautifulsoup4' tiada. Sila tambah draw secara manual."

    draws = load_draws(file_path)
    existing = {d["date"] for d in draws}

    tz = ZoneInfo("Asia/Kuala_Lumpur")
    cursor = datetime.now(tz).date()

    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }

    added = []
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    blocked = False

    with open(file_path, "a") as f:
        for _ in range(max(1, months_back)):
            url = (
                "https://www.sportstoto.com.my/results_past.asp"
                f"?date={cursor.month}/{cursor.day}/{cursor.year}"
            )
            try:
                resp = session.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    blocked = True
                    break
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(separator=" ")
            except Exception:
                blocked = True
                break

            for date_str, number in _parse_6d_draws_from_text(text):
                if date_str in existing:
                    continue
                f.write(f"{date_str} {number}\n")
                existing.add(date_str)
                added.append(date_str)

            # bulan sebelumnya
            first_of_month = cursor.replace(day=1)
            cursor = first_of_month - timedelta(days=1)

    if added:
        added.sort()
        return f"✔️ {len(added)} draw baru ditambah ({added[0]} → {added[-1]})."
    if blocked:
        return "⚠️ Laman menyekat capaian automatik (bot detection) atau tiada sambungan — sila tambah manual."
    return "ℹ️ Tiada draw baru ditemui buat masa ini."
