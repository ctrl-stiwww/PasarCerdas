# PasarCerdas — Indonesia Food Price Intelligence

**Pengembangan Sistem Prediksi dan Analisis Harga Komoditas Pangan di Indonesia Menggunakan Machine Learning.**

PasarCerdas adalah aplikasi web lokal (Streamlit) untuk memantau, membandingkan, menganalisis, dan memprediksi harga bulan berikutnya
untuk tujuh komoditas pangan (telur, bawang putih, daging ayam, minyak nabati, bawang merah, beras, gula) di 222 pasar Indonesia,
berdasarkan dataset World Bank *Monthly Food Price Estimates by Product and Market – Indonesia* (RTFP).

## 1. Keputusan metodologis penting (baca dulu)
| Temuan pada dataset | Keputusan |
|---|---|
| Kolom tanpa prefiks (`rice`, `eggs`, …) = harga **observasi**; `c_*` = *close estimate* (estimasi model World Bank, terisi penuh). Hanya ±32% sel adalah observasi. | **Target & riwayat harga = harga observasi.** `c_*` hanya referensi, tidak dianggap observasi. |
| Dataset berisi 223 `geo_id`: 222 pasar + 1 baris agregat "Market Average" (rata-rata nasional). Agregat ini **bukan pasar** dan dikeluarkan dari analisis & pemodelan. Observasi pasar hanya ada sejak 2016; padat hanya Jan 2020–Sep 2026 (2016 sebagian, 2017 nyaris kosong, 2018–2019 tidak ada). Oct–Nov 2026 tidak punya observasi (*last survey point* = Sep 2026). | Baris model = target observasi **dan** harga bulan sebelumnya observasi **dan** ≥3 observasi dari 6 bulan terakhir. Prediksi website = **Oktober 2026**. |
| 30 observasi dengan rasio terhadap estimasi di luar 0,5×–2× | Ditandai `is_outlier`, dikeluarkan dari pemodelan, tidak dihapus dari dataset. |
| `spatially_interpolated` = 0 di semua baris | Tidak ada interpolasi spasial yang perlu dipisah. |

Split waktu (bukan acak): **Train ≤ Des 2023 · Validasi 2024 · Test Jan 2025–Sep 2026**. Seleksi model/hyperparameter hanya memakai validasi.
Catatan: arti kolom diverifikasi lewat katalog data World Bank dan pemeriksaan empiris (c_ = observasi pada ±90% kasus observasi).

## 2. Fitur website
Navigasi menu di bagian atas dengan bahasa yang mudah dipahami: Beranda · Cek Harga (filter provinsi→kab/kota→pasar→periode) · Prediksi (3 langkah, horizon 1–3 bulan) · Bandingkan Wilayah (termasuk peta) · Tren · Seberapa Akurat? (evaluasi model). Palet hijau–biru, kartu interaktif, dan kotak penjelasan "Cara membaca".

## 3. Struktur folder
```
PasarCerdas/
├── app.py                 entry point Streamlit (navigasi + tema)
├── run.bat                peluncur otomatis Windows
├── retrain.py             jalankan ulang seluruh pipeline
├── requirements.txt
├── dataset/raw/           ZIP asli World Bank
├── dataset/processed/     prices_long.csv (long format), features_model.csv
├── notebooks/             01 audit/EDA · 02 preprocessing · 03 fitur · 04 training · 05 evaluasi
├── src/                   config, data_loader, preprocessing, feature_engineering, training,
│                          evaluation, prediction, eda, pipeline, ui
├── pages/                 halaman website (dashboard, harga_pangan, prediksi, perbandingan, analisis_tren, evaluasi_model)
├── models/                best_model.pkl, preprocessing.pkl, model_metadata.json, alternatif/
├── results/               evaluation_*.csv, prediction_results.csv, eda_summary.json, figures/
├── assets/style.css       CSS kustom
└── tests/test_all.py      uji akhir
```

## 4. Persyaratan sistem
Windows 10/11 64-bit, **Python 3.11–3.13**, RAM ≥ 4 GB, internet saat instalasi pertama (dan untuk font Google serta peta OpenStreetMap).

## 5. Menjalankan (Windows)
1. Instal Python dari https://www.python.org/downloads/ — centang **Add python.exe to PATH**.
2. Klik kanan `PasarCerdas.zip` → **Extract All…** (ekstrak penuh, jangan jalankan dari dalam ZIP).
3. Buka folder `PasarCerdas`, **klik dua kali `run.bat`**. Pertama kali akan membuat `.venv` dan menginstal dependensi (beberapa menit); run berikutnya langsung jalan.
4. Buka alamat yang tampil (biasanya http://localhost:8501).
5. Hentikan server: tekan **Ctrl+C** di jendela CMD (atau tutup jendela).

### Manual via CMD
```bat
cd path\ke\PasarCerdas
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## 6. Notebook
```bat
.venv\Scripts\activate
jupyter notebook notebooks
```
Jalankan berurutan 01 → 05. Notebook 04 melatih ulang semua eksperimen (±3–5 menit) tanpa menimpa `models/`.

## 7. Melatih ulang model
```bat
.venv\Scripts\activate
python retrain.py
```
Menjalankan: preprocessing → EDA → fitur → 12 eksperimen (+tuning di validasi) → evaluasi → penyimpanan model & metadata. `python retrain.py --quick` untuk uji cepat tanpa tuning (jangan dipakai untuk hasil akhir).

## 8. Mengganti dataset
Letakkan ZIP baru di `dataset/raw/`, ubah `RAW_ZIP` dan `RAW_CSV_NAME` di `src/config.py` (format kolom harus sama dengan RTFP Indonesia; sesuaikan `TRAIN_END`, `VAL_*`, `TEST_START` bila rentang data berubah), lalu jalankan `python retrain.py`.

## 9. Troubleshooting
| Masalah | Solusi |
|---|---|
| `Python belum terinstal` | Instal Python 3.11–3.13, centang *Add to PATH*, buka ulang CMD. |
| Versi Python tidak didukung | Gunakan 3.11–3.13 (pustaka dipin ke scikit-learn 1.9.1 / xgboost 3.2.0). |
| Instalasi gagal | Periksa internet/proxy; hapus folder `.venv` lalu jalankan `run.bat` lagi. |
| `Berkas penting tidak ditemukan` | ZIP belum diekstrak penuh; ekstrak ulang. |
| Port 8501 terpakai | `python -m streamlit run app.py --server.port 8502` |
| Peta/font tidak tampil | Butuh internet; fitur lain tetap berjalan. |
| Error memuat model | Versi scikit-learn/xgboost berbeda dari `requirements.txt`; instal ulang requirements atau `python retrain.py`. |

## 10. Keterbatasan
* Data observasi nyata terbatas (±2020 ke atas); model dilatih pada ±4 tahun riwayat.
* Prediksi hanya 1 bulan ke depan dan hanya untuk pasar yang punya observasi pada bulan terakhir data.
* Hasil di bawah ini dilaporkan apa adanya — lihat bagian hasil: baseline Naive sangat kuat untuk komoditas stabil.
* Model dilatih sampai 2023 (seperti yang dievaluasi) dan tidak dilatih ulang otomatis dengan data terbaru.

## 11. Pengujian
`python tests/test_all.py` (impor modul, memuat model, prediksi valid tanpa NaN, setiap halaman & filter).

## 12. Hasil (dari `results/evaluation_metrics.csv`)
Lihat halaman **Evaluasi Model** atau `results/training_log.txt`.
