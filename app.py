"""PasarCerdas - Indonesia Food Price Intelligence (entry point Streamlit)."""
import streamlit as st
from src.config import ASSETS_DIR
from src.ui import inject_css
from pages import dashboard, harga_pangan, prediksi, perbandingan, analisis_tren, evaluasi_model

st.set_page_config(page_title="PasarCerdas - Cek & Prediksi Harga Pangan", page_icon=":material/eco:",
                   layout="wide", initial_sidebar_state="collapsed")
inject_css()

PAGES = [
    (st.Page(dashboard.render, title="Beranda", url_path="dashboard", default=True), "Beranda"),
    (st.Page(harga_pangan.render, title="Cek Harga", url_path="harga"), "Cek Harga"),
    (st.Page(prediksi.render, title="Prediksi", url_path="prediksi"), "Prediksi"),
    (st.Page(perbandingan.render, title="Bandingkan Wilayah", url_path="wilayah"), "Bandingkan Wilayah"),
    (st.Page(analisis_tren.render, title="Tren", url_path="tren"), "Tren"),
    (st.Page(evaluasi_model.render, title="Seberapa Akurat?", url_path="evaluasi"), "Seberapa Akurat?"),
]
nav = st.navigation([p for p, _ in PAGES], position="hidden")   # navigasi bawaan disembunyikan
LOGO = str(ASSETS_DIR / "logo.svg")

# Laptop/tablet besar: navbar horizontal di atas (CSS menyembunyikannya di layar kecil)
with st.container(key="nav-desktop"):
    cols = st.columns([2.4, 1.0, 1.2, 1.1, 2.1, 0.9, 1.9], vertical_alignment="center")
    cols[0].image(LOGO, width=200)
    for col, (pg, label) in zip(cols[1:], PAGES):
        col.page_link(pg, label=label)

# HP / layar kecil: logo + tombol garis tiga yang membuka menu
with st.container(key="nav-mobile"):
    m = st.columns([3, 1], vertical_alignment="center")
    m[0].image(LOGO, width=170)
    with m[1].popover(":material/menu:"):
        for pg, label in PAGES:
            st.page_link(pg, label=label)

nav.run()
st.markdown("<div class='pc-footer'>PasarCerdas · Indonesia Food Price Intelligence · Sumber data: World Bank "
            "Real-Time Food Prices (Indonesia). Harga dalam Rupiah per kg. Prediksi bersifat indikatif, bukan jaminan.</div>",
            unsafe_allow_html=True)
