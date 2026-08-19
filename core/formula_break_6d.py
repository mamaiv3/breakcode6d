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


def backtest_rank_range(
    draws: list[dict],
    rank_range_candidates: list[tuple[int, int]],
    recent_n: int = DEFAULT_RECENT_N,
    score_recent_n: int | None = None,
    top_n: int = 10,
    rounds: int = 100,
    max_pool_size: int = 500_000,
) -> list[dict]:
    """
    Backtest EMPIRIKAL untuk cari "Julat Rank Digit" TERBAIK. Bagi SETIAP
    calon rank_range, base dijana SEMULA bagi setiap draw diuji guna
    HANYA draw SEBELUM draw tersebut ("as of" — tiada bocor maklumat
    masa depan, sama prinsip backtest dlm formula_break.py 4D).

    Bagi draw yang base-nya match PENUH (6/6 digit sebenar wujud dlm
    base — syarat perlu sebelum Top-N pun berpeluang tangkap nombor
    tu), semak sama ada nombor SEBENAR muncul dlm Top-N. Turut kira
    baseline rawak tulen (top_n ÷ saiz kolam) sbg perbandingan adil.

    PENTING utk 6D: berbanding 4D (4 posisi), keperluan "base penuh"
    jauh lebih ketat sebab 6 posisi kena betul SEKALI GUS — julat
    sempit (cth R1-R2) brtsy hampir MUSTAHIL diuji sebab peluang base
    penuh boleh serendah 0.006% (~1 kali dlm 15,000 draw). Kalau
    keputusan tunjuk "Base Penuh: 0", cuba julat lebih luas atau
    tambah bilangan draw diuji.

    Calon dgn kolam kombinasi > `max_pool_size` dilangkau (elak
    backtest jadi terlalu perlahan).
    """
    results = []
    for rank_range in rank_range_candidates:
        hits = 0
        base_full = 0
        baseline_probs = []
        score_recent_n_eff = score_recent_n or recent_n

        for i in range(1, rounds + 1):
            test_draw = draws[-i]
            past = draws[:-i]
            if len(past) < recent_n:
                break
            try:
                base = generate_break_base(past, recent_n, rank_range)
            except ValueError:
                continue

            pool_size = 1
            for p in base:
                pool_size *= len(p)
            if pool_size > max_pool_size:
                continue

            actual = f"{int(test_draw['number']):06d}"
            if not all(check_against_base(actual, base)):
                continue  # base tak cover penuh -- tak adil banding dgn baseline "given in pool"

            recent = past[-score_recent_n_eff:] if past else []
            counters = [Counter() for _ in range(NUM_POSITIONS)]
            for d in recent:
                num = f"{int(d['number']):06d}"
                for j in range(NUM_POSITIONS):
                    counters[j][num[j]] += 1

            scored = []
            for combo in itertools.product(*base):
                score = sum(counters[j][combo[j]] for j in range(NUM_POSITIONS))
                scored.append(("".join(combo), score))
            scored.sort(key=lambda x: x[1], reverse=True)
            top_nums = {num for num, _ in scored[:top_n]}

            base_full += 1
            baseline_probs.append(min(top_n, pool_size) / pool_size)
            if actual in top_nums:
                hits += 1

        if base_full == 0:
            results.append({
                "Julat": f"R{rank_range[0]}-R{rank_range[1]}",
                "rank_range": rank_range,
                "Base Penuh": 0,
                "Masuk Top-N": 0,
                "Recall (%)": None,
                "Baseline Rawak (%)": None,
                "Kelebihan vs Rawak": None,
            })
            continue

        recall_rate = round(hits / base_full * 100, 2)
        baseline_rate = round(sum(baseline_probs) / len(baseline_probs) * 100, 2)
        results.append({
            "Julat": f"R{rank_range[0]}-R{rank_range[1]}",
            "rank_range": rank_range,
            "Base Penuh": base_full,
            "Masuk Top-N": hits,
            "Recall (%)": recall_rate,
            "Baseline Rawak (%)": baseline_rate,
            "Kelebihan vs Rawak": round(recall_rate - baseline_rate, 2),
        })

    results.sort(key=lambda r: (r["Kelebihan vs Rawak"] is not None, r["Kelebihan vs Rawak"]), reverse=True)
    return results
