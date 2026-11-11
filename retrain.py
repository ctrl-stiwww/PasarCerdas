"""Latih ulang seluruh pipeline PasarCerdas: python retrain.py  (opsi --quick untuk uji cepat)."""
import sys, time
from pathlib import Path
from src.pipeline import run_all
from src.config import RESULTS_DIR

if __name__ == "__main__":
    t0 = time.time()
    lines = []
    def log(m):
        print(m, flush=True); lines.append(str(m))
    meta, res = run_all(log=log, quick="--quick" in sys.argv)
    log(f"Selesai dalam {time.time() - t0:.0f} detik")
    (RESULTS_DIR / "training_log.txt").write_text("\n".join(lines), encoding="utf-8")
