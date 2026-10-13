
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from obspy import read, UTCDateTime
from obspy.signal.filter import bandpass

from src.seismosignal.config import RAW_DATA_DIR, FIGURES_DIR

waveform_path = RAW_DATA_DIR / "us6000qw60_IU_PET_BHZ.mseed"
stream = read(str(waveform_path))
stream.merge(method=1, fill_value="interpolate")

trace = stream[0].copy()
trace.data = trace.data.astype("float64")
trace.detrend("demean")
trace.detrend("linear")

sampling_rate = float(trace.stats.sampling_rate)
trace.data = bandpass(
    trace.data,
    freqmin=1.0,
    freqmax=10.0,
    df=sampling_rate,
    corners=4,
    zerophase=True,
)

# Times are relative to the start of the recording.
origin_time = UTCDateTime("2025-07-29T23:24:52.483000Z")
p_arrival = 18.90
s_arrival = 33.35

p_seconds = origin_time - stream[0].stats.starttime + p_arrival
s_seconds = origin_time - stream[0].stats.starttime + s_arrival

time = trace.times()

# Plot the first 120 seconds.
mask = time <= 120
fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(time[mask], trace.data[mask], linewidth=0.6)

ax.axvline(
    p_seconds,
    linestyle="--",
    label=f"Theoretical P arrival ({p_seconds:.1f} s)",
)
ax.axvline(
    s_seconds,
    linestyle="--",
    label=f"Theoretical S arrival ({s_seconds:.1f} s)",
)

ax.set_title("Filtered seismic waveform near predicted arrivals")
ax.set_xlabel("Seconds since recording start")
ax.set_ylabel("Amplitude (counts)")
ax.grid(True, alpha=0.3)
ax.legend()
fig.tight_layout()

output_path = FIGURES_DIR / "predicted_arrivals.png"
fig.savefig(output_path, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"Recording start: {stream[0].stats.starttime}")
print(f"Predicted P arrival: {p_seconds:.2f} seconds into recording")
print(f"Predicted S arrival: {s_seconds:.2f} seconds into recording")
print(f"Plot saved to: {output_path}")
