#!/usr/bin/env python3
"""
Resonance Finder - Run a single MacrospinLLG experiment at specified frequency.

Usage:
    python run_experiment.py <frequency_hz>

Example:
    python run_experiment.py 5.5e8
"""

import sys
import os
import subprocess
import re
import csv
from datetime import datetime

# Project paths (adjust if needed)
PROJECT_DIR = r"D:\Desktop\AI PROJECT\MacrospinExample_STTFMR_Hx10mT\MacrospinCodeEle_Simulation"
CONFIG_FILE = os.path.join(PROJECT_DIR, "file_configuration", "ExternalExcitations_parameters.txt")
EXE_PATH = os.path.join(PROJECT_DIR, "MacrospinLLG.exe")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "output", "RES.out")
LOG_FILE = os.path.join(PROJECT_DIR, "input", "logs", "experiments.csv")


def update_config(frequency_hz):
    """
    Update ExternalExcitations_parameters.txt for single-frequency run.
    Sets both STT frequency and external field frequency to the same value.
    """
    with open(CONFIG_FILE, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    for line in lines:
        # Switch STT to single frequency mode (FLAG = 0)
        if re.match(r'^1\s+!\s+FLAG Current Frequency STT', line):
            updated_lines.append('0                  !                       FLAG Current Frequency STT\n')
        # Set STT frequency
        elif re.match(r'^\d+\.\d+e\+?\d+\s+!f_J_STT', line):
            updated_lines.append(f'{frequency_hz:.3e}          !f_J_STT (Hz)                    Current frequency STT\n')
        # Switch external field to single frequency mode (FLAG = 0)
        elif re.match(r'^1\s+!\s+FLAG External field frequency', line):
            updated_lines.append('0                  !                       FLAG External field frequency\n')
        # Set external field frequency
        elif re.match(r'^\d+\.\d+e\+?\d+\s+!f_ext', line):
            updated_lines.append(f'{frequency_hz:.3e}          !f_ext (Hz)                  External field frequency\n')
        else:
            updated_lines.append(line)
    
    with open(CONFIG_FILE, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"[CONFIG] Set STT and external field frequency to {frequency_hz:.3e} Hz")
    print("[CONFIG] Switched to single-frequency mode")


def run_simulation():
    """Run MacrospinLLG.exe and wait for completion."""
    print("[SIM] Running MacrospinLLG.exe...")
    
    # Change to project directory for execution
    result = subprocess.run(
        [EXE_PATH],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"[ERROR] Simulation failed: {result.stderr}")
        return False
    
    print("[SIM] Simulation completed successfully")
    return True


def parse_output():
    """
    Parse output/RES.out to extract amplitudes.
    Returns dict with frequencies and amplitudes.
    """
    if not os.path.exists(OUTPUT_FILE):
        print(f"[ERROR] Output file not found: {OUTPUT_FILE}")
        return None
    
    with open(OUTPUT_FILE, 'r') as f:
        lines = f.readlines()
    
    if len(lines) < 1:
        print("[ERROR] Output file is empty")
        return None
    
    # Read first data row (no header in RES.out)
    # Format: STT_freq SOT_freq EXT_freq VCMA_freq Mx_amp My_amp Mz_amp
    data_line = lines[0].strip()
    values = data_line.split()
    
    if len(values) < 7:
        print(f"[ERROR] Unexpected output format: {data_line}")
        return None
    
    return {
        'stt_freq': float(values[0]),
        'sot_freq': float(values[1]),
        'ext_freq': float(values[2]),
        'vcma_freq': float(values[3]),
        'mx_amp': float(values[4]),
        'my_amp': float(values[5]),
        'mz_amp': float(values[6])
    }


def log_result(data, frequency_hz):
    """Append result to experiments.csv."""
    timestamp = datetime.now().isoformat()
    
    # Determine run_id (next available number)
    run_id = 1
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            rows = list(reader)
            if rows:
                run_id = len(rows) + 1
    
    row = [
        run_id,
        timestamp,
        data['stt_freq'],
        data['sot_freq'],
        data['ext_freq'],
        data['vcma_freq'],
        data['mx_amp'],
        data['my_amp'],
        data['mz_amp'],
        f"Single frequency test at {frequency_hz:.3e} Hz"
    ]
    
    # Append to CSV
    file_exists = os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['run_id', 'timestamp', 'stt_freq_hz', 'sot_freq_hz', 'ext_freq_hz', 
                           'vcma_freq_hz', 'mx_amp', 'my_amp', 'mz_amp', 'notes'])
        writer.writerow(row)
    
    print(f"[LOG] Appended run {run_id} to experiments.csv")
    return run_id


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_experiment.py <frequency_hz>")
        print("Example: python run_experiment.py 5.5e8")
        sys.exit(1)
    
    try:
        frequency_hz = float(sys.argv[1])
    except ValueError:
        print(f"[ERROR] Invalid frequency: {sys.argv[1]}")
        sys.exit(1)
    
    print(f"\n{'='*50}")
    print(f"Resonance Finder - Experiment Runner")
    print(f"Target frequency: {frequency_hz:.3e} Hz")
    print(f"{'='*50}\n")
    
    # Step 1: Update config
    update_config(frequency_hz)
    
    # Step 2: Run simulation
    if not run_simulation():
        sys.exit(1)
    
    # Step 3: Parse output
    data = parse_output()
    if data is None:
        sys.exit(1)
    
    # Step 4: Log result
    run_id = log_result(data, frequency_hz)
    
    # Step 5: Report
    print(f"\n{'='*50}")
    print(f"Experiment {run_id} Complete")
    print(f"Frequency: {data['stt_freq']:.3e} Hz")
    print(f"Mz Amplitude: {data['mz_amp']:.6e}")
    print(f"Mx Amplitude: {data['mx_amp']:.6e}")
    print(f"My Amplitude: {data['my_amp']:.6e}")
    print(f"{'='*50}\n")
    
    # Return Mz amplitude for agent decision-making
    print(f"RESULT_MZ_AMP={data['mz_amp']}")


if __name__ == "__main__":
    main()
