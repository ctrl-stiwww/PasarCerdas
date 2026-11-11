import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import COMMODITIES
from src.ui import (get_long, get_obs, get_national, last_obs_month, hero, insight, help_box, price_grid, idr,
                    fmt_month, fmt_pct, style_fig, show, ICONS)


def _latest_changes(obs, last):
    prev = last - pd.DateOffset(months=1)
    a = obs[obs.date == last].set_index(["geo_id", "commodity"])["price_clean"]
    b = obs[obs.date == prev].set_index(["geo_id", "commodity"])["price_clean"]
    j = pd.concat([a.rename("now"), b.rename("prev")], axis=1).dropna().reset_index()
    g = j.groupby("commodity")[["now", "prev"]].mean()
    g["pct"] = (g["now"] / g["prev"] - 1) * 100
    return g, prev


def render():
    long, obs, nat, last = get_long(), get_obs(), get_national(), last_obs_month()
    chg, prev = _latest_changes(obs, last)
    chg["name"] = chg.index.map(COMMODITIES)
    hero("Pantau harga pangan Indonesia, tanpa ribet 🌾",
         "Lihat harga 7 bahan pokok di pasar-pasar seluruh Indonesia, bandingkan antarwilayah, "
         "dan perkirakan harga bulan depan.",
         [f"🏪 {long.geo_id.nunique()} pasar", f"🗺️ {long.adm1_name.nunique()} provinsi", "🥚 7 bahan pokok",
          f"📅 Data terbaru: {fmt_month(last)}"])

    st.subheader(f"Harga rata-rata nasional · {fmt_month(last)}")
    st.caption(f"Persen ▲▼ = perubahan dibanding {fmt_month(prev)}.")
    price_grid([(code, name, idr(chg.loc[code, "now"]), fmt_pct(abs(chg.loc[code, 'pct'])),
                 chg.loc[code, "pct"] >= 0) for code, name in COMMODITIES.items()])
    up, dn = chg.sort_values("pct").iloc[-1], chg.sort_values("pct").iloc[0]
    insight(f"Dibanding {fmt_month(prev)}, harga yang <b>paling naik</b> adalah <b>{up['name']}</b> "
            f"({fmt_pct(up['pct'], True)}), dan yang <b>paling turun</b> adalah <b>{dn['name']}</b> ({fmt_pct(dn['pct'], True)}). "
            "Merah ▲ berarti harga naik (lebih mahal), hijau ▼ berarti harga turun.")

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("#### 📈 Bagaimana harga bergerak?")
        sel = st.pills("Pilih bahan pokok (bisa lebih dari satu)", list(COMMODITIES.values()),
                       selection_mode="multi", default=["Beras", "Telur", "Gula"], key="dash_sel")
        if not sel:
            st.info("Pilih minimal satu bahan pokok untuk menampilkan grafik.")
        else:
            d = nat[nat.commodity_name.isin(sel) & (nat.date >= "2020-01-01")]
            fig = px.line(d, x="date", y="price", color="commodity_name",
                          labels={"date": "Bulan", "price": "Rata-rata harga (Rp/kg)", "commodity_name": ""})
            fig.update_traces(line=dict(width=3))
            if st.toggle("Tampilkan juga perkiraan World Bank setelah data terakhir (garis putus-putus)", key="dash_est"):
                e = long[(long.commodity_name.isin(sel)) & (long.date >= last)].groupby(
                    ["date", "commodity_name"], observed=True)["price_estimate"].mean().reset_index()
                for nm, g in e.groupby("commodity_name"):
                    fig.add_scatter(x=g.date, y=g.price_estimate, mode="lines+markers", name=f"{nm} (perkiraan WB)",
                                    line=dict(dash="dot"))
            show(style_fig(fig, 400))
            st.caption("Arahkan kursor ke grafik untuk melihat harga tiap bulan.")
    with right:
        st.markdown(f"#### ⚖️ Mana yang paling mahal? ({fmt_month(last)})")
        d = chg.sort_values("now")
        fig = px.bar(d, x="now", y="name", orientation="h", text=d["now"].map(lambda v: f"Rp {v:,.0f}".replace(",", ".")),
                     labels={"now": "Rp/kg", "name": ""}, color="now",
                     color_continuous_scale=["#9ADBCB", "#14A38B", "#1B6CA8", "#0A2F4F"])
        fig.update_layout(coloraxis_showscale=False)
        fig.update_traces(textposition="outside", cliponaxis=False)
        show(style_fig(fig, 400))

    help_box("Cara membaca halaman ini",
             "- **Harga** adalah rata-rata dari pasar yang mencatat harga bulan tersebut (Rupiah per kilogram).\n"
             f"- **Data terbaru** adalah {fmt_month(last)}. Bulan setelahnya belum punya catatan harga asli, "
             "hanya perkiraan dari World Bank, sehingga tidak dipakai sebagai harga.\n"
             "- Perubahan ▲▼ dihitung hanya dari pasar yang punya catatan harga di **kedua** bulan, supaya adil.\n"
             "- Ingin tahu harga di kotamu? Buka menu **Cek Harga**. Ingin perkiraan bulan depan? Buka **Prediksi**.")
