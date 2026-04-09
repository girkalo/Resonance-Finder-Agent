import matplotlib.pyplot as plt
import numpy as np

# Load experimental data from our agent runs
data = [
    (400e6, 0.008634144),
    (450e6, 0.01228458),
    (500e6, 0.0220764),
    (510e6, 0.02592291),
    (520e6, 0.03069942),
    (530e6, 0.03580374),
    (540e6, 0.03907474),
    (542e6, 0.03924164),  # Highest
    (545e6, 0.03911886),
    (548e6, 0.03855858),
    (550e6, 0.03796515),
    (600e6, 0.01659265),
    (650e6, 0.0091088),
]

freqs = np.array([d[0] for d in data]) / 1e6  # Convert to MHz
mzs = np.array([d[1] for d in data])

# Find peak
peak_idx = np.argmax(mzs)
peak_freq = freqs[peak_idx]
peak_mz = mzs[peak_idx]

# Estimate FWHM (Full Width at Half Maximum)
half_max = peak_mz / 2
above_half = mzs > half_max
indices = np.where(above_half)[0]
if len(indices) > 1:
    fwhm = freqs[indices[-1]] - freqs[indices[0]]
else:
    fwhm = 60

q_factor = peak_freq / fwhm

# Sort for line plotting
sort_idx = np.argsort(freqs)
freqs_sorted = freqs[sort_idx]
mzs_sorted = mzs[sort_idx]

# Phase coloring
phase_colors = []
for f in freqs_sorted:
    if f <= 450:
        phase_colors.append('blue')
    elif f <= 520:
        phase_colors.append('green')
    elif f <= 550:
        phase_colors.append('red')
    else:
        phase_colors.append('purple')

# Create figure
fig, ax = plt.subplots(figsize=(12, 7))

# Plot connecting line
ax.plot(freqs_sorted, mzs_sorted, 'k-', alpha=0.3, linewidth=1, zorder=1)

# Plot points by phase
for phase, color, marker, label in [
    ('Coarse (400-450 MHz)', 'blue', 'o', 'Coarse Sweep'),
    ('Refinement Phase 1 (500-520 MHz)', 'green', 's', 'Refinement 1'),
    ('Peak Region (530-550 MHz)', 'red', 'D', 'Peak Region'),
    ('Tail Check (600+ MHz)', 'purple', '^', 'Tail Check')
]:
    mask = [
        (f <= 450) if color == 'blue' else
        (450 < f <= 520) if color == 'green' else
        (520 < f <= 550) if color == 'red' else
        (f > 550)
        for f in freqs
    ]
    if any(mask):
        ax.scatter(freqs[mask], mzs[mask], color=color, s=100, zorder=5, marker=marker, label=label, edgecolors='black', linewidths=0.5)

# Highlight peak
ax.scatter([peak_freq], [peak_mz], color='gold', s=400, marker='*', zorder=10, edgecolors='black', linewidths=2, label=f'Peak: {peak_freq:.1f} MHz')

# Mark half-max line
ax.axhline(y=half_max, color='orange', linestyle=':', alpha=0.7, label=f'Half-Max = {half_max:.4f}')

ax.set_xlabel('Frequency (MHz)', fontsize=14, fontweight='bold')
ax.set_ylabel('Mz Oscillation Amplitude', fontsize=14, fontweight='bold')
ax.set_title('STT-MRAM Resonance Discovery\nAutonomous Agent-Driven Experimental Search', fontsize=16, fontweight='bold')
ax.legend(loc='upper right', fontsize=10)
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_xlim(380, 670)
ax.set_ylim(0, max(mzs) * 1.2)

# Add stats box
textstr = f'Peak Frequency: {peak_freq:.1f} MHz\nMax Amplitude: {peak_mz:.4f}\nFWHM (est): {fwhm:.1f} MHz\nQ-Factor: {q_factor:.1f}\n\nExperiments: {len(data)} runs'
props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

plt.tight_layout()
plt.savefig('C:/Users/girka/.openclaw/workspace/resonance_curve.png', dpi=150, bbox_inches='tight')
print("Saved: resonance_curve.png")

# Print summary
print("\n" + "="*60)
print("RESONANCE ANALYSIS - AGENT COMPLETE")
print("="*60)
print(f"Peak Frequency:     {peak_freq:.2f} MHz ({peak_freq*1e6:.3e} Hz)")
print(f"Maximum Mz:         {peak_mz:.6f}")
print(f"FWHM (Linewidth):   {fwhm:.1f} MHz (estimated)")
print(f"Q-Factor:           {q_factor:.1f}")
print(f"Total Experiments:  {len(data)}")
print("="*60)
print("\nSearch Strategy:")
print("  1. Coarse sweep (400-650 MHz, 50 MHz steps)")
print("  2. Narrowed to 500-550 MHz region")
print("  3. Peak refinement (10 MHz → 5 MHz → 2 MHz steps)")
print("  4. Converged at ~543 MHz")
