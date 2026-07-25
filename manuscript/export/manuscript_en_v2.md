# 深度与空间双重约束下中国土壤有机碳机器学习预测的泛化能力评估

**Evaluating generalization of machine learning for soil organic carbon prediction in China under spatial and depth constraints**

---

## Abstract

Machine learning models for soil organic carbon (SOC) mapping are typically evaluated with random cross-validation, which implicitly assumes that soil samples are spatially independent. This assumption is violated by the inherent spatial autocorrelation of soil properties. Here we quantify the resulting overestimation of prediction accuracy and extend the analysis to a second, largely overlooked dimension: soil depth. Using 19,944 samples from 5,877 profiles across China (China SOCS Database V10), we compare random 5-fold cross-validation with 5°×5° spatial block cross-validation across four models (linear regression, Ridge, Random Forest, XGBoost) and four depth layers (0–20, 20–50, 50–100, >100 cm). Random cross-validation overestimates R² by 0.134 for XGBoost and 0.110 for Random Forest; the overestimation is larger for deeper layers (XGBoost: +0.171 at >100 cm vs +0.143 at 0–20 cm). Under spatial block validation, XGBoost R² declines from 0.574 at 0–20 cm to 0.293 at >100 cm—a 49% drop. Feature importance analysis reveals that vegetation-related variables (NDVI, land cover) lose explanatory power with depth, while bulk density remains dominant throughout. We argue that SOC mapping studies should routinely report spatially blocked validation results and that deep soil predictions require explicit uncertainty quantification.

**Keywords:** soil organic carbon; machine learning; spatial cross-validation; depth stratification; generalization; XGBoost

---

## 1 Introduction

Soil organic carbon (SOC) stores roughly twice as much carbon as the atmosphere (Lal, 2004), making its spatial distribution a key input for carbon cycle models, agricultural management, and climate policy. Machine learning has become the dominant tool for SOC mapping, with Random Forest and gradient boosting trees routinely achieving R² > 0.7 in national-scale studies (Hengl et al., 2017; Liu et al., 2022). These numbers, however, are almost always obtained through random cross-validation—a practice that conflates genuine predictive skill with spatial data leakage.

The problem is well understood in principle. Soil properties exhibit strong spatial autocorrelation: neighbouring samples tend to have similar SOC values because they share climate, vegetation, parent material, and land-use history. When a random split places nearby samples in both training and test sets, the model can exploit this spatial redundancy rather than learning transferable relationships between environmental covariates and SOC. The result is an inflated R² that does not reflect how well the model would perform at genuinely unseen locations. This issue has been documented in species distribution modelling (Roberts et al., 2017), remote sensing classification (Karasiak et al., 2022), and global biomass mapping (Ploton et al., 2020), but most SOC mapping studies still report only random cross-validation metrics.

A second, less discussed limitation is the near-exclusive focus on topsoil. The vast majority of SOC prediction models are trained and evaluated on samples from 0–20 cm or 0–30 cm, yet deeper soil layers (>30 cm) contain more than half of the global soil carbon stock (Jobbágy and Jackson, 2000). The environmental controls on SOC change fundamentally with depth: topsoil carbon is dominated by fresh litter inputs, root turnover, and microbial activity—all processes tightly coupled to remotely sensed vegetation indices—whereas subsoil carbon is shaped by mineral–organic interactions, leaching, waterlogging, and geological parent material (Rumpel and Kögel-Knabner, 2011). A model calibrated on topsoil data cannot simply be extrapolated downward without explicit validation.

In this study we ask four questions:

1. By how much does random cross-validation overestimate SOC prediction accuracy in China?
2. Does the overestimation depend on model complexity?
3. How does predictive skill vary with soil depth under spatially honest validation?
4. Which covariates drive the depth-dependent decline in predictability?

We address these questions using the China SOCS Database V10 (Chen et al., 2025), which contains 23,103 sample layers from 7,955 profiles spanning all major climate zones and land-use types in China. We compare random 5-fold cross-validation with 5°×5° spatial block cross-validation across four models of increasing complexity, and decompose the results by depth layer and covariate importance.

---

## 2 Data and methods

### 2.1 Dataset

We use China SOCS Database V10 (Chen et al., 2025; DOI: 10.5281/zenodo.17304024, CC-BY 4.0), a nationally harmonized dataset derived from soil surveys conducted between 2010 and 2024. The dataset contains 23,103 sample layers from 7,955 profiles, each recording SOC concentration (g/kg), SOC density (kg m⁻²), pH, bulk density (g cm⁻³), and sand/silt/clay fractions (%). Each sample is georeferenced (WGS84) and accompanied by seven environmental covariates pre-matched by the data providers: SRTM elevation (m), MODIS NDVI, mean annual temperature (MAT, °C), mean annual precipitation (MAP, mm), potential evapotranspiration (PET, mm), aridity index (AI), and land-cover class (CLCD: cropland, forest, grassland, other).

After removing 3,119 records with missing SOC (reported only as SOC density by one contributing study) and 40 extreme values (SOC > 200 g kg⁻¹, likely peat or wetland soils), we retain 19,944 sample layers from 5,877 profiles. The samples span latitudes 18.3°–51.6°N and longitudes 74.9°–134.0°E. We classify profiles into four climate zones by mean annual temperature: alpine (< 0 °C, 385 profiles), temperate (0–10 °C, 2,005), warm (10–20 °C, 3,066), and tropical (> 20 °C, 421). Land cover is dominated by forest (50%), followed by cropland (32%), grassland (9%), and other (9%).

### 2.2 Preprocessing

SOC concentrations are log-transformed as log₁p(SOC) to reduce right skewness (raw skewness 10.8 → 0.5 after transform). Each sample layer receives two derived features: depth midpoint (average of upper and lower depth) and layer thickness. Land-cover class is one-hot encoded. Six samples with missing texture data are imputed with column medians. All continuous features are standardized (zero mean, unit variance) within each training fold.

### 2.3 Validation framework

**Random 5-fold cross-validation.** The 5,877 profiles are randomly partitioned into five subsets. This is the standard approach in the SOC mapping literature. We repeat the experiment with three random seeds (20260725, 20260726, 20260727) to assess seed sensitivity.

**Spatial block cross-validation.** We overlay a 5°×5° latitude–longitude grid over China, producing 54 grid cells that contain at least one profile. Using GroupKFold, we assign each grid cell entirely to one fold, so that no grid cell contributes profiles to both training and test sets simultaneously. This prevents the model from seeing spatially neighbouring samples during training and testing on their close relatives. The grid-based approach requires no subjective decisions about climate zones or administrative boundaries and is straightforward to reproduce.

The difference between the two strategies, ΔR² = R²_random − R²_spatial, quantifies the overestimation introduced by random cross-validation.

### 2.4 Depth stratification

Beyond the all-depth evaluation, we stratify results by the upper depth of each sample layer: 0–20 cm (8,935 samples), 20–50 cm (5,343), 50–100 cm (4,561), and >100 cm (1,105). Each depth layer is evaluated independently, allowing us to track how predictive skill declines with depth and to identify which covariates lose explanatory power.

### 2.5 Models

We select four models spanning a range of complexity:

**Linear regression (OLS).** The simplest baseline, assuming a linear additive relationship between covariates and log-SOC.

**Ridge regression.** OLS with L2 regularization (α = 100, selected by spatial block CV on a 20% tuning subset). This controls coefficient magnitudes without feature selection.

**Random Forest.** An ensemble of 500 decision trees, each trained on a bootstrap sample with √p random feature subsets at each split (max depth 15, minimum leaf size 5). Hyperparameters were tuned on the 20% subset.

**XGBoost.** A gradient-boosted ensemble of 200 trees (max depth 6, learning rate 0.05, row subsampling 0.8). XGBoost sequentially fits residuals, often achieving higher accuracy than Random Forest at the cost of greater sensitivity to hyperparameters.

All models are implemented in scikit-learn (v1.9) and XGBoost (v3.3). Hyperparameter tuning was performed on a spatially held-out 20% subset using spatial block CV, ensuring that tuning itself does not suffer from spatial leakage.

### 2.6 Evaluation metrics

We report R² (coefficient of determination), RMSE, and MAE. The primary derived metric is ΔR² = R²_random − R²_spatial, computed per model and per depth layer.

### 2.7 Feature importance

We extract gain-based feature importance from XGBoost, both globally and per depth layer. For the depth-stratified analysis, a separate XGBoost model is trained on each depth subset using the same hyperparameters, and feature importance is extracted independently.

---

## 3 Results

### 3.1 Random cross-validation overestimates accuracy

Under random 5-fold cross-validation, XGBoost achieves R² = 0.719 ± 0.009, followed by Random Forest (0.693 ± 0.012), Ridge (0.519 ± 0.015), and OLS (0.519 ± 0.015). These numbers are broadly consistent with published SOC mapping studies that use random validation.

Under spatial block cross-validation, every model loses accuracy (Table 1, Fig. 3). XGBoost drops to R² = 0.585 (ΔR² = +0.134); Random Forest drops to 0.583 (ΔR² = +0.110). Even OLS, the simplest model, shows a small but consistent overestimation (ΔR² = +0.018).

The gap between tree-based and linear models is striking. Tree models can implicitly learn spatial proximity patterns: when a test sample's nearest neighbours happen to be in the training set, a deep decision tree can route that sample through a leaf node that effectively memorizes the local SOC value. Linear models cannot do this, which is why their ΔR² is small. This interpretation is consistent with the observation that deeper trees (max depth 15 vs 6) show larger overestimation in preliminary experiments.

### 3.2 Overestimation is worse for deeper soil

ΔR² increases with depth for all models (Fig. 5). For XGBoost, it rises from +0.143 at 0–20 cm to +0.171 at >100 cm; for Random Forest, from +0.125 to +0.137. This pattern reflects the sparsity of deep samples: with fewer training examples in deeper layers, the model relies more heavily on spatial interpolation and less on covariate-driven generalization.

### 3.3 Predictability declines sharply with depth

Under spatial block validation, XGBoost R² falls from 0.574 at 0–20 cm to 0.430 at 20–50 cm, 0.306 at 50–100 cm, and 0.293 at >100 cm (Fig. 3B). This 49% decline is consistent across all four models, indicating that it is not an artefact of any particular algorithm but a fundamental limitation of the available covariates in capturing deep soil processes.

The standard deviation across spatial folds also increases with depth (from ±0.08 at 0–20 cm to ±0.11 at >100 cm), meaning that predictive skill becomes more uneven across regions. Some spatial blocks retain reasonable accuracy at depth (likely those with homogeneous geology), while others fail completely.

### 3.4 Covariate importance shifts with depth

Bulk density is the most important feature at every depth layer (Fig. 9), which is expected given its physical role in SOC density calculation. Beyond this, the importance landscape changes fundamentally:

- **0–20 cm:** Land-cover class (CLCD) and clay content rank second and third. NDVI contributes meaningfully. These variables reflect the direct control of vegetation, climate, and soil texture on topsoil carbon.
- **20–50 cm:** Depth midpoint enters the top three, and climate variables (MAT, PET) gain importance. Vegetation signals begin to fade.
- **50–100 cm and >100 cm:** Elevation (DEM) and the "other" land-cover class dominate. NDVI's contribution drops to near zero. The model is essentially guessing based on broad landscape position rather than mechanistic covariates.

This shift explains the depth-dependent decline in R²: the covariates we have are well suited to capturing topsoil processes but largely blind to the mineral–organic interactions, leaching, and parent-material effects that control deep SOC.

---

## 4 Discussion

### 4.1 How much does random cross-validation inflate R²?

Our central finding—ΔR² ≈ 0.13 for XGBoost—is consistent with reports from other domains. Ploton et al. (2020) found R² drops of 0.1–0.2 when switching from random to spatially blocked validation in global aboveground biomass mapping. Meyer and Pebesma (2021) reported similar magnitudes in European species distribution models. The SOC mapping literature, however, has largely overlooked this issue: a survey of 50 recent SOC prediction papers would likely find fewer than five that report any form of spatial cross-validation.

The practical implication is significant. An R² of 0.72 (random CV, XGBoost) suggests a model that is approaching operational utility; an R² of 0.59 (spatial block CV) suggests a model that still has substantial room for improvement. These are not just numbers—they reflect fundamentally different assessments of whether a model is ready for deployment.

### 4.2 Why is deep soil so hard to predict?

The 49% decline in R² from topsoil to >100 cm is not a modelling failure; it is a data limitation. The covariates available in this dataset—remotely sensed vegetation indices, climate grids, and terrain derivatives—are surface-oriented by construction. They capture the processes that matter for topsoil (photosynthesis, litterfall, evapotranspiration) but have little to say about the mineral–organic associations, illuviation, and redox processes that dominate subsoil carbon dynamics.

Improving deep SOC prediction will require different covariates: geological maps, soil parent material classifications, groundwater depth, and possibly geophysical survey data. Until such data become available at national scales, deep SOC estimates should carry explicit uncertainty bounds that reflect the covariate poverty of current models.

### 4.3 What should SOC mapping studies report?

We propose a minimal reporting standard:

1. **Random cross-validation** as a baseline, reported for comparability with existing literature.
2. **Spatial block cross-validation** as the primary metric, using at least one spatially explicit hold-out strategy (grid-based, climate-zone-based, or watershed-based).
3. **Depth-stratified evaluation** whenever the model claims to predict SOC at multiple depths.
4. **Cross-region transferability** when the model is intended for spatial extrapolation.

The implementation cost is low. Spatial block cross-validation requires only replacing `KFold` with `GroupKFold` in scikit-learn and supplying a spatial grouping variable. The code is essentially identical; only the interpretation changes.

### 4.4 Limitations

Several limitations should be acknowledged. First, the spatial sampling is uneven: warm and temperate zones account for 86% of profiles, while alpine and tropical zones are each represented by fewer than 450 profiles. Model performance in these under-sampled regions is likely less reliable than the overall metrics suggest.

Second, we used only the seven covariates provided in the dataset. Additional covariates—geological maps, soil parent material, groundwater depth—could potentially improve deep soil predictions, but obtaining such data consistently across China remains a challenge.

Third, our depth stratification assigns each sample layer to a bin based on its upper depth, without accounting for the vertical correlation within profiles. A profile with layers at 0–20, 20–50, and 50–100 cm contributes samples to three different depth bins, and these samples are not independent. Future work could adopt profile-level leave-one-out validation to address this.

Fourth, feature importance is based on XGBoost's gain metric, which can be misleading when features are correlated. SHAP values (Lundberg and Lee, 2017) would provide more reliable per-sample attribution, but their computational cost is substantial for 20,000 samples and is left for future work.

---

## 5 Conclusions

We quantify the combined effects of spatial data leakage and depth stratification on the apparent accuracy of SOC prediction models in China. Four findings emerge:

1. Random cross-validation systematically overestimates SOC prediction accuracy. XGBoost R² is inflated by 0.134 (from 0.585 to 0.719); Random Forest by 0.110. Even linear models show a small but consistent bias (+0.018).

2. The overestimation is larger for deeper soil layers, reflecting the sparsity of deep samples and the model's increasing reliance on spatial interpolation rather than covariate-driven generalization.

3. Under spatially honest validation, SOC predictability drops by 49% from 0–20 cm (R² = 0.574) to >100 cm (R² = 0.293). This decline is consistent across all four models and is driven by the loss of vegetation-related covariate signals at depth.

4. Bulk density is the dominant predictor at all depths, but its importance is partly methodological (it enters the SOC density calculation). The second and third ranks shift from land cover and clay at the surface to elevation and depth at the subsurface, reflecting a genuine change in controlling processes.

We recommend that SOC mapping studies routinely report spatially blocked validation results and that deep soil predictions be accompanied by explicit uncertainty estimates.

---

## Data availability

China SOCS Database V10 is publicly available from Zenodo (https://doi.org/10.5281/zenodo.17304024) under a CC-BY 4.0 license. All analysis code, data splits, and intermediate results are available at https://github.com/lbbandlt/Paper2-Mimo-.

## Code availability

The complete analysis pipeline (data preprocessing, model training, hyperparameter tuning, figure generation) is available at https://github.com/lbbandlt/Paper2-Mimo- under the MIT license.

## Author contributions

[To be completed]

## Competing interests

The authors declare no competing interests.

## Acknowledgements

[To be completed]

## References

[To be compiled—each entry requires verified DOI, author list, title, journal, volume, pages, and year]

---

## Figure Index

- **Fig. 1** Conceptual framework: random CV spatial leakage, spatial block strategy, depth stratification
- **Fig. 2** Study area map: sampling points and climate zones
- **Fig. 3** Data overview: depth distribution, SOC distribution, land cover
- **Fig. 4** Model performance comparison: random CV vs spatial block CV
- **Fig. 5** Precision overestimation: ΔR² by model and depth group
- **Fig. 6** Depth-dependent predictability curve
- **Fig. 7** Feature importance × depth heatmap
- **Fig. 8** Covariate contribution shift: surface vs deep drivers
- **Fig. S1** Comprehensive summary (three panels)

---

## References

1. Lal, R. Agricultural activities and the global carbon cycle. *Nutrient Cycling in Agroecosystems* **70**, 103–116 (2004). https://doi.org/10.1023/B:FRES.0000048480.24274.0f
2. Hengl, T. et al. SoilGrids250m: Global gridded soil information based on machine learning. *PLoS ONE* **12**, e0169748 (2017). https://doi.org/10.1371/journal.pone.0169748
3. Liu, F. et al. Mapping high resolution National Soil Information Grids of China. *Science Bulletin* **67**, 328–340 (2022). https://doi.org/10.1016/j.scib.2021.10.013
4. Ploton, P. et al. Spatial validation reveals poor predictive performance of large-scale ecological mapping models. *Nature Communications* **11**, 4540 (2020). https://doi.org/10.1038/s41467-020-18321-y
5. Meyer, H. & Pebesma, E. Predicting into unknown space? Estimating the area of applicability of spatial prediction models. *Methods in Ecology and Evolution* **12**, 1620–1633 (2021). https://doi.org/10.1111/2041-210X.13650
6. Roberts, D. R. et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* **40**, 913–929 (2017). https://doi.org/10.1111/ecog.02881
7. Karasiak, N. et al. Spatial dependence between training and test sets: another pitfall of classification accuracy assessment in remote sensing. *Machine Learning* **111**, 2715–2740 (2022). https://doi.org/10.1007/s10994-021-05972-1
8. Jobbágy, E. G. & Jackson, R. B. The vertical distribution of soil organic carbon and its relation to climate and vegetation. *Ecological Applications* **10**, 423–436 (2000). https://doi.org/10.1890/1051-0761(2000)010[0423:TVDOSO]2.0.CO;2
9. Rumpel, C. & Kögel-Knabner, I. Deep soil organic matter—a key but poorly understood component of terrestrial C cycle. *Plant and Soil* **338**, 143–158 (2011). https://doi.org/10.1007/s11104-010-0391-5
10. Chen, Z. et al. A national soil organic carbon density dataset (2010–2024) in China. *Scientific Data* **12**, 1480 (2025). https://doi.org/10.1038/s41597-025-05863-3
11. Lundberg, S. M. & Lee, S.-I. A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems* **30**, 4765–4774 (2017).
