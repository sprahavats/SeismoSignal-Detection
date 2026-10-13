
import matplotlib
matplotlib.use("Agg")

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.seismosignal.config import PROCESSED_DATA_DIR, FIGURES_DIR

rms_path = PROCESSED_DATA_DIR / "window_rms.csv"
rms_plot_path = FIGURES_DIR / "detected_energy_intervals.png"
events_path = PROCESSED_DATA_DIR / "candidate_intervals.csv"
summary_path = PROCESSED_DATA_DIR / "detection_summary.json"

# Load the RMS measurements produced by process_waveform.py.
df = pd.read_csv(rms_path)

times = df["window_center_seconds"].to_numpy(dtype=float)
rms = df["rms_amplitude_counts"].to_numpy(dtype=float)

if len(rms) < 5:
    raise SystemExit("Not enough RMS windows to estimate a robust threshold.")

# Robust baseline estimate using the median and median absolute deviation.
baseline = float(np.median(rms))
mad = float(np.median(np.abs(rms - baseline)))
robust_sigma = 1.4826 * mad

if robust_sigma == 0:
    raise SystemExit(
        "RMS variability is too small for a MAD threshold. "
        "Inspect the RMS data before selecting another method."
    )

threshold = baseline + 4.0 * robust_sigma
active = rms > threshold

# Group consecutive above-threshold windows into intervals.
intervals = []
start_idx = None

for i, is_active in enumerate(active):
    if is_active and start_idx is None:
        start_idx = i

    is_last = i == len(active) - 1
    if start_idx is not None and (not is_active or is_last):
        end_idx = i if is_active and is_last else i - 1

        intervals.append({
            "start_seconds": float(times[start_idx] - 5.0),
            "end_seconds": float(times[end_idx] + 5.0),
            "peak_rms_counts": float(np.max(rms[start_idx:end_idx + 1])),
            "windows_above_threshold": int(end_idx - start_idx + 1),
        })
        start_idx = None

# Save candidate intervals.
pd.DataFrame(
    intervals,
    columns=[
        "start_seconds",
        "end_seconds",
        "peak_rms_counts",
        "windows_above_threshold",
    ],
).to_csv(events_path, index=False)

# Plot RMS and the estimated threshold.
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(times, rms, marker="o", markersize=3, linewidth=1, label="10-second RMS")
ax.axhline(threshold, linestyle="--", label="Robust threshold (median + 4 × robust sigma)")

for interval in intervals:
    ax.axvspan(
        interval["start_seconds"],
        interval["end_seconds"],
        alpha=0.2,
    )

ax.set_title("Candidate high-energy intervals")
ax.set_xlabel("Time since recording start (seconds)")
ax.set_ylabel("RMS amplitude (counts)")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()
fig.savefig(rms_plot_path, dpi=200, bbox_inches="tight")
plt.close(fig)

summary = {
    "method": "10-second RMS threshold using median + 4 × (1.4826 × MAD)",
    "baseline_median_counts": baseline,
    "robust_sigma_counts": robust_sigma,
    "threshold_counts": float(threshold),
    "total_windows": int(len(rms)),
    "windows_above_threshold": int(np.sum(active)),
    "candidate_intervals": intervals,
    "interpretation_note": (
        "Intervals are high-energy candidates, not confirmed earthquake arrivals."
    ),
}

summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

print(f"Baseline median RMS: {baseline:.2f} counts")
print(f"Robust variability estimate: {robust_sigma:.2f} counts")
print(f"Detection threshold: {threshold:.2f} counts")
print(f"Windows above threshold: {int(np.sum(active))} / {len(rms)}")
print(f"Candidate intervals detected: {len(intervals)}")

for i, interval in enumerate(intervals, start=1):
    print(
        f"{i}. {interval['start_seconds']:.1f}–"
        f"{interval['end_seconds']:.1f} s; "
        f"peak RMS = {interval['peak_rms_counts']:.2f} counts"
    )

print(f"\nPlot saved to: {rms_plot_path}")
print(f"Intervals saved to: {events_path}")
print(f"Summary saved to: {summary_path}")
