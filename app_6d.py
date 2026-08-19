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

from core.data_draw_6d import DRAW_FILE, add_draw, load_draws, scrape_latest
from core.formula_break_6d import DEFAULT_RANK_RANGE, DEFAULT_RECENT_N, predict_top10

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

tab_dash, tab_data = st.tabs(["📊 Dashboard", "📋 Data"])

# =================================================================== DASHBOARD ===
with tab_dash:
    if len(draws) < 10:
        st.warning("⚠️ Data draw terlalu sedikit (<10). Tambah draw di tab **📋 Data** dahulu.")
    else:
        last_draw = draws[-1]
        m1, m2 = st.columns(2)
        m1.metric("Jumlah Draw Direkod", len(draws))
        m2.metric("Draw Terkini", f"{last_draw['date']} — {last_draw['number']}")

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

            top_text = "\n".join(r["Nombor"] for r in top_results)
            st.code(top_text, language="text")
            st.download_button(
                "💾 Muat Turun Top 10", data=top_text.encode(),
                file_name="toto6d_top10.txt", mime="text/plain", key="dl_top10_6d",
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
        st.markdown("**📥 Kemas Kini Automatik**")
        st.caption(
            "Cuba tarik keputusan TOTO 6D dari sportstoto.com.my (perlu sambungan "
            "internet; laman kadang menyekat capaian automatik — kalau gagal, "
            "tambah manual di sebelah)."
        )
        months_back = st.slider("Bilangan bulan ke belakang:", 1, 12, 3, key="scrape_months_6d")
        if st.button("Kemas Kini Draw", key="scrape_btn_6d"):
            with st.spinner("Menarik data..."):
                msg = scrape_latest(months_back=months_back)
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
