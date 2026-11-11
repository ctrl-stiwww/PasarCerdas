"""Prediksi harga bulan berikutnya memakai model tersimpan + fitur yang sama dengan training."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .config import MODELS_DIR, MIN_OBS_LAST6, COMMODITIES
from .feature_engineering import build_features, FEATURES
from .preprocessing import last_observed_month
from . import training as T


class InsufficientHistory(Exception):
    """Riwayat harga tidak memenuhi syarat model."""


def load_metadata() -> dict:
    p = MODELS_DIR / "model_metadata.json"
    if not p.exists():
        raise FileNotFoundError(f"{p} tidak ditemukan. Jalankan 'python retrain.py'.")
    return json.loads(p.read_text(encoding="utf-8"))


def list_models() -> dict:
    """{label: path} -> model terbaik + model terbaik per algoritma."""
    meta = load_metadata()
    out = {f"{meta['model_name']}  (terpilih)": MODELS_DIR / "best_model.pkl"}
    for f in sorted((MODELS_DIR / "alternatif").glob("*.pkl")):
        b_name = f.stem
        out[f"Alternatif: {b_name.replace('_', ' ')}"] = f
    return out


def load_bundle(path) -> dict:
    return joblib.load(path)


def predict_next(bundle: dict, long: pd.DataFrame, geo_id: str, commodity: str) -> dict:
    """Prediksi harga bulan setelah bulan observasi terakhir dataset untuk satu pasar-komoditas."""
    last_obs = last_observed_month(long)
    sub = long[(long["geo_id"] == geo_id) & (long["commodity"] == commodity) & (long["date"] <= last_obs)]
    return _predict_from(bundle, sub, geo_id, commodity)


def _predict_from(bundle: dict, sub: pd.DataFrame, geo_id: str, commodity: str) -> dict:
    if sub.empty:
        raise InsufficientHistory("Pasar/komoditas tidak ditemukan pada dataset.")
    last_obs = sub["date"].max()
    target_date = last_obs + pd.DateOffset(months=1)
    sub = sub.copy()
    sub["geo_id"] = sub["geo_id"].astype(str); sub["commodity"] = sub["commodity"].astype(str)
    sub["adm1_name"] = sub["adm1_name"].astype(str)
    feat = build_features(sub, extend_months=1)
    row = feat[feat["date"] == target_date]
    hist = sub.set_index("date")["price_clean"]
    n_obs = int(hist.notna().sum())
    if row.empty or pd.isna(row["price_lag_1"].iloc[0]):
        raise InsufficientHistory(
            f"Pasar ini tidak memiliki harga observasi pada {last_obs:%B %Y} (bulan terakhir data), sehingga "
            "prediksi bulan berikutnya tidak dapat dibuat tanpa mengisi data secara sembarangan.")
    if row["n_obs_last6"].iloc[0] < MIN_OBS_LAST6:
        raise InsufficientHistory(
            f"Riwayat tidak cukup: hanya {int(row['n_obs_last6'].iloc[0])} bulan observasi dari 6 bulan terakhir "
            f"(minimal {MIN_OBS_LAST6}).")
    models = bundle["models"]
    key = "global" if bundle["strategy"] == "global" else commodity
    if key not in models:
        raise InsufficientHistory("Model untuk komoditas ini tidak tersedia.")
    yhat = models[key].predict(row[bundle["features"]])
    pred = float(T.to_price(row, yhat, bundle["target_mode"])[0])
    if not np.isfinite(pred) or pred <= 0:
        raise InsufficientHistory("Model menghasilkan nilai tidak valid; prediksi tidak ditampilkan.")
    last_price = float(row["price_lag_1"].iloc[0])
    return {"target_date": target_date, "last_date": last_obs, "last_price": last_price,
            "prediction": pred, "change": pred - last_price, "change_pct": (pred / last_price - 1) * 100,
            "history": hist.dropna(), "features": row[bundle["features"]].iloc[0].to_dict(),
            "n_observed": n_obs}


def eligible_markets(long: pd.DataFrame) -> set:
    """Pasangan (geo_id, komoditas) yang memenuhi syarat prediksi bulan berikutnya."""
    last_obs = last_observed_month(long)
    feat = build_features(long, extend_months=1)
    row = feat[(feat["date"] == last_obs + pd.DateOffset(months=1)) & feat["eligible"]]
    return set(zip(row["geo_id"], row["commodity"]))


def predict_path(bundle: dict, long: pd.DataFrame, geo_id: str, commodity: str, horizon: int = 1) -> list:
    """Prediksi 1..horizon bulan ke depan. Langkah >1 bersifat REKURSIF: hasil prediksi bulan
    sebelumnya dipakai sebagai lag. Model dilatih untuk 1 bulan, jadi galat menumpuk."""
    last_obs = last_observed_month(long)
    sub = long[(long["geo_id"] == geo_id) & (long["commodity"] == commodity) & (long["date"] <= last_obs)].copy()
    for c in ("geo_id", "commodity", "adm1_name"):
        sub[c] = sub[c].astype(str)
    out = []
    work = sub
    for step in range(1, horizon + 1):
        # predict_next selalu memprediksi bulan setelah bulan terakhir pada `work`
        r = _predict_from(bundle, work, geo_id, commodity)
        r["step"] = step
        r["anchor_price"] = out[0]["last_price"] if out else r["last_price"]
        out.append(r)
        new = work.iloc[[-1]].copy()
        new["date"] = r["target_date"]; new["price_clean"] = r["prediction"]
        work = pd.concat([work, new], ignore_index=True)
    first = out[0]
    for r in out:
        r["change_vs_observed"] = r["prediction"] - first["last_price"]
        r["change_vs_observed_pct"] = (r["prediction"] / first["last_price"] - 1) * 100
    return out
