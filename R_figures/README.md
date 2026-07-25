# R Figures — 使用说明

## 文件清单

| 文件 | 说明 |
|---|---|
| `palette.R` | 统一配色方案 |
| `soil_project_figures.R` | 主图件脚本（弹窗选文件版） |
| `fig1_study_area_profiles.csv` | 研究区域剖面坐标 |
| `fig2a_depth_distribution.csv` | 深度分布 |
| `fig2b_soc_by_depth.csv` | SOC 按深度分组 |
| `fig2c_landcover.csv` | 土地覆盖类型 |
| `fig3_formal_aggregated.csv` | 模型性能汇总 |
| `fig4_grid_stats.csv` | 网格统计 |
| `fig5_delta_r2.csv` | ΔR² 数据 |
| `fig9_feature_importance.csv` | 特征重要性 |

## 运行方式

```r
# 在 RStudio 中打开此文件夹，然后运行：
source("soil_project_figures.R")
```

运行后会弹出 7 个文件选择窗口，依次选择上面的 CSV 文件即可。
最后选一个输出目录保存图件。
