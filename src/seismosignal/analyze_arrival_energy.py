
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from obspy import read
from obspy.signal.filter import bandpass

from src.seismosignal.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR

waveform_path = RAW_DATA_DIR / "us6000qw60_IU_PET_BHZ.mseed"
stream = read(str(waveform_path))
stream.merge(method=1, fill_value="interpolate")

trace = stream[0].copy()
trace.data = trace.data.astype(np.float64)
trace.detrend("demean")
trace.detrend("linear")

fs = float(trace.stats.sampling_rate)
filtered = bandpass(
    trace.data,
    freqmin=1.0,
    freqmax=10.0,
    df=fs,
    corners=4,
    zerophase=True,
)

# Five-second RMS windows.
window_seconds = 5
window_samples = int(window_seconds * fs)
n_windows = len(filtered) // window_samples

times = []
rms_values = []

for i in range(n_windows):
    start = i * window_samples
    end = start + window_samples
    segment = filtered[start:end]

    times.append((start + end) / (2 * fs))
    rms_values.append(float(np.sqrt(np.mean(segment**2))))

times = np.asarray(times)
rms_values = np.asarray(rms_values)

# Recording starts about 60 seconds before the event origin.
origin_offset = 60.0
p_time = origin_offset + 18.90
s_time = origin_offset + 33.35

# Compare RMS in baseline, P-wave, and S-wave windows.
windows = {
    "Pre-arrival baseline (30–55 s)": (30, 55),
    "P-wave region (75–90 s)": (75, 90),
    "S-wave region (90–110 s)": (90, 110),
}

print("Five-second RMS comparison:")
for label, (start, end) in windows.items():
    values = rms_values[(times >= start) & (times < end)]
    if len(values):
        print(
            f"{label}: median RMS = {np.median(values):.2f} counts; "
            f"maximum RMS = {np.max(values):.2f} counts"
        )

# Save detailed measurements.
csv_path = PROCESSED_DATA_DIR / "five_second_rms.csv"
pd.DataFrame({
    "window_center_seconds": times,
    "rms_amplitude_counts": rms_values,
}).to_csv(csv_path, index=False)

# Plot RMS near predicted arrivals.
mask = (times >= 30) & (times <= 120)

fig, ax = plt.subplots(figsize=(13, 5))
ax.plot(times[mask], rms_values[mask], marker="o", markersize=3)
ax.axvline(p_time, linestyle="--", label="Predicted P arrival")
ax.axvline(s_time, linestyle="--", label="Predicted S arrival")
ax.set_title("Five-second RMS energy near predicted seismic arrivals")
ax.set_xlabel("Seconds since recording start")
ax.set_ylabel("RMS amplitude (counts)")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

plot_path = FIGURES_DIR / "arrival_energy_comparison.png"
fig.savefig(plot_path, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"\nMeasurements saved: {csv_path}")
print(f"Plot saved: {plot_path}")
