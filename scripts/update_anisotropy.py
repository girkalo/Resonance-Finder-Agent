#!/usr/bin/env python3
"""
Update uniaxial anisotropy (K_u) in LayerFree_parameters.txt

Usage:
    python update_anisotropy.py <K_u_value>
    
Example:
    python update_anisotropy.py 6.787e+05  # Default
    python update_anisotropy.py 8.0e+05    # Increase anisotropy
"""

import sys
import os
import re

PROJECT_DIR = r"D:\Desktop\AI PROJECT\MacrospinExample_STTFMR_Hx10mT\MacrospinCodeEle_Simulation"
LAYERFREE_FILE = os.path.join(PROJECT_DIR, "file_configuration", "LayerFree_parameters.txt")


def update_anisotropy(K_u_new):
    """Update K_u (uniaxial anisotropy coefficient)."""
    
    with open(LAYERFREE_FILE, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    K_u_old = None
    
    for line in lines:
        # Match K_u line (e.g., "6.787e+05          !K_u (J/m^3)...")
        if re.match(r'^\d+\.\d+e\+?\d+\s+!K_u \(J/m\^3\)', line):
            K_u_old = re.search(r'([\d\.e\+]+)', line).group(1)
            updated_lines.append(f'{K_u_new:.3e}          !K_u (J/m^3)                 Uniaxial anisotropy coefficient LF\n')
        else:
            updated_lines.append(line)
    
    with open(LAYERFREE_FILE, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"[LAYERFREE] Updated K_u: {K_u_old} → {K_u_new:.3e} J/m³")
    print(f"[LAYERFREE] File: {LAYERFREE_FILE}")
    
    return K_u_old, K_u_new


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_anisotropy.py <K_u_value>")
        print("Example: python update_anisotropy.py 8.0e+05")
        sys.exit(1)
    
    try:
        K_u_new = float(sys.argv[1])
    except ValueError:
        print(f"[ERROR] Invalid K_u value: {sys.argv[1]}")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print(f"Updating Anisotropy (K_u)")
    print(f"{'='*50}\n")
    
    old, new = update_anisotropy(K_u_new)
    
    print(f"\n[NOTE] Higher K_u → Higher resonance frequency")
    print(f"[NOTE] Current value: {new:.3e} J/m³")


if __name__ == "__main__":
    main()
