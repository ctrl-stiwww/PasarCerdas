"""Konfigurasi terpusat PasarCerdas. Semua path relatif terhadap folder proyek."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "dataset" / "raw"
PROCESSED_DIR = ROOT / "dataset" / "processed"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
FIG_DIR = RESULTS_DIR / "figures"
ASSETS_DIR = ROOT / "assets"

RAW_ZIP = RAW_DIR / "IDN_RTFP_mkt_2007_2026-11-02.zip"
RAW_CSV_NAME = "IDN_RTFP_mkt_2007_2026-11-02.csv"

LONG_CSV = PROCESSED_DIR / "prices_long.csv"
FEATURES_CSV = PROCESSED_DIR / "features_model.csv"

# kode kolom dataset -> nama tampilan (bahasa Indonesia)
COMMODITIES = {
    "eggs": "Telur",
    "garlic": "Bawang Putih",
    "meat_chicken": "Daging Ayam",
    "oil": "Minyak Nabati",
    "onions": "Bawang Merah",
    "rice": "Beras",
    "sugar": "Gula",
}

SEED = 42

# Pembagian waktu (berdasarkan urutan waktu, bukan acak)
TRAIN_END = "2023-12-01"
VAL_START, VAL_END = "2024-01-01", "2024-12-01"
TEST_START = "2025-01-01"          # akhir test = bulan observasi terakhir di dataset

# Aturan kualitas data
OUTLIER_RATIO_LOW, OUTLIER_RATIO_HIGH = 0.5, 2.0   # harga observasi / estimasi close
MIN_OBS_LAST6 = 3                                  # syarat minimal riwayat (dari 6 bulan terakhir)

# Baris agregat "Market Average" (rata-rata nasional) bukan pasar -> dikeluarkan dari analisis pasar & pemodelan
AGGREGATE_GEO_ID = "gid_idn_national_average"
