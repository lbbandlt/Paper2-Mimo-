"""
Fig 3: Study Area Map
======================
China base map + sampling points colored by climate zone
+ inset maps for context
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / 'figures'
SRC = ROOT / 'results' / 'source_data'

# ============================================================
# 1. Load data
# ============================================================
print("Loading data...")
profiles = pd.read_csv(SRC / 'fig1_study_area_profiles.csv')

# Climate zone from MAT
def climate_zone(mat):
    if mat < 0: return 'Alpine (< 0°C)'
    elif mat < 10: return 'Temperate (0–10°C)'
    elif mat < 20: return 'Warm (10–20°C)'
    else: return 'Tropical (> 20°C)'

profiles['climate_zone'] = profiles['MAT'].apply(climate_zone)
profiles['climate_code'] = profiles['MAT'].apply(lambda x: 0 if x < 0 else (1 if x < 10 else (2 if x < 20 else 3)))

# ============================================================
# 2. Load China boundary
# ============================================================
print("Loading China boundary...")
world = gpd.read_file(ROOT / 'data_raw' / 'gis' / 'ne_countries.zip')
china = world[world['NAME'] == 'China']
# Also get neighboring countries for context
neighbors = world[world['NAME'].isin(['India', 'Myanmar', 'Laos', 'Vietnam', 'Nepal',
                                       'Bhutan', 'Bangladesh', 'Pakistan', 'Afghanistan',
                                       'Tajikistan', 'Kyrgyzstan', 'Kazakhstan', 'Mongolia',
                                       'Russia', 'North Korea', 'South Korea', 'Japan',
                                       'Thailand', 'Cambodia', 'Philippines', 'Malaysia',
                                       'Indonesia', 'Taiwan'])]

# ============================================================
# 3. Main map
# ============================================================
print("Drawing map...")

fig, ax = plt.subplots(1, 1, figsize=(10, 10))

# Plot neighbors (light gray)
neighbors.plot(ax=ax, facecolor='#F5F5F5', edgecolor='#CCCCCC', linewidth=0.5)

# Plot China (light fill)
china.plot(ax=ax, facecolor='#FFF8DC', edgecolor='black', linewidth=1.2)

# Climate zone colors
cz_colors = {
    'Alpine (< 0°C)': '#B8A9C9',
    'Temperate (0–10°C)': '#90C695',
    'Warm (10–20°C)': '#F28E2B',
    'Tropical (> 20°C)': '#E15759',
}
cz_order = ['Alpine (< 0°C)', 'Temperate (0–10°C)', 'Warm (10–20°C)', 'Tropical (> 20°C)']

# Plot sampling points by climate zone
for cz in cz_order:
    mask = profiles['climate_zone'] == cz
    ax.scatter(profiles.loc[mask, 'Longitude'], profiles.loc[mask, 'Latitude'],
               c=cz_colors[cz], s=15, alpha=0.7, edgecolors='black', linewidth=0.3,
               label=f'{cz} (n={mask.sum()})', zorder=5)

# Set extent (China bounds)
ax.set_xlim(73, 136)
ax.set_ylim(17, 54)
ax.set_aspect(1.3)

# Labels
ax.set_xlabel('Longitude (°E)', fontsize=13)
ax.set_ylabel('Latitude (°N)', fontsize=13)
ax.tick_params(labelsize=11)

# Legend
legend = ax.legend(loc='lower left', fontsize=10, title='Climate zone',
                   title_fontsize=11, framealpha=0.95, edgecolor='gray',
                   markerscale=2)

# Grid
ax.grid(alpha=0.2, linestyle='--')

# Add a scale bar (approximate)
ax.plot([115, 120], [18.5, 18.5], 'k-', linewidth=2)
ax.text(117.5, 19.2, '≈ 500 km', ha='center', fontsize=9)

# North arrow
ax.annotate('N', xy=(133, 51), fontsize=14, fontweight='bold', ha='center',
            arrowprops=dict(arrowstyle='->', lw=2), xytext=(133, 48))

plt.tight_layout()
plt.savefig(FIGS / 'fig3_study_area.png', dpi=300, bbox_inches='tight')
plt.savefig(FIGS / 'fig3_study_area.pdf', bbox_inches='tight')
print(f"Saved: fig3_study_area.png/pdf")
print(f"  Profiles: {len(profiles)}")
print(f"  Climate zones: {profiles['climate_zone'].value_counts().to_dict()}")
plt.close()
