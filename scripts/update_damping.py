#!/usr/bin/env python3
"""
Update Gilbert damping constant (alpha) in LayerFree_parameters.txt

Usage:
    python update_damping.py <alpha_value>
    
Example:
    python update_damping.py 0.02     # Default
    python update_damping.py 0.01     # Lower damping (sharper resonance)
    python update_damping.py 0.05     # Higher damping (broader resonance)
"""

import sys
import os
import re

PROJECT_DIR = r"D:\Desktop\AI PROJECT\MacrospinExample_STTFMR_Hx10mT\MacrospinCodeEle_Simulation"
LAYERFREE_FILE = os.path.join(PROJECT_DIR, "file_configuration", "LayerFree_parameters.txt")


def update_damping(alpha_new):
    """Update alpha (Gilbert damping constant)."""
    
    with open(LAYERFREE_FILE, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    alpha_old = None
    
    for line in lines:
        # Match alpha line (e.g., "0.02000000         !alpha...")
        # Pattern: floating point number followed by whitespace and !alpha
        match = re.match(r'^(\d+\.\d+)\s+(!alpha\s+.*)', line)
        if match:
            alpha_old = match.group(1)
            updated_lines.append(f'{float(alpha_new):.8f}         {match.group(2)}\n')
        else:
            updated_lines.append(line)
    
    with open(LAYERFREE_FILE, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"[LAYERFREE] Updated alpha: {alpha_old} -> {float(alpha_new):.8f}")
    print(f"[LAYERFREE] File: {LAYERFREE_FILE}")
    
    return alpha_old, alpha_new


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_damping.py <alpha_value>")
        print("Example: python update_damping.py 0.01")
        print("")
        print("Notes:")
        print("  - alpha = 0.02 is the default")
        print("  - Lower alpha → Sharper resonance peak (higher Q-factor)")
        print("  - Higher alpha → Broader resonance, faster relaxation")
        sys.exit(1)
    
    try:
        alpha_new = float(sys.argv[1])
        if alpha_new <= 0:
            print(f"[ERROR] Damping must be positive: {alpha_new}")
            sys.exit(1)
    except ValueError:
        print(f"[ERROR] Invalid alpha value: {sys.argv[1]}")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print(f"Updating Damping Constant (alpha)")
    print(f"{'='*50}\n")
    
    old, new = update_damping(alpha_new)
    
    print(f"\n[NOTE] Damping affects resonance linewidth:")
    print(f"[NOTE]   Lower alpha ({float(new)/2:.4f}) → Sharper peak, longer oscillations")
    print(f"[NOTE]   Higher alpha ({float(new)*2:.4f}) → Broader peak, faster damping")
    print(f"[NOTE] Current value: {float(new):.8f}")


if __name__ == "__main__":
    main()
