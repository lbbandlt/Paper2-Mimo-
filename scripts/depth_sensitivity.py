"""Depth-gradient sensitivity analysis on harmonized standard layers.

Three designs are evaluated with spatial 5-degree GroupKFold:
1. matched_n: equal record count per depth, without matching grid composition;
2. matched_spatial: equal count within every grid and depth;
3. paired_profile: only profiles observed in all four standard depths.

All models are trained jointly across depths. Preprocessing is fitted inside
each training fold, and all layers from a held-out grid remain in the test set.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DEPTHS = ["0-20cm", "20-50cm", "50-100cm", "100-200cm"]
CONTINUOUS = [
    "BD_g_cm3", "pH", "Sand_%", "Silt_%", "Clay_%", "DEM_m", "NDVI",
    "MAT_°C", "MAP_mm", "PET_mm", "AI", "depth_mid", "depth_thickness",
]
CATEGORICAL = ["CLCD"]


def add_features(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    out["log_SOC"] = np.log1p(out["SOC_g_kg"])
    out["depth_mid"] = (out["Upper_depth_cm"] + out["Lower_depth_cm"]) / 2
    out["depth_thickness"] = out["Lower_depth_cm"] - out["Upper_depth_cm"]
    out["grid_id_5deg"] = (
        np.floor(out["Latitude"] / 5).astype(int) * 1000
        + np.floor(out["Longitude"] / 5).astype(int)
    )
    return out


def pipeline(model: str, seed: int) -> Pipeline:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    prep = ColumnTransformer([
        ("numeric", numeric, CONTINUOUS),
        ("categorical", categorical, CATEGORICAL),
    ])
    if model == "Ridge":
        estimator = Ridge(alpha=100.0)
    elif model == "RF":
        estimator = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_leaf=5,
            max_features="sqrt",
            random_state=seed,
            n_jobs=-1,
        )
    else:
        raise ValueError(model)
    return Pipeline([("preprocess", prep), ("model", estimator)])


def matched_n(data: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = min((data["standard_depth"] == d).sum() for d in DEPTHS)
    parts = []
    for depth in DEPTHS:
        idx = data.index[data["standard_depth"] == depth].to_numpy()
        parts.append(data.loc[rng.choice(idx, n, replace=False)])
    return pd.concat(parts, ignore_index=True)


def matched_spatial(data: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = data.groupby(["grid_id_5deg", "standard_depth"]).size().unstack(fill_value=0)
    counts = counts.reindex(columns=DEPTHS, fill_value=0)
    target = counts.min(axis=1)
    parts = []
    for grid, n in target[target > 0].items():
        n = int(n)
        for depth in DEPTHS:
            idx = data.index[
                (data["grid_id_5deg"] == grid)
                & (data["standard_depth"] == depth)
            ].to_numpy()
            parts.append(data.loc[rng.choice(idx, n, replace=False)])
    return pd.concat(parts, ignore_index=True)


def paired_profile(data: pd.DataFrame) -> pd.DataFrame:
    counts = data.groupby("Profile")["standard_depth"].nunique()
    profiles = counts.index[counts == len(DEPTHS)]
    return data.loc[data["Profile"].isin(profiles)].copy().reset_index(drop=True)


def validate_design(sample: pd.DataFrame, design: str) -> dict:
    depth_counts = sample.groupby("standard_depth").size().reindex(DEPTHS)
    if depth_counts.isna().any() or depth_counts.nunique() != 1:
        raise RuntimeError(f"Unequal depth counts in {design}: {depth_counts.to_dict()}")
    grid_counts = sample.groupby(["grid_id_5deg", "standard_depth"]).size().unstack(fill_value=0)
    grid_matched = bool((grid_counts.reindex(columns=DEPTHS, fill_value=0).nunique(axis=1) == 1).all())
    return {
        "design": design,
        "n_per_depth": int(depth_counts.iloc[0]),
        "n_profiles": int(sample["Profile"].nunique()),
        "n_grids": int(sample["grid_id_5deg"].nunique()),
        "grid_counts_identical_across_depths": grid_matched,
    }


def evaluate(sample: pd.DataFrame, design: str, repeat: int, seed: int) -> tuple[list[dict], list[dict]]:
    rows = []
    predictions = []
    X = sample[CONTINUOUS + CATEGORICAL]
    y = sample["log_SOC"].to_numpy()
    groups = sample["grid_id_5deg"].to_numpy()
    depth = sample["standard_depth"].to_numpy()
    profiles = sample["Profile"].to_numpy()
    splitter = GroupKFold(n_splits=5)
    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups)):
        if set(profiles[train_idx]) & set(profiles[test_idx]):
            raise RuntimeError(f"Profile leakage in {design}, repeat {repeat}, fold {fold}")
        for model in ("Ridge", "RF"):
            fit = pipeline(model, seed + fold)
            fit.fit(X.iloc[train_idx], y[train_idx])
            pred = fit.predict(X.iloc[test_idx])
            for label in DEPTHS:
                mask = depth[test_idx] == label
                yt = y[test_idx][mask]
                yp = pred[mask]
                rows.append({
                    "design": design,
                    "repeat": repeat,
                    "seed": seed,
                    "fold": fold,
                    "model": model,
                    "standard_depth": label,
                    "n_train": len(train_idx),
                    "n_test_depth": int(mask.sum()),
                    "n_test_profiles_depth": int(pd.Series(profiles[test_idx][mask]).nunique()),
                    "R2_log": r2_score(yt, yp) if len(yt) >= 2 else np.nan,
                    "RMSE_log": mean_squared_error(yt, yp) ** 0.5 if len(yt) else np.nan,
                    "MAE_log": mean_absolute_error(yt, yp) if len(yt) else np.nan,
                    "profile_overlap": 0,
                })
                for local_i, sample_i in enumerate(test_idx[mask]):
                    predictions.append({
                        "design": design,
                        "repeat": repeat,
                        "seed": seed,
                        "fold": fold,
                        "model": model,
                        "standard_depth": label,
                        "Samples": sample.iloc[sample_i]["Samples"],
                        "Profile": int(profiles[sample_i]),
                        "grid_id_5deg": int(groups[sample_i]),
                        "y_log": float(yt[local_i]),
                        "pred_log": float(yp[local_i]),
                    })
    return rows, predictions


def pooled_metrics(group: pd.DataFrame) -> pd.Series:
    y = group["y_log"].to_numpy()
    p = group["pred_log"].to_numpy()
    return pd.Series({
        "n_oof": len(group),
        "R2_pooled": r2_score(y, p),
        "RMSE_pooled": mean_squared_error(y, p) ** 0.5,
        "MAE_pooled": mean_absolute_error(y, p),
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=30)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    data = add_features(pd.read_csv(args.input, encoding="utf-8-sig"))
    data = data.loc[data["standard_depth"].isin(DEPTHS)].copy()
    all_rows = []
    all_predictions = []
    design_rows = []
    for repeat in range(args.repeats):
        seed = 20260813 + repeat
        for design, sample in (
            ("matched_n", matched_n(data, seed)),
            ("matched_spatial", matched_spatial(data, seed)),
        ):
            design_rows.append({"repeat": repeat} | validate_design(sample, design))
            metrics_part, predictions_part = evaluate(sample, design, repeat, seed)
            all_rows.extend(metrics_part)
            all_predictions.extend(predictions_part)

    paired = paired_profile(data)
    design_rows.append({"repeat": 0} | validate_design(paired, "paired_profile"))
    metrics_part, predictions_part = evaluate(paired, "paired_profile", 0, 20260813)
    all_rows.extend(metrics_part)
    all_predictions.extend(predictions_part)

    metrics = pd.DataFrame(all_rows)
    predictions = pd.DataFrame(all_predictions)
    designs = pd.DataFrame(design_rows)
    metrics.to_csv(args.output / "depth_sensitivity_fold_metrics.csv", index=False)
    predictions.to_csv(args.output / "depth_sensitivity_oof_predictions.csv", index=False)
    designs.to_csv(args.output / "depth_sensitivity_design_audit.csv", index=False)
    summary = metrics.groupby(
        ["design", "model", "standard_depth"], as_index=False
    ).agg(
        n_evaluations=("R2_log", "size"),
        R2_mean=("R2_log", "mean"),
        R2_sd=("R2_log", "std"),
        R2_median=("R2_log", "median"),
        RMSE_mean=("RMSE_log", "mean"),
        MAE_mean=("MAE_log", "mean"),
        min_test_n=("n_test_depth", "min"),
    )
    summary.to_csv(args.output / "depth_sensitivity_summary.csv", index=False)
    pooled = predictions.groupby(
        ["design", "repeat", "model", "standard_depth"], as_index=False
    ).apply(pooled_metrics, include_groups=False).reset_index(drop=True)
    pooled.to_csv(args.output / "depth_sensitivity_pooled_by_repeat.csv", index=False)
    pooled_summary = pooled.groupby(
        ["design", "model", "standard_depth"], as_index=False
    ).agg(
        n_repeats=("R2_pooled", "size"),
        R2_pooled_mean=("R2_pooled", "mean"),
        R2_pooled_sd=("R2_pooled", "std"),
        R2_pooled_q025=("R2_pooled", lambda x: x.quantile(0.025)),
        R2_pooled_median=("R2_pooled", "median"),
        R2_pooled_q975=("R2_pooled", lambda x: x.quantile(0.975)),
        RMSE_pooled_mean=("RMSE_pooled", "mean"),
    )
    pooled_summary.to_csv(args.output / "depth_sensitivity_pooled_summary.csv", index=False)
    print(designs.groupby("design").first().to_string())
    print("\nRandom Forest summary")
    print(summary.loc[summary["model"] == "RF"].to_string(index=False))
    print("\nRandom Forest pooled OOF summary")
    print(pooled_summary.loc[pooled_summary["model"] == "RF"].to_string(index=False))


if __name__ == "__main__":
    main()
