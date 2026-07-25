# Data Audit Summary – China SOCS V10

**Audit date:** 2026-07-25

## 1. Dataset Overview

- **Rows:** 23,103
- **Columns:** 24
- **Profiles (unique):** 7,955
- **Depth layers per profile:** 2.9 (mean)
- **CSV file size:** 3.7 MB
- **In-memory size:** 9.0 MB
- **Temporal range:** 2010–2023
- **Spatial range:** Lat 18.26°–51.63°, Lon 74.92°–133.98°

## 2. Data Dictionary Summary

| Field | Type | Missing | Missing% | Min | Max | Mean |
|---|---|---|---|---|---|---|
| Samples | int64 | 0 | 0.0% | 1 | 23103 | 11552.0 |
| Profile | int64 | 0 | 0.0% | 1 | 7955 | 3121.4893 |
| Latitude | float64 | 0 | 0.0% | 18.2583 | 51.626 | 33.3747 |
| Longitude | float64 | 0 | 0.0% | 74.9181 | 133.9782 | 109.0489 |
| Upper_depth_cm | int64 | 0 | 0.0% | 0 | 550 | 28.2497 |
| Lower_depth_cm | int64 | 0 | 0.0% | 1 | 750 | 56.5756 |
| Depth_cm | str | 0 | 0.0% |  |  |  |
| BD_g_cm3 | float64 | 3119 | 13.5% | 0.13 | 2.59 | 1.3777 |
| SOC_g_kg | float64 | 3119 | 13.5% | 0.01 | 640.4872 | 11.5662 |
| pH | float64 | 0 | 0.0% | 2.4 | 10.7 | 7.0599 |
| Sand_% | float64 | 6 | 0.03% | 0.91 | 91.68 | 32.1026 |
| Silt_% | float64 | 6 | 0.03% | 3.34 | 90.49 | 45.4828 |
| Clay_% | float64 | 6 | 0.03% | 1.92 | 64.37 | 22.4148 |
| DEM_m | float64 | 0 | 0.0% | -150.62 | 5748.85 | 1141.8091 |
| NDVI | float64 | 0 | 0.0% | -0.16 | 0.82 | 0.405 |
| MAT_°C | float64 | 0 | 0.0% | -8.56 | 25.74 | 10.9757 |
| MAP_mm | float64 | 0 | 0.0% | 1.25 | 192.33 | 69.1191 |
| PET_mm | float64 | 0 | 0.0% | 511.86 | 2265.17 | 1266.3451 |
| AI | float64 | 0 | 0.0% | 0.01 | 2.56 | 0.6788 |
| CLCD | str | 0 | 0.0% |  |  |  |
| SOCD_kg_m_2 | float64 | 0 | 0.0% | 0.0 | 400.43 | 3.1765 |
| SOCD_methods | str | 0 | 0.0% |  |  |  |
| References | str | 0 | 0.0% |  |  |  |
| Time | int64 | 0 | 0.0% | 2010 | 2023 | 2014.2628 |
| log1p_SOC_g_kg | float64 | 3119 | 13.5% | 0.01 | 6.4638 | 2.1016 |

## 3. Missing Value Analysis

Fields with missing values:

- **BD_g_cm3**: 3,119 missing (13.5%)
- **SOC_g_kg**: 3,119 missing (13.5%)
- **Sand_%**: 6 missing (0.0%)
- **Silt_%**: 6 missing (0.0%)
- **Clay_%**: 6 missing (0.0%)

**Key observation:** BD_g_cm3 and SOC_g_kg share the same 3,119 missing rows (13.5%), likely representing layers where SOC was not measured.

## 4. Target Variable Distribution

### SOC_g_kg
- Mean: 11.566, Median: 6.659, Std: 20.289
- Skewness: 10.84, Kurtosis: 201.50
- Range: [0.010, 640.487]
- IQR: [3.480, 13.051]

### pH
- Mean: 7.060, Median: 7.399, Std: 1.357
- Skewness: -0.43, Kurtosis: -0.85
- Range: [2.400, 10.700]
- IQR: [6.000, 8.186]

### SOCD_kg_m_2
- Mean: 3.177, Median: 2.090, Std: 4.844
- Skewness: 29.04, Kurtosis: 2046.58
- Range: [0.000, 400.430]
- IQR: [1.150, 3.770]

### SOC_g_kg log transform
- log1p(SOC): Mean=2.102, Std=0.845, Skew=0.54

## 5. Spatial Clustering Conclusion

- **Moran's I** = 0.5827 (expected under null: -0.0005)
- **Nearest-neighbor mean distance** = 22.89 km
- **Verdict:** Significant spatial clustering detected. Spatial cross-validation is **essential**.

## 6. Resource Estimates

- **Feature dimensions:** ~20 (excluding IDs/targets)
- **Training rows (all depths):** 23,103
- **Training rows (surface only 0-30cm):** 14,514
- **Estimated RAM during training:** ~0.5 GB (with overhead)
- **Estimated disk (processed):** ~6 MB
- **Estimated training time (GBM):** ~5–15 min (CPU), ~1–3 min (GPU)
- **Estimated training time (DNN):** ~10–30 min per fold (GPU)

## 7. Recommended Data Splitting Strategy

### Option 1: Spatial Block CV (5°×5° grid) — **Recommended**
- Divide China into 5°×5° grid cells
- Each fold holds out ~20% of grid cells
- Preserves spatial independence between train/test
- Most realistic estimate of map generalization ability

### Option 2: Climate-Zone Stratified CV
- Split by MAT-based climate zones (Alpine/Temperate/Warm/Tropical)
- Tests extrapolation to unseen climate conditions
- Useful if the goal is climate-change scenario prediction

### Option 3: Leave-One-Province-Out (LOPO)
- Requires province assignment (not directly available in data)
- Good for policy-relevant regional assessment
- High variance across folds; may be impractical for 30+ provinces

### Option 4: Random 5-Fold CV (baseline only)
- Use as baseline comparison only
- Will likely overestimate R² by 0.05–0.15 due to spatial leakage

**Primary recommendation:** Use **5°×5° spatial block CV** as the main evaluation strategy, with random CV as a lower-bound sanity check.

## 8. Recommended Data Cleaning Steps

1. **Handle missing SOC/BD:** 3,119 rows (13.5%) missing both BD and SOC. Options: (a) exclude these rows for SOC modeling; (b) impute using depth-profile regression or KNN.
2. **Handle missing texture:** 6 rows missing Sand/Silt/Clay – impute or drop.
3. **Outlier check:** SOC_g_kg max=400+ g/kg is extreme; verify if peat/wetland. Consider winsorizing at 99.5th percentile or log-transform.
4. **Log transform targets:** Both SOC_g_kg and SOCD_kg_m_2 are right-skewed. Use log1p transform for regression models.
5. **Feature engineering:**
   - Encode CLCD as one-hot or target-encode
   - Add depth_midpoint = (Upper + Lower) / 2
   - Consider interaction terms: MAT×MAP, sand×clay, elevation×AI
6. **Normalize features:** StandardScaler for continuous; one-hot for categorical.
7. **Profile-level aggregation:** For profile-level SOC prediction, aggregate depth layers using depth-weighted mean or predict per-layer.
