"""EDA: statistik ringkas dan visualisasi (Matplotlib) dari data aktual."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .config import AGGREGATE_GEO_ID, COMMODITIES, FIG_DIR, RESULTS_DIR

NAVY, GREEN, SOFT = "#142D4E", "#1D7657", "#E9F0EA"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "figure.dpi": 110})


def _save(fig, name):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=130)
    plt.close(fig)


def audit_summary(raw: pd.DataFrame, long: pd.DataFrame) -> dict:
    cols = list(COMMODITIES)
    n_agg_rows = int((raw["geo_id"] == AGGREGATE_GEO_ID).sum())
    raw = raw[raw["geo_id"] != AGGREGATE_GEO_ID]
    s = {
        "rows": int(len(raw) + n_agg_rows), "aggregate_rows_excluded": n_agg_rows, "rows_markets_only": int(len(raw)), "columns": int(raw.shape[1]),
        "markets": int(raw["geo_id"].nunique()), "provinces": int(raw["adm1_name"].nunique()),
        "regencies": int(raw["adm2_name"].nunique()),
        "date_min": str(raw["price_date"].min()), "date_max": str(raw["price_date"].max()),
        "months": int(raw["price_date"].nunique()),
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_market_month": int(raw.duplicated(["geo_id", "price_date"]).sum()),
        "spatially_interpolated_values": sorted(raw["spatially_interpolated"].unique().tolist()),
        "last_survey_point": str(raw["last_survey_point"].iloc[0]),
        "last_month_with_observation": str(long.loc[long.price_clean.notna(), "date"].max().date()),
        "observed_share_overall": float(long["is_observed"].mean()),
        "outliers_flagged": int(long["is_outlier"].sum()),
        "per_commodity": {},
    }
    for c in cols:
        o = long[(long.commodity == c) & long.price_clean.notna()]["price_clean"]
        e = long[long.commodity == c]["price_estimate"]
        s["per_commodity"][c] = {
            "n_observed": int(o.size), "observed_share": float(o.size / (long.commodity == c).sum()),
            "obs_min": float(o.min()), "obs_max": float(o.max()), "obs_mean": float(o.mean()),
            "obs_median": float(o.median()), "est_min": float(e.min()), "est_max": float(e.max()),
            "est_mean": float(e.mean()), "est_median": float(e.median()),
        }
    yr = long.groupby("year")["is_observed"].mean()
    s["observed_share_by_year"] = {int(k): float(v) for k, v in yr.items()}
    return s


def make_eda_figures(raw: pd.DataFrame, long: pd.DataFrame) -> dict:
    summary = audit_summary(raw, long)
    raw = raw[raw["geo_id"] != AGGREGATE_GEO_ID]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "eda_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    obs = long[long.price_clean.notna()]
    names = COMMODITIES

    # 1. histogram distribusi harga observasi
    fig, ax = plt.subplots(2, 4, figsize=(14, 6))
    for a, (c, n) in zip(ax.ravel(), names.items()):
        v = obs.loc[obs.commodity == c, "price_clean"]
        a.hist(v, bins=60, color=GREEN, alpha=.9)
        a.axvline(v.median(), color=NAVY, ls="--", lw=1.2, label=f"median {v.median():,.0f}")
        a.set_title(n); a.set_xlabel("Harga (IDR/kg)"); a.set_ylabel("Jumlah observasi"); a.legend(frameon=False)
    ax.ravel()[-1].axis("off")
    fig.suptitle("Distribusi harga observasi per komoditas (IDR/kg)", fontweight="bold")
    _save(fig, "eda_01_histogram_harga.png")

    # 2. tren bulanan (rata-rata antarpasar, hanya observasi) + estimasi
    mean_obs = obs.groupby(["date", "commodity"])["price_clean"].mean().unstack()
    mean_est = long.groupby(["date", "commodity"])["price_estimate"].mean().unstack()
    fig, ax = plt.subplots(2, 4, figsize=(14, 6), sharex=True)
    for a, (c, n) in zip(ax.ravel(), names.items()):
        a.plot(mean_est.index, mean_est[c], color="#9aa7b8", lw=1, label="Estimasi WB (c_)")
        a.plot(mean_obs.index, mean_obs[c], color=GREEN, lw=1.4, marker=".", ms=3, label="Observasi (rata-rata pasar)")
        a.set_title(n); a.set_ylabel("IDR/kg"); a.tick_params(axis="x", rotation=30)
    ax.ravel()[0].legend(frameon=False, fontsize=7)
    ax.ravel()[-1].axis("off")
    fig.suptitle("Tren harga bulanan rata-rata nasional: observasi vs estimasi", fontweight="bold")
    _save(fig, "eda_02_tren_bulanan.png")

    # 3. missing value (kolom harga mentah)
    miss = raw[list(names)].isna().mean().mul(100).rename(index=names).sort_values()
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.barh(miss.index, miss.values, color=NAVY)
    for i, v in enumerate(miss.values):
        ax.text(v + .5, i, f"{v:.1f}%", va="center")
    ax.set_xlabel("Persentase nilai kosong (%)"); ax.set_title("Missing value harga observasi per komoditas")
    ax.set_xlim(0, 80)
    _save(fig, "eda_03_missing_value.png")

    # 3b. missing per tahun
    share = long.groupby("year")["is_observed"].mean().mul(100)
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.bar(share.index.astype(str), share.values, color=GREEN)
    ax.set_ylabel("% baris dengan harga observasi"); ax.set_xlabel("Tahun")
    ax.set_title("Ketersediaan observasi per tahun (sisanya hanya estimasi model)")
    ax.tick_params(axis="x", rotation=45)
    _save(fig, "eda_03b_observasi_per_tahun.png")

    # 4. perbandingan harga komoditas
    med = obs.groupby("commodity")["price_clean"].agg(["median", "mean"]).rename(index=names)
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(med))
    ax.bar(x - .2, med["median"], .4, label="Median", color=GREEN)
    ax.bar(x + .2, med["mean"], .4, label="Rata-rata", color=NAVY)
    ax.set_xticks(x); ax.set_xticklabels(med.index, rotation=20); ax.set_ylabel("IDR/kg")
    ax.set_title("Perbandingan harga observasi antarkomoditas"); ax.legend(frameon=False)
    _save(fig, "eda_04_perbandingan_komoditas.png")

    # 5. distribusi antarwilayah: boxplot harga rata-rata pasar per provinsi (Beras)
    r = obs[(obs.commodity == "rice") & (obs.date >= "2025-01-01")]
    pm = r.groupby(["adm1_name", "geo_id"], observed=True)["price_clean"].mean().reset_index()
    order = pm.groupby("adm1_name", observed=True)["price_clean"].median().sort_values().index
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.boxplot([pm.loc[pm.adm1_name == o, "price_clean"] for o in order], vert=False,
               patch_artist=True, boxprops=dict(facecolor=SOFT, color=GREEN), medianprops=dict(color=NAVY))
    ax.set_yticklabels(list(order))
    ax.set_xlabel("Rata-rata harga beras per pasar, 2025-2026 (IDR/kg)")
    ax.set_title("Distribusi harga beras antarpasar menurut provinsi"); ax.tick_params(axis="y", labelsize=7)
    _save(fig, "eda_05_distribusi_wilayah.png")

    # 6. kelengkapan data pasar
    comp = long[long.commodity.isin(names)].groupby("geo_id", observed=True)["is_observed"].mean().mul(100)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.hist(comp, bins=40, color=NAVY)
    ax.set_xlabel("% bulan (2007-2026) dengan harga observasi per pasar-komoditas")
    ax.set_ylabel("Jumlah pasar"); ax.set_title("Kelengkapan riwayat harga observasi per pasar")
    _save(fig, "eda_06_kelengkapan_pasar.png")

    # 7. rasio observasi/estimasi (pemeriksaan outlier)
    ratio = (obs["price_observed"] / obs["price_estimate"]).clip(0, 4)
    allobs = long[long.is_observed]
    ratio = (allobs["price_observed"] / allobs["price_estimate"]).clip(0, 4)
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.hist(ratio, bins=120, color=GREEN); ax.set_yscale("log")
    ax.axvline(.5, color="crimson", ls="--"); ax.axvline(2, color="crimson", ls="--", label="batas outlier 0,5x / 2x")
    ax.set_xlabel("Harga observasi / estimasi close"); ax.set_ylabel("Frekuensi (log)")
    ax.set_title("Identifikasi nilai ekstrem terhadap estimasi World Bank"); ax.legend(frameon=False)
    _save(fig, "eda_07_rasio_outlier.png")
    return summary
