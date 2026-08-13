"""Create standard-depth SOC records with explicit coverage auditing.

The main candidates use thickness-overlap weighting for 0-20, 20-50,
50-100, and 100-200 cm. Profiles containing overlapping source layers are
excluded from the weighted candidates because the database does not identify
which overlapping layers belong to parallel sampling sequences.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


STANDARD = [
    ("0-20cm", 0.0, 20.0),
    ("20-50cm", 20.0, 50.0),
    ("50-100cm", 50.0, 100.0),
    ("100-200cm", 100.0, 200.0),
]
WEIGHTED_COLUMNS = ["SOC_g_kg", "BD_g_cm3", "pH", "Sand_%", "Silt_%", "Clay_%"]
STATIC_NUMERIC = ["Latitude", "Longitude", "DEM_m", "NDVI", "MAT_°C", "MAP_mm", "PET_mm", "AI", "Time"]


def read_source(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "gb18030", "gbk"):
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            pass
    raise UnicodeError(f"Cannot decode {path}")


def mode_or_first(series: pd.Series):
    values = series.dropna()
    if values.empty:
        return np.nan
    mode = values.mode()
    return mode.iloc[0] if not mode.empty else values.iloc[0]


def interval_diagnostics(group: pd.DataFrame) -> tuple[float, float, int, int]:
    a = group.sort_values(["Upper_depth_cm", "Lower_depth_cm"])[
        ["Upper_depth_cm", "Lower_depth_cm"]
    ].to_numpy(float)
    if len(a) < 2:
        return 0.0, 0.0, 0, 0
    delta = a[1:, 0] - a[:-1, 1]
    return (
        float(delta[delta > 0].sum()),
        float((-delta[delta < 0]).sum()),
        int((delta > 0).sum()),
        int((delta < 0).sum()),
    )


def union_coverage(intervals: list[tuple[float, float]], lo: float, hi: float) -> float:
    clipped = sorted((max(lo, a), min(hi, b)) for a, b in intervals if min(hi, b) > max(lo, a))
    if not clipped:
        return 0.0
    start, end = clipped[0]
    total = 0.0
    for a, b in clipped[1:]:
        if a <= end:
            end = max(end, b)
        else:
            total += end - start
            start, end = a, b
    total += end - start
    return total / (hi - lo)


def weighted_mean(values: pd.Series, weights: np.ndarray) -> float:
    valid = values.notna().to_numpy() & np.isfinite(weights) & (weights > 0)
    if not valid.any():
        return np.nan
    return float(np.average(values.to_numpy(float)[valid], weights=weights[valid]))


def harmonize_profile(profile: int, group: pd.DataFrame) -> list[dict]:
    output = []
    intervals = list(group[["Upper_depth_cm", "Lower_depth_cm"]].itertuples(index=False, name=None))
    for label, lo, hi in STANDARD:
        overlap = np.maximum(
            0.0,
            np.minimum(group["Lower_depth_cm"].to_numpy(float), hi)
            - np.maximum(group["Upper_depth_cm"].to_numpy(float), lo),
        )
        use = overlap > 0
        if not use.any():
            continue
        part = group.loc[use]
        weights = overlap[use]
        row = {
            "Samples": f"P{int(profile)}_{int(lo)}_{int(hi)}",
            "Profile": int(profile),
            "Upper_depth_cm": int(lo),
            "Lower_depth_cm": int(hi),
            "Depth_cm": label,
            "standard_depth": label,
            "coverage_fraction": union_coverage(intervals, lo, hi),
            "overlap_thickness_sum_cm": float(weights.sum()),
            "n_source_layers": int(use.sum()),
            "CLCD": mode_or_first(part["CLCD"]),
            "References": mode_or_first(part["References"]),
            "SOCD_methods": mode_or_first(part["SOCD_methods"]),
        }
        for col in WEIGHTED_COLUMNS:
            row[col] = weighted_mean(part[col], weights)
        for col in STATIC_NUMERIC:
            row[col] = float(part[col].median()) if part[col].notna().any() else np.nan
        output.append(row)
    return output


def midpoint_version(data: pd.DataFrame) -> pd.DataFrame:
    mid = (data["Upper_depth_cm"] + data["Lower_depth_cm"]) / 2
    labels = np.select(
        [mid < 20, mid < 50, mid < 100, (mid >= 100) & (mid < 200)],
        [x[0] for x in STANDARD],
        default=">=200cm",
    )
    out = data.copy()
    out["midpoint_depth_bin"] = labels
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    raw = read_source(args.input)
    data = raw.dropna(subset=["SOC_g_kg"]).copy()
    data = data.loc[data["SOC_g_kg"] <= 200].copy()

    profile_qa = []
    harmonized = []
    for profile, group in data.groupby("Profile", sort=True):
        gap_cm, overlap_cm, n_gaps, n_overlaps = interval_diagnostics(group)
        profile_qa.append({
            "Profile": int(profile),
            "n_source_layers": len(group),
            "gap_cm_sum": gap_cm,
            "overlap_cm_sum": overlap_cm,
            "n_gaps": n_gaps,
            "n_overlaps": n_overlaps,
            "eligible_nonoverlap": n_overlaps == 0,
        })
        if n_overlaps == 0:
            harmonized.extend(harmonize_profile(profile, group))

    qa = pd.DataFrame(profile_qa)
    weighted = pd.DataFrame(harmonized)
    midpoint = midpoint_version(data)

    qa.to_csv(args.output / "profile_interval_qa.csv", index=False)
    weighted.to_csv(args.output / "standard_depth_all_coverage.csv", index=False, encoding="utf-8-sig")
    midpoint.to_csv(args.output / "midpoint_depth_sensitivity.csv", index=False, encoding="utf-8-sig")

    summaries = []
    for threshold in (0.5, 0.8, 1.0):
        selected = weighted.loc[weighted["coverage_fraction"] >= threshold].copy()
        selected.to_csv(
            args.output / f"standard_depth_coverage_{int(threshold*100):03d}.csv",
            index=False,
            encoding="utf-8-sig",
        )
        for depth, group in selected.groupby("standard_depth", sort=False):
            summaries.append({
                "coverage_threshold": threshold,
                "standard_depth": depth,
                "n_records": len(group),
                "n_profiles": group["Profile"].nunique(),
                "SOC_mean_g_kg": group["SOC_g_kg"].mean(),
                "SOC_median_g_kg": group["SOC_g_kg"].median(),
            })
    summary = pd.DataFrame(summaries)
    summary.to_csv(args.output / "coverage_threshold_summary.csv", index=False)

    midpoint_summary = midpoint.groupby("midpoint_depth_bin", as_index=False).agg(
        n_layers=("Samples", "size"), n_profiles=("Profile", "nunique")
    )
    midpoint_summary.to_csv(args.output / "midpoint_depth_summary.csv", index=False)

    report = {
        "analysis_profiles": int(data["Profile"].nunique()),
        "profiles_with_gaps": int((qa["n_gaps"] > 0).sum()),
        "profiles_with_overlaps": int((qa["n_overlaps"] > 0).sum()),
        "profiles_eligible_for_weighted_harmonization": int(qa["eligible_nonoverlap"].sum()),
        "excluded_overlap_profile_pct": float((qa["n_overlaps"] > 0).mean() * 100),
        "standard_intervals_cm": [{"label": x, "upper": lo, "lower": hi} for x, lo, hi in STANDARD],
        "coverage_summary": summary.to_dict("records"),
    }
    (args.output / "depth_harmonization_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
