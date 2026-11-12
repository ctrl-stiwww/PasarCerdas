import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import COMMODITIES
from src.ui import get_national, page_header, style_fig, show, fmt_month, help_box


def render():
    page_header("Tren Harga", "Apakah harga cenderung naik atau turun? Bahan apa yang paling sering berubah-ubah?")
    nat = get_national()
    nat = nat[nat.date >= "2020-01-01"].copy()
    nat["mom"] = nat.groupby("commodity")["price"].pct_change() * 100
    # hanya bulan berurutan (tanpa celah) untuk perubahan bulanan
    nat["gap"] = nat.groupby("commodity")["date"].diff().dt.days
    nat.loc[nat["gap"] > 31, "mom"] = np.nan
    st.caption("Rata-rata nasional hanya dihitung pada bulan dengan ≥100 pasar teramati agar tidak bias oleh perubahan "
               "komposisi pasar (mis. Feb–Mei 2024 dan Jan 2026 dikecualikan).")
    help_box("Cara membaca halaman ini", "- **Indeks harga**: harga Januari 2020 dianggap 100. Indeks 130 berarti harga sudah naik 30% dari Januari 2020.\n- **Volatilitas**: seberapa besar harga biasanya berubah dari bulan ke bulan. Makin besar, makin tidak stabil.\n- **MoM** = perubahan dari bulan sebelumnya; **YoY** = perubahan dari bulan yang sama tahun lalu.")
    sel = st.multiselect("Komoditas", list(COMMODITIES.values()), default=list(COMMODITIES.values()), key="tr_sel")
    d = nat[nat.commodity_name.isin(sel)]
    if d.empty:
        st.warning("Pilih minimal satu komoditas."); return
    idx = d.copy(); idx["indeks"] = idx.groupby("commodity")["price"].transform(lambda s: s / s.iloc[0] * 100)
    show(style_fig(px.line(idx, x="date", y="indeks", color="commodity_name", title="Indeks harga (Jan 2020 = 100)",
                           labels={"date": "Bulan", "indeks": "Indeks", "commodity_name": ""}), 420))

    vol = d.groupby("commodity_name").agg(volatilitas=("mom", "std"), naik=("mom", lambda s: (s > 0).sum()),
                                          turun=("mom", lambda s: (s < 0).sum()), maks_naik=("mom", "max"),
                                          maks_turun=("mom", "min")).reset_index().sort_values("volatilitas", ascending=False)
    a, b = st.columns([2, 3])
    with a:
        st.subheader("Paling fluktuatif")
        st.caption("Volatilitas = simpangan baku perubahan harga bulanan (%).")
        fig = px.bar(vol, x="volatilitas", y="commodity_name", orientation="h", labels={"volatilitas": "Std. perubahan bulanan (%)", "commodity_name": ""})
        fig.update_yaxes(autorange="reversed"); show(style_fig(fig, 340))
    with b:
        st.subheader("Kenaikan & penurunan")
        v = vol.rename(columns={"commodity_name": "Komoditas", "volatilitas": "Volatilitas (%)", "naik": "Bulan naik",
                                "turun": "Bulan turun", "maks_naik": "Kenaikan maks (%)", "maks_turun": "Penurunan maks (%)"}).round(2)
        st.dataframe(v, hide_index=True, width="stretch")

    one = st.selectbox("Detail komoditas", sel, key="tr_one")
    e = nat[nat.commodity_name == one].copy()
    e["yoy"] = np.nan
    prev = e.set_index("date")["price"]
    e["yoy"] = [(p / prev.get(dt - pd.DateOffset(years=1), np.nan) - 1) * 100 for dt, p in zip(e.date, e.price)]
    c1, c2 = st.columns(2)
    with c1:
        f = px.bar(e.dropna(subset=["mom"]), x="date", y="mom", title=f"Perubahan bulanan {one} (%)",
                   labels={"mom": "% MoM", "date": ""}, color=(e.dropna(subset=["mom"])["mom"] > 0).map({True: "Naik", False: "Turun"}),
                   color_discrete_map={"Naik": "#E8734A", "Turun": "#4D7111"})
        show(style_fig(f, 340))
    with c2:
        y = e.dropna(subset=["yoy"])
        f = px.line(y, x="date", y="yoy", title=f"Perubahan tahunan {one} (% YoY)", labels={"yoy": "% YoY", "date": ""})
        f.add_hline(y=0, line_dash="dot"); show(style_fig(f, 340))
    ya = e.assign(tahun=e.date.dt.year).groupby("tahun").agg(rata2=("price", "mean"), bulan=("price", "size")).reset_index()
    ya["Perubahan thd tahun sebelumnya (%)"] = ya["rata2"].pct_change() * 100
    ya.columns = ["Tahun", "Rata-rata (IDR/kg)", "Jumlah bulan", "Perubahan thd tahun sebelumnya (%)"]
    st.markdown("**Rata-rata tahunan** (tahun berjalan hanya mencakup bulan yang tersedia)")
    st.dataframe(ya.round(1), hide_index=True, width="stretch")
