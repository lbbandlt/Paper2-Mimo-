China Soil Organic Carbon Stock (SOCS) Database, Version 10 (V10)

1. Dataset Overview

We present Version 10 (V10) of the China Soil Organic Carbon Stock (SOCS) Database, a national-scale dataset derived from 23,103 rigorously validated soil samples (7,995 profiles) using ensemble pedotransfer function (PTF) modeling.
After re-validation and correction of profile statistics in the original files, the total number of profiles decreased to 7,995.
The final V10 dataset provides standardized soil profile information, environmental covariates, and metadata, ensuring consistency and application-readiness.

This dataset supports the manuscript:
Chen et al. (2025). A national soil organic carbon density dataset (2010–2024) in China using ensemble modelling based pedotransfer functions.

Users must cite both the repository (https://doi.org/10.1038/s41597-025-05863-3) and the above publication.
Technical inquiries should be directed to Dr. Songchao Chen (chensongchao@zju.edu.cn).

2. Relationship Between Versions

- V8: Developmental dataset including field observations and model predictions, used for training ensemble algorithms. Code is available on GitHub.
- V9: The first finalized dataset, harmonized and validated for end-users.
- V10: Updated, quality-checked dataset with unified metadata structure, improved variable naming consistency, and expanded coverage of sampling years (2010–2024). V10 supersedes V9 for applications.

Each version is independent:
- V8 supports reproducibility of modeling.
- V9 was the initial application-ready dataset.
- V10 is the latest standardized dataset for end-users.

3. Data Structure

Each row corresponds to a soil layer within a profile, linked to source references and the field sampling year.

Main fields include:
- Samples: Unique sample identifier
- Profile: Profile ID (multiple layers per profile)
- Latitude, Longitude: Geographic coordinates (WGS84)
- Upper_depth_cm, Lower_depth_cm: Layer boundaries (cm)
- Depth_cm: Depth range (string, e.g., "0–20")
- BD_g_cm3: Bulk density (g/cm³)
- SOC_g_kg: Soil organic carbon concentration (g/kg)
- SOCD_kg_m-2: Soil organic carbon density (kg/m²)
- pH: Soil pH (measured in water or KCl, source-specific)
- Sand_%, Silt_%, Clay_%: Soil particle size fractions (%)
- DEM_m: Elevation from SRTM DEM (m)
- NDVI: MODIS NDVI (dimensionless)
- MAT_°C: Mean annual temperature (°C)
- MAP_mm: Mean annual precipitation (mm)
- PET_mm: Potential evapotranspiration (mm)
- AI: Aridity index
- CLCD: Land cover class (numeric code; see below; numeric coding is maintained for backward compatibility with V8/V9)
- SOCD__methods: Method for SOCD estimation (direct measurement / modeled)
- References: Data source (published papers, datasets)
- Time: Field sampling year

4. Special Notes

a) Source references & sampling year
   Every record includes the original reference (e.g., Liu et al., 2022) and the year of field sampling for traceability.

b) Records with only SOCD
   For a subset of sources (e.g., Xu et al.), only SOCD was reported. In these records, BD_g_cm3 and SOC_g_kg are not provided and are recorded as NA.

c) Land cover classification (CLCD)
   - 1 = Cropland
   - 2 = Forest
   - 3 = Grassland
   - 4 = Other

d) Depth coverage (>200 cm)
   For layers deeper than 200 cm, soil properties cannot be consistently extracted from National Soil Information Grids of China. The corresponding fields in these layers are recorded as NA.

5. Usage and Citation

- For scientific applications: Use V10 as the harmonized, validated dataset.
- For reproducibility / algorithm training: Refer to V8 with GitHub model code.
- V9 remains archived but is superseded by V10.

Citation requirement:
- Repository DOI: https://doi.org/10.1038/s41597-025-05863-3
- Publication: Chen et al., 2025
