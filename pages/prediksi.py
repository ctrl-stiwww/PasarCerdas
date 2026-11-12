import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from src.config import COMMODITIES
from src.prediction import (list_models, load_bundle, predict_path, InsufficientHistory, load_metadata,
                            eligible_markets)
from src.ui import (get_long, get_obs, last_obs_month, page_header, idr, fmt_month, fmt_pct, style_fig, show, stat_card,
                    insight, step, help_box, read_csv_result, arrow_icon, NAVY, GREEN)


@st.cache_resource
def _bundle(path):
    return load_bundle(path)


@st.cache_data(show_spinner="Memeriksa kecukupan riwayat tiap pasar...")
def _eligible():
    return eligible_markets(get_long())


def render():
    page_header("Prediksi Harga", "Perkirakan harga bulan-bulan mendatang untuk pasar pilihanmu dalam 3 langkah mudah.")
    obs, long, last = get_obs(), get_long(), last_obs_month()
    meta = load_metadata(); models = list_models(); elig = _eligible()
    nxt = last + pd.DateOffset(months=1)
    st.markdown(f"<div class='pc-note'>Harga asli terakhir yang tercatat: <b>{fmt_month(last)}</b>. "
                f"Prediksi dimulai dari <b>{fmt_month(nxt)}</b>. Hanya pasar dengan riwayat harga yang cukup yang bisa dipilih.</div>",
                unsafe_allow_html=True)

    step(1, "Pilih bahan pokok dan lokasi pasar")
    c = st.columns(4)
    com_name = c[0].selectbox("Bahan pokok", list(COMMODITIES.values()), key="pr_com")
    code = {v: k for k, v in COMMODITIES.items()}[com_name]
    d = obs[(obs.commodity == code) & obs.geo_id.map(lambda g: (g, code) in elig)].drop_duplicates("geo_id")
    if d.empty:
        st.warning("Tidak ada pasar yang memenuhi syarat untuk bahan pokok ini."); return
    prov = c[1].selectbox("Provinsi", sorted(d.adm1_name.unique()), key="pr_prov")
    d = d[d.adm1_name == prov]
    kab = c[2].selectbox("Kabupaten/Kota", sorted(d.adm2_name.unique()), key=f"pr_kab_{prov}")
    d = d[d.adm2_name == kab]
    pas = c[3].selectbox("Pasar", sorted(d.mkt_name.unique()), key=f"pr_pas_{prov}_{kab}")
    geo = d[d.mkt_name == pas].geo_id.iloc[0]
    st.caption(f"{len(obs[(obs.commodity == code) & obs.geo_id.map(lambda g: (g, code) in elig)].geo_id.unique())} pasar tersedia untuk {com_name}.")

    step(2, "Pilih seberapa jauh ke depan")
    h1, h2 = st.columns([2, 3])
    horizon = h1.segmented_control("Prediksi untuk", [1, 2, 3], default=1, key="pr_hor",
                                   format_func=lambda h: f"{h} bulan lagi") or 1
    with h2.expander("Pengaturan lanjutan (model)"):
        model_label = st.selectbox("Model yang dipakai", list(models), key="pr_model")
    model_label = st.session_state.get("pr_model", list(models)[0])

    step(3, "Lihat hasilnya")
    if not st.button("Perkirakan harga sekarang"):
        st.caption("Tekan tombol di atas untuk melihat perkiraan."); return
    bundle = _bundle(models[model_label])
    try:
        path = predict_path(bundle, long, geo, code, horizon)
    except InsufficientHistory as e:
        st.markdown(f"<div class='pc-warn'>{e}</div>", unsafe_allow_html=True); return
    r, fin = path[0], path[-1]
    up = fin["change_vs_observed"] >= 0
    arrow_word = "naik" if up else "turun"
    em = read_csv_result("evaluation_by_commodity.csv")
    row = em[(em.commodity == code) & (em.model == bundle["name"])]

    st.markdown(f"<div class='pc-result'><div class='sm'>Perkiraan harga {com_name} di {pas} pada {fmt_month(fin['target_date'])}</div>"
                f"<div class='big'>{idr(fin['prediction'])} <span style='font-size:1rem;font-weight:700;color:#E4F7D0'>/kg</span></div>"
                f"<div class='sm'>{arrow_icon(up)} {arrow_word} {idr(abs(fin['change_vs_observed']))} "
                f"({fmt_pct(abs(fin['change_vs_observed_pct']))}) dibanding harga terakhir {idr(r['last_price'])} ({fmt_month(r['last_date'])})</div></div>",
                unsafe_allow_html=True)
    msg = (f"Harga {com_name} di {pas}, {kab.title()} diperkirakan <b>{arrow_word}</b> sekitar <b>{idr(abs(fin['change_vs_observed']))}</b> per kg. ")
    if not row.empty:
        msg += (f"Pada pengujian, tebakan model ini rata-rata meleset sekitar <b>{idr(row.MAE.iloc[0])}</b> per kg untuk {com_name}, "
                "jadi anggap hasilnya sebagai <b>perkiraan</b>, bukan angka pasti.")
    insight(msg)
    if horizon > 1:
        st.markdown("<div class='pc-warn'>Perkiraan lebih dari 1 bulan dihitung bertahap (hasil bulan sebelumnya dipakai untuk bulan berikutnya). "
                    "Makin jauh bulannya, makin kurang pasti.</div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({"Bulan": [fmt_month(p["target_date"]) for p in path],
                                   "Perkiraan (Rp/kg)": [round(p["prediction"]) for p in path],
                                   "Perubahan dari harga terakhir (%)": [round(p["change_vs_observed_pct"], 2) for p in path]}),
                     hide_index=True, width="stretch")
    k = st.columns(3)
    with k[0]: stat_card("Harga terakhir tercatat", idr(r["last_price"]), fmt_month(r["last_date"]), "navy")
    with k[1]: stat_card("Perubahan", f"{fin['change_vs_observed']:+,.0f}".replace(",", "."), fmt_pct(fin['change_vs_observed_pct'], True, 2), "up" if up else "down")
    with k[2]: stat_card("Kecenderungan", "Naik" if up else "Turun", "indikatif, bukan jaminan", "up" if up else "down")

    h = r["history"].tail(24)
    fig = go.Figure()
    fig.add_scatter(x=h.index, y=h.values, mode="lines+markers", name="Harga tercatat", line=dict(color=NAVY, width=3))
    fig.add_scatter(x=[r["last_date"]] + [p["target_date"] for p in path], y=[r["last_price"]] + [p["prediction"] for p in path],
                    mode="lines+markers", name="Perkiraan", line=dict(color="#E8734A", dash="dash", width=3),
                    marker=dict(size=11, symbol="star"))
    fig.update_layout(title="Harga 24 bulan terakhir dan perkiraan", xaxis_title="Bulan", yaxis_title="Rp/kg")
    show(style_fig(fig, 400))
    with st.expander("Detail teknis model (untuk yang ingin tahu)"):
        st.write(f"**Model:** {bundle['name']} · **Latih:** {meta['train_period'][0][:7]} – {meta['train_period'][1][:7]} · "
                 f"**Uji:** {meta['test_period'][0][:7]} – {meta['test_period'][1][:7]}")
        ft = {k_: v for k_, v in r["features"].items() if k_ not in ("commodity", "geo_id", "adm1_name")}
        st.dataframe(pd.DataFrame({"Fitur": list(ft), "Nilai": list(ft.values())}), hide_index=True, width="stretch")
