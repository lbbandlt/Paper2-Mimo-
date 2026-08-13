"""100-km buffered bulk-density ablation and grouped permutation importance."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.neighbors import BallTree
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


OFFSETS = [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)]
DEPTHS = ["0-20cm", "20-50cm", "50-100cm", "100-200cm"]
BUFFER_KM = 100
CONTINUOUS = [
    "BD_g_cm3", "pH", "Sand_%", "Silt_%", "Clay_%", "DEM_m", "NDVI",
    "MAT_°C", "MAP_mm", "PET_mm", "AI", "depth_mid", "depth_thickness",
]
CATEGORICAL = ["CLCD"]
GROUPS = {
    "bulk_density": ["BD_g_cm3"],
    "soil_texture": ["Sand_%", "Silt_%", "Clay_%"],
    "soil_pH": ["pH"],
    "climate": ["MAT_°C", "MAP_mm", "PET_mm", "AI"],
    "vegetation_landcover": ["NDVI", "CLCD"],
    "topography": ["DEM_m"],
    "layer_geometry": ["depth_mid", "depth_thickness"],
}


def prepare(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["log_SOC"] = np.log1p(d["SOC_g_kg"])
    d["depth_mid"] = (d["Upper_depth_cm"] + d["Lower_depth_cm"]) / 2
    d["depth_thickness"] = d["Lower_depth_cm"] - d["Upper_depth_cm"]
    return d


def pipeline(features: list[str]) -> Pipeline:
    continuous = [c for c in CONTINUOUS if c in features]
    categorical = [c for c in CATEGORICAL if c in features]
    pre = ColumnTransformer([
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), continuous),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categorical),
    ])
    rf = RandomForestRegressor(
        n_estimators=200, max_depth=15, min_samples_leaf=5,
        max_features="sqrt", random_state=20260813, n_jobs=-1,
    )
    return Pipeline([("preprocess", pre), ("model", rf)])


def grid_id(p: pd.DataFrame, lat_fraction: float, lon_fraction: float) -> np.ndarray:
    lat = np.floor((p["Latitude"] - lat_fraction * 5) / 5).astype(int)
    lon = np.floor((p["Longitude"] - lon_fraction * 5) / 5).astype(int)
    return (lat.astype(str) + "_" + lon.astype(str)).to_numpy()


def nearest_km(source: pd.DataFrame, target: pd.DataFrame) -> np.ndarray:
    tree = BallTree(np.deg2rad(target[["Latitude", "Longitude"]]), metric="haversine")
    dist, _ = tree.query(np.deg2rad(source[["Latitude", "Longitude"]]), k=1)
    return dist[:, 0] * 6371.0088


def score(y: np.ndarray, pred: np.ndarray) -> dict:
    return {
        "n_oof": len(y), "R2_log": r2_score(y, pred),
        "RMSE_log": mean_squared_error(y, pred) ** 0.5,
        "MAE_log": mean_absolute_error(y, pred),
    }


def add_subsets(store: dict, d: pd.DataFrame, idx: np.ndarray, y: np.ndarray, pred: np.ndarray) -> None:
    store.setdefault("all", [[], []]); store["all"][0].append(y); store["all"][1].append(pred)
    labels = d.iloc[idx]["standard_depth"].to_numpy()
    for depth in DEPTHS:
        m = labels == depth
        store.setdefault(depth, [[], []]); store[depth][0].append(y[m]); store[depth][1].append(pred[m])
    methods = d.iloc[idx]["SOCD_methods"].astype(str).to_numpy()
    for method in sorted(set(methods)):
        m = methods == method
        key = f"method:{method}"
        store.setdefault(key, [[], []]); store[key][0].append(y[m]); store[key][1].append(pred[m])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=20)
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    d = prepare(pd.read_csv(a.input, encoding="utf-8-sig"))
    d = d.loc[d["standard_depth"].isin(DEPTHS)].reset_index(drop=True)
    full_features = CONTINUOUS + CATEGORICAL
    no_bd_features = [x for x in full_features if x != "BD_g_cm3"]
    y_all = d["log_SOC"].to_numpy()
    profiles = d.groupby("Profile", as_index=False).agg(
        Latitude=("Latitude", "median"), Longitude=("Longitude", "median")
    ).sort_values("Profile").reset_index(drop=True)
    metric_rows, perm_rows, audit_rows = [], [], []

    for offset_id, (latf, lonf) in enumerate(OFFSETS):
        print(f"offset {offset_id + 1}/4", flush=True)
        folds = list(GroupKFold(5).split(profiles, groups=grid_id(profiles, latf, lonf)))
        base_store, ablation_store = {}, {}
        perm_store = {(g, r): {} for g in GROUPS for r in range(a.repeats)}
        for fold, (tri, tei) in enumerate(folds):
            candidate, testp = profiles.iloc[tri], profiles.iloc[tei]
            keep = nearest_km(candidate, testp) >= BUFFER_KM
            trainp = candidate.loc[keep]
            train_ids, test_ids = set(trainp.Profile.astype(int)), set(testp.Profile.astype(int))
            if train_ids & test_ids: raise RuntimeError("profile leakage")
            train_idx = np.flatnonzero(d.Profile.isin(train_ids).to_numpy())
            test_idx = np.flatnonzero(d.Profile.isin(test_ids).to_numpy())
            actual = nearest_km(testp, trainp)
            if actual.min() + 1e-8 < BUFFER_KM: raise RuntimeError("buffer violation")
            audit_rows.append({
                "offset_id": offset_id, "lat_offset_deg": latf*5, "lon_offset_deg": lonf*5,
                "fold": fold, "candidate_train_profiles": len(candidate),
                "removed_train_profiles": int((~keep).sum()), "retained_train_profiles": len(trainp),
                "train_records": len(train_idx), "test_profiles": len(testp), "test_records": len(test_idx),
                "profile_overlap": 0, "actual_min_test_train_km": actual.min(),
                "actual_median_test_train_km": np.median(actual),
            })
            full = pipeline(full_features); full.fit(d.iloc[train_idx][full_features], y_all[train_idx])
            pred = full.predict(d.iloc[test_idx][full_features])
            add_subsets(base_store, d, test_idx, y_all[test_idx], pred)
            nobd = pipeline(no_bd_features); nobd.fit(d.iloc[train_idx][no_bd_features], y_all[train_idx])
            pred_nobd = nobd.predict(d.iloc[test_idx][no_bd_features])
            add_subsets(ablation_store, d, test_idx, y_all[test_idx], pred_nobd)
            raw_test = d.iloc[test_idx][full_features].copy()
            for group, cols in GROUPS.items():
                for repeat in range(a.repeats):
                    rng = np.random.default_rng(2026081300 + offset_id*100000 + fold*10000 + repeat*100 + list(GROUPS).index(group))
                    order = rng.permutation(len(raw_test))
                    xp = raw_test.copy()
                    xp.loc[:, cols] = raw_test.iloc[order][cols].to_numpy()
                    pp = full.predict(xp)
                    add_subsets(perm_store[(group, repeat)], d, test_idx, y_all[test_idx], pp)

        for variant, store in [("full", base_store), ("no_bulk_density", ablation_store)]:
            for subset, (ys, ps) in store.items():
                metric_rows.append({"offset_id": offset_id, "variant": variant, "subset": subset} |
                                   score(np.concatenate(ys), np.concatenate(ps)))
        base_scores = {s: score(np.concatenate(v[0]), np.concatenate(v[1])) for s, v in base_store.items()}
        for (group, repeat), store in perm_store.items():
            for subset, (ys, ps) in store.items():
                s = score(np.concatenate(ys), np.concatenate(ps))
                perm_rows.append({"offset_id": offset_id, "group": group, "repeat": repeat,
                                  "subset": subset, "baseline_R2_log": base_scores[subset]["R2_log"],
                                  "permuted_R2_log": s["R2_log"],
                                  "delta_R2": base_scores[subset]["R2_log"] - s["R2_log"]})

    metrics = pd.DataFrame(metric_rows); perm = pd.DataFrame(perm_rows); audit = pd.DataFrame(audit_rows)
    metrics.to_csv(a.output/"bd_ablation_pooled_metrics.csv", index=False)
    perm.to_csv(a.output/"grouped_permutation_pooled_metrics.csv", index=False)
    audit.to_csv(a.output/"explanation_fold_audit.csv", index=False)
    summary = metrics.groupby(["variant", "subset"], as_index=False).agg(
        n_offsets=("R2_log", "size"), R2_mean=("R2_log", "mean"), R2_sd=("R2_log", "std"),
        RMSE_mean=("RMSE_log", "mean"), MAE_mean=("MAE_log", "mean"))
    summary.to_csv(a.output/"bd_ablation_summary.csv", index=False)
    wide = summary.pivot(index="subset", columns="variant", values="R2_mean").reset_index()
    wide["delta_R2_full_minus_noBD"] = wide["full"] - wide["no_bulk_density"]
    wide.to_csv(a.output/"bd_ablation_comparison.csv", index=False)
    ps = perm.groupby(["group", "subset"], as_index=False).agg(
        n=("delta_R2", "size"), delta_R2_mean=("delta_R2", "mean"),
        delta_R2_sd=("delta_R2", "std"), delta_R2_q025=("delta_R2", lambda x: x.quantile(.025)),
        delta_R2_median=("delta_R2", "median"), delta_R2_q975=("delta_R2", lambda x: x.quantile(.975)))
    ps.to_csv(a.output/"grouped_permutation_summary.csv", index=False)
    print("\nAblation:\n", wide.to_string(index=False), flush=True)
    print("\nImportance (all):\n", ps[ps.subset.eq("all")].sort_values("delta_R2_mean", ascending=False).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
