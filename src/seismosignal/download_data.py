import os
import json
from datetime import datetime, timezone

from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

from src.seismosignal.config import RAW_DATA_DIR
os.environ["SSL_CERT_FILE"] = __import__("certifi").where()
# Public seismic data service
client = Client(
    "https://service.earthscope.org",
    service_mappings={
        "station": "https://service.earthscope.org/fdsnws/station/1",
        "dataselect": "https://service.earthscope.org/fdsnws/dataselect/1",
        "event": "https://earthquake.usgs.gov/fdsnws/event/1",
    },
    _discover_services=False,
)

# Search historical events with established waveform records.
search_start = UTCDateTime("2020-01-01")
search_end = UTCDateTime("2025-12-31")

print("Searching the earthquake catalog...")

try:
    catalog = client.get_events(
        starttime=search_start,
        endtime=search_end,
        minmagnitude=6.5,
        orderby="magnitude",
        limit=10,
    )
except Exception as exc:
    raise SystemExit(
        f"Could not retrieve earthquake catalog: {exc}\n"
        "Check your internet connection and try again."
    )

if len(catalog) == 0:
    raise SystemExit("No matching earthquake events were returned.")

print(f"Found {len(catalog)} candidate events.")

downloaded = False

# Try the candidate events until we find a usable waveform.
for event in catalog:
    origin = event.preferred_origin() or event.origins[0]
    magnitude = event.preferred_magnitude()

    if magnitude is None and event.magnitudes:
        magnitude = event.magnitudes[0]

    print(
        f"\nTrying event at {origin.time}; "
        f"magnitude: {magnitude.mag if magnitude else 'unknown'}"
    )

    starttime = origin.time - 60
    endtime = origin.time + 600

    try:
        inventory = client.get_stations(
            latitude=origin.latitude,
            longitude=origin.longitude,
            maxradius=3,
            starttime=starttime,
            endtime=endtime,
            channel="HHZ,BHZ",
            level="channel",
        )
    except Exception as exc:
        print(f"Station search failed: {exc}")
        continue

    attempts = 0

    for network in inventory:
        for station in network:
            for channel in station:
                if attempts >= 20:
                    break

                attempts += 1

                try:
                    stream = client.get_waveforms(
                        network=network.code,
                        station=station.code,
                        location=channel.location_code,
                        channel=channel.code,
                        starttime=starttime,
                        endtime=endtime,
                    )

                    if len(stream) == 0:
                        continue

                    # Use a unique, descriptive filename.
                    event_id = str(event.resource_id).split("/")[-1]
                    filename = (
                        f"{event_id}_{network.code}_"
                        f"{station.code}_{channel.code}"
                    )

                    waveform_path = RAW_DATA_DIR / f"{filename}.mseed"
                    metadata_path = RAW_DATA_DIR / f"{filename}.json"

                    stream.write(str(waveform_path), format="MSEED")

                    metadata = {
                        "event_id": str(event.resource_id),
                        "origin_time_utc": str(origin.time),
                        "latitude": origin.latitude,
                        "longitude": origin.longitude,
                        "depth_m": origin.depth,
                        "magnitude": (
                            magnitude.mag if magnitude else None
                        ),
                        "magnitude_type": (
                            magnitude.magnitude_type if magnitude else None
                        ),
                        "network": network.code,
                        "station": station.code,
                        "channel": channel.code,
                        "location": channel.location_code,
                        "waveform_start_utc": str(starttime),
                        "waveform_end_utc": str(endtime),
                        "sampling_rates_hz": sorted({
                            float(trace.stats.sampling_rate)
                            for trace in stream
                        }),
                        "n_traces": len(stream),
                        "downloaded_at_utc": datetime.now(
                            timezone.utc
                        ).isoformat(),
                        "data_provider": "IRIS FDSN",
                    }

                    metadata_path.write_text(
                        json.dumps(metadata, indent=2),
                        encoding="utf-8",
                    )

                    print("\nSUCCESS: waveform downloaded!")
                    print(f"Waveform: {waveform_path}")
                    print(f"Metadata: {metadata_path}")
                    print(stream)

                    downloaded = True
                    break

                except FDSNNoDataException:
                    continue
                except Exception as exc:
                    print(
                        f"Unavailable: {network.code}.{station.code} "
                        f"{channel.code}: {exc}"
                    )
                    continue

            if downloaded or attempts >= 20:
                break
        if downloaded or attempts >= 20:
            break

    if downloaded:
        break

if not downloaded:
    raise SystemExit(
        "\nNo usable waveform was downloaded from the candidates. "
        "We'll adjust the event/station search rather than fabricate data."
    )

