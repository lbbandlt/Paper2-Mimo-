# Spatial Clustering Analysis – China SOCS V10

**Profile count:** 7955

**Coordinate range:** Lat 18.26°–51.63°, Lon 74.92°–133.98°

## 1. Nearest-Neighbor Distance Distribution

Computed on 2000 subsampled profiles:

| Statistic | Value (km) |
|---|---|
| Mean NN distance | 22.89 |
| Median NN distance | 16.68 |
| Std NN distance | 25.14 |
| Min NN distance | 0.0001 |
| Max NN distance | 428.46 |
| 5th percentile | 0.3627 |
| 95th percentile | 66.93 |

## 2. Moran's I (Spatial Autocorrelation of SOC)

- **Moran's I** = 0.5827
- **Expected I (null)** = -0.0005
- **Approx z-score** = 26.08
- **Conclusion:** Significant positive spatial autocorrelation (z > 1.96). SOC values are spatially clustered.

## 3. Profile Density by Land Cover Type (CLCD)

| CLCD | Profiles | Pct |
|---|---|---|
| Forest | 4348 | 54.7% |
| Cropland | 2310 | 29.0% |
| Other | 658 | 8.3% |
| Grassland | 639 | 8.0% |

## 4. Profile Density by Climate Zone (MAT-based)

| Climate Zone | Profiles | Pct |
|---|---|---|
| Alpine (<0°C) | 906 | 11.4% |
| Temperate (0-10°C) | 2808 | 35.3% |
| Warm (10-20°C) | 3730 | 46.9% |
| Tropical (>20°C) | 511 | 6.4% |

## 5. Conclusions on Spatial Blocking

### Spatial clustering assessment

- The mean nearest-neighbor distance (22.9 km) indicates well-distributed sampling.
- Moran's I = 0.583 indicates **strong positive spatial autocorrelation**. Nearby profiles have similar SOC values.

### Implications for spatial cross-validation

- **Spatial blocking is recommended** to avoid optimistic bias from spatial data leakage.
- Random CV will overestimate performance because nearby profiles share spatial autocorrelation.
- Spatial block CV (e.g., 5°×5° grid or climate-zone stratified) better estimates true generalization.
