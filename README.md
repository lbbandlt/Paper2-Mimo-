# 深度与空间双重约束下中国土壤有机碳机器学习预测的泛化能力评估

**Evaluating generalization of machine learning for soil organic carbon prediction in China under spatial and depth constraints**

---

## 研究背景

土壤有机碳（Soil Organic Carbon, SOC）是陆地碳循环的关键组成部分，其精准制图对于理解碳收支、指导农业管理和应对气候变化具有重要意义。近年来，机器学习（Machine Learning, ML）方法在 SOC 空间预测中得到广泛应用，但大多数研究采用随机交叉验证来评估模型性能，这种做法忽略了土壤属性固有的空间自相关性，可能导致对模型泛化能力的系统性高估。

与此同时，现有 ML 预测研究多聚焦于表层土壤（0–20 cm 或 0–30 cm），对深层土壤（>30 cm）的可预测性关注不足。深层 SOC 储量约占全球土壤碳库的一半以上，但其与环境因子的关系、可用训练样本的密度以及预测不确定性均与表层存在本质差异。缺乏对深度维度的系统评估，使得当前 SOC 制图结果在深度方向上的可靠性存疑。

本研究旨在构建一个同时考虑空间维度和深度维度的系统性验证框架，量化传统随机划分方法导致的精度虚高程度，揭示 SOC 预测能力随深度变化的规律及其驱动因素，为 SOC 制图领域的模型选择和验证策略提供方法论参考。

## 数据来源

**China SOCS Database V10** (Chen et al., 2025, *Nature Scientific Data* 12, 1480)

- DOI: [10.5281/zenodo.17304024](https://doi.org/10.5281/zenodo.17304024)
- 样本量: 23,103 样本层，7,955 个土壤剖面
- 空间范围: 中国全国（Lat 18.26°–51.63°, Lon 74.92°–133.98°）
- 许可: CC-BY 4.0

## 核心故事线

1. **随机划分因空间自相关高估 SOC 预测精度** — 传统随机交叉验证因相邻样本在训练集和测试集中共现，导致模型性能被系统性高估。
2. **空间阻断验证揭示真实泛化能力** — 通过气候区或空间分块的 Leave-one-out 设计，隔离空间自相关的影响，暴露模型在未见区域的真实预测能力。
3. **深层土壤可预测性系统低于表层** — 深层 SOC 与环境因子的耦合关系更弱、训练样本更稀疏，导致预测精度随深度显著下降。
4. **协变量重要性随深度变化解释了深度依赖差异** — 地表过程（如 NDVI、土地覆盖）对表层 SOC 解释力强，而深层 SOC 更受地质和水文过程控制，这种驱动因子的深度分异是可预测性差异的根本原因。

## 目录结构

```
soil_project/
├── README.md                       # 项目主页（本文件）
├── DATA_AVAILABILITY.md            # 数据可用性声明
├── REPRODUCIBILITY.md              # 复现指南
├── MANUSCRIPT_PLAN.md              # 稿件计划
├── environment/
│   └── requirements-python.txt     # Python 依赖
├── data_inventory/                 # 数据清单
├── data_splits/                    # 数据划分方案
├── notebooks/                      # Jupyter notebooks
├── scripts/                        # 训练与分析脚本
├── results/
│   ├── source_data/                # 图表源数据
│   └── qa/                         # 质量保证记录
├── figures/
│   ├── palette.R                   # R 配色方案
│   └── README_运行说明.md           # 图件生成说明
└── manuscript/                     # 稿件写作
```

## 快速开始

```bash
# 1. 克隆仓库
git clone <repo-url> && cd soil_project

# 2. 创建 Python 环境
conda create -n soc python=3.10 -y
conda activate soc
pip install -r environment/requirements-python.txt

# 3. 获取数据
# 将 SOCS_V10.csv 放入 data_raw/ 目录
# DOI: https://doi.org/10.5281/zenodo.17304024

# 4. 运行预处理
python scripts/preprocessing.py

# 5. 训练模型
python scripts/train_models.py

# 6. 生成图件
# 在 RStudio 中运行 figures/ 目录下的 R 脚本
```

## 引用

```bibtex
@article{chen2025china,
  title={China SOCS Database V10},
  author={Chen, Shuisen and others},
  journal={Nature Scientific Data},
  volume={12},
  pages={1480},
  year={2025},
  doi={10.1038/s41597-025-04785-0}
}
```
