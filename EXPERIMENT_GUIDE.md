# EnergyTracer: Experiment Guide

*Based on the methodology described by Luís Cruz in his [guide to scientific energy measurements](https://luiscruz.github.io/2021/10/10/scientific-guide.html).*

Energy measurements are inherently **noisy**. Background processes, thermal throttling, and hardware variability can all skew results. This guide explains how to obtain **reliable, reproducible** measurements with EnergyTracer by controlling the environment, running the automated script, and interpreting the outputs.

---

## TL;DR — Quick Checklist

Before launching the experiment, go through this checklist:

- [ ] Close **all** non-essential applications (including background apps and menu-bar utilities)
- [ ] Disconnect unnecessary peripherals (external drives, printers, etc.)
- [ ] Prefer a **wired** network connection — or disconnect the network entirely
- [ ] Lock display settings: brightness, volume, power-saving mode, screensaver off, sleep mode off
- [ ] **Plug in the power adapter** to avoid battery-level fluctuations
- [ ] Ensure a **stable ambient temperature** (avoid direct sunlight, heaters, etc.)
- [ ] Do **not** interact with the machine once the experiment starts

Then simply run:

```shell
./run_experiment.sh mac      # macOS (Apple Silicon): carbon + mac
./run_experiment.sh carbon   # Any platform: CodeCarbon only
```

On Windows, the batch script runs CodeCarbon only (no argument needed):

```bat
run_experiment.bat
```

The `mac` mode runs both `carbon` and `mac` profilers per iteration. The `carbon` mode runs CodeCarbon only. Run the shell script without arguments to see the usage.

---

## 1. Prepare the Environment

A controlled environment is the foundation of meaningful energy measurements. Each factor below can introduce variance that masks the real difference between code variants.

### 1.1 Minimize System Noise

| Action | Why |
|---|---|
| Disable non-essential services and applications | Background CPU/GPU/disk activity directly affects energy readings |
| Disconnect irrelevant peripherals | USB devices draw power and can trigger driver activity |
| Prefer wired over wireless connections | Wi-Fi radios consume variable power depending on signal strength |
| Disconnect the internet (if possible) | Prevents automatic updates, cloud sync, and telemetry |

### 1.2 Freeze System Settings

Lock all settings that could shift mid-experiment:

- **Screen brightness** — set to a fixed level (or minimum)
- **Volume** — mute or set to a fixed level
- **Power-saving / performance mode** — choose one and keep it
- **Screensaver & sleep** — disable both entirely
- **Notifications** — enable Do Not Disturb

### 1.3 Stabilize the Physical Environment

- Work in a room with **stable temperature** (thermal throttling alters CPU frequency and thus energy draw)
- **Plug in the power adapter** — battery discharge curves introduce non-linear noise, and the experiment can be long enough to drain your battery
- Avoid moving or touching the machine during the run

---

## 2. Run the Experiment

The automated script (`run_experiment.sh` / `run_experiment.bat`) executes all the steps described below. The shell script takes a **mode** argument: `mac` (runs both `carbon` and `mac` profilers) or `carbon` (runs CodeCarbon only). The Windows batch script always runs CodeCarbon only. Understanding the phases helps you verify that the protocol is sound.

### 2.1 Warm-Up Phase

The script begins by running **10 warm-up iterations** (×2 profilers) with 500 code iterations each. This brings the CPU, GPU, and memory subsystems to a steady thermal and performance state, eliminating cold-start bias.

### 2.2 Measurement Phase

Next, **30 measurement iterations** are performed for each profiler, each with 1 000 code iterations. The high number of repetitions is necessary to reach **statistical significance** and smooth out per-run variance.

### 2.3 Randomized Execution Order

Within every iteration, the `--shuffle` flag randomizes the order in which code variants are executed. This mitigates **time-correlated bias** (e.g., gradual thermal drift, OS scheduling changes).

### 2.4 Cooldown Between Runs

A **60-second cooldown** separates each measurement run, giving the hardware time to return to baseline temperature. Without cooldowns, heat accumulation from earlier runs would inflate energy readings for later ones.

### 2.5 Summary of Script Parameters

| Parameter | Value | Purpose |
|---|---|---|
| Warm-up runs | 10 | Stabilize the system |
| Warm-up code iterations | 500 | Enough work to reach thermal equilibrium |
| Measurement runs | 30 | Statistical significance |
| Measurement code iterations | 1 000 | Representative workload per run |
| Cooldown | 60 s | Thermal reset between runs |

> **Do not interact with the system** while the script is running. Any user activity (mouse movement, app switching, typing) introduces measurable energy noise.

---

## 3. Analyze the Results

Once the experiment completes, the automated script runs **ET-analyzer** to aggregate, clean, and statistically compare the measurements. You can also run it manually:

```shell
uv run ET-analyzer -v
```

### 3.1 Generated Outputs

- **CSV files** — raw per-iteration energy data for each profiler and code variant, ready for custom statistical analysis
- **Merged CSV files** — all runs concatenated per (profiler, data type, variant), saved under `results/`
- **Comparison plots** — per-component (CPU, GPU, ANE/gCO₂, DRAM) and overall energy comparison charts
- **Box plots** — distribution visualizations to inspect variance and outliers
- **Markdown reports** — a PR-ready statistical report per profiler / data type, including Welch's t-test, Cohen's d effect sizes, and a verdict section (saved as `results/<data_type>/<profiler>/<profiler>_report.md`)

### 3.2 What to Look For

1. **Magnitude of difference** — Is the energy gap between variants consistent across runs?
2. **Variance** — Large variance (wide box plots) suggests unstable measurements; consider increasing the number of runs or tightening the controlled environment.
3. **Outliers** — Occasional spikes may indicate garbage collection, OS interrupts, or thermal events. A few outliers in 30 runs are normal; many are a red flag.
4. **Component breakdown** — Check which hardware component (CPU, DRAM, GPU, ANE) drives the difference. This reveals *where* the code smell wastes energy.

### 3.3 Statistical Validation

For rigorous analysis beyond visual inspection, consider:

- **Mann–Whitney U test** — non-parametric test to determine if two distributions differ significantly (recommended for energy data, which is rarely normally distributed)
- **Effect size (Cliff's delta)** — quantifies how large the difference is, beyond mere statistical significance
- **Confidence intervals** — report medians with 95 % confidence intervals rather than means, to limit the influence of outliers

---

## References

- Luís Cruz, *[Tools and Techniques for Measuring Energy Consumption in Software](https://luiscruz.github.io/2021/10/10/scientific-guide.html)*, 2021
- CodeCarbon documentation: [https://codecarbon.io](https://codecarbon.io)
- Zeus (Apple Silicon energy measurement): [https://ml.energy/zeus](https://ml.energy/zeus)