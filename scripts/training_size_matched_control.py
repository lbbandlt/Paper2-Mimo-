"""Training-size-matched no-buffer controls for explicit buffer validation.

For each 5-degree offset/fold/buffer, randomly sample the unbuffered candidate
training profiles to exactly the number retained by the corresponding buffer.
The test profiles remain identical. Ten repeats quantify the performance loss
caused by training-set size alone; comparison with the buffered model estimates
the additional penalty associated with spatially selective removal.
"""

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


BUFFERS_KM = [50, 100, 200]
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


def make_pipeline() -> Pipeline:
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
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=20260813,
        n_jobs=-1,
    )
    return Pipeline([("preprocess", preprocessing), ("model", model)])


def grid_id(profiles: pd.DataFrame, lat_fraction: float, lon_fraction: float) -> pd.Series:
    scale = 5.0
    lat = np.floor((profiles["Latitude"] - lat_fraction * scale) / scale).astype(int)
    lon = np.floor((profiles["Longitude"] - lon_fraction * scale) / scale).astype(int)
    return lat.astype(str) + "_" + lon.astype(str)


def nearest_km(source: pd.DataFrame, target: pd.DataFrame) -> np.ndarray:
    tree = BallTree(
        np.deg2rad(target[["Latitude", "Longitude"]].to_numpy()),
        metric="haversine",
    )
    distance, _ = tree.query(
        np.deg2rad(source[["Latitude", "Longitude"]].to_numpy()), k=1
    )
    return distance[:, 0] * 6371.0088


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    return {
        "n_oof": len(y),
        "R2_log": r2_score(y, pred),
        "RMSE_log": mean_squared_error(y, pred) ** 0.5,
        "MAE_log": mean_absolute_error(y, pred),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--buffered-metrics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=10)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    data = prepare(pd.read_csv(args.input, encoding="utf-8-sig"))
    data = data.loc[data["standard_depth"].isin(DEPTHS)].reset_index(drop=True)
    X = data[CONTINUOUS + CATEGORICAL]
    y = data["log_SOC"].to_numpy()
    profiles = data.groupby("Profile", as_index=False).agg(
        Latitude=("Latitude", "median"), Longitude=("Longitude", "median")
    ).sort_values("Profile").reset_index(drop=True)

    pooled_rows = []
    fold_rows = []
    for offset_id, (lat_fraction, lon_fraction) in enumerate(OFFSETS):
        groups = grid_id(profiles, lat_fraction, lon_fraction).to_numpy()
        base_folds = list(GroupKFold(5).split(profiles, groups=groups))
        for buffer_km in BUFFERS_KM:
            targets = []
            for train_profile_idx, test_profile_idx in base_folds:
                candidate = profiles.iloc[train_profile_idx]
                test = profiles.iloc[test_profile_idx]
                distance = nearest_km(candidate, test)
                targets.append(int((distance >= buffer_km).sum()))

            for repeat in range(args.repeats):
                rng = np.random.default_rng(
                    2026081300 + offset_id * 10000 + buffer_km * 10 + repeat
                )
                collected = {"all": [[], []]}
                for depth in DEPTHS:
                    collected[depth] = [[], []]

                for fold, (train_profile_idx, test_profile_idx) in enumerate(base_folds):
                    candidate = profiles.iloc[train_profile_idx]
                    test = profiles.iloc[test_profile_idx]
                    chosen_positions = rng.choice(
                        len(candidate), targets[fold], replace=False
                    )
                    chosen = candidate.iloc[chosen_positions]
                    chosen_ids = set(chosen["Profile"].astype(int))
                    test_ids = set(test["Profile"].astype(int))
                    if chosen_ids & test_ids:
                        raise RuntimeError("Profile leakage")
                    train_idx = np.flatnonzero(
                        data["Profile"].isin(chosen_ids).to_numpy()
                    )
                    test_idx = np.flatnonzero(
                        data["Profile"].isin(test_ids).to_numpy()
                    )
                    distance_test_to_chosen = nearest_km(test, chosen)
                    fold_rows.append({
                        "offset_id": offset_id,
                        "buffer_km_target": buffer_km,
                        "repeat": repeat,
                        "fold": fold,
                        "candidate_train_profiles": len(candidate),
                        "target_train_profiles": targets[fold],
                        "sampled_train_profiles": len(chosen),
                        "sampled_train_records": len(train_idx),
                        "test_profiles": len(test),
                        "test_records": len(test_idx),
                        "profile_overlap": 0,
                        "sampled_actual_min_km": float(distance_test_to_chosen.min()),
                        "sampled_actual_median_km": float(np.median(distance_test_to_chosen)),
                    })
                    model = make_pipeline()
                    model.fit(X.iloc[train_idx], y[train_idx])
                    pred = model.predict(X.iloc[test_idx])
                    collected["all"][0].append(y[test_idx])
                    collected["all"][1].append(pred)
                    test_depth = data.iloc[test_idx]["standard_depth"].to_numpy()
                    for depth in DEPTHS:
                        mask = test_depth == depth
                        collected[depth][0].append(y[test_idx][mask])
                        collected[depth][1].append(pred[mask])

                for subset, (ys, preds) in collected.items():
                    yt = np.concatenate(ys)
                    yp = np.concatenate(preds)
                    pooled_rows.append({
                        "offset_id": offset_id,
                        "buffer_km_target": buffer_km,
                        "repeat": repeat,
                        "model": "RF",
                        "subset": subset,
                    } | metrics(yt, yp))

    pooled = pd.DataFrame(pooled_rows)
    fold_audit = pd.DataFrame(fold_rows)
    pooled.to_csv(args.output / "size_matched_pooled_metrics.csv", index=False)
    fold_audit.to_csv(args.output / "size_matched_fold_audit.csv", index=False)

    summary = pooled.groupby(
        ["buffer_km_target", "model", "subset"], as_index=False
    ).agg(
        n_offset_repeats=("R2_log", "size"),
        R2_size_matched_mean=("R2_log", "mean"),
        R2_size_matched_sd=("R2_log", "std"),
        R2_size_matched_q025=("R2_log", lambda x: x.quantile(0.025)),
        R2_size_matched_median=("R2_log", "median"),
        R2_size_matched_q975=("R2_log", lambda x: x.quantile(0.975)),
    )
    summary.to_csv(args.output / "size_matched_summary.csv", index=False)

    buffered = pd.read_csv(args.buffered_metrics)
    buffered = buffered.loc[
        (buffered["model"] == "RF") & buffered["buffer_km"].isin(BUFFERS_KM),
        ["offset_id", "buffer_km", "subset", "R2_log"],
    ].rename(columns={"R2_log": "R2_buffered"})
    comparison = pooled.merge(
        buffered,
        left_on=["offset_id", "buffer_km_target", "subset"],
        right_on=["offset_id", "buffer_km", "subset"],
        how="left",
        validate="many_to_one",
    )
    comparison["additional_buffer_penalty"] = (
        comparison["R2_log"] - comparison["R2_buffered"]
    )
    comparison.to_csv(args.output / "buffer_vs_size_matched_comparison.csv", index=False)
    comparison_summary = comparison.groupby(
        ["buffer_km_target", "subset"], as_index=False
    ).agg(
        R2_size_matched_mean=("R2_log", "mean"),
        R2_buffered_mean=("R2_buffered", "mean"),
        additional_buffer_penalty_mean=("additional_buffer_penalty", "mean"),
        additional_buffer_penalty_sd=("additional_buffer_penalty", "std"),
        additional_buffer_penalty_q025=("additional_buffer_penalty", lambda x: x.quantile(0.025)),
        additional_buffer_penalty_q975=("additional_buffer_penalty", lambda x: x.quantile(0.975)),
    )
    comparison_summary.to_csv(
        args.output / "buffer_vs_size_matched_summary.csv", index=False
    )
    print(comparison_summary.loc[comparison_summary["subset"] == "all"].to_string(index=False))


if __name__ == "__main__":
    main()
