import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from obspy import read
from obspy.signal.filter import bandpass
from obspy.signal.trigger import classic_sta_lta, trigger_onset

from src.seismosignal.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR

# --------------------------------------------------
# Configuration
# --------------------------------------------------
waveform_path = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else RAW_DATA_DIR / "us6000qw60_IU_PET_BHZ.mseed"
)

if not waveform_path.is_file():
    raise SystemExit(f"Waveform file not found: {waveform_path}")

sta_seconds = 1.0
lta_seconds = 20.0
trigger_on = 3.5
trigger_off = 1.0

# Predicted arrivals relative to recording start.
p_arrival_seconds = 78.888
s_arrival_seconds = 93.338

# Output files
output_stem = waveform_path.stem

events_path = PROCESSED_DATA_DIR / f"{output_stem}_sta_lta_intervals.csv"
summary_path = PROCESSED_DATA_DIR / f"{output_stem}_sta_lta_summary.json"
plot_path = FIGURES_DIR / f"{output_stem}_sta_lta_detection.png"


# --------------------------------------------------
# Load and preprocess the waveform
# Use the same preprocessing as the RMS detector.
# --------------------------------------------------
stream = read(str(waveform_path))
stream.merge(method=1, fill_value="interpolate")
trace = stream[0].copy()
trace.data = trace.data.astype(np.float64)

sampling_rate = float(trace.stats.sampling_rate)
raw = trace.data.copy()

trace.detrend("demean")
trace.detrend("linear")

filtered = bandpass(
    trace.data,
    freqmin=1.0,
    freqmax=10.0,
    df=sampling_rate,
    corners=4,
    zerophase=True,
)

times = np.arange(len(filtered)) / sampling_rate

# --------------------------------------------------
# Calculate STA/LTA characteristic function
# --------------------------------------------------
nsta = int(sta_seconds * sampling_rate)
nlta = int(lta_seconds * sampling_rate)

if nsta < 1 or nlta <= nsta:
    raise ValueError("Invalid STA/LTA window lengths.")

characteristic = classic_sta_lta(filtered, nsta, nlta)

# Hysteresis: trigger above trigger_on and end below trigger_off.
trigger_samples = trigger_onset(
    characteristic,
    trigger_on,
    trigger_off,
)

# Ignore any trigger that begins before the LTA has filled.
candidate_intervals = []

for start_sample, end_sample in trigger_samples:
    if start_sample < nlta:
        continue

    start_seconds = float(start_sample / sampling_rate)
    end_seconds = float(end_sample / sampling_rate)

    candidate_intervals.append({
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "duration_seconds": end_seconds - start_seconds,
        "peak_sta_lta": float(
            np.max(characteristic[start_sample:end_sample + 1])
        ),
    })

# --------------------------------------------------
# Save candidate intervals and metadata
# --------------------------------------------------
columns = [
    "start_seconds",
    "end_seconds",
    "duration_seconds",
    "peak_sta_lta",
]

pd.DataFrame(candidate_intervals, columns=columns).to_csv(
    events_path, index=False
)

summary = {
    "method": "Classic STA/LTA on detrended 1-10 Hz waveform",
    "sta_seconds": sta_seconds,
    "lta_seconds": lta_seconds,
    "trigger_on": trigger_on,
    "trigger_off": trigger_off,
    "sampling_rate_hz": sampling_rate,
    "candidate_intervals": candidate_intervals,
    "interpretation_note": (
        "STA/LTA intervals are candidate triggers, not confirmed "
        "earthquake detections. Parameters have not yet been validated "
        "on independent recordings."
    ),
}

summary_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8",
)

# --------------------------------------------------
# Plot waveform and STA/LTA characteristic function
# --------------------------------------------------
fig, axes = plt.subplots(
    2, 1, figsize=(14, 8), sharex=True,
    gridspec_kw={"height_ratios": [2, 1]}
)

axes[0].plot(times, filtered, linewidth=0.5, label="Filtered waveform")
if waveform_path.name == "us6000qw60_IU_PET_BHZ.mseed":
    axes[0].axvline(
        p_arrival_seconds, color="green", linestyle="--", label="Predicted P"
    )
    axes[0].axvline(
        s_arrival_seconds, color="red", linestyle="--", label="Predicted S"
    )

for interval in candidate_intervals:
    axes[0].axvspan(
        interval["start_seconds"],
        interval["end_seconds"],
        alpha=0.2,
    )

axes[0].set_title("STA/LTA candidate triggers on seismic waveform")
axes[0].set_ylabel("Amplitude (counts)")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

axes[1].plot(times, characteristic, linewidth=0.8, label="STA/LTA")
axes[1].axhline(
    trigger_on, linestyle="--", label=f"Trigger on ({trigger_on})"
)
axes[1].axhline(
    trigger_off, linestyle=":", label=f"Trigger off ({trigger_off})"
)

axes[1].set_xlabel("Time since recording start (seconds)")
axes[1].set_ylabel("STA/LTA ratio")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

fig.tight_layout()
fig.savefig(plot_path, dpi=200, bbox_inches="tight")
plt.close(fig)

# --------------------------------------------------
# Report results
# --------------------------------------------------
print(f"Sampling rate: {sampling_rate:.1f} Hz")
print(f"STA window: {sta_seconds:.1f} s ({nsta} samples)")
print(f"LTA window: {lta_seconds:.1f} s ({nlta} samples)")
print(f"Trigger thresholds: on={trigger_on}, off={trigger_off}")
print(f"Candidate intervals: {len(candidate_intervals)}")

for i, interval in enumerate(candidate_intervals, start=1):
    print(
        f"{i}. {interval['start_seconds']:.2f}–"
        f"{interval['end_seconds']:.2f} s; "
        f"duration={interval['duration_seconds']:.2f} s; "
        f"peak STA/LTA={interval['peak_sta_lta']:.2f}"
    )

print(f"\nPlot saved to: {plot_path}")
print(f"Intervals saved to: {events_path}")
print(f"Summary saved to: {summary_path}")
