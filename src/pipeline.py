"""Pipeline end-to-end: preprocessing -> EDA -> fitur -> training -> evaluasi -> simpan model."""
import json, re
from datetime import datetime
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import (MODELS_DIR, RESULTS_DIR, FIG_DIR, FEATURES_CSV, COMMODITIES, SEED,
                     TRAIN_END, VAL_START, VAL_END, TEST_START)
from .data_loader import load_raw
from .preprocessing import build_long, save_long, last_observed_month
from .eda import make_eda_figures, NAVY, GREEN
from .feature_engineering import build_features, FEATURES
from .evaluation import metrics_table
from . import training as T


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def eval_figures(res, test, preds_test, best_name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    cn = COMMODITIES
    t = res[res.split == "test"].copy()
    t["label"] = t["model"].str.replace(" | ", "\n", regex=False)
    t = t.sort_values("MAE")
    for metric, fname in (("MAE", "eval_01_mae.png"), ("RMSE", "eval_02_rmse.png"), ("R2", "eval_03_r2.png")):
        d = t.sort_values(metric, ascending=(metric != "R2"))
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = [GREEN if m == best_name else ("#c0392b" if m == "Naive Forecast" else NAVY) for m in d.model]
        ax.barh(d["model"], d[metric], color=colors)
        ax.invert_yaxis(); ax.set_xlabel(metric + (" (IDR/kg)" if metric != "R2" else ""))
        ax.set_title(f"Perbandingan {metric} pada data test (hijau = model terpilih, merah = baseline naive)")
        ax.tick_params(axis="y", labelsize=7)
        fig.tight_layout(); fig.savefig(FIG_DIR / fname, dpi=130); plt.close(fig)

    y = test["target"].values; p = preds_test[best_name]
    # Actual vs predicted per komoditas
    fig, ax = plt.subplots(2, 4, figsize=(15, 7))
    rng = np.random.default_rng(SEED)
    for a, (c, n) in zip(ax.ravel(), cn.items()):
        idx = np.where(test["commodity"].values == c)[0]
        idx = rng.choice(idx, min(2500, len(idx)), replace=False)
        a.scatter(y[idx], p[idx], s=4, alpha=.35, color=GREEN)
        lo, hi = min(y[idx].min(), p[idx].min()), max(y[idx].max(), p[idx].max())
        a.plot([lo, hi], [lo, hi], color=NAVY, lw=1)
        a.set_title(n); a.set_xlabel("Aktual (IDR/kg)"); a.set_ylabel("Prediksi (IDR/kg)")
    ax.ravel()[-1].axis("off")
    fig.suptitle(f"Actual vs Predicted (data test) - {best_name}", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG_DIR / "eval_04_actual_vs_predicted.png", dpi=130); plt.close(fig)

    # Residual plot
    r = y - p
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    ax[0].scatter(p, r, s=3, alpha=.25, color=NAVY); ax[0].axhline(0, color="crimson")
    ax[0].set_xlabel("Prediksi (IDR/kg)"); ax[0].set_ylabel("Residual = aktual - prediksi"); ax[0].set_title("Residual vs prediksi")
    ax[1].hist(np.clip(r, -8000, 8000), bins=100, color=GREEN); ax[1].set_xlabel("Residual (IDR/kg, dipotong +/-8000)")
    ax[1].set_ylabel("Frekuensi"); ax[1].set_title("Distribusi residual")
    fig.suptitle(f"Analisis residual - {best_name}", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG_DIR / "eval_05_residual.png", dpi=130); plt.close(fig)

    # Global vs separate
    g = t[t.model != "Naive Forecast"].pivot_table(index=["algo", "target_mode"], columns="strategy", values="MAE")
    fig, ax = plt.subplots(figsize=(8, 4.2)); g.plot.bar(ax=ax, color=[GREEN, NAVY], rot=20)
    ax.set_ylabel("MAE test (IDR/kg)"); ax.set_title("Strategi Global vs Separate (MAE data test)"); ax.set_xlabel("")
    fig.tight_layout(); fig.savefig(FIG_DIR / "eval_06_global_vs_separate.png", dpi=130); plt.close(fig)


def run_all(log=print, quick=False):
    for d in (MODELS_DIR, RESULTS_DIR, FIG_DIR, MODELS_DIR / "alternatif"):
        d.mkdir(parents=True, exist_ok=True)

    log("== 1. Muat & preprocessing ==")
    raw = load_raw(); long = build_long(raw); save_long(long)
    log("== 2. EDA ==")
    make_eda_figures(raw, long)
    last_obs = last_observed_month(long)
    log(f"Bulan observasi terakhir: {last_obs.date()}")

    log("== 3. Feature engineering ==")
    feat = build_features(long)
    feat_out = feat[feat["target"].notna() & feat["eligible"]].copy()
    feat_out["date"] = feat_out["date"].dt.strftime("%Y-%m-%d")
    feat_out.to_csv(FEATURES_CSV, index=False, float_format="%.4f")
    log(f"Baris siap modeling: {len(feat_out):,}")

    log("== 4. Training & tuning ==")
    train, val, test, res, pv, pt, store = T.run_experiments(feat, log=log, quick=quick)
    best_name = T.select_best(res)
    log(f"Model terpilih (MAE validasi terendah): {best_name}")

    log("== 5. Evaluasi ==")
    res.to_csv(RESULTS_DIR / "evaluation_metrics.csv", index=False)
    pred_df = test[["date", "geo_id", "commodity", "adm1_name", "target", "price_lag_1"]].rename(
        columns={"target": "y_true"}).reset_index(drop=True)
    for k, v in pt.items():
        pred_df[k] = v
    models_cols = list(pt)
    by_com = metrics_table(pred_df, ["commodity"], pred_cols=models_cols)
    by_com.to_csv(RESULTS_DIR / "evaluation_by_commodity.csv", index=False)
    pred_df["period"] = pred_df["date"].dt.strftime("%Y-%m"); pred_df["year"] = pred_df["date"].dt.year
    metrics_table(pred_df, ["year"], pred_cols=models_cols).to_csv(RESULTS_DIR / "evaluation_by_year.csv", index=False)
    metrics_table(pred_df, ["period"], pred_cols=models_cols).to_csv(RESULTS_DIR / "evaluation_by_period.csv", index=False)
    out = pred_df.drop(columns=["period", "year"]).copy(); out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(RESULTS_DIR / "prediction_results.csv", index=False, float_format="%.2f")
    eval_figures(res, test, pt, best_name)

    log("== 6. Simpan model ==")
    versions = T.library_versions()
    # model terbaik per algoritma (berdasarkan MAE validasi) -> alternatif untuk website
    v = res[(res.split == "validation") & (res.model != "Naive Forecast")]
    alt = {}
    for algo, g in v.groupby("algo"):
        nm = g.sort_values("MAE").iloc[0]["model"]
        bundle = T.make_bundle(store[nm], nm)
        fn = MODELS_DIR / "alternatif" / f"{slug(nm)}.pkl"
        joblib.dump(bundle, fn, compress=3)
        alt[T.ALGO_NAMES[store[nm]['algo']] if False else algo] = nm
    best_bundle = T.make_bundle(store[best_name], best_name)
    joblib.dump(best_bundle, MODELS_DIR / "best_model.pkl", compress=3)
    first = next(iter(best_bundle["models"].values()))
    joblib.dump({k: m.named_steps["prep"] for k, m in best_bundle["models"].items()},
                MODELS_DIR / "preprocessing.pkl", compress=3)

    best_rows = res[res.model == best_name].set_index("split")
    naive_rows = res[res.model == "Naive Forecast"].set_index("split")
    meta = {
        "model_name": best_name, "algorithm": best_bundle["algo_name"], "strategy": best_bundle["strategy"],
        "target_mode": best_bundle["target_mode"], "hyperparameters": best_bundle["params"], "seed": SEED,
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "train_period": [str(train.date.min().date()), str(train.date.max().date())],
        "validation_period": [str(val.date.min().date()), str(val.date.max().date())],
        "test_period": [str(test.date.min().date()), str(test.date.max().date())],
        "rows": {"train": int(len(train)), "validation": int(len(val)), "test": int(len(test))},
        "last_observed_month": str(last_obs.date()),
        "supported_commodities": COMMODITIES, "features": FEATURES,
        "selection_rule": "MAE validasi (2024) terendah di antara seluruh kombinasi model; data test tidak dipakai memilih.",
        "metrics_validation": {k: best_rows.loc["validation", k] for k in ["MAE", "RMSE", "R2", "MAPE_%"]},
        "metrics_test": {k: best_rows.loc["test", k] for k in ["MAE", "RMSE", "R2", "MAPE_%"]},
        "naive_baseline_test": {k: naive_rows.loc["test", k] for k in ["MAE", "RMSE", "R2", "MAPE_%"]},
        "alternative_models": alt, "library_versions": versions,
    }
    (MODELS_DIR / "model_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=float))

    # verifikasi: model yang dimuat ulang menghasilkan prediksi identik
    re_b = joblib.load(MODELS_DIR / "best_model.pkl")
    p2 = T.predict_strategy(re_b["models"], test, re_b["strategy"], re_b["target_mode"])
    assert np.allclose(p2, pt[best_name]), "Prediksi model hasil load tidak konsisten!"
    log("Verifikasi load model: prediksi konsisten (OK)")
    return meta, res
