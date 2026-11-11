"""Pemuatan dataset mentah dan dataset hasil preprocessing."""
import pandas as pd
from .config import RAW_ZIP, RAW_CSV_NAME, LONG_CSV


def load_raw() -> pd.DataFrame:
    """Baca CSV mentah langsung dari ZIP World Bank (tanpa perlu ekstraksi manual)."""
    if not RAW_ZIP.exists():
        raise FileNotFoundError(
            f"Dataset mentah tidak ditemukan: {RAW_ZIP}\n"
            "Letakkan file IDN_RTFP_mkt_2007_2026-11-02.zip di folder dataset/raw/."
        )
    return pd.read_csv(RAW_ZIP, compression="zip")


def load_long() -> pd.DataFrame:
    """Baca dataset long format hasil preprocessing."""
    if not LONG_CSV.exists():
        raise FileNotFoundError(
            f"Dataset hasil preprocessing tidak ditemukan: {LONG_CSV}\n"
            "Jalankan 'python retrain.py' untuk membuatnya."
        )
    df = pd.read_csv(
        LONG_CSV,
        parse_dates=["date"],
        dtype={"geo_id": "category", "adm1_name": "category", "adm2_name": "category",
               "mkt_name": "category", "commodity": "category", "commodity_name": "category",
               "data_status": "category"},
    )
    return df
