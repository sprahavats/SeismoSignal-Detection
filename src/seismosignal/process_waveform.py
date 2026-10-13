

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from obspy import read
from obspy.signal.filter import bandpass

from src.seismosignal.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR

waveform_path = RAW_DATA_DIR / "us6000qw60_IU_PET_BHZ.mseed"

# Load the original waveform.
stream = read(str(waveform_path))
stream.merge(method=1, fill_value="interpolate")
trace = stream[0].copy()

# Convert to floating point before processing.
trace.data = trace.data.astype(np.float64)
raw = trace.data.copy()
sampling_rate = float(trace.stats.sampling_rate)
time = np.arange(len(raw)) / sampling_rate

# Remove the mean and linear trend.
trace.detrend("demean")
trace.detrend("linear")

# Band-pass filter: retain frequencies between 1 and 10 Hz.
filtered = bandpass(
    trace.data,
    freqmin=1.0,
    freqmax=10.0,
    df=sampling_rate,
    corners=4,
    zerophase=True,
)

# Calculate RMS amplitude in non-overlapping 10-second windows.
window_seconds = 10
window_samples = int(window_seconds * sampling_rate)
n_windows = len(filtered) // window_samples

rms_times = []
rms_values = []

for i in range(n_windows):
    start = i * window_samples
    end = start + window_samples
    segment = filtered[start:end]

    rms_times.append((start + end) / (2 * sampling_rate))
    rms_values.append(float(np.sqrt(np.mean(segment**2))))

# Save window-level measurements.
rms_path = PROCESSED_DATA_DIR / "window_rms.csv"
np.savetxt(
    rms_path,
    np.column_stack((rms_times, rms_values)),
    delimiter=",",
    header="window_center_seconds,rms_amplitude_counts",
    comments="",
)

# Plot raw and filtered traces.
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

axes[0].plot(time, raw, linewidth=0.5)
axes[0].set_title("Raw seismic waveform")
axes[0].set_ylabel("Amplitude (counts)")
axes[0].grid(True, alpha=0.3)

axes[1].plot(time, filtered, linewidth=0.5)
axes[1].set_title("Detrended, 1–10 Hz band-pass filtered waveform")
axes[1].set_xlabel("Time since recording start (seconds)")
axes[1].set_ylabel("Amplitude (counts)")
axes[1].grid(True, alpha=0.3)

fig.tight_layout()
plot_path = FIGURES_DIR / "raw_vs_filtered_waveform.png"
fig.savefig(plot_path, dpi=200, bbox_inches="tight")
plt.close(fig)

# Plot RMS energy over time.
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(rms_times, rms_values, marker="o", markersize=3, linewidth=1)
ax.set_title("Filtered waveform RMS energy (10-second windows)")
ax.set_xlabel("Time since recording start (seconds)")
ax.set_ylabel("RMS amplitude (counts)")
ax.grid(True, alpha=0.3)
fig.tight_layout()

rms_plot_path = FIGURES_DIR / "window_rms.png"
fig.savefig(rms_plot_path, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"Sampling rate: {sampling_rate:.1f} Hz")
print(f"Recording duration: {len(raw) / sampling_rate:.1f} seconds")
print(f"Filter: 1–10 Hz band-pass")
print(f"RMS windows: {n_windows} of {window_seconds} seconds")
print(f"Filtered waveform plot: {plot_path}")
print(f"RMS plot: {rms_plot_path}")
print(f"RMS measurements: {rms_path}")

if rms_values:
    peak_index = int(np.argmax(rms_values))
    print(
        f"Highest-RMS window: {rms_times[peak_index]:.1f} seconds "
        f"(RMS = {rms_values[peak_index]:.2f} counts)"
    )
