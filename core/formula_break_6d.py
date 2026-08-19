"""
core/formula_break_6d.py
---------------------------
Formula Break untuk Sports Toto 6D — konsep SAMA seperti core/formula_break.py
(4D), digeneralisasikan drpd 4 posisi kepada 6 posisi (P1–P6).

Alat analisis statistik/corak sejarah SAHAJA — bukan jaminan keputusan.
Toto 6D (macam semua permainan loteri berlesen) adalah draw rawak tulen.
"""

import itertools
from collections import Counter

NUM_POSITIONS = 6
DEFAULT_RECENT_N = 100
DEFAULT_RANK_RANGE = (1, 3)


def generate_break_base(
    draws: list[dict],
    recent_n: int = DEFAULT_RECENT_N,
    rank_range: tuple[int, int] = DEFAULT_RANK_RANGE,
) -> list[list[str]]:
    """
    Jana base 6-posisi drpd `recent_n` draw terkini: bagi setiap posisi
    (P1–P6), kira kekerapan setiap digit (0–9), susun ikut rank
    (1 = paling kerap), ambil digit dlm julat rank_range
    (cth (1,3) = 3 digit paling kerap sahaja bagi posisi tsb).
    """
    recent = draws[-recent_n:] if draws else []
    if not recent:
        raise ValueError("Tiada draw untuk dijana base.")

    rank_start, rank_end = rank_range
    if not (1 <= rank_start <= rank_end <= 10):
        raise ValueError("Julat rank mesti dlm 1–10 dan rank_start ≤ rank_end.")

    base = []
    for i in range(NUM_POSITIONS):
        counter = Counter()
        for d in recent:
            num = f"{int(d['number']):06d}"
            counter[num[i]] += 1
        for digit in "0123456789":
            counter.setdefault(digit, 0)
        ranked = [digit for digit, _ in counter.most_common(10)]
        selected = ranked[rank_start - 1:rank_end]
        if not selected:
            raise ValueError(f"Julat rank tidak sah untuk posisi P{i + 1}.")
        base.append(selected)
    return base


def check_against_base(number: str, base: list[list[str]]) -> list[bool]:
    """Semak digit mana (P1–P6) drpd `number` yang wujud dlm base."""
    num = f"{int(number):06d}"
    return [num[i] in base[i] for i in range(NUM_POSITIONS)]


def predict_top10(
    draws: list[dict],
    recent_n: int = DEFAULT_RECENT_N,
    rank_range: tuple[int, int] = DEFAULT_RANK_RANGE,
    score_recent_n: int | None = None,
    top_n: int = 10,
) -> tuple[list[list[str]], list[dict]]:
    """
    Jana base (lihat generate_break_base), bina SEMUA kombinasi yg
    mungkin drpd base tu (cartesian product 6 posisi), skor setiap
    kombinasi ikut JUMLAH kekerapan digit gabungan 6 posisi (gaya sama
    macam skor "sum" asal dlm Wheelpick 4D), pulangkan `top_n`
    kombinasi teratas.

    PENTING: ni sekadar analisis corak sejarah — draw sebenar rawak
    tulen, jadi TIADA jaminan mana-mana kombinasi dlm Top-N akan
    menang.
    """
    base = generate_break_base(draws, recent_n, rank_range)
    score_recent_n = score_recent_n or recent_n
    recent = draws[-score_recent_n:] if draws else []

    counters = [Counter() for _ in range(NUM_POSITIONS)]
    for d in recent:
        num = f"{int(d['number']):06d}"
        for i in range(NUM_POSITIONS):
            counters[i][num[i]] += 1

    scored = []
    for combo in itertools.product(*base):
        score = sum(counters[i][combo[i]] for i in range(NUM_POSITIONS))
        scored.append(("".join(combo), score))
    scored.sort(key=lambda x: x[1], reverse=True)

    top_results = [
        {"Rank": i + 1, "Nombor": num, "Skor": score}
        for i, (num, score) in enumerate(scored[:top_n])
    ]
    return base, top_results
