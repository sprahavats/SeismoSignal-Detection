import os
import json
import certifi
import pandas as pd

from obspy import UTCDateTime, read
from obspy.clients.fdsn import Client
from obspy.taup import TauPyModel
from obspy.geodetics import locations2degrees

from src.seismosignal.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

os.environ["SSL_CERT_FILE"] = certifi.where()

client = Client(
    "https://service.earthscope.org",
    service_mappings={
        "station": "https://service.earthscope.org/fdsnws/station/1",
    },
    _discover_services=False,
)

model = TauPyModel(model="iasp91")

recordings = [
    {
        "type": "earthquake",
        "waveform": "us6000qw60_IU_PET_BHZ.mseed",
        "intervals": "sta_lta_candidate_intervals.csv",
        "summary": "sta_lta_detection_summary.json",
    },
    {
        "type": "earthquake",
        "waveform": "ak0219neiszm_AK_CHN_BHZ.mseed",
        "intervals": "ak0219neiszm_AK_CHN_BHZ_sta_lta_intervals.csv",
        "summary": "ak0219neiszm_AK_CHN_BHZ_sta_lta_summary.json",
    },
    {
        "type": "background_control",
        "waveform": "background_AK_CHN_BHZ.mseed",
        "intervals": "background_AK_CHN_BHZ_sta_lta_intervals.csv",
        "summary": "background_AK_CHN_BHZ_sta_lta_summary.json",
    },
]

results = []

for item in recordings:
    waveform_path = RAW_DATA_DIR / item["waveform"]
    metadata_path = waveform_path.with_suffix(".json")
    intervals_path = PROCESSED_DATA_DIR / item["intervals"]
    summary_path = PROCESSED_DATA_DIR / item["summary"]

    for path in (
        waveform_path, metadata_path, intervals_path, summary_path
    ):
        if not path.is_file():
            raise FileNotFoundError(f"Required file not found: {path}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    intervals = pd.read_csv(intervals_path)

    stream = read(str(waveform_path))
    stream.merge(method=1, fill_value="interpolate")
    sampling_rate = float(stream[0].stats.sampling_rate)

    peak_ratio = (
        float(intervals["peak_sta_lta"].max())
        if not intervals.empty else None
    )

    result = {
        "recording_type": item["type"],
        "waveform": item["waveform"],
        "event_id": metadata.get("event_id"),
        "station": (
            f"{metadata['network']}.{metadata['station']}."
            f"{metadata['channel']}"
        ),
        "magnitude": metadata.get("magnitude"),
        "sampling_rate_hz": sampling_rate,
        "candidate_interval_count": len(intervals),
        "strongest_trigger_ratio": peak_ratio,
        "predicted_P_seconds": None,
        "predicted_S_seconds": None,
        "P_associated_trigger_start_seconds": None,
        "P_associated_start_minus_P_seconds": None,
        "trigger_contains_P": None,
        "trigger_contains_S": None,
        "same_trigger_contains_P_and_S": None,
        "sta_seconds": summary["sta_seconds"],
        "lta_seconds": summary["lta_seconds"],
        "trigger_on": summary["trigger_on"],
        "trigger_off": summary["trigger_off"],
        "interpretation": (
            "Candidate triggers only; not confirmed detections"
        ),
    }

    if item["type"] == "earthquake":
        origin = UTCDateTime(metadata["origin_time_utc"])
        waveform_start = UTCDateTime(metadata["waveform_start_utc"])

        inventory = client.get_stations(
            network=metadata["network"],
            station=metadata["station"],
            location="*",
            channel=metadata["channel"],
            starttime=waveform_start,
            endtime=waveform_start + 1,
            level="channel",
        )

        if len(inventory) == 0:
            raise RuntimeError(
                f"Station metadata unavailable for {result['station']}"
            )

        station = inventory[0][0]
        distance_deg = locations2degrees(
            float(metadata["latitude"]),
            float(metadata["longitude"]),
            float(station.latitude),
            float(station.longitude),
        )

        arrivals = model.get_travel_times(
            source_depth_in_km=float(metadata["depth_m"]) / 1000.0,
            distance_in_degree=distance_deg,
            phase_list=["P", "S"],
        )

        for phase in ("P", "S"):
            matching = [a for a in arrivals if a.name == phase]
            if matching:
                result[f"predicted_{phase}_seconds"] = float(
                    origin + matching[0].time - waveform_start
                )

        p_time = result["predicted_P_seconds"]
        s_time = result["predicted_S_seconds"]

        p_matches = intervals[
            (intervals["start_seconds"] <= p_time)
            & (intervals["end_seconds"] >= p_time)
        ] if p_time is not None else intervals.iloc[0:0]

        s_matches = intervals[
            (intervals["start_seconds"] <= s_time)
            & (intervals["end_seconds"] >= s_time)
        ] if s_time is not None else intervals.iloc[0:0]

        result["trigger_contains_P"] = not p_matches.empty
        result["trigger_contains_S"] = not s_matches.empty

        result["same_trigger_contains_P_and_S"] = any(
            row["start_seconds"] <= p_time <= row["end_seconds"]
            and row["start_seconds"] <= s_time <= row["end_seconds"]
            for _, row in intervals.iterrows()
            if p_time is not None and s_time is not None
        )

        if not p_matches.empty:
            associated = p_matches.iloc[0]
        elif p_time is not None and not intervals.empty:
            associated = intervals.loc[
                (intervals["start_seconds"] - p_time).abs().idxmin()
            ]
        else:
            associated = None

        if associated is not None:
            result["P_associated_trigger_start_seconds"] = float(
                associated["start_seconds"]
            )
            if p_time is not None:
                result["P_associated_start_minus_P_seconds"] = (
                    float(associated["start_seconds"]) - p_time
                )

        result["epicentral_distance_deg"] = distance_deg
    else:
        result["interpretation"] = (
            "Background control; triggers are unclassified, "
            "not automatically false alarms"
        )

    results.append(result)

    print(
        f"{item['type']}: {item['waveform']} | "
        f"triggers={len(intervals)} | strongest ratio={peak_ratio}"
    )

output_path = PROCESSED_DATA_DIR / "sta_lta_evaluation.csv"
evaluation = pd.DataFrame(results)
evaluation.to_csv(output_path, index=False)

print("\n=== Combined STA/LTA Evaluation ===")
print(
    evaluation[
        [
            "recording_type",
            "station",
            "candidate_interval_count",
            "strongest_trigger_ratio",
            "predicted_P_seconds",
            "predicted_S_seconds",
            "trigger_contains_P",
            "trigger_contains_S",
            "same_trigger_contains_P_and_S",
        ]
    ].to_string(index=False)
)
print(f"\nSaved evaluation: {output_path}")
