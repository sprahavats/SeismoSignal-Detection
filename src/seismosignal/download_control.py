
import os
import json
import certifi

from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

from src.seismosignal.config import RAW_DATA_DIR

os.environ["SSL_CERT_FILE"] = certifi.where()

client = Client(
    "https://service.earthscope.org",
    service_mappings={
        "station": "https://service.earthscope.org/fdsnws/station/1",
    },
    _discover_services=False,
)

# Background window: one week after the Alaska earthquake.
start = UTCDateTime("2021-08-05T06:14:49")
end = start + 660

network = "AK"
station = "CHN"
location = ""
channel = "BHZ"

waveform_path = RAW_DATA_DIR / "background_AK_CHN_BHZ.mseed"
metadata_path = RAW_DATA_DIR / "background_AK_CHN_BHZ.json"

try:
    stream = client.get_waveforms(
        network=network,
        station=station,
        location=location,
        channel=channel,
        starttime=start,
        endtime=end,
    )

    if len(stream) == 0:
        raise SystemExit("The service returned an empty waveform.")

    stream.write(str(waveform_path), format="MSEED")

    metadata = {
        "recording_type": "background_control",
        "network": network,
        "station": station,
        "channel": channel,
        "location": location,
        "waveform_start_utc": str(stream[0].stats.starttime),
        "waveform_end_utc": str(stream[0].stats.endtime),
        "sampling_rates_hz": sorted({
            float(trace.stats.sampling_rate)
            for trace in stream
        }),
        "n_traces": len(stream),
        "data_provider": "EarthScope FDSN",
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    print("Background recording downloaded.")
    print(stream)
    print(f"Waveform: {waveform_path}")
    print(f"Metadata: {metadata_path}")

except FDSNNoDataException:
    raise SystemExit(
        "No data available for this exact window. "
        "We'll choose another window rather than fabricate data."
    )
