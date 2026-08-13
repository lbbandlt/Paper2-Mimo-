# SOC spatial-generalization manuscript rebuild

This revision replaces the earlier fixed-grid comparison with a profile-safe,
distance-aware validation workflow and a five-figure Chinese manuscript.

## Main deliverables

- `manuscript/export/manuscript_cn_revised_5fig.docx`: complete Chinese draft.
- `figures/Figure2_depth_harmonization.png`: standard-depth harmonization.
- `figures/Figure3_multiscale_validation.png`: multiscale spatial validation.
- `figures/Figure4_buffer_depth_dependence.png`: explicit buffers and depth dependence.
- `figures/Figure5_robustness_and_explanation.png`: robustness, bulk-density ablation and grouped permutation.
- `R_figures/Figures2_to_5_revised.R`: reproducible R plotting script.
- `results/source_data/revised/`: source data for the revised figures.

## Analysis changes

- All train/test splits are grouped by soil profile.
- Irregular layers are harmonized to 0–20, 20–50, 50–100 and 100–200 cm.
- Spatial validation is repeated across four grid scales and four grid origins.
- Explicit 0, 50, 100 and 200 km exclusion buffers are compared with equal-size controls.
- Depth conclusions are checked using equal sample size, equal spatial coverage and paired-profile designs.
- Bulk density is evaluated by retraining ablation and grouped permutation on spatial test folds.

The earlier two-figure assembly and old Figure 8 numbering are not part of this revision.
