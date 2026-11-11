"""PasarCerdas - Indonesia Food Price Intelligence (entry point Streamlit)."""
import streamlit as st
from src.config import ASSETS_DIR
from src.ui import inject_css
from pages import dashboard, harga_pangan, prediksi, perbandingan, analisis_tren, evaluasi_model

st.set_page_config(page_title="PasarCerdas - Cek & Prediksi Harga Pangan", page_icon="🌾", layout="wide",
                   initial_sidebar_state="collapsed")
inject_css()
PAGES = [
    (st.Page(dashboard.render, title="Beranda", icon="🏠", url_path="dashboard", default=True), "Beranda", "🏠"),
    (st.Page(harga_pangan.render, title="Cek Harga", icon="🏷️", url_path="harga"), "Cek Harga", "🏷️"),
    (st.Page(prediksi.render, title="Prediksi", icon="🔮", url_path="prediksi"), "Prediksi", "🔮"),
    (st.Page(perbandingan.render, title="Bandingkan Wilayah", icon="🗺️", url_path="wilayah"), "Bandingkan Wilayah", "🗺️"),
    (st.Page(analisis_tren.render, title="Tren", icon="📈", url_path="tren"), "Tren", "📈"),
    (st.Page(evaluasi_model.render, title="Seberapa Akurat?", icon="🧪", url_path="evaluasi"), "Seberapa Akurat?", "🧪"),
]
nav = st.navigation([p for p, _, _ in PAGES], position="hidden")   # navigasi bawaan disembunyikan

# Navbar atas buatan sendiri (selalu tampil, tidak bergantung pada komponen internal Streamlit)
with st.container(key="topnav"):
    cols = st.columns([2.3] + [1.2] * len(PAGES), vertical_alignment="center")
    cols[0].image(str(ASSETS_DIR / "logo.svg"), width=210)
    for col, (pg, label, icon) in zip(cols[1:], PAGES):
        col.page_link(pg, label=label, icon=icon)
nav.run()
st.markdown("<div class='pc-footer'>PasarCerdas · Indonesia Food Price Intelligence · Sumber data: World Bank "
            "Real-Time Food Prices (Indonesia). Harga dalam Rupiah per kg. Prediksi bersifat indikatif, bukan jaminan.</div>",
            unsafe_allow_html=True)
