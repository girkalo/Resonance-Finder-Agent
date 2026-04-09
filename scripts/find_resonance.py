#!/usr/bin/env python3
"""
Complete resonance-finding workflow for STT-MRAM.

Automatically updates parameters, runs search, generates plot.

Usage:
    python find_resonance.py --h-dc 15 --k-u 7.0e+05
    python find_resonance.py --h-dc 20 (keep current K_u)
    python find_resonance.py (use current parameters)

Options:
    --h-dc <mT>       Set external DC field (default: keep current)
    --k-u <J/m^3>     Set anisotropy (default: keep current)
    --coarse-step     Coarse sweep step size MHz (default: 50)
    --fine-step       Fine sweep step size MHz (default: 10)
    --freq-min        Minimum search frequency Hz (default: 300e6)
    --freq-max        Maximum search frequency Hz (default: 900e6)
"""

import sys
import os
import subprocess
import argparse
import json
from datetime import datetime

# Paths
PROJECT_DIR = r"D:\Desktop\AI PROJECT\MacrospinExample_STTFMR_Hx10mT\MacrospinCodeEle_Simulation"
WORKSPACE_DIR = r"C:\Users\girka\.openclaw\workspace"


def run_script(script_name, args=None):
    """Run a Python script and capture output."""
    script_path = os.path.join(WORKSPACE_DIR, "scripts", script_name)
    cmd = ["python", script_path]
    if args:
        cmd.extend(args)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def coarse_sweep(freq_min, freq_max, step_mhz):
    """Run coarse sweep and return best frequency."""
    print(f"\n{'='*50}")
    print(f"PHASE 1: Coarse Sweep ({freq_min/1e6:.0f}-{freq_max/1e6:.0f} MHz, step {step_mhz} MHz)")
    print(f"{'='*50}\n")
    
    results = []
    freq = freq_min
    
    while freq <= freq_max:
        success, stdout, stderr = run_script("run_experiment.py", [f"{freq:.3e}"])
        
        # Parse Mz from output
        for line in stdout.split('\n'):
            if 'RESULT_MZ_AMP=' in line:
                mz = float(line.split('=')[1])
                results.append((freq, mz))
                print(f"  {freq/1e6:.0f} MHz -> Mz = {mz:.6f}")
                break
        
        freq += step_mhz * 1e6
    
    # Find best
    best_freq, best_mz = max(results, key=lambda x: x[1])
    print(f"\n[COARSE] Best: {best_freq/1e6:.0f} MHz, Mz = {best_mz:.6f}")
    
    return best_freq, results


def refine_peak(center_freq, step_mhz, num_points_each_side=3):
    """Refine around peak."""
    print(f"\n{'='*50}")
    print(f"PHASE 2: Refinement (±{num_points_each_side*step_mhz} MHz around peak)")
    print(f"{'='*50}\n")
    
    results = []
    
    for i in range(-num_points_each_side, num_points_each_side + 1):
        freq = center_freq + (i * step_mhz * 1e6)
        success, stdout, stderr = run_script("run_experiment.py", [f"{freq:.3e}"])
        
        for line in stdout.split('\n'):
            if 'RESULT_MZ_AMP=' in line:
                mz = float(line.split('=')[1])
                results.append((freq, mz))
                print(f"  {freq/1e6:.1f} MHz -> Mz = {mz:.6f}")
                break
    
    best_freq, best_mz = max(results, key=lambda x: x[1])
    print(f"\n[REFINE] Best: {best_freq/1e6:.1f} MHz, Mz = {best_mz:.6f}")
    
    return best_freq, results


def main():
    parser = argparse.ArgumentParser(description='Find resonance frequency in STT-MRAM')
    parser.add_argument('--h-dc', type=float, help='External DC field (mT)')
    parser.add_argument('--k-u', type=float, help='Uniaxial anisotropy (J/m³)')
    parser.add_argument('--coarse-step', type=int, default=50, help='Coarse step (MHz)')
    parser.add_argument('--fine-step', type=int, default=10, help='Fine step (MHz)')
    parser.add_argument('--freq-min', type=float, default=300e6, help='Min frequency (Hz)')
    parser.add_argument('--freq-max', type=float, default=900e6, help='Max frequency (Hz)')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"RESONANCE FINDER AGENT")
    print(f"{'='*60}")
    print(f"\nProject: {PROJECT_DIR}")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Update parameters if requested
    if args.h_dc:
        print(f"\n[SETUP] Updating DC field to {args.h_dc} mT")
        run_script("update_dc_field.py", [str(args.h_dc)])
    
    if args.k_u:
        print(f"[SETUP] Updating anisotropy to {args.k_u:.3e} J/m³")
        run_script("update_anisotropy.py", [f"{args.k_u:.3e}"])
    
    # Phase 1: Coarse sweep
    best_coarse, coarse_results = coarse_sweep(args.freq_min, args.freq_max, args.coarse_step)
    
    # Phase 2: Refinement
    best_refined, refine_results = refine_peak(best_coarse, args.fine_step)
    
    # Phase 3: Generate plot
    print(f"\n{'='*50}")
    print(f"PHASE 3: Generating Plot")
    print(f"{'='*50}\n")
    run_script("plot_resonance.py")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Peak Frequency: {best_refined/1e6:.2f} MHz")
    print(f"Max Mz: {max([r[1] for r in refine_results]):.6f}")
    print(f"Total experiments: {len(coarse_results) + len(refine_results)}")
    print(f"\nPlot saved: resonance_curve.png")
    print(f"Data saved: experiments.csv")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
