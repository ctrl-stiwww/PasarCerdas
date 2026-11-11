@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title PasarCerdas
echo ==============================================
echo   PasarCerdas - Indonesia Food Price Intelligence
echo ==============================================

rem --- 1. Cek Python (py launcher atau python)
set "PYCMD="
where py >nul 2>nul && (
  for %%V in (3.13 3.12 3.11) do (
    if not defined PYCMD (
      py -%%V -c "import sys" >nul 2>nul && set "PYCMD=py -%%V"
    )
  )
)
if not defined PYCMD (where python >nul 2>nul && set "PYCMD=python")
if not defined PYCMD (
  echo [ERROR] Python belum terinstal atau belum masuk PATH.
  echo Instal Python 3.11-3.13 dari https://www.python.org/downloads/ lalu centang "Add python.exe to PATH".
  pause & exit /b 1
)
%PYCMD% -c "import sys; sys.exit(0 if (3,11)<=sys.version_info[:2]<=(3,13) else 1)" >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Versi Python tidak didukung. Gunakan Python 3.11, 3.12, atau 3.13 (Python 3.14 belum didukung).
  %PYCMD% --version
  pause & exit /b 1
)

rem --- 2. Cek berkas yang diperlukan
for %%F in (app.py requirements.txt models\best_model.pkl models\model_metadata.json dataset\processed\prices_long.csv assets\style.css) do (
  if not exist "%%F" (
    echo [ERROR] Berkas penting tidak ditemukan: %%F
    echo Pastikan ZIP sudah diekstrak seluruhnya. Untuk membuat ulang model/dataset olahan: python retrain.py
    pause & exit /b 1
  )
)

rem --- 3. Virtual environment
if not exist ".venv\Scripts\activate.bat" (
  echo [INFO] Membuat virtual environment .venv ...
  %PYCMD% -m venv .venv
  if errorlevel 1 ( echo [ERROR] Gagal membuat virtual environment. & pause & exit /b 1 )
)
call ".venv\Scripts\activate.bat"

rem --- 4. Instal dependensi hanya jika belum lengkap / requirements berubah
set "STAMP=.venv\.deps_installed"
python -c "import streamlit, sklearn, xgboost, plotly, pandas, joblib, matplotlib" >nul 2>nul
set "HAVE=%errorlevel%"
if not "%HAVE%"=="0" ( if exist "%STAMP%" del "%STAMP%" )
if not exist "%STAMP%" (
  echo [INFO] Menginstal dependensi ^(pertama kali, butuh internet, beberapa menit^) ...
  python -m pip install --upgrade pip >nul 2>nul
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Instalasi dependensi gagal. Periksa koneksi internet lalu jalankan run.bat lagi.
    pause & exit /b 1
  )
  echo ok> "%STAMP%"
) else (
  echo [INFO] Dependensi sudah terinstal - dilewati.
)

rem --- 5. Jalankan Streamlit
echo.
echo [INFO] Menjalankan PasarCerdas. Buka alamat yang tampil di bawah (biasanya http://localhost:8501).
echo        Tekan Ctrl+C untuk menghentikan server.
echo.
python -m streamlit run app.py --browser.gatherUsageStats false
if errorlevel 1 (
  echo [ERROR] Streamlit gagal berjalan. Lihat pesan di atas.
  pause & exit /b 1
)
endlocal
