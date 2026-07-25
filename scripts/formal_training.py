"""
Formal Training: China SOCS V10
================================
Full experiment: 3 seeds × 5 folds × 5 models × 2 CV types
With checkpointing and depth-stratified evaluation.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import KFold, GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb
import json, time, hashlib, warnings
warnings.filterwarnings('ignore')

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. Load frozen manifest
# ============================================================
print("=" * 60)
print("FORMAL TRAINING — China SOCS V10")
print("=" * 60)

with open(ROOT / 'data_splits' / 'formal_experiment_manifest.json') as f:
    manifest = json.load(f)

seeds = manifest['random_seeds']
print(f"Seeds: {seeds}")

# ============================================================
# 2. Load & prepare data
# ============================================================
print("\n1. Loading data...")
df = pd.read_csv(ROOT / 'data_raw' / 'SOCS_V10.csv', encoding='gbk')
df = df.dropna(subset=['SOC_g_kg'])
df = df[df['SOC_g_kg'] <= 200].copy()
df['log_SOC'] = np.log1p(df['SOC_g_kg'])
df['depth_mid'] = (df['Upper_depth_cm'] + df['Lower_depth_cm']) / 2.0
df['depth_thickness'] = df['Lower_depth_cm'] - df['Upper_depth_cm']
df['is_surface'] = (df['Upper_depth_cm'] == 0) & (df['Lower_depth_cm'] <= 30)

clcd_dummies = pd.get_dummies(df['CLCD'], prefix='clcd', dtype=float)
feature_cols = ['BD_g_cm3','pH','Sand_%','Silt_%','Clay_%','DEM_m','NDVI',
                'MAT_°C','MAP_mm','PET_mm','AI','depth_mid','depth_thickness']
feat_df = pd.concat([df[feature_cols], clcd_dummies], axis=1).fillna(0)
feat_df = feat_df.fillna(feat_df.median())
feature_names = list(feat_df.columns)

X = feat_df.values.astype(np.float64)
y = df['log_SOC'].values
profiles = df['Profile'].values
lat = df['Latitude'].values
lon = df['Longitude'].values
grid = (np.floor(lat/5)*1000 + np.floor(lon/5)).astype(int)
is_surf = df['is_surface'].values
upper_depth = df['Upper_depth_cm'].values

n_samples = len(X)
print(f"   Samples: {n_samples}, Features: {X.shape[1]}")

# Depth bins
depth_bin_labels = ['0-20cm', '20-50cm', '50-100cm', '>100cm']
depth_bin_masks = {
    '0-20cm': (upper_depth >= 0) & (upper_depth < 20),
    '20-50cm': (upper_depth >= 20) & (upper_depth < 50),
    '50-100cm': (upper_depth >= 50) & (upper_depth < 100),
    '>100cm': (upper_depth >= 100),
}

# ============================================================
# 3. Model definitions (with tuned hyperparameters)
# ============================================================
models = {
    'Mean': {'type': 'baseline'},
    'LinearReg': {'type': 'linear'},
    'Ridge': {'type': 'ridge', 'alpha': 100.0},
    'RF': {'type': 'rf', 'n_estimators': 500, 'max_depth': 15, 'min_samples_leaf': 5},
    'XGBoost': {'type': 'xgb', 'n_estimators': 200, 'max_depth': 6, 'learning_rate': 0.05, 'subsample': 0.8},
}

def make_model(mdef):
    if mdef['type'] == 'baseline':
        return None
    elif mdef['type'] == 'linear':
        return LinearRegression()
    elif mdef['type'] == 'ridge':
        return Ridge(alpha=mdef['alpha'])
    elif mdef['type'] == 'rf':
        return RandomForestRegressor(
            n_estimators=mdef['n_estimators'], max_depth=mdef['max_depth'],
            min_samples_leaf=mdef['min_samples_leaf'], random_state=42, n_jobs=-1)
    elif mdef['type'] == 'xgb':
        return xgb.XGBRegressor(
            n_estimators=mdef['n_estimators'], max_depth=mdef['max_depth'],
            learning_rate=mdef['learning_rate'], subsample=mdef['subsample'],
            random_state=42, n_jobs=-1, tree_method='hist', verbosity=0)

# ============================================================
# 4. Metrics
# ============================================================
def calc_metrics(y_true, y_pred):
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    yt, yp = y_true[mask], y_pred[mask]
    if len(yt) < 2:
        return {'R2': np.nan, 'RMSE': np.nan, 'MAE': np.nan}
    return {
        'R2': r2_score(yt, yp),
        'RMSE': np.sqrt(mean_squared_error(yt, yp)),
        'MAE': mean_absolute_error(yt, yp),
    }

# ============================================================
# 5. Checkpoint management
# ============================================================
CKPT = RESULTS / 'training_checkpoint.json'

def load_checkpoint():
    if CKPT.exists():
        with open(CKPT) as f:
            return json.load(f)
    return {'completed': []}

def save_checkpoint(ckpt):
    with open(CKPT, 'w') as f:
        json.dump(ckpt, f)

def is_done(ckpt, key):
    return key in ckpt['completed']

# ============================================================
# 6. Training loop
# ============================================================
print("\n2. Starting training...")
ckpt = load_checkpoint()
all_results = []

# Load partial results if they exist
partial_csv = RESULTS / 'formal_results.csv'
if partial_csv.exists():
    existing = pd.read_csv(partial_csv)
    all_results = existing.to_dict('records')
    print(f"   Loaded {len(all_results)} existing results from checkpoint")

total_runs = 0
t_start = time.time()

for cv_type, cv_setup in [
    ('Spatial_block', lambda: GroupKFold(n_splits=5).split(X, y, groups=grid)),
    ('Random_5fold', None),  # handled per seed
]:
    if cv_type == 'Spatial_block':
        # Spatial CV: seed-independent (grid assignment is fixed)
        # But we run with different model random seeds
        seeds_for_cv = [42]  # single run, but models have their own randomness
    else:
        seeds_for_cv = seeds

    for seed in seeds_for_cv:
        if cv_type == 'Random_5fold':
            kf = KFold(n_splits=5, shuffle=True, random_state=seed)
            fold_iter = kf.split(X)
        else:
            fold_iter = GroupKFold(n_splits=5).split(X, y, groups=grid)

        for fold_i, (tr_idx, te_idx) in enumerate(fold_iter):
            for model_name, mdef in models.items():
                run_key = f"{cv_type}_s{seed}_f{fold_i}_{model_name}"
                total_runs += 1

                if is_done(ckpt, run_key):
                    continue

                t0 = time.time()
                X_tr, X_te = X[tr_idx], X[te_idx]
                y_tr, y_te = y[tr_idx], y[te_idx]
                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_tr)
                X_te_s = scaler.transform(X_te)

                if mdef['type'] == 'baseline':
                    y_pred = np.full(len(y_te), y_tr.mean())
                else:
                    m = make_model(mdef)
                    m.fit(X_tr_s, y_tr)
                    y_pred = m.predict(X_te_s)

                # Overall metrics
                m_all = calc_metrics(y_te, y_pred)

                # Surface vs Deep
                s_mask = is_surf[te_idx]
                d_mask = ~is_surf[te_idx]
                m_surf = calc_metrics(y_te[s_mask], y_pred[s_mask]) if s_mask.sum() > 10 else {'R2':np.nan,'RMSE':np.nan,'MAE':np.nan}
                m_deep = calc_metrics(y_te[d_mask], y_pred[d_mask]) if d_mask.sum() > 10 else {'R2':np.nan,'RMSE':np.nan,'MAE':np.nan}

                # Depth-stratified
                depth_metrics = {}
                for db_label, db_mask_full in depth_bin_masks.items():
                    db_mask = db_mask_full[te_idx]
                    if db_mask.sum() > 10:
                        depth_metrics[db_label] = calc_metrics(y_te[db_mask], y_pred[db_mask])
                    else:
                        depth_metrics[db_label] = {'R2':np.nan,'RMSE':np.nan,'MAE':np.nan}

                elapsed = time.time() - t0

                row = {
                    'cv_type': cv_type, 'seed': seed, 'fold': fold_i,
                    'model': model_name, 'n_train': len(tr_idx), 'n_test': len(te_idx),
                    'R2_all': m_all['R2'], 'RMSE_all': m_all['RMSE'], 'MAE_all': m_all['MAE'],
                    'R2_surface': m_surf['R2'], 'RMSE_surface': m_surf['RMSE'],
                    'R2_deep': m_deep['R2'], 'RMSE_deep': m_deep['RMSE'],
                }
                for db_label in depth_bin_labels:
                    row[f'R2_{db_label}'] = depth_metrics[db_label]['R2']
                    row[f'RMSE_{db_label}'] = depth_metrics[db_label]['RMSE']

                all_results.append(row)

                # Checkpoint
                ckpt['completed'].append(run_key)
                save_checkpoint(ckpt)

                # Save partial results
                pd.DataFrame(all_results).to_csv(partial_csv, index=False)

                print(f"   ✓ {run_key:45s} R²={m_all['R2']:.4f} surf={m_surf['R2']:.4f} deep={m_deep['R2']:.4f} ({elapsed:.1f}s)")

# ============================================================
# 7. Final summary
# ============================================================
elapsed_total = time.time() - t_start
print(f"\n{'='*60}")
print(f"TRAINING COMPLETE ({elapsed_total/60:.1f} min)")
print(f"{'='*60}")

res_df = pd.DataFrame(all_results)
res_df.to_csv(RESULTS / 'formal_results.csv', index=False)
print(f"Results: {len(res_df)} rows → results/formal_results.csv")

# ============================================================
# 8. Summary tables
# ============================================================
print(f"\n{'='*60}")
print("SUMMARY: Mean R² across folds/seeds")
print(f"{'='*60}")

# Aggregate by CV type and model
for cv_type in ['Spatial_block', 'Random_5fold']:
    print(f"\n--- {cv_type} ---")
    cv_df = res_df[res_df['cv_type'] == cv_type]
    print(f"  {'Model':<14} {'R²(all)':>8} {'R²(surf)':>9} {'R²(deep)':>9} {'0-20cm':>7} {'20-50':>7} {'50-100':>7} {'>100':>7}")
    print(f"  {'-'*75}")
    for model_name in models.keys():
        m_df = cv_df[cv_df['model'] == model_name]
        if len(m_df) == 0:
            continue
        r2_a = m_df['R2_all'].mean()
        r2_s = m_df['R2_surface'].mean()
        r2_d = m_df['R2_deep'].mean()
        d_vals = [m_df[f'R2_{db}'].mean() for db in depth_bin_labels]
        print(f"  {model_name:<14} {r2_a:>8.4f} {r2_s:>9.4f} {r2_d:>9.4f} "
              f"{d_vals[0]:>7.3f} {d_vals[1]:>7.3f} {d_vals[2]:>7.3f} {d_vals[3]:>7.3f}")

# Delta R²
print(f"\n{'='*60}")
print("DELTA R² (Random - Spatial)")
print(f"{'='*60}")
for model_name in ['LinearReg', 'Ridge', 'RF', 'XGBoost']:
    for dk in ['all', 'surface', 'deep']:
        col = f'R2_{dk}'
        r_r = res_df[(res_df['cv_type']=='Random_5fold') & (res_df['model']==model_name)][col].mean()
        r_s = res_df[(res_df['cv_type']=='Spatial_block') & (res_df['model']==model_name)][col].mean()
        delta = r_r - r_s
        print(f"  {model_name:<14} {dk:<8} ΔR²={delta:+.4f}  (Random={r_r:.4f} - Spatial={r_s:.4f})")

print(f"\n{'='*60}")
print(f"All results saved to results/formal_results.csv")
print(f"{'='*60}")
