"""
Fig 8: Why is deep soil harder to predict?
==========================================
Covariate shift with depth — clean version without emoji
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
from pathlib import Path

FIGS = Path(__file__).resolve().parent

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# ============================================================
# Panel A: Surface (0–20 cm)
# ============================================================
ax = axes[0]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('A) Surface soil (0–20 cm)', fontsize=15, fontweight='bold', pad=15)

# Soil layer
rect = plt.Rectangle((0.5, 1.5), 9, 3.5, facecolor='#8BC34A', alpha=0.25,
                     edgecolor='#4CAF50', linewidth=2)
ax.add_patch(rect)

# Surface covariates
covs = [
    (2, 8.5, 'NDVI', '#4CAF50', 0.85),
    (5, 8.5, 'MAT / PET', '#FF9800', 0.80),
    (8, 8.5, 'Land cover', '#8D6E63', 0.75),
]
for x, y, label, color, strength in covs:
    box = FancyBboxPatch((x-1.3, y-0.5), 2.6, 1, boxstyle="round,pad=0.2",
                         facecolor=color, alpha=0.3, edgecolor=color, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center', fontsize=12, fontweight='bold')

    # Strong arrow
    ax.annotate('', xy=(x, 5.2), xytext=(x, y-0.6),
                arrowprops=dict(arrowstyle='->', color=color, lw=3.5*strength))

    # Contribution label
    ax.text(x, y-0.9, f'Contribution: {strength:.0%}', ha='center', va='center',
            fontsize=8, color=color, fontweight='bold')

# SOC box
soc_box = FancyBboxPatch((3, 2.2), 4, 1.8, boxstyle="round,pad=0.3",
                         facecolor='white', edgecolor='#4CAF50', linewidth=2)
ax.add_patch(soc_box)
ax.text(5, 3.1, 'SOC', ha='center', va='center', fontsize=16, fontweight='bold', color='#1B5E20')
ax.text(5, 2.6, 'R² = 0.57', ha='center', va='center', fontsize=13, color='#2E7D32')

# Summary
ax.text(5, 0.5, 'Strong coupling: vegetation & climate directly control topsoil carbon',
        ha='center', fontsize=11, color='#2E7D32', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#E8F5E9', edgecolor='#4CAF50', alpha=0.8))

# ============================================================
# Panel B: Deep soil (>100 cm)
# ============================================================
ax = axes[1]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')
ax.set_title('B) Deep soil (>100 cm)', fontsize=15, fontweight='bold', pad=15)

# Deep soil layer
rect = plt.Rectangle((0.5, 1.5), 9, 3.5, facecolor='#FF9800', alpha=0.25,
                     edgecolor='#E65100', linewidth=2)
ax.add_patch(rect)

# Surface covariates — faded
covs_weak = [
    (2, 8.5, 'NDVI', '#4CAF50', 0.10),
    (5, 8.5, 'MAT / PET', '#FF9800', 0.30),
    (8, 8.5, 'Land cover', '#8D6E63', 0.15),
]
for x, y, label, color, strength in covs_weak:
    box = FancyBboxPatch((x-1.3, y-0.5), 2.6, 1, boxstyle="round,pad=0.2",
                         facecolor=color, alpha=0.1, edgecolor=color, linewidth=1, linestyle='--')
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center', fontsize=12,
            fontweight='bold', alpha=0.35)

    # Weak dashed arrow
    ax.annotate('', xy=(x, 5.2), xytext=(x, y-0.6),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5, alpha=0.3, linestyle='--'))

    ax.text(x, y-0.9, f'Contribution: {strength:.0%}', ha='center', va='center',
            fontsize=8, color=color, alpha=0.4)

# Deep covariates — unavailable but important
deep_covs = [
    (3.5, 8.5, 'Geology /\nParent material', '#795548', 'Not in\ncurrent data'),
    (6.5, 8.5, 'Groundwater\ndepth', '#2196F3', 'Not in\ncurrent data'),
]
for x, y, label, color, note in deep_covs:
    box = FancyBboxPatch((x-1.4, y-0.6), 2.8, 1.2, boxstyle="round,pad=0.2",
                         facecolor=color, alpha=0.25, edgecolor=color, linewidth=2)
    ax.add_patch(box)
    ax.text(x, y, label, ha='center', va='center', fontsize=11, fontweight='bold', color=color)

    # Arrow with X
    ax.annotate('', xy=(x, 5.2), xytext=(x, y-0.8),
                arrowprops=dict(arrowstyle='->', color=color, lw=2.5, alpha=0.6))
    ax.text(x, 6.3, 'X', ha='center', va='center', fontsize=14,
            fontweight='bold', color='#D32F2F')
    ax.text(x, 5.8, note, ha='center', va='center', fontsize=8, color='#D32F2F')

# SOC box
soc_box = FancyBboxPatch((3, 2.2), 4, 1.8, boxstyle="round,pad=0.3",
                         facecolor='white', edgecolor='#E65100', linewidth=2)
ax.add_patch(soc_box)
ax.text(5, 3.1, 'SOC', ha='center', va='center', fontsize=16, fontweight='bold', color='#BF360C')
ax.text(5, 2.6, 'R² = 0.29', ha='center', va='center', fontsize=13, color='#E65100')

# Summary
ax.text(5, 0.5, 'Weak coupling: surface covariates blind to deep soil processes',
        ha='center', fontsize=11, color='#BF360C', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#FFF3E0', edgecolor='#E65100', alpha=0.8))

plt.tight_layout(pad=2)
plt.savefig(FIGS / 'fig8_covariate_shift.png', dpi=300, bbox_inches='tight')
plt.savefig(FIGS / 'fig8_covariate_shift.pdf', bbox_inches='tight')
print("Saved: fig8_covariate_shift.png/pdf")
plt.close()
