"""Training, tuning, evaluasi, dan penyimpanan model PasarCerdas.

Eksperimen:
  strategi  : global (1 model utk 7 komoditas) | separate (1 model per komoditas)
  target    : level  -> memprediksi harga langsung
              ratio  -> memprediksi log(harga / harga_lag_1), lalu dikonversi kembali ke Rupiah
  algoritma : linear (Linear Regression) | rf (Random Forest) | xgb (XGBoost)
Seleksi model & hyperparameter memakai VALIDASI (2024). Data TEST (2025-2026) hanya untuk pelaporan.
"""
import json, time, platform, itertools
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
import sklearn, xgboost
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from xgboost import XGBRegressor

from .config import (SEED, TRAIN_END, VAL_START, VAL_END, TEST_START, COMMODITIES,
                     MODELS_DIR, RESULTS_DIR)
from .evaluation import regression_metrics, metrics_table
from .feature_engineering import CATEGORICAL, NUMERIC, FEATURES

ALGO_NAMES = {"linear": "Linear Regression", "rf": "Random Forest", "xgb": "XGBoost"}

RF_GRID = [dict(n_estimators=100, max_depth=12, min_samples_leaf=10, max_features=0.6),
           dict(n_estimators=100, max_depth=18, min_samples_leaf=5, max_features=0.6)]
XGB_GRID = [dict(n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8),
            dict(n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8),
            dict(n_estimators=600, max_depth=8, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8)]


# ----------------------------------------------------------------------------- data
def make_splits(feat: pd.DataFrame):
    """Pisahkan berdasarkan WAKTU. Hanya baris dengan target observasi & fitur eligible."""
    d = feat[feat["target"].notna() & feat["eligible"]].copy()
    train = d[d["date"] <= TRAIN_END]
    val = d[(d["date"] >= VAL_START) & (d["date"] <= VAL_END)]
    test = d[d["date"] >= TEST_START]
    return train, val, test


def to_target(df: pd.DataFrame, mode: str) -> np.ndarray:
    return df["target"].values if mode == "level" else np.log(df["target"].values / df["price_lag_1"].values)


def to_price(df: pd.DataFrame, yhat: np.ndarray, mode: str) -> np.ndarray:
    return yhat if mode == "level" else df["price_lag_1"].values * np.exp(yhat)


# ----------------------------------------------------------------------------- pipeline
def make_pipeline(algo: str, params: dict | None = None) -> Pipeline:
    params = params or {}
    if algo == "linear":
        pre = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), NUMERIC),
        ])
        model = LinearRegression()
    else:
        ord_enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        num = (Pipeline([("imp", SimpleImputer(strategy="median"))]) if algo == "rf" else "passthrough")
        pre = ColumnTransformer([
            ("com", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["commodity"]),
            ("ord", ord_enc, ["geo_id", "adm1_name"]),
            ("num", num, NUMERIC),
        ])
        if algo == "rf":
            model = RandomForestRegressor(random_state=SEED, n_jobs=-1, **params)
        else:
            model = XGBRegressor(random_state=SEED, n_jobs=-1, tree_method="hist", verbosity=0, **params)
    return Pipeline([("prep", pre), ("model", model)])


def fit_strategy(train: pd.DataFrame, algo, params, strategy, mode) -> dict:
    """Latih model; kembalikan dict {kunci: pipeline}. kunci='global' atau kode komoditas."""
    models = {}
    groups = {"global": train} if strategy == "global" else {c: train[train.commodity == c] for c in COMMODITIES}
    for key, g in groups.items():
        pipe = make_pipeline(algo, params)
        pipe.fit(g[FEATURES], to_target(g, mode))
        models[key] = pipe
    return models


def predict_strategy(models: dict, df: pd.DataFrame, strategy, mode) -> np.ndarray:
    out = np.full(len(df), np.nan)
    if strategy == "global":
        out[:] = to_price(df, models["global"].predict(df[FEATURES]), mode)
    else:
        for c, pipe in models.items():
            idx = (df["commodity"] == c).values
            if idx.any():
                sub = df[idx]
                out[idx] = to_price(sub, pipe.predict(sub[FEATURES]), mode)
    return out


# ----------------------------------------------------------------------------- experiment
def run_experiments(feat: pd.DataFrame, log=print, quick: bool = False):
    train, val, test = make_splits(feat)
    log(f"Split -> train {len(train):,} ({train.date.min().date()}..{train.date.max().date()}) | "
        f"val {len(val):,} ({val.date.min().date()}..{val.date.max().date()}) | "
        f"test {len(test):,} ({test.date.min().date()}..{test.date.max().date()})")

    results, preds_val, preds_test, store = [], {}, {}, {}
    best_params = {}
    for mode, strategy in itertools.product(["level", "ratio"], ["global", "separate"]):
        for algo in ["linear", "rf", "xgb"]:
            grid = {"linear": [{}], "rf": RF_GRID, "xgb": XGB_GRID}[algo]
            if quick: grid = grid[:1]
            if strategy == "separate" and algo != "linear":
                grid = [best_params[(mode, algo)]]      # hyperparameter dari tuning model global
            best = None
            for params in grid:
                t0 = time.time()
                models = fit_strategy(train, algo, params, strategy, mode)
                pv = predict_strategy(models, val, strategy, mode)
                mae_v = float(np.mean(np.abs(val["target"].values - pv)))
                log(f"  [{mode:5s}|{strategy:8s}|{algo:6s}] {params} val MAE={mae_v:,.1f} ({time.time()-t0:.0f}s)")
                if best is None or mae_v < best[0]:
                    best = (mae_v, params, models, pv)
            mae_v, params, models, pv = best
            if strategy == "global": best_params[(mode, algo)] = params
            name = f"{ALGO_NAMES[algo]} | {strategy} | {mode}"
            pt = predict_strategy(models, test, strategy, mode)
            preds_val[name], preds_test[name] = pv, pt
            store[name] = dict(algo=algo, strategy=strategy, mode=mode, params=params, models=models)
            for split, df_, p in (("validation", val, pv), ("test", test, pt)):
                results.append(dict(model=name, algo=ALGO_NAMES[algo], strategy=strategy, target_mode=mode,
                                    split=split, params=json.dumps(params),
                                    **regression_metrics(df_["target"], p)))
    # baseline naive
    for split, df_ in (("validation", val), ("test", test)):
        preds = df_["price_lag_1"].values
        results.append(dict(model="Naive Forecast", algo="Naive", strategy="-", target_mode="-",
                            split=split, params="{}", **regression_metrics(df_["target"], preds)))
    preds_val["Naive Forecast"] = val["price_lag_1"].values
    preds_test["Naive Forecast"] = test["price_lag_1"].values
    return train, val, test, pd.DataFrame(results), preds_val, preds_test, store


def select_best(res: pd.DataFrame) -> str:
    """Model terbaik = MAE validasi terendah (test tidak dipakai untuk seleksi)."""
    v = res[(res.split == "validation") & (res.model != "Naive Forecast")]
    return v.sort_values("MAE").iloc[0]["model"]


# ----------------------------------------------------------------------------- saving
def library_versions() -> dict:
    return {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
            "xgboost": xgboost.__version__, "pandas": pd.__version__, "numpy": np.__version__,
            "joblib": joblib.__version__}


def make_bundle(entry: dict, name: str) -> dict:
    return {"name": name, "algo": entry["algo"], "algo_name": ALGO_NAMES[entry["algo"]],
            "strategy": entry["strategy"], "target_mode": entry["mode"], "params": entry["params"],
            "models": entry["models"], "features": FEATURES, "categorical": CATEGORICAL,
            "numeric": NUMERIC, "commodities": list(COMMODITIES), "seed": SEED}
