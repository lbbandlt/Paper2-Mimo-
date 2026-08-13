"""Explicit 0/50/100/200 km buffer validation on four 5-degree grid origins."""

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


BUFFERS_KM = [0, 50, 100, 200]
OFFSETS = [(0.0, 0.0), (0.5, 0.0), (0.0, 0.5), (0.5, 0.5)]
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
    preprocessing = ColumnTransformer([
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
    return Pipeline([("preprocess", preprocessing), ("model", model)])


def grid_id(profiles: pd.DataFrame, offset_lat_fraction: float, offset_lon_fraction: float) -> pd.Series:
    scale = 5.0
    lat = np.floor((profiles["Latitude"] - offset_lat_fraction * scale) / scale).astype(int)
    lon = np.floor((profiles["Longitude"] - offset_lon_fraction * scale) / scale).astype(int)
    return lat.astype(str) + "_" + lon.astype(str)


def train_to_test_distance_km(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    test_tree = BallTree(
        np.deg2rad(test[["Latitude", "Longitude"]].to_numpy()), metric="haversine"
    )
    distance, _ = test_tree.query(
        np.deg2rad(train[["Latitude", "Longitude"]].to_numpy()), k=1
    )
    return distance[:, 0] * 6371.0088


def test_to_train_distance_km(test: pd.DataFrame, train: pd.DataFrame) -> np.ndarray:
    train_tree = BallTree(
        np.deg2rad(train[["Latitude", "Longitude"]].to_numpy()), metric="haversine"
    )
    distance, _ = train_tree.query(
        np.deg2rad(test[["Latitude", "Longitude"]].to_numpy()), k=1
    )
    return distance[:, 0] * 6371.0088


def calculate(group: pd.DataFrame) -> pd.Series:
    y = group["y_log"].to_numpy()
    p = group["pred_log"].to_numpy()
    return pd.Series({
        "n_oof": len(group),
        "n_profiles": group["Profile"].nunique(),
        "R2_log": r2_score(y, p),
        "RMSE_log": mean_squared_error(y, p) ** 0.5,
        "MAE_log": mean_absolute_error(y, p),
        "nearest_train_min_km": group["nearest_train_km"].min(),
        "nearest_train_q25_km": group["nearest_train_km"].quantile(0.25),
        "nearest_train_median_km": group["nearest_train_km"].median(),
        "nearest_train_q75_km": group["nearest_train_km"].quantile(0.75),
        "nearest_train_max_km": group["nearest_train_km"].max(),
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
    ).sort_values("Profile").reset_index(drop=True)

    predictions = []
    fold_audit = []
    for offset_id, (lat_fraction, lon_fraction) in enumerate(OFFSETS):
        groups = grid_id(profiles, lat_fraction, lon_fraction).to_numpy()
        splitter = GroupKFold(n_splits=5)
        for fold, (train_profile_idx, test_profile_idx) in enumerate(
            splitter.split(profiles, groups=groups)
        ):
            candidate_train = profiles.iloc[train_profile_idx].copy()
            test_profiles = profiles.iloc[test_profile_idx].copy()
            candidate_distance = train_to_test_distance_km(candidate_train, test_profiles)
            test_ids = set(test_profiles["Profile"].astype(int))
            for buffer_km in BUFFERS_KM:
                keep = candidate_distance >= buffer_km
                retained_train = candidate_train.loc[keep].copy()
                train_ids = set(retained_train["Profile"].astype(int))
                if train_ids & test_ids:
                    raise RuntimeError(f"Profile leakage offset={offset_id}, fold={fold}")
                train_idx = np.flatnonzero(data["Profile"].isin(train_ids).to_numpy())
                test_idx = np.flatnonzero(data["Profile"].isin(test_ids).to_numpy())
                test_profile_distance = test_to_train_distance_km(test_profiles, retained_train)
                distance_map = dict(zip(test_profiles["Profile"].astype(int), test_profile_distance))
                test_record_distance = data.iloc[test_idx]["Profile"].astype(int).map(distance_map).to_numpy()
                guaranteed_min = float(test_profile_distance.min())
                if guaranteed_min + 1e-8 < buffer_km:
                    raise RuntimeError(
                        f"Buffer violation: {guaranteed_min} < {buffer_km}"
                    )
                fold_audit.append({
                    "offset_id": offset_id,
                    "lat_offset_deg": lat_fraction * 5,
                    "lon_offset_deg": lon_fraction * 5,
                    "fold": fold,
                    "buffer_km": buffer_km,
                    "candidate_train_profiles": len(candidate_train),
                    "removed_train_profiles": int((~keep).sum()),
                    "retained_train_profiles": len(retained_train),
                    "retained_train_records": len(train_idx),
                    "test_profiles": len(test_profiles),
                    "test_records": len(test_idx),
                    "profile_overlap": 0,
                    "actual_min_test_train_km": guaranteed_min,
                    "actual_median_test_train_km": float(np.median(test_profile_distance)),
                })
                for model_name in ("Ridge", "RF"):
                    model = make_pipeline(model_name)
                    model.fit(X.iloc[train_idx], y[train_idx])
                    pred = model.predict(X.iloc[test_idx])
                    for local, row_idx in enumerate(test_idx):
                        row = data.iloc[row_idx]
                        predictions.append({
                            "offset_id": offset_id,
                            "fold": fold,
                            "buffer_km": buffer_km,
                            "model": model_name,
                            "Samples": row["Samples"],
                            "Profile": int(row["Profile"]),
                            "standard_depth": row["standard_depth"],
                            "y_log": float(y[row_idx]),
                            "pred_log": float(pred[local]),
                            "nearest_train_km": float(test_record_distance[local]),
                        })

    predictions = pd.DataFrame(predictions)
    audit = pd.DataFrame(fold_audit)
    predictions.to_csv(args.output / "buffered_oof_predictions.csv", index=False)
    audit.to_csv(args.output / "buffered_fold_audit.csv", index=False)

    overall = predictions.groupby(
        ["offset_id", "buffer_km", "model"], as_index=False
    ).apply(calculate, include_groups=False).reset_index(drop=True)
    overall["subset"] = "all"
    depth = predictions.groupby(
        ["offset_id", "buffer_km", "model", "standard_depth"], as_index=False
    ).apply(calculate, include_groups=False).reset_index(drop=True)
    depth = depth.rename(columns={"standard_depth": "subset"})
    metrics = pd.concat([overall, depth], ignore_index=True)
    metrics.to_csv(args.output / "buffered_pooled_metrics.csv", index=False)

    summary = metrics.groupby(["buffer_km", "model", "subset"], as_index=False).agg(
        n_offsets=("R2_log", "size"),
        R2_mean=("R2_log", "mean"),
        R2_sd_offsets=("R2_log", "std"),
        R2_min=("R2_log", "min"),
        R2_max=("R2_log", "max"),
        actual_distance_median_mean_km=("nearest_train_median_km", "mean"),
        actual_distance_min_min_km=("nearest_train_min_km", "min"),
    )
    summary.to_csv(args.output / "buffered_summary.csv", index=False)
    print(summary.loc[(summary["model"] == "RF") & (summary["subset"] == "all")].to_string(index=False))


if __name__ == "__main__":
    main()
