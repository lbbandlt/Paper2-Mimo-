# 复现指南

本指南说明如何从零开始复现本研究的全部分析结果。

---

## 1. 环境要求

| 软件 | 版本要求 |
|------|----------|
| Python | ≥ 3.10 |
| R | ≥ 4.3 |
| Git | ≥ 2.30 |

## 2. Python 依赖

```bash
# 创建虚拟环境
conda create -n soc python=3.10 -y
conda activate soc

# 安装依赖
pip install -r environment/requirements-python.txt
```

主要依赖包：

| 包名 | 最低版本 | 用途 |
|------|----------|------|
| numpy | 1.24 | 数值计算 |
| pandas | 2.0 | 数据处理 |
| scikit-learn | 1.3 | 机器学习 |
| xgboost | 2.0 | 梯度提升树 |
| lightgbm | 4.0 | 梯度提升树 |
| matplotlib | 3.7 | 绑图 |
| seaborn | 0.12 | 统计可视化 |
| geopandas | 0.13 | 空间数据 |
| shapely | 2.0 | 几何操作 |
| pysal | 23.0 | 空间分析 |
| scipy | 1.11 | 科学计算 |
| statsmodels | 0.14 | 统计建模 |

## 3. 数据获取

```bash
# 步骤 1：从 Zenodo 下载数据
# DOI: https://doi.org/10.5281/zenodo.17304024
wget https://zenodo.org/records/17304024/files/SOCS_V10.csv

# 步骤 2：放入 data_raw 目录
mkdir -p data_raw
mv SOCS_V10.csv data_raw/

# 步骤 3：验证文件完整性
sha256sum data_raw/SOCS_V10.csv
# 预期校验值：<SHA256_PLACEHOLDER>
```

## 4. 预处理流程

```bash
python scripts/preprocessing.py
```

预处理步骤包括：
1. 读取 GBK 编码的原始 CSV
2. 缺失值检查与处理
3. 异常值识别（3σ 准则 + 领域知识）
4. 坐标系标准化（WGS84）
5. 环境协变量提取与匹配
6. 深度层标准化
7. 输出模型就绪数据集

## 5. 模型训练流程

```bash
# 基线模型
python scripts/train_baseline.py

# 空间阻断验证
python scripts/train_spatial_block.py

# 深度分层验证
python scripts/train_depth_stratified.py
```

### 验证框架

| 验证方案 | 说明 |
|----------|------|
| 随机划分 | 10 折交叉验证（基线） |
| 空间阻断 | Leave-one-climate-zone-out |
| 深度分层 | 按深度层独立建模 |

### 模型列表

| 模型 | 类型 |
|------|------|
| MLR | 多元线性回归 |
| RF | 随机森林 |
| XGBoost | 梯度提升树 |
| MLP | 多层感知机 |
| 1D-CNN | 一维卷积网络 |
| LSTM | 长短期记忆网络 |

## 6. 图件生成流程

```bash
# 在 RStudio 中打开 figures/ 目录下的 R 脚本
# 详见 figures/README_运行说明.md
```

## 7. 文件校验值

> 以下 SHA256 校验值为占位符，待完整运行后更新。

```
# 原始数据
# data_raw/SOCS_V10.csv: <SHA256_PLACEHOLDER>

# 预处理后数据
# data_splits/train.csv: <SHA256_PLACEHOLDER>
# data_splits/test_random.csv: <SHA256_PLACEHOLDER>
# data_splits/test_spatial.csv: <SHA256_PLACEHOLDER>

# 模型输出
# results/model_performance.csv: <SHA256_PLACEHOLDER>
```

## 常见问题

**Q: GBK 编码读取报错？**
A: 确保使用 `pd.read_csv(..., encoding='gbk')`。

**Q: 内存不足？**
A: 尝试减小 batch_size 或使用 LightGBM 替代 XGBoost。

**Q: R 包安装失败？**
A: 确保 R ≥ 4.3，并使用 `install.packages()` 安装缺失包。
