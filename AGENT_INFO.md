# Agent Documentation

## Agent: Resonance Finder
- **Created by:** Lizard (OpenClaw Agent) + Liza
- **Date:** 2026-04-07
- **Purpose:** Autonomous discovery of STT-MRAM resonance frequency

## Files Created by This Agent

### Core Scripts
- `scripts/run_experiment.py` - Execute single-frequency experiments
- `scripts/plot_resonance.py` - Generate resonance curve visualization

### Data & Results
- `input/logs/experiments.csv` - Experiment log (13 runs)
- `resonance_curve.png` - Resonance plot with peak marked

### Configuration Modified
- `file_configuration/ExternalExcitations_parameters.txt` - Frequency parameters (STT and external field)

## How to Reproduce

1. Run experiment at specific frequency:
   ```bash
   python scripts/run_experiment.py 5.42e8
   ```

2. Generate plot:
   ```bash
   python scripts/plot_resonance.py
   ```

3. View results:
   - Open `resonance_curve.png`
   - Check `input/logs/experiments.csv`

## Results Summary

- **Peak Frequency:** 542.0 MHz
- **Maximum Mz:** 0.0392
- **Q-Factor:** ~10.8
- **Search Method:** Coarse-to-fine (13 adaptive runs)

## For Future Agents

To create a new agent for this project:
1. Document in `AGENTS.md` at workspace root
2. Create new scripts in `scripts/` or `agents/<name>/`
3. Update this file with new agent info
4. Keep agent-specific data in dedicated folders

## Contact

Agent managed via OpenClaw session.
See workspace `AGENTS.md` for full registry.
