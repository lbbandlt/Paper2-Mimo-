# 图件生成运行说明

## 前置准备

### 1. 安装 R 包

在 RStudio Console 中运行：

```r
install.packages(c(
  "ggplot2", "sf", "rnaturalearth", "rnaturalearthdata",
  "tidyr", "dplyr", "patchwork", "RColorBrewer", "scales",
  "readr", "viridis"
))
```

### 2. 目录约定

```
figures/
├── palette.R              # 配色方案（所有图脚本共享）
├── README_运行说明.md      # 本文件
├── fig1_study_area.R      # 研究区域图
├── fig2_data_overview.R   # 数据概览图
├── fig3_performance.R     # 模型性能对比
├── fig4_spatial_delta.R   # 空间阻断退化地图
├── fig5_migration.R       # 跨气候区迁移矩阵
├── fig6_depth_curve.R     # 深度可预测性曲线
├── fig7_covariate_depth.R # 协变量重要性深度变化
└── fig8_conceptual.R      # 概念框架图
```

输出文件统一保存到 `figures/output/`（脚本会自动创建）。

---

## 运行方式

### 方式一：RStudio 交互运行（推荐）

1. 打开 RStudio
2. `File → Open` 选择 `figures/` 目录下的 `.R` 脚本
3. 将工作目录设为项目根目录：
   ```r
   setwd("/path/to/soil_project")
   ```
4. 逐行或选中代码块后 `Ctrl+Enter`（macOS: `Cmd+Enter`）运行
5. 图件同时显示在 **Plots 窗格**（右下角）并自动保存为 PDF/PNG

### 方式二：命令行批量生成

```bash
cd soil_project
for script in figures/fig*.R; do
  echo "Running $script ..."
  Rscript "$script"
done
```

### 方式三：单张图生成

```bash
cd soil_project
Rscript figures/fig1_study_area.R
```

---

## 输出格式

每个脚本默认生成两种格式：

| 格式 | 用途 | 分辨率 |
|------|------|--------|
| `.pdf` | 投稿（矢量图，可编辑） | 矢量 |
| `.png` | 预览 / PPT | 300 dpi |

输出路径：`figures/output/fig1_study_area.pdf` 等。

---

## 常见问题

**Q: 出现 "could not find function" 错误？**
A: 检查是否安装了所有必需的 R 包。运行脚本开头的 `library()` 逐个排查。

**Q: 中文字体显示为方块？**
A: 在脚本开头添加：
```r
# macOS
theme_set(theme_minimal(base_family = "PingFang SC"))
# Windows
theme_set(theme_minimal(base_family = "Microsoft YaHei"))
# Linux
theme_set(theme_minimal(base_family = "Noto Sans CJK SC"))
```

**Q: 输出图片中文字体不显示（PDF）？**
A: 使用 `ggsave()` 时指定 `device = cairo_pdf`：
```r
ggsave("figures/output/fig1.pdf", device = cairo_pdf, width = 8, height = 6)
```

**Q: 如何修改配色？**
A: 编辑 `figures/palette.R`，所有图脚本都 `source()` 了此文件。
