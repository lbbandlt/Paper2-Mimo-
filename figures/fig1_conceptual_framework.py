"""
Fig 1: Conceptual Framework — Final Clean Version
====================================================
Three panels, no text overlap, generous spacing
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

FIGS = Path(__file__).resolve().parent

fig, axes = plt.subplots(1, 3, figsize=(18, 7))

for ax in axes:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

# ============================================================
# Panel A: Random CV
# ============================================================
ax = axes[0]
ax.set_title('A)  Random cross-validation', fontsize=15, fontweight='bold', pad=20)

# Grid cells — centered and higher
np.random.seed(42)
x_off, y_off = 1.0, 1.8  # shift grid up
for i in range(5):
    for j in range(5):
        is_test = (i + j) % 3 == 0
        fc = '#FADBD8' if is_test else '#D6EAF8'
        ec = '#E74C3C' if is_test else '#2980B9'
        rect = plt.Rectangle((x_off + j * 1.5, y_off + (4 - i) * 1.3), 1.3, 1.1,
                             facecolor=fc, edgecolor=ec, linewidth=1.8)
        ax.add_patch(rect)
        for _ in range(3):
            dx, dy = np.random.uniform(0.15, 1.15), np.random.uniform(0.15, 0.95)
            c = '#E74C3C' if is_test else '#2980B9'
            ax.plot(x_off + j * 1.5 + dx, y_off + (4 - i) * 1.3 + dy, 'o', color=c, markersize=4)

# Warning text
ax.text(5, 0.3, '⚠ Nearby train / test samples\ncause spatial leakage',
        ha='center', va='bottom', fontsize=12, color='#C0392B', fontweight='bold')

# Legend — left side, near grid
ax.plot([], [], 'o', color='#2980B9', markersize=6, label='Train')
ax.plot([], [], 'o', color='#E74C3C', markersize=6, label='Test')
ax.legend(loc='upper left', fontsize=10, framealpha=0.9)

# ============================================================
# Panel B: Spatial Block CV
# ============================================================
ax = axes[1]
ax.set_title('B)  Spatial block cross-validation', fontsize=15, fontweight='bold', pad=20)

# Large clean blocks — centered
blocks = [
    (0.5, 5.3, 4.0, 3.8, 'TRAIN', '#D6EAF8', '#2980B9'),
    (4.8, 5.3, 4.7, 3.8, 'TRAIN', '#D6EAF8', '#2980B9'),
    (0.5, 0.8, 6.0, 4.2, 'TRAIN', '#D6EAF8', '#2980B9'),
    (6.8, 0.8, 2.7, 4.2, 'TRAIN', '#D6EAF8', '#2980B9'),
    (5.0, 5.3, 2.0, 3.8, 'TEST', '#FADBD8', '#E74C3C'),
]

# Draw train blocks first
for x, y, w, h, label, fc, ec in blocks[:-1]:
    rect = plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=2)
    ax.add_patch(rect)
    ax.text(x + w / 2, y + h / 2, label, ha='center', va='center',
            fontsize=16, fontweight='bold', color='#2471A3', alpha=0.6)

# Test block on top
x, y, w, h, label, fc, ec = blocks[-1]
rect = plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=3)
ax.add_patch(rect)
ax.text(x + w / 2, y + h / 2, label, ha='center', va='center',
        fontsize=16, fontweight='bold', color='#C0392B')

# Check mark
ax.text(5, 0.1, '✓ Test block spatially isolated\n→ honest R² estimate',
        ha='center', va='bottom', fontsize=12, color='#27AE60', fontweight='bold')

# ============================================================
# Panel C: Depth Stratification
# ============================================================
ax = axes[2]
ax.set_title('C)  Depth-dependent predictability', fontsize=15, fontweight='bold', pad=20)

# Soil layers — clean horizontal bars on the left
layers = [
    (7.5, 2.0, '0–20 cm', '#8BC34A', 0.57),
    (5.2, 2.0, '20–50 cm', '#CDDC39', 0.43),
    (2.9, 2.0, '50–100 cm', '#FFC107', 0.31),
    (0.8, 1.8, '> 100 cm', '#FF9800', 0.29),
]

for y, h, label, color, r2 in layers:
    # Layer bar
    rect = plt.Rectangle((0.3, y), 3.5, h, facecolor=color, alpha=0.7,
                         edgecolor='black', linewidth=1.5)
    ax.add_patch(rect)
    ax.text(2.05, y + h / 2, label, ha='center', va='center',
            fontsize=13, fontweight='bold')

# R² bars on the right
for y, h, label, color, r2 in layers:
    bar_w = r2 * 4.5
    rect = plt.Rectangle((4.5, y + 0.2), bar_w, h - 0.4,
                         facecolor=color, alpha=0.8, edgecolor='black', linewidth=1)
    ax.add_patch(rect)
    ax.text(4.5 + bar_w + 0.15, y + h / 2, f'R² = {r2:.2f}',
            ha='left', va='center', fontsize=12, fontweight='bold')

# Decline arrow — between the two columns, top to bottom
ax.annotate('', xy=(4.2, 1.3), xytext=(4.2, 8.8),
            arrowprops=dict(arrowstyle='->', color='#C0392B', lw=3, shrinkA=0, shrinkB=0))
ax.text(4.2, 5.0, 'R² declines', ha='center', va='center', fontsize=11,
        fontweight='bold', color='#C0392B', rotation=90,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='none', alpha=0.8))

ax.text(5, 0.1, 'Predictability drops with depth\n→ must validate per layer',
        ha='center', va='bottom', fontsize=12, color='#555', style='italic')

plt.tight_layout(pad=2.0)
plt.savefig(FIGS / 'fig1_conceptual_framework.png', dpi=300, bbox_inches='tight')
plt.savefig(FIGS / 'fig1_conceptual_framework.pdf', bbox_inches='tight')
print("Saved: fig1_conceptual_framework.png/pdf")
plt.close()
