"""Metrik evaluasi regresi."""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, float); y_pred = np.asarray(y_pred, float)
    nz = y_true != 0   # MAPE aman: harga pangan selalu > 0 (nol dikecualikan jika ada)
    return {
        "n": int(len(y_true)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else float("nan"),
        "MAPE_%": float(np.mean(np.abs((y_true[nz] - y_pred[nz]) / y_true[nz])) * 100),
    }


def metrics_table(df: pd.DataFrame, group_cols, y="y_true", pred_cols=()) -> pd.DataFrame:
    rows = []
    for keys, g in df.groupby(group_cols, observed=True) if group_cols else [((), df)]:
        keys = keys if isinstance(keys, tuple) else (keys,)
        for pc in pred_cols:
            m = regression_metrics(g[y], g[pc])
            rows.append({**dict(zip(group_cols or [], keys)), "model": pc, **m})
    return pd.DataFrame(rows)
