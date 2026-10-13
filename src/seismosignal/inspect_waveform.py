
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from obspy import read

from src.seismosignal.config import RAW_DATA_DIR, FIGURES_DIR

waveform_path = RAW_DATA_DIR / "us6000qw60_IU_PET_BHZ.mseed"

# Read the seismic waveform.
stream = read(str(waveform_path))
stream.merge(method=1, fill_value="interpolate")

print("Waveform summary:")
print(stream)

for trace in stream:
    print(f"\nStation: {trace.stats.network}.{trace.stats.station}")
    print(f"Channel: {trace.stats.channel}")
    print(f"Sampling rate: {trace.stats.sampling_rate} Hz")
    print(f"Number of samples: {trace.stats.npts}")
    print(f"Start time (UTC): {trace.stats.starttime}")
    print(f"End time (UTC): {trace.stats.endtime}")
    print(f"Duration: {trace.stats.npts / trace.stats.sampling_rate:.2f} seconds")
    print(f"Minimum amplitude: {trace.data.min():.2f}")
    print(f"Maximum amplitude: {trace.data.max():.2f}")

# Plot the waveform.
fig = stream.plot(
    type="relative",
    show=False,
    handle=True,
    size=(1200, 500),
)

output_path = FIGURES_DIR / "raw_seismic_waveform.png"
fig.savefig(output_path, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"\nWaveform plot saved to: {output_path}")
