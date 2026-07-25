"""
Hyperparameter Tuning for Formal Experiment
=============================================
Uses 20% validation subset; tunes RF and XGBoost via spatial block CV.
Records best parameters for full training.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb
import json, time, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
ROOT = Path(__file__).resolve().parent.parent
SPLITS = ROOT / 'data_splits'
RESULTS = ROOT / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. Load data
# ============================================================
print("=" * 60)
print("1. Loading data...")
df = pd.read_csv(ROOT / 'data_raw' / 'SOCS_V10.csv', encoding='gbk')
df = df.dropna(subset=['SOC_g_kg'])
df = df[df['SOC_g_kg'] <= 200].copy()
df['log_SOC'] = np.log1p(df['SOC_g_kg'])
df['depth_mid'] = (df['Upper_depth_cm'] + df['Lower_depth_cm']) / 2.0
df['depth_thickness'] = df['Lower_depth_cm'] - df['Upper_depth_cm']
df['is_surface'] = (df['Upper_depth_cm'] == 0) & (df['Lower_depth_cm'] <= 30)
df['depth_bin'] = np.select(
    [df['Upper_depth_cm']<20, df['Upper_depth_cm']<50, df['Upper_depth_cm']<100, df['Upper_depth_cm']>=100],
    ['0-20cm','20-50cm','50-100cm','>100cm'], default='unknown')

# Features
clcd_dummies = pd.get_dummies(df['CLCD'], prefix='clcd', dtype=float)
feature_cols = ['BD_g_cm3','pH','Sand_%','Silt_%','Clay_%','DEM_m','NDVI',
                'MAT_°C','MAP_mm','PET_mm','AI','depth_mid','depth_thickness']
feat_df = pd.concat([df[feature_cols], clcd_dummies], axis=1).fillna(feat_df.median() if 'feat_df' in dir() else 0)
feat_df = feat_df.fillna(feat_df.median())
feature_names = list(feat_df.columns)

X_all = feat_df.values.astype(np.float64)
y_all = df['log_SOC'].values
profiles_all = df['Profile'].values
lat_all = df['Latitude'].values
lon_all = df['Longitude'].values
grid_all = (np.floor(lat_all/5)*1000 + np.floor(lon_all/5)).astype(int)

print(f"   Samples: {len(X_all)}, Features: {X_all.shape[1]}")

# ============================================================
# 2. 20% tuning subset (stratified by grid)
# ============================================================
print("\n2. Creating tuning subset (20%)...")
unique_profiles = np.unique(profiles_all)
np.random.shuffle(unique_profiles)
n_tune = int(len(unique_profiles) * 0.20)
tune_profiles = set(unique_profiles[:n_tune])
tune_mask = np.array([p in tune_profiles for p in profiles_all])

X_t = X_all[tune_mask]
y_t = y_all[tune_mask]
grid_t = grid_all[tune_mask]
prof_t = profiles_all[tune_mask]
surf_t = df['is_surface'].values[tune_mask]
depth_t = df['Upper_depth_cm'].values[tune_mask]

print(f"   Tuning samples: {len(X_t)} ({n_tune} profiles)")

# ============================================================
# 3. CV helper
# ============================================================
def run_cv(X, y, grid, model_fn, n_folds=5):
    """Run spatial GroupKFold CV, return list of fold metrics."""
    gkf = GroupKFold(n_splits=n_folds)
    results = []
    for tr, te in gkf.split(X, y, groups=grid):
        X_tr, X_te = X[tr], X[te]
        y_tr, y_te = y[tr], y[te]
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_te_s = scaler.transform(X_te)
        m = model_fn()
        m.fit(X_tr_s, y_tr)
        y_pred = m.predict(X_te_s)
        r2 = r2_score(y_te, y_pred)
        rmse = np.sqrt(mean_squared_error(y_te, y_pred))
        results.append({'R2': r2, 'RMSE': rmse})
    return results

def summarize(results):
    r2s = [r['R2'] for r in results]
    return {'R2_mean': np.mean(r2s), 'R2_std': np.std(r2s),
            'RMSE_mean': np.mean([r['RMSE'] for r in results]),
            'RMSE_std': np.std([r['RMSE'] for r in results])}

# ============================================================
# 4. RF hyperparameter search
# ============================================================
print("\n" + "=" * 60)
print("3. RF Hyperparameter Search")
print("=" * 60)

rf_grid = [
    {'n_estimators': 100, 'max_depth': 10, 'min_samples_leaf': 5},
    {'n_estimators': 100, 'max_depth': 15, 'min_samples_leaf': 5},
    {'n_estimators': 100, 'max_depth': 20, 'min_samples_leaf': 5},
    {'n_estimators': 200, 'max_depth': 10, 'min_samples_leaf': 5},
    {'n_estimators': 200, 'max_depth': 15, 'min_samples_leaf': 5},
    {'n_estimators': 200, 'max_depth': 15, 'min_samples_leaf': 10},
    {'n_estimators': 200, 'max_depth': 20, 'min_samples_leaf': 5},
    {'n_estimators': 300, 'max_depth': 15, 'min_samples_leaf': 5},
    {'n_estimators': 300, 'max_depth': 20, 'min_samples_leaf': 10},
    {'n_estimators': 500, 'max_depth': 15, 'min_samples_leaf': 5},
]

rf_results = []
best_rf_r2 = -999
best_rf_params = None

for i, params in enumerate(rf_grid):
    t0 = time.time()
    cv = run_cv(X_t, y_t, grid_t,
                lambda p=params: RandomForestRegressor(**p, random_state=42, n_jobs=-1))
    s = summarize(cv)
    elapsed = time.time() - t0
    rf_results.append({**params, **s})
    print(f"   [{i+1}/{len(rf_grid)}] n={params['n_estimators']:3d} depth={params['max_depth']:2d} "
          f"leaf={params['min_samples_leaf']:2d} → R²={s['R2_mean']:.4f}±{s['R2_std']:.4f} "
          f"RMSE={s['RMSE_mean']:.4f}  ({elapsed:.1f}s)")
    if s['R2_mean'] > best_rf_r2:
        best_rf_r2 = s['R2_mean']
        best_rf_params = params

print(f"\n   ★ Best RF: {best_rf_params} → R²={best_rf_r2:.4f}")

# ============================================================
# 5. XGBoost hyperparameter search
# ============================================================
print("\n" + "=" * 60)
print("4. XGBoost Hyperparameter Search")
print("=" * 60)

xgb_grid = [
    {'n_estimators': 100, 'max_depth': 4, 'learning_rate': 0.1, 'subsample': 0.8},
    {'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8},
    {'n_estimators': 200, 'max_depth': 4, 'learning_rate': 0.1, 'subsample': 0.8},
    {'n_estimators': 200, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8},
    {'n_estimators': 200, 'max_depth': 6, 'learning_rate': 0.05, 'subsample': 0.8},
    {'n_estimators': 200, 'max_depth': 8, 'learning_rate': 0.1, 'subsample': 0.8},
    {'n_estimators': 300, 'max_depth': 6, 'learning_rate': 0.05, 'subsample': 0.8},
    {'n_estimators': 300, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.7},
    {'n_estimators': 500, 'max_depth': 6, 'learning_rate': 0.05, 'subsample': 0.8},
    {'n_estimators': 500, 'max_depth': 8, 'learning_rate': 0.03, 'subsample': 0.7},
]

xgb_results = []
best_xgb_r2 = -999
best_xgb_params = None

for i, params in enumerate(xgb_grid):
    t0 = time.time()
    cv = run_cv(X_t, y_t, grid_t,
                lambda p=params: xgb.XGBRegressor(**p, random_state=42, n_jobs=-1,
                                                    tree_method='hist', verbosity=0))
    s = summarize(cv)
    elapsed = time.time() - t0
    xgb_results.append({**params, **s})
    print(f"   [{i+1}/{len(xgb_grid)}] n={params['n_estimators']:3d} depth={params['max_depth']} "
          f"lr={params['learning_rate']} → R²={s['R2_mean']:.4f}±{s['R2_std']:.4f} "
          f"RMSE={s['RMSE_mean']:.4f}  ({elapsed:.1f}s)")
    if s['R2_mean'] > best_xgb_r2:
        best_xgb_r2 = s['R2_mean']
        best_xgb_params = params

print(f"\n   ★ Best XGBoost: {best_xgb_params} → R²={best_xgb_r2:.4f}")

# ============================================================
# 6. Also tune Ridge alpha
# ============================================================
print("\n" + "=" * 60)
print("5. Ridge Alpha Search")
print("=" * 60)

ridge_results = []
best_ridge_r2 = -999
best_ridge_alpha = None

for alpha in [0.01, 0.1, 1.0, 10.0, 100.0]:
    cv = run_cv(X_t, y_t, grid_t,
                lambda a=alpha: Ridge(alpha=a))
    s = summarize(cv)
    ridge_results.append({'alpha': alpha, **s})
    print(f"   alpha={alpha:>6} → R²={s['R2_mean']:.4f}±{s['R2_std']:.4f}")
    if s['R2_mean'] > best_ridge_r2:
        best_ridge_r2 = s['R2_mean']
        best_ridge_alpha = alpha

print(f"\n   ★ Best Ridge: alpha={best_ridge_alpha} → R²={best_ridge_r2:.4f}")

# ============================================================
# 7. Save results
# ============================================================
print("\n" + "=" * 60)
print("6. Saving results...")

# RF results
pd.DataFrame(rf_results).to_csv(RESULTS / 'tuning_rf.csv', index=False)
# XGB results
pd.DataFrame(xgb_results).to_csv(RESULTS / 'tuning_xgboost.csv', index=False)
# Ridge results
pd.DataFrame(ridge_results).to_csv(RESULTS / 'tuning_ridge.csv', index=False)

# Best parameters summary
best = {
    'RF': {
        'n_estimators': best_rf_params['n_estimators'],
        'max_depth': best_rf_params['max_depth'],
        'min_samples_leaf': best_rf_params['min_samples_leaf'],
        'R2_tuning': round(best_rf_r2, 4)
    },
    'XGBoost': {
        'n_estimators': best_xgb_params['n_estimators'],
        'max_depth': best_xgb_params['max_depth'],
        'learning_rate': best_xgb_params['learning_rate'],
        'subsample': best_xgb_params['subsample'],
        'R2_tuning': round(best_xgb_r2, 4)
    },
    'Ridge': {
        'alpha': best_ridge_alpha,
        'R2_tuning': round(best_ridge_r2, 4)
    }
}

with open(RESULTS / 'best_hyperparameters.json', 'w') as f:
    json.dump(best, f, indent=2)

print(f"\n   Saved: results/tuning_rf.csv ({len(rf_results)} configs)")
print(f"   Saved: results/tuning_xgboost.csv ({len(xgb_results)} configs)")
print(f"   Saved: results/tuning_ridge.csv ({len(ridge_results)} configs)")
print(f"   Saved: results/best_hyperparameters.json")

# ============================================================
# 8. Summary comparison
# ============================================================
print("\n" + "=" * 60)
print("7. MODEL COMPARISON (Spatial Block CV, 20% subset)")
print("=" * 60)

# Quick baseline: LinearReg
cv_lr = run_cv(X_t, y_t, grid_t, lambda: LinearRegression())
s_lr = summarize(cv_lr)

print(f"\n   {'Model':<16} {'R²':>8} {'±std':>8}")
print(f"   {'-'*32}")
print(f"   {'LinearReg':<16} {s_lr['R2_mean']:>8.4f} {s_lr['R2_std']:>8.4f}")
print(f"   {'Ridge':<16} {best_ridge_r2:>8.4f} —")
print(f"   {'RF (best)':<16} {best_rf_r2:>8.4f} —")
print(f"   {'XGBoost (best)':<16} {best_xgb_r2:>8.4f} —")

print("\n" + "=" * 60)
print("TUNING COMPLETE")
print("=" * 60)
