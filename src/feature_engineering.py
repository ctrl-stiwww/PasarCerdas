"""Feature engineering time series (lag & rolling) per pasar x komoditas.

Satu fungsi inti (`build_features`) dipakai untuk TRAINING maupun PREDIKSI di website,
sehingga fitur selalu konsisten. Semua fitur historis hanya memakai bulan < bulan target
(shift >= 1), sehingga tidak ada kebocoran data masa depan.
"""
import numpy as np
import pandas as pd
from .config import MIN_OBS_LAST6

CATEGORICAL = ["commodity", "geo_id", "adm1_name"]
NUMERIC = ["year", "month", "price_lag_1", "price_lag_2", "price_lag_3", "price_lag_12",
           "rolling_mean_3", "rolling_mean_6", "n_obs_last6", "mom_1", "dev_roll3", "dev_roll6"]
FEATURES = CATEGORICAL + NUMERIC


def build_features(long: pd.DataFrame, extend_months: int = 0) -> pd.DataFrame:
    """Bangun fitur lag/rolling dari `price_clean` (hanya harga observasi valid).

    extend_months: tambah N bulan setelah bulan terakhir (target = NaN) -> dipakai untuk prediksi.
    Kolom hasil: date, geo_id, commodity, adm1_name, target (price_clean), fitur, `eligible`.
    """
    wide = long.pivot_table(index="date", columns=["geo_id", "commodity"], values="price_clean",
                            aggfunc="last", observed=True, dropna=False)
    full_idx = pd.date_range(wide.index.min(), wide.index.max() + pd.DateOffset(months=extend_months),
                             freq="MS")
    wide = wide.reindex(full_idx)
    wide.index.name = "date"

    prev = wide.shift(1)                                   # hanya informasi sebelum bulan target
    feats = {
        "target": wide,
        "price_lag_1": wide.shift(1),
        "price_lag_2": wide.shift(2),
        "price_lag_3": wide.shift(3),
        "price_lag_12": wide.shift(12),
        "rolling_mean_3": prev.rolling(3, min_periods=1).mean(),
        "rolling_mean_6": prev.rolling(6, min_periods=1).mean(),
        "n_obs_last6": prev.notna().astype(float).rolling(6, min_periods=1).sum(),
    }
    frames = {k: v.stack([0, 1], future_stack=True).rename(k) for k, v in feats.items()}
    out = pd.concat(frames.values(), axis=1).reset_index()

    out["mom_1"] = out["price_lag_1"] / out["price_lag_2"] - 1
    out["dev_roll3"] = out["price_lag_1"] / out["rolling_mean_3"] - 1
    out["dev_roll6"] = out["price_lag_1"] / out["rolling_mean_6"] - 1
    out["year"] = out["date"].dt.year
    out["month"] = out["date"].dt.month

    meta = long[["geo_id", "adm1_name"]].drop_duplicates("geo_id")
    out = out.merge(meta, on="geo_id", how="left")
    out["geo_id"] = out["geo_id"].astype(str)
    out["adm1_name"] = out["adm1_name"].astype(str)
    out["commodity"] = out["commodity"].astype(str)
    # syarat prediksi yang valid: harga bulan sebelumnya tersedia & riwayat cukup
    out["eligible"] = out["price_lag_1"].notna() & (out["n_obs_last6"] >= MIN_OBS_LAST6)
    return out.sort_values(["commodity", "geo_id", "date"]).reset_index(drop=True)
