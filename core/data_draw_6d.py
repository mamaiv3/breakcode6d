"""
core/data_draw_6d.py
----------------------
Pengurusan data draw 6D (Sports Toto 6D).

Format fail data/draws6d.txt ikut format RASMI Sports Toto (CSV):
    DrawNo,DrawDate,1stPrizeNo
    040792,19920506,893424
    ...
- DrawNo    : nombor siri draw rasmi (cth "617226" = draw #6172, tahun '26)
- DrawDate  : YYYYMMDD
- 1stPrizeNo: nombor 1st Prize, 6 digit

Fail ni serasi TERUS dengan muat turun rasmi drpd rst.sportstoto.com.my/upload/6D.zip
-- untuk kemas kini, cukup panggil update_from_official_source() (atau guna
butang "Muat Turun Data Rasmi" dlm tab Data), ATAU muat turun & ganti fail
tu secara manual.
"""

import csv
import io
import os
import re
import zipfile

DRAW_FILE = "data/draws6d.txt"
OFFICIAL_6D_ZIP_URL = "https://rst.sportstoto.com.my/upload/6D.zip"
CSV_HEADER = "DrawNo,DrawDate,1stPrizeNo"


def load_draws(file_path: str = DRAW_FILE) -> list[dict]:
    """Baca semua draw dari fail CSV format rasmi (header 'DrawNo,DrawDate,1stPrizeNo').
    Pulangkan list of dict {"draw_no", "date" (YYYY-MM-DD), "number"} tersusun ikut tarikh menaik."""
    if not os.path.exists(file_path):
        return []

    draws = []
    with open(file_path, "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) != 3:
                continue
            draw_no, draw_date, prize = (x.strip() for x in row)
            if draw_no == "DrawNo":  # baris header
                continue
            if not re.match(r"^\d{8}$", draw_date) or not re.match(r"^\d{6}$", prize):
                continue
            date_str = f"{draw_date[0:4]}-{draw_date[4:6]}-{draw_date[6:8]}"
            draws.append({"draw_no": draw_no, "date": date_str, "number": prize})

    return sorted(draws, key=lambda d: d["date"])


def add_draw(date_str: str, number: str, draw_no: str = "", file_path: str = DRAW_FILE) -> tuple[bool, str]:
    """Tambah satu draw secara manual (format CSV rasmi). Menolak tarikh/nombor
    tak sah atau pendua. `draw_no` pilihan (boleh dibiar kosong utk entri manual)."""
    date_str = date_str.strip()
    number = number.strip()
    draw_no = draw_no.strip()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False, "❌ Format tarikh mesti YYYY-MM-DD."
    if not re.match(r"^\d{6}$", number):
        return False, "❌ Nombor mesti tepat 6 digit (000000–999999)."

    draws = load_draws(file_path)
    if any(d["date"] == date_str for d in draws):
        return False, f"⚠️ Draw untuk {date_str} sudah wujud."

    yyyymmdd = date_str.replace("-", "")
    file_exists = os.path.exists(file_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None

    with open(file_path, "a", newline="\n") as f:
        if not file_exists:
            f.write(CSV_HEADER + "\n")
        f.write(f"{draw_no},{yyyymmdd},{number}\n")
    return True, "✅ Draw berjaya ditambah."


def update_from_official_source(file_path: str = DRAW_FILE, url: str = OFFICIAL_6D_ZIP_URL) -> str:
    """
    Muat turun fail sejarah PENUH rasmi terus dari rst.sportstoto.com.my
    (zip berisi 1 fail .txt, format CSV 'DrawNo,DrawDate,1stPrizeNo'), dan
    GANTIKAN draws6d.txt sepenuhnya dgn versi rasmi terkini.

    Jauh lebih boleh dipercayai drpd scrape HTML halaman results_past.asp
    (tiada isu bot-detection sebab ini muat turun fail bulk terus), tapi
    tetap perlukan sambungan internet semasa aplikasi dijalankan.
    """
    try:
        import requests
    except ImportError:
        return "⚠️ Modul 'requests' tiada. Sila muat turun & ganti fail secara manual."

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        return f"⚠️ Gagal muat turun fail rasmi ({e}). Cuba lagi, atau muat turun & ganti fail secara manual."

    try:
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            txt_names = [n for n in zf.namelist() if n.lower().endswith(".txt")]
            if not txt_names:
                return "⚠️ Fail .txt tidak dijumpai dlm zip rasmi — struktur mungkin berubah."
            raw = zf.read(txt_names[0]).decode("utf-8", errors="ignore")
    except Exception as e:
        return f"⚠️ Gagal buka fail zip ({e})."

    lines = raw.replace("\r\n", "\n").strip().split("\n")
    if not lines or not lines[0].startswith("DrawNo"):
        return "⚠️ Format fail rasmi tidak dikenali (dijangka header 'DrawNo,DrawDate,1stPrizeNo') — struktur mungkin berubah."

    os.makedirs(os.path.dirname(file_path), exist_ok=True) if os.path.dirname(file_path) else None
    with open(file_path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    draws = load_draws(file_path)
    if not draws:
        return "⚠️ Fail dimuat turun tapi tiada draw sah diurai — sila semak fail secara manual."
    return f"✔️ Fail rasmi berjaya dimuat turun & disimpan — {len(draws)} draw ({draws[0]['date']} → {draws[-1]['date']})."
