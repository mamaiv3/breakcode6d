"""
app_6d.py — Breakcode6D (Sports Toto 6D, versi ringkas)
-----------------------------------------------------------
2 tab sahaja, konsep sama macam Breakcode4D (app.py) tapi digeneralisasikan
drpd 4 posisi kepada 6 posisi, dan dipermudahkan:
  1. 📊 Dashboard — base + prediksi Top 10
  2. 📋 Data      — data draw (tambah manual / scrape / senarai)

Sumber data: Sports Toto Malaysia (lesen rasmi) — results_past.asp.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from core.data_draw_6d import DRAW_FILE, add_draw, load_draws, update_from_official_source
from core.formula_break_6d import DEFAULT_RANK_RANGE, DEFAULT_RECENT_N, backtest_rank_range, predict_top10

st.set_page_config(page_title="Breakcode6D — Toto 6D", page_icon="🎯", layout="wide")


def load_css() -> None:
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def section_title(icon: str, text: str, subtitle: str = "") -> None:
    sub = f'<div class="bc4d-section-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="bc4d-section-title"><span class="icon">{icon}</span>'
        f'<span class="text">{text}</span></div>{sub}',
        unsafe_allow_html=True,
    )


def divider() -> None:
    st.markdown('<hr class="bc4d-divider" />', unsafe_allow_html=True)


load_css()
st.title("🎯 Breakcode6D — Toto 6D")
st.caption(
    "Alat analisis statistik/corak sejarah SAHAJA — bukan jaminan keputusan. "
    "Toto 6D permainan nasib; mainlah secara bertanggungjawab."
)

draws = load_draws()

tab_dash, tab_backtest, tab_data = st.tabs(["📊 Dashboard", "🔬 Backtest", "📋 Data"])

# =================================================================== DASHBOARD ===
with tab_dash:
    if len(draws) < 10:
        st.warning("⚠️ Data draw terlalu sedikit (<10). Tambah draw di tab **📋 Data** dahulu.")
    else:
        last_draw = draws[-1]
        m1, m2 = st.columns(2)
        m1.metric("Jumlah Draw Direkod", len(draws))
        m2.metric("Draw Terkini", f"{last_draw['date']} — {last_draw['number']} (Draw {last_draw['draw_no']})")

        divider()
        section_title("🔮", "Tetapan Base", "Digit paling kerap setiap posisi (P1–P6).")
        bc1, bc2 = st.columns(2)
        recent_n = bc1.slider(
            "Jumlah draw terkini:", 10, len(draws), min(DEFAULT_RECENT_N, len(draws)), 5, key="recent_n_6d",
        )
        rank_range = bc2.select_slider(
            "Julat rank digit:", options=list(range(1, 11)), value=DEFAULT_RANK_RANGE, key="rank_range_6d",
        )

        try:
            base, top_results = predict_top10(draws, recent_n=recent_n, rank_range=rank_range, top_n=10)
        except ValueError as e:
            st.error(str(e))
        else:
            pool_size = 1
            for p in base:
                pool_size *= len(p)
            if pool_size > 100_000:
                st.caption(f"ℹ️ Kolam kombinasi agak besar ({pool_size:,}) — mungkin ambil beberapa saat.")

            st.markdown("**🔢 Base (boleh salin terus):**")
            st.code("\n".join(" ".join(p) for p in base), language="text")

            divider()
            section_title(
                "🏆", "Top 10 Prediksi",
                f"Disusun ikut kekerapan digit gabungan P1–P6 dlm {recent_n} draw terkini.",
            )
            st.dataframe(pd.DataFrame(top_results), use_container_width=True, hide_index=True)

            lot = st.text_input("Saiz Lot:", value="0.10", key="lot_6d")

            top_text = "\n".join(r["Nombor"] for r in top_results)
            st.code(top_text, language="text")
            st.download_button(
                "💾 Muat Turun Top 10", data=top_text.encode(),
                file_name="toto6d_top10.txt", mime="text/plain", key="dl_top10_6d",
            )

            st.markdown(f"**📋 Top 10 (format lot — `NNNNNN#{lot}`):**")
            top_lot_text = "\n".join(f"{r['Nombor']}#{lot}" for r in top_results)
            st.code(top_lot_text, language="text")
            st.download_button(
                "💾 Muat Turun Top 10 (format lot)", data=top_lot_text.encode(),
                file_name="toto6d_top10_lot.txt", mime="text/plain", key="dl_top10_lot_6d",
            )

# =================================================================== BACKTEST ===
with tab_backtest:
    section_title(
        "🔬", "Backtest — Cari Julat Rank Terbaik",
        "Uji beberapa \"Julat Rank Digit\" terhadap draw lepas (\"as of\" — tiada bocor maklumat masa depan).",
    )

    if len(draws) < 50:
        st.warning("⚠️ Data draw terlalu sedikit (<50) untuk backtest bermakna.")
    else:
        st.info(
            "⚠️ **Had penting untuk 6D:** kolam kombinasi (cth R1-R8 = 262,144) jauh lebih besar drpd "
            "Top-N (10) — baseline rawak sendiri boleh serendah 0.004%. Ini bermakna \"Masuk Top-N\" "
            "hampir mustahil diperhatikan dlm backtest walaupun dgn ratusan sampel base-penuh — bukan "
            "salah julat atau bug, tapi had matematik skala 6D. Anggap lajur **\"Base Penuh\"** (peratus "
            "julat berjaya cover digit sebenar) sbg penunjuk lebih berguna drpd \"Kelebihan vs Rawak\" "
            "buat masa ini."
        )
        bt1, bt2 = st.columns(2)
        bt_recent_n = bt1.slider(
            "N (draw terkini utk base):", 10, len(draws), min(DEFAULT_RECENT_N, len(draws)), 5, key="bt_recent_n_6d",
        )
        bt_top_n = bt2.selectbox(
            "Top-N untuk diuji:", [5, 10, 20, 30, 50], index=1, key="bt_top_n_6d",
        )

        julat_options = {f"R1-R{k}": (1, k) for k in range(2, 9)}
        chosen_julat = st.multiselect(
            "Julat rank untuk dibandingkan:", list(julat_options.keys()),
            default=["R1-R5", "R1-R6", "R1-R7", "R1-R8"], key="bt_julat_6d",
        )
        st.caption(
            "ℹ️ Julat sempit (R1-R2/R1-R3) hampir mustahil diuji utk 6D — 6 posisi kena "
            "betul SEKALI GUS, jadi peluang \"base penuh\" jadi sangat rendah. Julat lebar "
            "(R1-R5 ke atas) lebih realistik utk backtest bermakna."
        )

        max_rounds = max(50, min(3000, len(draws) - bt_recent_n))
        bt_rounds = st.slider(
            "Bilangan draw lepas untuk diuji:", 50, max_rounds, min(1000, max_rounds), 50, key="bt_rounds_6d",
        )

        if st.button("🚀 Jalankan Backtest", key="bt_run_6d"):
            if len(chosen_julat) < 2:
                st.warning("⚠️ Pilih sekurang-kurangnya 2 julat untuk dibandingkan.")
            else:
                candidates = [julat_options[k] for k in chosen_julat]
                with st.spinner("Menguji setiap julat terhadap draw lepas..."):
                    bt_results = backtest_rank_range(
                        draws, rank_range_candidates=candidates,
                        recent_n=bt_recent_n, top_n=bt_top_n, rounds=bt_rounds,
                    )
                if not bt_results:
                    st.warning("⚠️ Tiada julat berjaya diuji — cuba kurangkan N atau bilangan draw diuji.")
                else:
                    zero_julat = [r["Julat"] for r in bt_results if r["Base Penuh"] == 0]
                    if zero_julat:
                        st.caption(
                            f"⚠️ {', '.join(zero_julat)} — 0 kali base penuh dlm ujian ni (julat terlalu "
                            "sempit utk saiz sampel ni). Naikkan bilangan draw diuji atau lebarkan julat."
                        )
                    valid_results = [r for r in bt_results if r["Base Penuh"] > 0]
                    if not valid_results:
                        st.warning("⚠️ Semua julat dipilih tak pernah base penuh — lebarkan julat atau naikkan bilangan draw diuji.")
                    else:
                        sample_n = valid_results[0]["Base Penuh"]
                        if sample_n < 30:
                            st.caption(
                                f"⚠️ Cuma {sample_n} sampel (base penuh) utk julat terbaik — naikkan "
                                "\"Bilangan draw lepas untuk diuji\" utk keputusan yang lebih boleh dipercayai."
                            )
                        st.dataframe(
                            pd.DataFrame(bt_results).drop(columns=["rank_range"]),
                            use_container_width=True, hide_index=True,
                        )
                        winner = valid_results[0]
                        if winner["Kelebihan vs Rawak"] > 0:
                            st.success(
                                f"🏆 **{winner['Julat']}** terdepan (+{winner['Kelebihan vs Rawak']} drpd rawak) — "
                                "pergi ke tab Dashboard & tetapkan \"Julat rank digit\" ke nilai ni."
                            )
                        else:
                            st.caption(
                                "⚠️ Tiada julat pun mengatasi baseline rawak dlm ujian ini — draw 6D nampak "
                                "konsisten dgn rawak tulen buat masa ini."
                            )

# =================================================================== DATA ===
with tab_data:
    section_title("📋", "Data Draw 6D", "Sumber data mentah untuk Dashboard.")

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**➕ Tambah Draw Manual**")
        new_date = st.text_input("Tarikh (YYYY-MM-DD):", key="add_date_6d")
        new_number = st.text_input("Nombor (6 digit):", key="add_number_6d")
        if st.button("Tambah", key="add_btn_6d"):
            ok, msg = add_draw(new_date, new_number)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with d2:
        st.markdown("**📥 Kemas Kini Data Rasmi**")
        st.caption(
            "Muat turun fail sejarah PENUH terus dari rst.sportstoto.com.my/upload/6D.zip "
            "(perlu sambungan internet) — menggantikan draws6d.txt dgn versi rasmi terkini."
        )
        if st.button("⬇️ Muat Turun Data Rasmi Terkini", key="update_btn_6d"):
            with st.spinner("Memuat turun & mengurai fail rasmi..."):
                msg = update_from_official_source()
            st.info(msg)
            st.rerun()

    divider()
    col_list, col_dl = st.columns([3, 1])
    col_list.markdown(f"**📜 Senarai Draw** (jumlah: {len(draws)})")
    draws_txt_path = Path(DRAW_FILE)
    if draws_txt_path.exists():
        col_dl.download_button(
            "💾 draws6d.txt", data=draws_txt_path.read_bytes(),
            file_name="draws6d.txt", mime="text/plain", key="dl_draws6d_txt",
        )
    df_draws = pd.DataFrame(draws[::-1])
    st.dataframe(df_draws, use_container_width=True, height=420, hide_index=True)
