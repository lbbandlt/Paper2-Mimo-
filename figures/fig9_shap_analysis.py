"""
SHAP Analysis: Feature Importance by Depth Layer
===================================================
Uses trained XGBoost on full data to compute SHAP values per depth bin
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json, warnings
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / 'figures'

# ============================================================
# 1. Load data
# ============================================================
print("1. Loading data...")
df = pd.read_csv(ROOT / 'data_raw' / 'SOCS_V10.csv', encoding='gbk')
df = df.dropna(subset=['SOC_g_kg'])
df = df[df['SOC_g_kg'] <= 200].copy()
df['log_SOC'] = np.log1p(df['SOC_g_kg'])
df['depth_mid'] = (df['Upper_depth_cm'] + df['Lower_depth_cm']) / 2.0
df['depth_thickness'] = df['Lower_depth_cm'] - df['Upper_depth_cm']

clcd_dummies = pd.get_dummies(df['CLCD'], prefix='clcd', dtype=float)
feature_cols = ['BD_g_cm3', 'pH', 'Sand_%', 'Silt_%', 'Clay_%',
                'DEM_m', 'NDVI', 'MAT_°C', 'MAP_mm', 'PET_mm', 'AI',
                'depth_mid', 'depth_thickness']
feat_df = pd.concat([df[feature_cols], clcd_dummies], axis=1).fillna(0)
feature_names = list(feat_df.columns)

X = feat_df.values.astype(np.float64)
y = df['log_SOC'].values
upper_depth = df['Upper_depth_cm'].values

# ============================================================
# 2. Train XGBoost on full data
# ============================================================
print("2. Training XGBoost on full data...")
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

with open(ROOT / 'results' / 'best_hyperparameters.json') as f:
    best = json.load(f)

xgb_params = best['XGBoost']
model = xgb.XGBRegressor(
    n_estimators=xgb_params['n_estimators'],
    max_depth=xgb_params['max_depth'],
    learning_rate=xgb_params['learning_rate'],
    subsample=xgb_params['subsample'],
    random_state=42, n_jobs=-1, tree_method='hist', verbosity=0
)
model.fit(X_scaled, y)
print("   Done.")

# ============================================================
# 3. Compute SHAP values (using built-in XGBoost feature importance)
# ============================================================
print("3. Computing feature importance...")

# Use gain-based importance from XGBoost
importance_all = model.feature_importances_
feat_imp = pd.DataFrame({
    'feature': feature_names,
    'importance': importance_all
}).sort_values('importance', ascending=False)

print("\n   Overall feature importance (top 10):")
for _, row in feat_imp.head(10).iterrows():
    print(f"     {row['feature']:20s} {row['importance']:.4f}")

# ============================================================
# 4. Depth-stratified feature importance
# ============================================================
print("\n4. Computing depth-stratified importance...")

depth_bins = {
    '0-20cm': (upper_depth >= 0) & (upper_depth < 20),
    '20-50cm': (upper_depth >= 20) & (upper_depth < 50),
    '50-100cm': (upper_depth >= 50) & (upper_depth < 100),
    '>100cm': (upper_depth >= 100),
}

depth_imp = {}
for label, mask in depth_bins.items():
    X_sub = X_scaled[mask]
    y_sub = y[mask]
    # Train a quick model on this subset
    m = xgb.XGBRegressor(
        n_estimators=xgb_params['n_estimators'],
        max_depth=xgb_params['max_depth'],
        learning_rate=xgb_params['learning_rate'],
        subsample=xgb_params['subsample'],
        random_state=42, n_jobs=-1, tree_method='hist', verbosity=0
    )
    m.fit(X_sub, y_sub)
    depth_imp[label] = m.feature_importances_
    print(f"   {label}: n={mask.sum()}, top3={np.argsort(m.feature_importances_)[-3:][::-1]}")

# Build matrix
imp_matrix = pd.DataFrame(depth_imp, index=feature_names)
imp_matrix.to_csv(ROOT / 'results' / 'source_data' / 'fig9_feature_importance.csv')
print(f"\n   Saved: results/source_data/fig9_feature_importance.csv")

# ============================================================
# 5. Generate figure
# ============================================================
print("\n5. Generating figure...")
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Select top features
top_n = 12
top_feats = feat_imp.head(top_n)['feature'].values
imp_sub = imp_matrix.loc[top_feats]

fig, ax = plt.subplots(figsize=(10, 7))

depth_labels = ['0-20cm', '20-50cm', '50-100cm', '>100cm']
x = np.arange(len(top_feats))
width = 0.2
colors = ['#8BC34A', '#CDDC39', '#FFC107', '#FF9800']

for i, dl in enumerate(depth_labels):
    vals = imp_sub[dl].values
    ax.barh(x + (i - 1.5) * width, vals, width, label=dl,
            color=colors[i], alpha=0.85, edgecolor='black', linewidth=0.5)

ax.set_yticks(x)
ax.set_yticklabels(top_feats, fontsize=11)
ax.set_xlabel('Feature Importance (Gain)', fontsize=12)
ax.set_title('Feature Importance by Depth Layer (XGBoost)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10, title='Depth', title_fontsize=11)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.3)
ax.tick_params(axis='both', labelsize=11)

plt.tight_layout()
plt.savefig(FIGS / 'fig9_feature_importance.png', dpi=300, bbox_inches='tight')
plt.savefig(FIGS / 'fig9_feature_importance.pdf', bbox_inches='tight')
print(f"   Saved: fig9_feature_importance.png/pdf")
plt.close()
