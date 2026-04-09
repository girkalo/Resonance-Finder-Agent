#!/usr/bin/env python3
"""
Update external DC field (H_DC_x) in ExternalExcitations_parameters.txt

Usage:
    python update_dc_field.py <H_DC_mT>
    
Example:
    python update_dc_field.py 10     # 10 mT (current)
    python update_dc_field.py 20     # 20 mT (stronger field)
"""

import sys
import os
import re

PROJECT_DIR = r"D:\Desktop\AI PROJECT\MacrospinExample_STTFMR_Hx10mT\MacrospinCodeEle_Simulation"
EXCITATIONS_FILE = os.path.join(PROJECT_DIR, "file_configuration", "ExternalExcitations_parameters.txt")


def update_dc_field(H_DC_new):
    """Update H_DC_x (external DC field in mT)."""
    
    with open(EXCITATIONS_FILE, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    H_DC_old = None
    
    for line in lines:
        # Match H_DC_x line (e.g., "10                 !H_DC_x (mT)...")
        if re.match(r'^\d+\s+!H_DC_x \(mT\)', line):
            H_DC_old = re.search(r'^(\d+)', line).group(1)
            updated_lines.append(f'{int(H_DC_new)}                 !H_DC_x (mT)                 External field DC x component\n')
        else:
            updated_lines.append(line)
    
    with open(EXCITATIONS_FILE, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"[EXCITATIONS] Updated H_DC_x: {H_DC_old} mT -> {int(H_DC_new)} mT")
    print(f"[EXCITATIONS] File: {EXCITATIONS_FILE}")
    
    return H_DC_old, H_DC_new


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_dc_field.py <H_DC_mT>")
        print("Example: python update_dc_field.py 20")
        sys.exit(1)
    
    try:
        H_DC_new = float(sys.argv[1])
    except ValueError:
        print(f"[ERROR] Invalid H_DC value: {sys.argv[1]}")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print(f"Updating External DC Field (H_DC_x)")
    print(f"{'='*50}\n")
    
    old, new = update_dc_field(H_DC_new)
    
    print(f"\n[NOTE] Higher H_DC → Higher resonance frequency")
    print(f"[NOTE] Current value: {int(new)} mT")


if __name__ == "__main__":
    main()
