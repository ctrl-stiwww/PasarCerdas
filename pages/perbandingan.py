import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import COMMODITIES
from src.ui import get_obs, last_obs_month, page_header, idr, fmt_month, style_fig, show


def render():
    page_header("Bandingkan Wilayah", "Di mana harga paling murah dan paling mahal? Bandingkan provinsi, kota, dan pasar pada bulan yang sama.", "🗺️")
    obs, last = get_obs(), last_obs_month()
    months = sorted(obs.date.unique(), reverse=True)
    months = [pd.Timestamp(m) for m in months if (obs[obs.date == m].geo_id.nunique() >= 100)]
    c = st.columns(3)
    com = c[0].selectbox("Komoditas", list(COMMODITIES.values()), key="pb_com")
    mon = c[1].selectbox("Bulan", months, format_func=fmt_month, key="pb_mon")
    n = c[2].slider("Jumlah item ditampilkan", 5, 20, 10, key="pb_n")
    d = obs[(obs.commodity_name == com) & (obs.date == mon)]
    if d.empty:
        st.warning("Tidak ada data untuk pilihan ini."); return
    st.caption(f"{len(d)} pasar memiliki harga observasi untuk {com} pada {fmt_month(mon)}. "
               "Semua perbandingan memakai komoditas dan bulan yang sama.")
    t1, t2, t3, t4 = st.tabs(["Provinsi", "Kabupaten/Kota", "Pasar", "Peta"])
    with t1:
        g = d.groupby("adm1_name").agg(harga=("price_clean", "mean"), pasar=("geo_id", "nunique")).reset_index().sort_values("harga")
        fig = px.bar(g, x="harga", y="adm1_name", orientation="h", hover_data=["pasar"],
                     labels={"harga": "Rata-rata IDR/kg", "adm1_name": ""}, title="Rata-rata harga per provinsi")
        show(style_fig(fig, max(380, 22 * len(g))))
    with t2:
        g = d.groupby(["adm2_name", "adm1_name"]).agg(harga=("price_clean", "mean")).reset_index().sort_values("harga")
        a, b = st.columns(2)
        a.markdown("**Termurah**"); a.dataframe(g.head(n).rename(columns={"adm2_name": "Kab/Kota", "adm1_name": "Provinsi", "harga": "IDR/kg"}), hide_index=True, width="stretch")
        b.markdown("**Termahal**"); b.dataframe(g.tail(n).iloc[::-1].rename(columns={"adm2_name": "Kab/Kota", "adm1_name": "Provinsi", "harga": "IDR/kg"}), hide_index=True, width="stretch")
    with t3:
        g = d[["mkt_name", "adm2_name", "adm1_name", "price_clean"]].sort_values("price_clean")
        g.columns = ["Pasar", "Kab/Kota", "Provinsi", "IDR/kg"]
        lo, hi = g.iloc[0], g.iloc[-1]
        k = st.columns(2)
        k[0].success(f"Terendah: **{lo['Pasar']}** ({lo['Kab/Kota'].title()}) · {idr(lo['IDR/kg'])}/kg")
        k[1].error(f"Tertinggi: **{hi['Pasar']}** ({hi['Kab/Kota'].title()}) · {idr(hi['IDR/kg'])}/kg")
        a, b = st.columns(2)
        a.markdown("**10 pasar termurah**"); a.dataframe(g.head(n), hide_index=True, width="stretch")
        b.markdown("**10 pasar termahal**"); b.dataframe(g.tail(n).iloc[::-1], hide_index=True, width="stretch")
    with t4:
        m = d.dropna(subset=["lat", "lon"])
        if m.empty:
            st.info("Koordinat tidak tersedia.")
        else:
            fig = px.scatter_map(m, lat="lat", lon="lon", color="price_clean", hover_name="mkt_name",
                                 hover_data={"adm1_name": True, "price_clean": ":,.0f", "lat": False, "lon": False},
                                 color_continuous_scale=["#E9F0EA", "#1D7657", "#142D4E"], zoom=3.3,
                                 center={"lat": -2.5, "lon": 118}, map_style="open-street-map",
                                 labels={"price_clean": "IDR/kg"})
            show(style_fig(fig, 520))
            st.caption(f"{len(d) - len(m)} pasar tanpa koordinat tidak ditampilkan di peta.")
