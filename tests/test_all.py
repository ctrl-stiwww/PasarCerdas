"""Uji akhir PasarCerdas: python tests/test_all.py"""
import sys, importlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from streamlit.testing.v1 import AppTest

ok = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name, extra); ok.append(cond)

# 1. import semua modul
for m in ["src.config", "src.data_loader", "src.preprocessing", "src.feature_engineering", "src.training",
          "src.evaluation", "src.prediction", "src.ui", "src.pipeline", "pages.dashboard", "pages.harga_pangan",
          "pages.prediksi", "pages.perbandingan", "pages.analisis_tren", "pages.evaluasi_model"]:
    importlib.import_module(m)
check("import semua modul", True)

# 2. model & prediksi
from src.prediction import list_models, load_bundle, predict_next, InsufficientHistory
from src.data_loader import load_long
long = load_long()
for label, path in list_models().items():
    b = load_bundle(path); n = bad = 0; skipped = 0
    sample = long[(long.date == "2026-09-01") & long.price_clean.notna()].sample(120, random_state=1)
    for _, r in sample.iterrows():
        try:
            p = predict_next(b, long, r.geo_id, r.commodity)
            n += 1; bad += (not np.isfinite(p["prediction"])) or p["prediction"] <= 0 or abs(p["change_pct"]) > 60
        except InsufficientHistory:
            skipped += 1
    check(f"prediksi valid: {label}", n > 50 and bad == 0, f"(ok={n}, ditolak={skipped}, tidak valid={bad})")

# 3. halaman Streamlit
def run_page(mod, steps=None):
    at = AppTest.from_string(f"import sys; sys.path.insert(0, r'{ROOT}')\nfrom pages import {mod}\n{mod}.render()",
                             default_timeout=120).run()
    if steps: at = steps(at)
    return at

for mod in ["dashboard", "harga_pangan", "perbandingan", "analisis_tren", "evaluasi_model", "prediksi"]:
    at = run_page(mod); check(f"halaman {mod} dapat dibuka", not at.exception, str([e.value for e in at.exception]))

def filt(at):
    at.selectbox(key="hp_com").select("Beras").run()
    at.selectbox(key="hp_prov").select("JAWA BARAT").run()
    return at
at = run_page("harga_pangan", filt)
check("filter Informasi Harga saling terhubung", not at.exception and len(at.selectbox) >= 4)

def pred(at):
    at.button[0].click().run(); return at
at = run_page("prediksi", pred)
def pred3(at):
    at.session_state["pr_hor"] = 3; at.button[0].click().run(); return at
at3 = run_page("prediksi", pred3)
check("prediksi horizon 3 bulan", not at3.exception and any("bertahap" in m.value for m in at3.markdown), str([e.value for e in at3.exception]))
check("tombol prediksi menghasilkan output", not at.exception and any("Perkiraan harga" in m.value for m in at.markdown),
      str([e.value for e in at.exception]))
at = run_page("perbandingan", lambda a: a.selectbox(key="pb_com").select("Telur").run())
check("filter Perbandingan Wilayah", not at.exception)
at = run_page("analisis_tren", lambda a: a.multiselect(key="tr_sel").set_value(["Beras", "Gula"]).run())
check("filter Analisis Tren", not at.exception)

full = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120).run()
check("app.py (navigasi penuh) berjalan", not full.exception)
print("\nHASIL:", sum(ok), "/", len(ok), "lulus"); sys.exit(0 if all(ok) else 1)
