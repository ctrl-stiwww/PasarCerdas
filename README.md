# PasarCerdas — Indonesia Food Price Intelligence

**Pengembangan Sistem Prediksi dan Analisis Harga Komoditas Pangan di Indonesia Menggunakan Machine Learning**

<p align="center">
  <a href="https://pasarcerdas.streamlit.app/">
    <strong>🌐 Buka Aplikasi PasarCerdas</strong>
  </a>
  &nbsp; | &nbsp;
  <a href="https://github.com/ctrl-stiwww/PasarCerdas/">
    <strong>GitHub Repository</strong>
  </a>
</p>

PasarCerdas merupakan aplikasi web berbasis Streamlit untuk memantau, membandingkan, menganalisis, dan memprediksi harga komoditas pangan di Indonesia. Aplikasi ini menggunakan data historis World Bank *Monthly Food Price Estimates by Product and Market – Indonesia* (RTFP).

Sistem mencakup **7 komoditas pangan** (telur, bawang putih, daging ayam, minyak nabati, bawang merah, beras, dan gula) yang tersebar di **222 pasar** dalam dataset.

---

## 1. Keputusan Metodologis

Beberapa keputusan penting dalam pengolahan dataset:

| Temuan pada Dataset | Keputusan |
|---|---|
| Kolom tanpa prefiks (`rice`, `eggs`, dan lainnya) merupakan harga observasi, sedangkan `c_*` merupakan *close estimate* dari model World Bank. | Target dan riwayat harga menggunakan harga observasi. `c_*` hanya digunakan sebagai referensi. |
| Dataset memiliki 223 `geo_id`, terdiri dari 222 pasar dan 1 agregat nasional (*Market Average*). | Baris agregat nasional dikeluarkan dari analisis dan pemodelan. |
| Observasi pasar tersedia sejak 2016, tetapi data lebih padat pada Januari 2020–September 2026. | Pemodelan menggunakan data observasi yang memenuhi kriteria kelayakan. |
| Oktober–November 2026 belum memiliki observasi aktual. | Prediksi website ditujukan untuk Oktober 2026. |
| Terdapat 30 observasi dengan rasio terhadap estimasi di luar rentang 0,5×–2×. | Data ditandai sebagai `is_outlier` dan dikeluarkan dari pemodelan, tetapi tidak dihapus dari dataset. |
| `spatially_interpolated` bernilai 0 pada seluruh baris. | Tidak ada interpolasi spasial yang perlu dipisahkan. |

**Kriteria data untuk pemodelan:**
- Target harga merupakan harga observasi.
- Harga bulan sebelumnya juga harus berupa observasi.
- Minimal terdapat 3 observasi dalam 6 bulan terakhir.

**Pembagian data berdasarkan waktu:**

| Dataset | Periode |
|---|---|
| Training | Hingga Desember 2023 |
| Validation | Januari–Desember 2024 |
| Testing | Januari 2025–September 2026 |

Seleksi model dan hyperparameter hanya menggunakan data validasi untuk menghindari penggunaan data testing dalam proses pemilihan model.

*Catatan: Interpretasi kolom diverifikasi melalui katalog data World Bank dan pemeriksaan empiris.*

---

## 2. Fitur Website

PasarCerdas menyediakan beberapa halaman utama dengan navigasi yang dirancang agar mudah digunakan oleh masyarakat umum.

| Halaman | Fitur |
|---|---|
| Beranda | Ringkasan informasi dan kondisi harga pangan. |
| Cek Harga | Melihat harga berdasarkan provinsi, kabupaten/kota, pasar, dan periode. |
| Prediksi | Memperkirakan harga komoditas pada periode berikutnya. |
| Bandingkan Wilayah | Membandingkan harga antarwilayah, termasuk melalui peta. |
| Tren | Menganalisis perkembangan dan pola perubahan harga. |
| Seberapa Akurat? | Melihat hasil evaluasi dan performa model Machine Learning. |

Aplikasi menggunakan tampilan interaktif dengan palet warna hijau–biru, visualisasi data, kartu informasi, serta penjelasan untuk membantu pengguna memahami hasil yang ditampilkan.

---

## 3. Struktur Folder

```text
PasarCerdas/
│
├── app.py
├── run.bat
├── retrain.py
├── requirements.txt
│
├── assets/
│   └── style.css
│
├── dataset/
│   ├── raw/
│   └── processed/
│       ├── prices_long.csv
│       └── features_model.csv
│
├── notebooks/
│   ├── 01_dataset_audit_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_model_evaluation.ipynb
│
├── src/
│   ├── config.py
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── training.py
│   ├── evaluation.py
│   ├── prediction.py
│   ├── eda.py
│   ├── pipeline.py
│   └── ui/
│
├── pages/
│   ├── dashboard.py
│   ├── harga_pangan.py
│   ├── prediksi.py
│   ├── perbandingan.py
│   ├── analisis_tren.py
│   └── evaluasi_model.py
│
├── models/
│   ├── best_model.pkl
│   ├── preprocessing.pkl
│   ├── model_metadata.json
│   └── alternatif/
│
├── results/
│   ├── evaluation_*.csv
│   ├── prediction_results.csv
│   ├── eda_summary.json
│   └── figures/
│
└── tests/
    └── test_all.py
```

---

## 4. Persyaratan Sistem

| Komponen | Persyaratan |
|---|---|
| Sistem Operasi | Windows 10/11 64-bit |
| Python | 3.11–3.13 |
| RAM | Minimal 4 GB |
| Koneksi Internet | Dibutuhkan saat instalasi pertama, serta untuk font Google dan peta OpenStreetMap. |

---

## 5. Cara Menjalankan Aplikasi

### A. Instalasi

1. Download dan instal Python melalui [python.org](https://www.python.org/downloads/).
2. Saat instalasi, centang opsi **Add python.exe to PATH**.
3. Download repository melalui GitHub atau gunakan tombol **Code → Download ZIP**.
4. Ekstrak file ZIP secara penuh.
5. Buka folder `PasarCerdas`.
6. Jalankan aplikasi dengan klik dua kali file `run.bat`.

Pada proses pertama, sistem akan membuat virtual environment `.venv` dan menginstal seluruh dependensi yang diperlukan. Proses ini membutuhkan koneksi internet.

### B. Membuka Aplikasi

Setelah proses instalasi selesai, Streamlit akan berjalan secara otomatis.

Buka alamat berikut melalui browser:

```text
http://localhost:8501
```

Untuk menghentikan aplikasi, tekan `Ctrl + C` pada jendela CMD atau tutup jendela tersebut.

### C. Menjalankan Secara Manual melalui CMD

```bat
cd path\ke\PasarCerdas

py -3 -m venv .venv

.venv\Scripts\activate

python -m pip install -r requirements.txt

python -m streamlit run app.py
```

---

## 6. Menjalankan Notebook

Notebook digunakan untuk melihat tahapan pengolahan data, eksplorasi, pelatihan, dan evaluasi model.

Aktifkan virtual environment:

```bat
.venv\Scripts\activate
```

Jalankan Jupyter Notebook:

```bat
jupyter notebook notebooks
```

Jalankan notebook secara berurutan:

1. `01_dataset_audit_eda.ipynb`
2. `02_preprocessing.ipynb`
3. `03_feature_engineering.ipynb`
4. `04_model_training.ipynb`
5. `05_model_evaluation.ipynb`

Notebook 04 menjalankan eksperimen pelatihan ulang model, termasuk tuning hyperparameter, tanpa menimpa file model pada folder `models/`.

---

## 7. Melatih Ulang Model

Untuk menjalankan kembali seluruh pipeline Machine Learning:

```bat
.venv\Scripts\activate

python retrain.py
```

Pipeline mencakup:

1. Preprocessing data.
2. Exploratory Data Analysis (EDA).
3. Feature Engineering.
4. Pelatihan 12 eksperimen model beserta tuning hyperparameter.
5. Evaluasi model.
6. Penyimpanan model dan metadata.

Untuk menjalankan pengujian cepat tanpa tuning:

```bat
python retrain.py --quick
```

**Catatan:** Mode `--quick` hanya digunakan untuk pengujian awal, bukan untuk menghasilkan hasil evaluasi akhir.

---

## 8. Mengganti Dataset

Untuk menggunakan dataset baru:

1. Letakkan file ZIP dataset di folder `dataset/raw/`.
2. Sesuaikan konfigurasi `RAW_ZIP` dan `RAW_CSV_NAME` pada `src/config.py`.
3. Pastikan format kolom dataset sesuai dengan RTFP Indonesia.
4. Sesuaikan periode training, validation, dan testing jika rentang data berubah.
5. Jalankan kembali pipeline:

```bat
python retrain.py
```

---

## 9. Troubleshooting

| Masalah | Solusi |
|---|---|
| Python belum terinstal | Instal Python 3.11–3.13 dan aktifkan opsi Add to PATH. |
| Versi Python tidak didukung | Gunakan Python 3.12.x |
| Instalasi dependensi gagal | Periksa koneksi internet atau proxy. Hapus folder `.venv`, lalu jalankan `run.bat` kembali. |
| Berkas penting tidak ditemukan | Pastikan ZIP sudah diekstrak secara penuh. |
| Port 8501 sedang digunakan | Jalankan Streamlit menggunakan port alternatif. |
| Peta atau font tidak tampil | Pastikan perangkat terhubung ke internet. |
| Error saat memuat model | Pastikan versi library sesuai dengan `requirements.txt`, atau jalankan ulang training. |

Untuk menggunakan port alternatif:

```bat
python -m streamlit run app.py --server.port 8502
```

---

## 10. Keterbatasan Sistem

- Data observasi aktual memiliki keterbatasan cakupan waktu dan lebih padat mulai sekitar tahun 2020.
- Model dilatih menggunakan data historis yang memenuhi kriteria kelayakan.
- Prediksi ditujukan untuk satu bulan ke depan dan hanya tersedia untuk pasar yang memiliki observasi pada periode terakhir data.
- Performa model berbeda pada setiap komoditas. Naive Forecast masih menjadi baseline yang kuat untuk beberapa komoditas dengan pola harga relatif stabil.
- Model yang tersedia tidak otomatis dilatih ulang menggunakan data terbaru.
- Data merupakan estimasi harga berdasarkan dataset World Bank, bukan harga resmi real-time seluruh pasar Indonesia.

---

## 11. Pengujian Sistem

Untuk menjalankan pengujian:

```bat
python tests/test_all.py
```

Pengujian mencakup:
- Import modul.
- Pemuatan model.
- Validasi hasil prediksi agar tidak menghasilkan nilai NaN.
- Pemeriksaan halaman aplikasi dan filter.

---

## 12. Hasil Evaluasi Model

Hasil evaluasi dapat dilihat melalui halaman **Seberapa Akurat?** pada aplikasi atau file berikut:

```text
results/evaluation_metrics.csv
results/training_log.txt
```

Evaluasi dilakukan menggunakan metrik:
- **MAE (Mean Absolute Error):** mengukur rata-rata kesalahan absolut prediksi.
- **RMSE (Root Mean Squared Error):** memberikan penalti lebih besar pada kesalahan prediksi yang besar.
- **MAPE (Mean Absolute Percentage Error):** mengukur rata-rata kesalahan dalam persentase.
- **R² (R-squared):** mengukur kemampuan model dalam menjelaskan variasi target.

---

## 13. Sumber Data

**World Bank — Monthly Food Price Estimates by Product and Market (Indonesia)**

[World Bank Microdata Library](https://microdata.worldbank.org/catalog/6166/get-microdata)

Dataset digunakan sebagai sumber data historis harga komoditas pangan untuk proses eksplorasi, pengolahan, pelatihan, dan evaluasi model Machine Learning.

---

<p align="center">
  <strong>PasarCerdas — Indonesia Food Price Intelligence</strong><br>
  Mengolah data historis menjadi informasi harga pangan yang lebih mudah dipahami.
</p>
