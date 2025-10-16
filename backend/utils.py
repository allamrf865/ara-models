import numpy as np, pandas as pd, xgboost as xgb

def norm01(a):
    lo = float(np.min(a)); hi = float(np.max(a))
    return (a - lo) / (hi - lo + 1e-12) if hi > lo else np.zeros_like(a, dtype=float)

def predict_mean(models, X, calibrator=None):
    dm = xgb.DMatrix(X)
    p = np.mean(np.vstack([m.predict(dm) for m in models]), axis=0)
    p = norm01(p)
    if calibrator is not None:
        p = calibrator.transform(p)
    return p

def enrich_vol_rank(raw_latest: pd.DataFrame) -> pd.DataFrame:
    vr = raw_latest[["Ticker","Volume"]].copy()
    vr["vol_rank_day"] = vr["Volume"].rank(pct=True)
    return vr[["Ticker","vol_rank_day"]]

def screen(out: pd.DataFrame, exclude_pemantauan: bool, liq_floor: float) -> pd.DataFrame:
    mask_board = True
    if "Papan" in out.columns and exclude_pemantauan:
        mask_board = out["Papan"].fillna("").str.lower().ne("pemantauan khusus")
    mask_liq = out["vol_rank_day"].fillna(0) >= float(liq_floor)
    return out[mask_board & mask_liq]
