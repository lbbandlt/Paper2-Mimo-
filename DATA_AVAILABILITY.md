# 数据可用性声明

## 数据集信息

| 项目 | 内容 |
|------|------|
| **数据集名称** | China SOCS Database V10 |
| **DOI** | [10.5281/zenodo.17304024](https://doi.org/10.5281/zenodo.17304024) |
| **论文** | Chen et al. (2025) *Nature Scientific Data* 12, 1480 |
| **许可证** | CC-BY 4.0 |
| **文件** | SOCS_V10.csv (3.6 MB, GBK 编码) |
| **样本量** | 23,103 样本层，7,955 个土壤剖面 |
| **空间范围** | 中国全国（Lat 18.26°–51.63°, Lon 74.92°–133.98°） |
| **深度范围** | 0–200+ cm 多层 |

## 目标变量

| 变量 | 说明 | 单位 |
|------|------|------|
| SOC | 土壤有机碳含量 | g/kg |
| SOCD | 土壤有机碳密度 | kg/m² |
| pH | 酸碱度 | — |

## 环境协变量

| 类别 | 变量 | 来源 |
|------|------|------|
| **土壤理化** | BD（容重）、Sand、Silt、Clay | 原始数据库 |
| **地形** | DEM（数字高程模型） | SRTM / ASTER |
| **植被** | NDVI（归一化植被指数） | MODIS |
| **气候** | MAT（年均温）、MAP（年降水量）、PET（潜在蒸散）、AI（干旱指数） | WorldClim / CRU |
| **土地利用** | CLCD（中国土地覆盖数据） | CLCD |

## 本项目中的数据存放

```
data_raw/
└── SOCS_V10.csv          # 原始数据（< 4 MB，可直接存于 GitHub）

data_inventory/            # 数据清单与质量检查
data_splits/               # 训练/测试划分方案
```

## 大文件归档策略

| 数据类型 | 大小估计 | 归档方式 |
|----------|----------|----------|
| 原始数据 SOCS_V10.csv | < 4 MB | 可直接放入 GitHub 仓库 |
| 模型就绪数据（预处理后） | 10–100 MB | Zenodo DOI 归档 |
| 模型训练 checkpoint | 100 MB – 1 GB | Zenodo DOI 归档 |
| 大规模中间结果 | 视情况 | Zenodo DOI 归档 |

## 引用

使用本项目数据时，请同时引用原始数据集论文：

> Chen, S. et al. (2025). China SOCS Database V10. *Nature Scientific Data*, 12, 1480. https://doi.org/10.1038/s41597-025-04785-0
