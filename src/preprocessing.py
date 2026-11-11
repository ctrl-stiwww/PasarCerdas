"""Preprocessing: wide -> long, penanganan data observasi vs estimasi, flag outlier."""
import numpy as np
import pandas as pd
from .config import (AGGREGATE_GEO_ID, COMMODITIES, OUTLIER_RATIO_LOW, OUTLIER_RATIO_HIGH,
                     LONG_CSV, PROCESSED_DIR)

ID_COLS = ["geo_id", "adm1_name", "adm2_name", "mkt_name", "lat", "lon", "price_date",
           "year", "month", "spatially_interpolated"]


def build_long(raw: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """Ubah dataset wide menjadi long (satu baris = pasar x bulan x komoditas).

    Prinsip metodologis:
    * kolom tanpa prefiks (mis. `rice`)  = harga observasi/mentah  -> dipakai sebagai TARGET & riwayat harga
    * kolom `c_*` (close estimate)       = estimasi model World Bank -> hanya referensi/pembanding,
      TIDAK dianggap observasi.
    * observasi yang rasionya terhadap estimasi di luar [0.5, 2.0] ditandai outlier dan
      dikeluarkan dari pemodelan (data tidak dihapus, hanya diberi flag).
    """
    df = raw.copy()
    df["date"] = pd.to_datetime(df["price_date"])
    n_agg = int((df["geo_id"] == AGGREGATE_GEO_ID).sum())
    df = df[df["geo_id"] != AGGREGATE_GEO_ID]     # baris "Market Average" = agregat nasional, bukan pasar
    if verbose:
        print(f"Baris agregat rata-rata nasional dikeluarkan: {n_agg}")
    n0 = len(df)
    df = df.drop_duplicates(subset=["geo_id", "date"], keep="last")
    if verbose:
        print(f"Duplikasi (geo_id, tanggal) dihapus: {n0 - len(df)}")

    parts = []
    for code, name in COMMODITIES.items():
        p = df[["geo_id", "adm1_name", "adm2_name", "mkt_name", "lat", "lon", "date",
                "spatially_interpolated"]].copy()
        p["commodity"] = code
        p["commodity_name"] = name
        p["price_observed"] = df[code].values
        p["price_estimate"] = df[f"c_{code}"].values
        p["trust_score"] = df[f"trust_{code}"].values
        parts.append(p)
    long = pd.concat(parts, ignore_index=True)

    obs = long["price_observed"].notna()
    valid_price = long["price_observed"] > 0
    ratio = long["price_observed"] / long["price_estimate"]
    outlier = obs & (~valid_price | (ratio < OUTLIER_RATIO_LOW) | (ratio > OUTLIER_RATIO_HIGH))
    long["is_observed"] = obs
    long["is_outlier"] = outlier
    long["price_clean"] = long["price_observed"].where(obs & ~outlier)
    long["data_status"] = np.where(outlier, "outlier_dikecualikan",
                                   np.where(obs, "observasi", "hanya_estimasi"))
    long["year"] = long["date"].dt.year
    long["month"] = long["date"].dt.month
    long = long.sort_values(["commodity", "geo_id", "date"]).reset_index(drop=True)
    if verbose:
        print(f"Baris long: {len(long):,} | observasi: {obs.sum():,} | "
              f"outlier ditandai: {outlier.sum():,} | hanya estimasi: {(~obs).sum():,}")
    return long


def save_long(long: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = long.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(LONG_CSV, index=False, float_format="%.2f")


def last_observed_month(long: pd.DataFrame) -> pd.Timestamp:
    """Bulan terakhir yang memiliki setidaknya satu harga observasi valid."""
    return long.loc[long["price_clean"].notna(), "date"].max()
