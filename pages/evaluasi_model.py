import json
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from src.config import FIG_DIR, COMMODITIES
from src.prediction import load_metadata
from src.ui import page_header, insight, help_box, read_csv_result, style_fig, show, stat_card, idr, GREEN, NAVY


def render():
    page_header("Seberapa Akurat Prediksinya?", "Hasil uji model pada data yang belum pernah dilihatnya (Januari 2025 – September 2026).")
    meta = load_metadata()
    res = read_csv_result("evaluation_metrics.csv")
    test = res[res.split == "test"].copy(); val = res[res.split == "validation"]
    best = meta["model_name"]; mt, nv = meta["metrics_test"], meta["naive_baseline_test"]

    st.markdown(f"<div class='pc-note'><b>Model terpilih:</b> {best} (MAE validasi terendah). "
                f"Latih: {meta['train_period'][0][:7]}–{meta['train_period'][1][:7]} · Validasi: 2024 · "
                f"Uji: {meta['test_period'][0][:7]}–{meta['test_period'][1][:7]} · "
                f"{meta['rows']['train']:,}/{meta['rows']['validation']:,}/{meta['rows']['test']:,} baris.</div>".replace(",", "."),
                unsafe_allow_html=True)
    insight(f"Secara sederhana: pada data uji, tebakan model rata-rata meleset sekitar <b>{idr(mt['MAE'])} per kg</b> "
            f"(sekitar <b>{str(round(mt['MAPE_%'], 1)).replace('.', ',')}%</b> dari harga). Tebakan sederhana \"harga bulan depan = harga bulan ini\" meleset "
            f"{idr(nv['MAE'])} per kg. Artinya, untuk bahan yang harganya stabil, harga bulan lalu sudah prediktor yang sangat baik.")
    help_box("Apa arti MAE, RMSE, R², dan MAPE?", "- **MAE**: rata-rata selisih antara tebakan dan harga sebenarnya (Rp/kg). Makin kecil makin baik.\n- **RMSE**: seperti MAE tetapi lebih menghukum kesalahan besar. Makin kecil makin baik.\n- **R²**: seberapa baik model mengikuti pola harga (maks 1). Makin dekat ke 1 makin baik.\n- **MAPE**: rata-rata kesalahan dalam persen.\n- **Naive**: tebakan pembanding sederhana, yaitu harga bulan depan dianggap sama dengan bulan ini.")
    c = st.columns(4)
    with c[0]: stat_card("MAE (test)", idr(mt["MAE"]), f"Naive: {idr(nv['MAE'])}", "navy")
    with c[1]: stat_card("RMSE (test)", idr(mt["RMSE"]), f"Naive: {idr(nv['RMSE'])}", "navy")
    with c[2]: stat_card("R² (test)", f"{mt['R2']:.3f}", f"Naive: {nv['R2']:.3f}", "navy")
    with c[3]: stat_card("MAPE (test)", f"{mt['MAPE_%']:.2f}%", f"Naive: {nv['MAPE_%']:.2f}%", "navy")
    beat = mt["MAE"] < nv["MAE"]
    st.markdown(f"<div class='pc-warn'><b>Catatan jujur:</b> pada MAE data uji, model terpilih "
                f"{'mengungguli' if beat else 'belum mengungguli'} baseline Naive Forecast "
                f"({idr(mt['MAE'])} vs {idr(nv['MAE'])}). Keunggulan model terlihat pada RMSE/R² dan komoditas bawang merah; "
                "untuk komoditas yang harganya sangat stabil (beras, gula, minyak) harga bulan lalu sudah menjadi prediktor sangat kuat.</div>",
                unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.tabs(["Perbandingan model", "Global vs Separate", "Per komoditas", "Per periode", "Grafik"])
    with t1:
        split = st.radio("Data", ["test", "validation"], horizontal=True, key="ev_split",
                         format_func=lambda x: {"test": "Uji (2025–Sep 2026)", "validation": "Validasi (2024)"}[x])
        d = (test if split == "test" else val)[["model", "algo", "strategy", "target_mode", "MAE", "RMSE", "R2", "MAPE_%"]]
        d = d.sort_values("MAE").reset_index(drop=True)
        d.insert(0, "Peringkat", range(1, len(d) + 1))
        d["Keterangan"] = np.where(d.model == best, "terpilih", np.where(d.model == "Naive Forecast", "baseline", ""))
        view = d.rename(columns={"model": "Model", "algo": "Algoritma", "strategy": "Strategi", "target_mode": "Target",
                                 "MAE": "MAE (Rp/kg)", "RMSE": "RMSE (Rp/kg)", "R2": "R²", "MAPE_%": "MAPE (%)"})
        st.caption("Diurutkan dari MAE terkecil. Model terpilih ditentukan dari MAE **validasi**; data uji tidak dipakai untuk memilih.")
        st.dataframe(view, hide_index=True, width="stretch",
                     column_config={"MAE (Rp/kg)": st.column_config.NumberColumn(format="%.0f"),
                                    "RMSE (Rp/kg)": st.column_config.NumberColumn(format="%.0f"),
                                    "R²": st.column_config.NumberColumn(format="%.3f"),
                                    "MAPE (%)": st.column_config.NumberColumn(format="%.2f")})
        m = st.radio("Metrik", ["MAE", "RMSE", "R2"], horizontal=True, key="ev_metric")
        x = d.sort_values(m, ascending=(m != "R2"))
        fig = px.bar(x, x=m, y="model", orientation="h", color=(x["model"] == best).map({True: "Terpilih", False: "Lainnya"}),
                     color_discrete_map={"Terpilih": GREEN, "Lainnya": NAVY})
        fig.update_yaxes(autorange="reversed"); show(style_fig(fig, 520))
        st.markdown("**Algoritma:** Linear Regression (baseline linear), Random Forest Regressor, XGBoost Regressor, "
                    "dibandingkan dengan Naive Forecast (harga bulan sebelumnya).")
    with t2:
        g = test[test.model != "Naive Forecast"].pivot_table(index=["algo", "target_mode"], columns="strategy",
                                                             values=["MAE", "RMSE", "R2"]).round(3)
        g.columns = [f"{a} {b}" for a, b in g.columns]
        st.dataframe(g.reset_index(), hide_index=True, width="stretch")
        st.image(str(FIG_DIR / "eval_06_global_vs_separate.png"))
    with t3:
        pc = read_csv_result("evaluation_by_commodity.csv")
        sel = st.selectbox("Model", sorted(pc.model.unique()), index=sorted(pc.model.unique()).index(best), key="ev_pcm")
        a = pc[pc.model == sel].copy(); n_ = pc[pc.model == "Naive Forecast"].set_index("commodity")
        a["Komoditas"] = a.commodity.map(COMMODITIES); a["MAE Naive"] = a.commodity.map(n_["MAE"])
        a = a[["Komoditas", "n", "MAE", "MAE Naive", "RMSE", "R2", "MAPE_%"]]
        st.dataframe(a.round(3), hide_index=True, width="stretch")
    with t4:
        py = read_csv_result("evaluation_by_year.csv")
        st.dataframe(py[py.model.isin([best, "Naive Forecast"])].round(3), hide_index=True, width="stretch")
        pp = read_csv_result("evaluation_by_period.csv")
        pp = pp[pp.model.isin([best, "Naive Forecast"])]
        fig = px.line(pp, x="period", y="MAE", color="model", markers=True, title="MAE per bulan pada periode uji")
        show(style_fig(fig, 360))
    with t5:
        for f, cap in [("eval_04_actual_vs_predicted.png", "Actual vs Predicted"), ("eval_05_residual.png", "Residual")]:
            st.markdown(f"**{cap}**"); st.image(str(FIG_DIR / f))
