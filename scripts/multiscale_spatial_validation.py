"""Multi-scale, offset spatial CV with observed train-test distances.

Evaluates four grid sizes and four grid origins. All layers from a profile are
kept together. Preprocessing is fitted inside each training fold. Performance
is reported from pooled out-of-fold predictions for all records and standard
depth subsets, together with nearest-training-profile distances.
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
from sklearn.neighbors import BallTree
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SCALES = [2.5, 5.0, 7.5, 10.0]
OFFSET_FRACTIONS = [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)]
DEPTHS = ["0-20cm", "20-50cm", "50-100cm", "100-200cm"]
CONTINUOUS = [
    "BD_g_cm3", "pH", "Sand_%", "Silt_%", "Clay_%", "DEM_m", "NDVI",
    "MAT_°C", "MAP_mm", "PET_mm", "AI", "depth_mid", "depth_thickness",
]
CATEGORICAL = ["CLCD"]


def prepare(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    out["log_SOC"] = np.log1p(out["SOC_g_kg"])
    out["depth_mid"] = (out["Upper_depth_cm"] + out["Lower_depth_cm"]) / 2
    out["depth_thickness"] = out["Lower_depth_cm"] - out["Upper_depth_cm"]
    return out


def make_pipeline(model_name: str) -> Pipeline:
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocess = ColumnTransformer([
        ("numeric", numeric, CONTINUOUS),
        ("categorical", categorical, CATEGORICAL),
    ])
    if model_name == "Ridge":
        model = Ridge(alpha=100.0)
    elif model_name == "RF":
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_leaf=5,
            max_features="sqrt",
            random_state=20260813,
            n_jobs=-1,
        )
    else:
        raise ValueError(model_name)
    return Pipeline([("preprocess", preprocess), ("model", model)])


def grid_ids(data: pd.DataFrame, scale: float, lat_fraction: float, lon_fraction: float) -> pd.Series:
    lat_origin = lat_fraction * scale
    lon_origin = lon_fraction * scale
    lat_bin = np.floor((data["Latitude"] - lat_origin) / scale).astype(int)
    lon_bin = np.floor((data["Longitude"] - lon_origin) / scale).astype(int)
    return lat_bin.astype(str) + "_" + lon_bin.astype(str)


def nearest_distances_km(
    profiles: pd.DataFrame, train_profiles: set[int], test_profiles: set[int]
) -> dict[int, float]:
    train = profiles.loc[profiles["Profile"].isin(train_profiles)]
    test = profiles.loc[profiles["Profile"].isin(test_profiles)]
    train_rad = np.deg2rad(train[["Latitude", "Longitude"]].to_numpy())
    test_rad = np.deg2rad(test[["Latitude", "Longitude"]].to_numpy())
    tree = BallTree(train_rad, metric="haversine")
    distance, _ = tree.query(test_rad, k=1)
    km = distance[:, 0] * 6371.0088
    return dict(zip(test["Profile"].astype(int), km.astype(float)))


def metric_row(group: pd.DataFrame) -> pd.Series:
    y = group["y_log"].to_numpy()
    pred = group["pred_log"].to_numpy()
    return pd.Series({
        "n_oof": len(group),
        "n_profiles": group["Profile"].nunique(),
        "R2_log": r2_score(y, pred),
        "RMSE_log": mean_squared_error(y, pred) ** 0.5,
        "MAE_log": mean_absolute_error(y, pred),
        "distance_min_km": group["nearest_train_km"].min(),
        "distance_q25_km": group["nearest_train_km"].quantile(0.25),
        "distance_median_km": group["nearest_train_km"].median(),
        "distance_q75_km": group["nearest_train_km"].quantile(0.75),
        "distance_max_km": group["nearest_train_km"].max(),
        "pct_under_50km": (group["nearest_train_km"] < 50).mean() * 100,
        "pct_under_100km": (group["nearest_train_km"] < 100).mean() * 100,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    data = prepare(pd.read_csv(args.input, encoding="utf-8-sig"))
    data = data.loc[data["standard_depth"].isin(DEPTHS)].reset_index(drop=True)
    X = data[CONTINUOUS + CATEGORICAL]
    y = data["log_SOC"].to_numpy()
    profiles = data.groupby("Profile", as_index=False).agg(
        Latitude=("Latitude", "median"), Longitude=("Longitude", "median")
    )

    predictions = []
    design_audit = []
    fold_audit = []
    for scale in SCALES:
        for offset_id, (lat_fraction, lon_fraction) in enumerate(OFFSET_FRACTIONS):
            design = f"grid_{scale:g}deg_offset_{offset_id}"
            profile_groups = grid_ids(
                profiles, scale, lat_fraction, lon_fraction
            ).to_numpy()
            n_grids = pd.Series(profile_groups).nunique()
            if n_grids < 5:
                raise RuntimeError(f"{design} has fewer than five occupied grids")
            design_audit.append({
                "design": design,
                "grid_scale_deg": scale,
                "offset_id": offset_id,
                "lat_offset_deg": lat_fraction * scale,
                "lon_offset_deg": lon_fraction * scale,
                "n_occupied_grids": n_grids,
                "n_profiles": data["Profile"].nunique(),
                "n_records": len(data),
            })
            splitter = GroupKFold(n_splits=5)
            for fold, (train_profile_idx, test_profile_idx) in enumerate(
                splitter.split(profiles, groups=profile_groups)
            ):
                train_profiles = set(
                    profiles.iloc[train_profile_idx]["Profile"].astype(int)
                )
                test_profiles = set(
                    profiles.iloc[test_profile_idx]["Profile"].astype(int)
                )
                overlap = train_profiles & test_profiles
                if overlap:
                    raise RuntimeError(f"Profile leakage in {design}, fold {fold}")
                train_idx = np.flatnonzero(
                    data["Profile"].isin(train_profiles).to_numpy()
                )
                test_idx = np.flatnonzero(
                    data["Profile"].isin(test_profiles).to_numpy()
                )
                distances = nearest_distances_km(profiles, train_profiles, test_profiles)
                test_distance = data.iloc[test_idx]["Profile"].astype(int).map(distances).to_numpy()
                fold_audit.append({
                    "design": design,
                    "grid_scale_deg": scale,
                    "offset_id": offset_id,
                    "fold": fold,
                    "n_train_records": len(train_idx),
                    "n_test_records": len(test_idx),
                    "n_train_profiles": len(train_profiles),
                    "n_test_profiles": len(test_profiles),
                    "profile_overlap": 0,
                    "nearest_train_median_km": float(np.median(test_distance)),
                    "nearest_train_q25_km": float(np.quantile(test_distance, 0.25)),
                    "nearest_train_q75_km": float(np.quantile(test_distance, 0.75)),
                })
                for model_name in ("Ridge", "RF"):
                    model = make_pipeline(model_name)
                    model.fit(X.iloc[train_idx], y[train_idx])
                    pred = model.predict(X.iloc[test_idx])
                    for local, row_idx in enumerate(test_idx):
                        row = data.iloc[row_idx]
                        predictions.append({
                            "design": design,
                            "grid_scale_deg": scale,
                            "offset_id": offset_id,
                            "fold": fold,
                            "model": model_name,
                            "Samples": row["Samples"],
                            "Profile": int(row["Profile"]),
                            "standard_depth": row["standard_depth"],
                            "y_log": float(y[row_idx]),
                            "pred_log": float(pred[local]),
                            "nearest_train_km": float(test_distance[local]),
                        })

    predictions = pd.DataFrame(predictions)
    design_audit = pd.DataFrame(design_audit)
    fold_audit = pd.DataFrame(fold_audit)
    predictions.to_csv(args.output / "multiscale_oof_predictions.csv", index=False)
    design_audit.to_csv(args.output / "multiscale_design_audit.csv", index=False)
    fold_audit.to_csv(args.output / "multiscale_fold_audit.csv", index=False)

    overall = predictions.groupby(
        ["design", "grid_scale_deg", "offset_id", "model"], as_index=False
    ).apply(metric_row, include_groups=False).reset_index(drop=True)
    overall["subset"] = "all"
    by_depth = predictions.groupby(
        ["design", "grid_scale_deg", "offset_id", "model", "standard_depth"],
        as_index=False,
    ).apply(metric_row, include_groups=False).reset_index(drop=True)
    by_depth = by_depth.rename(columns={"standard_depth": "subset"})
    metrics = pd.concat([overall, by_depth], ignore_index=True)
    metrics.to_csv(args.output / "multiscale_pooled_metrics.csv", index=False)

    scale_summary = metrics.groupby(
        ["grid_scale_deg", "model", "subset"], as_index=False
    ).agg(
        n_offsets=("R2_log", "size"),
        R2_mean=("R2_log", "mean"),
        R2_sd_offsets=("R2_log", "std"),
        R2_min=("R2_log", "min"),
        R2_max=("R2_log", "max"),
        distance_median_mean_km=("distance_median_km", "mean"),
        pct_under_100km_mean=("pct_under_100km", "mean"),
    )
    scale_summary.to_csv(args.output / "multiscale_scale_summary.csv", index=False)
    print(scale_summary.loc[(scale_summary["model"] == "RF") & (scale_summary["subset"] == "all")].to_string(index=False))


if __name__ == "__main__":
    main()
