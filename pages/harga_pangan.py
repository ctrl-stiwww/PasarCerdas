import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import COMMODITIES
from src.ui import get_long, get_obs, last_obs_month, page_header, idr, fmt_month, style_fig, show, stat_card, help_box


def render():
    page_header("Cek Harga", "Cari harga bahan pokok di daerahmu: pilih bahan, lokasi, dan periode.")
    obs, long = get_obs(), get_long()
    names = list(COMMODITIES.values())
    f = st.columns(5)
    com = f[0].selectbox("Komoditas", names, key="hp_com")
    d = obs[obs.commodity_name == com]
    prov_opts = ["Semua"] + sorted(d.adm1_name.unique())
    prov = f[1].selectbox("Provinsi", prov_opts, key="hp_prov")
    if prov != "Semua": d = d[d.adm1_name == prov]
    kab = f[2].selectbox("Kabupaten/Kota", ["Semua"] + sorted(d.adm2_name.unique()), key=f"hp_kab_{prov}")
    if kab != "Semua": d = d[d.adm2_name == kab]
    pas = f[3].selectbox("Pasar", ["Semua"] + sorted(d.mkt_name.unique()), key=f"hp_pas_{prov}_{kab}")
    if pas != "Semua": d = d[d.mkt_name == pas]
    dmin, dmax = obs.date.min().date(), last_obs_month().date()
    rng = f[4].date_input("Periode", (max(dmin, pd.Timestamp("2020-01-01").date()), dmax),
                          min_value=dmin, max_value=dmax, key="hp_rng")
    if isinstance(rng, tuple) and len(rng) == 2:
        d = d[(d.date >= pd.Timestamp(rng[0])) & (d.date <= pd.Timestamp(rng[1]))]
    show_est = st.checkbox("Tampilkan juga estimasi model World Bank (garis putus-putus, bukan observasi)", key="hp_est")

    if d.empty:
        st.warning("Tidak ada data observasi untuk kombinasi filter ini."); return
    c = st.columns(4)
    with c[0]: stat_card("Harga minimum", idr(d.price_clean.min()), "IDR/kg", "down")
    with c[1]: stat_card("Harga maksimum", idr(d.price_clean.max()), "IDR/kg", "up")
    with c[2]: stat_card("Harga rata-rata", idr(d.price_clean.mean()), "IDR/kg", "navy")
    with c[3]: stat_card("Periode data", f"{fmt_month(d.date.min())} – {fmt_month(d.date.max())}",
                         f"{len(d):,} observasi dari {d.geo_id.nunique()} pasar".replace(",", "."))
    ts = d.groupby("date").agg(rata_rata=("price_clean", "mean"), minimum=("price_clean", "min"),
                               maksimum=("price_clean", "max")).reset_index()
    fig = px.line(ts, x="date", y=["rata_rata", "minimum", "maksimum"],
                  labels={"date": "Bulan", "value": "Harga (IDR/kg)", "variable": ""},
                  title=f"Perubahan harga {com} (observasi)")
    if show_est:
        e = long[long.commodity_name == com]
        e = e[e.geo_id.isin(d.geo_id.unique()) & e.date.between(d.date.min(), d.date.max())]
        e = e.groupby("date")["price_estimate"].mean().reset_index()
        fig.add_scatter(x=e.date, y=e.price_estimate, name="estimasi WB (c_)", line=dict(dash="dot", color="#888"))
    show(style_fig(fig, 400))
    help_box("Cara membaca halaman ini", "- Garis **rata-rata** = harga rata-rata dari semua pasar yang terpilih; **minimum/maksimum** = pasar termurah/termahal pada bulan itu.\n- Pilih provinsi lalu kabupaten/kota untuk mempersempit ke pasar tertentu.\n- Hanya harga asli yang ditampilkan; perkiraan World Bank bisa ditambahkan lewat kotak centang.")
    st.subheader("Tabel harga")
    t = d[["date", "mkt_name", "adm2_name", "adm1_name", "commodity_name", "price_clean"]].sort_values(
        ["date", "mkt_name"], ascending=[False, True])
    t.columns = ["Tanggal", "Pasar", "Kabupaten/Kota", "Provinsi", "Komoditas", "Harga (IDR/kg)"]
    t["Tanggal"] = t["Tanggal"].dt.strftime("%Y-%m")
    st.dataframe(t, width="stretch", hide_index=True, height=360)
    st.download_button("Unduh CSV (hasil filter)", t.to_csv(index=False).encode("utf-8"), "harga_pasarcerdas.csv", "text/csv")
