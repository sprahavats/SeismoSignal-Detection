# SeismoSignal-Detection
### Preliminary Seismic Event Detection Using Signal Processing and STA/LTA Analysis

**Author:** Spraha Vats
**Project Type:** Independent Research Project
**Domain:** Seismology, Signal Processing, Scientific Computing

## Abstract

Seismic waveform analysis is an important component of earthquake characterization and seismic event detection. However, identifying earthquake-related signals in continuous ground-motion recordings is challenging because recorded waveforms may also contain background seismic activity, local disturbances, and instrumental noise.

**SeismoSignal-Detection** is a Python-based exploratory research project investigating signal-processing approaches for identifying candidate seismic events in real waveform data. The project combines waveform visualization, detrending, bandpass filtering, rolling root mean square (RMS) energy analysis, robust statistical thresholding, and the classic Short-Term Average/Long-Term Average (STA/LTA) triggering algorithm.

The initial energy-based analysis was performed on a 660-second waveform associated with the 29 July 2025 Kamchatka earthquake (magnitude 8.8), recorded at station IU.PET. The project was subsequently extended to include a second earthquake recording from the 2021 Alaska Peninsula earthquake (magnitude 8.2) and a background-control recording from the same Alaska station.

In the preliminary STA/LTA evaluation, candidate intervals in both earthquake recordings contained the theoretically predicted P- and S-wave arrival times. However, the background-control recording also produced ten candidate intervals, including a strong transient with a peak STA/LTA ratio of approximately 17.46. These findings demonstrate why signal-energy thresholds alone are insufficient to establish whether a detected transient is an earthquake.

The project establishes a reproducible foundation for further experimentation with seismic event detection. Its current findings are preliminary and do not constitute validated detection performance.

---

## 1. Introduction

Earthquakes generate seismic waves that propagate through the Earth and are recorded by seismometers. These waveforms contain information about the timing, amplitude, frequency content, and characteristics of seismic arrivals.

Two important phases are the primary (P) wave, which generally arrives first, and the secondary (S) wave, which generally follows. Their theoretical arrival times can be estimated using seismic travel-time models when the earthquake location, source depth, and recording-station coordinates are known.

Automated identification of these phases and other seismic signals requires distinguishing relevant waveform changes from background activity. Simple approaches based on amplitude or signal energy can identify unusual intervals, but they may also respond to unrelated transients.

This project explores two complementary detection approaches:

1. **Energy-based detection:** Identifying unusually energetic waveform intervals using rolling RMS measurements and a robust statistical threshold.
2. **STA/LTA triggering:** Comparing short-term signal energy with a longer-term estimate of the local signal level to identify sudden changes.

The two approaches provide a basis for examining how different detection methods respond to earthquake recordings and background signals.

## 2. Research Objectives

The main objectives are to:

- Acquire real seismic waveform data and associated earthquake metadata through FDSN services.
- Inspect waveform duration, sampling frequency, amplitude, and signal characteristics.
- Apply detrending and bandpass filtering to reduce trends and restrict the analysed frequency range.
- Quantify signal energy using rolling RMS measurements.
- Identify candidate high-energy intervals using median absolute deviation (MAD)-based thresholding.
- Implement classic STA/LTA triggering for automated identification of candidate intervals.
- Compare candidate intervals with theoretically predicted P- and S-wave arrival times.
- Evaluate detector behaviour across two earthquake recordings and one background-control recording.
- Develop a reproducible analysis pipeline and identify limitations requiring further investigation.

## 3. Dataset and Experimental Design

The project uses waveform data obtained through EarthScope FDSN services, with earthquake information and theoretical arrival estimates used to interpret the recordings.

### 3.1 Earthquake recordings

| Parameter | Kamchatka earthquake | Alaska Peninsula earthquake |
|---|---|---|
| Earthquake date | 29 July 2025 | 29 July 2021 |
| Reported magnitude | 8.8 | 8.2 |
| Event identifier | `us6000qw60` | `ak0219neiszm` |
| Network | IU | AK |
| Station | PET | CHN |
| Channel | BHZ | BHZ |
| Sampling frequency | 40 Hz | 50 Hz |
| Recording duration | 660 seconds | 660 seconds |
| Analysis role | Earthquake example | Additional earthquake example |

The recordings contain vertical-component seismic waveforms. The Alaska recording provides an additional example at a different station and sampling frequency.

### 3.2 Background-control recording

A third recording was obtained from station `AK.CHN.BHZ` for the interval beginning 5 August 2021 at approximately 06:14:49 UTC.

| Parameter | Value |
|---|---|
| Recording type | Background control |
| Station | `AK.CHN.BHZ` |
| Sampling frequency | 50 Hz |
| Recording duration | 660 seconds |
| Detector role | Examine candidate triggers outside the two selected earthquake recordings |

The background recording was selected as a control for evaluating detector behaviour. It has not been independently established as completely free of earthquakes or other seismic events. Therefore, its candidate triggers cannot automatically be classified as false alarms.

### 3.3 Data management

Raw waveform files and generated processed tables are stored locally and excluded from version control. The repository contains the analysis scripts, documentation, and generated figures.

The raw files used in the experiments are:

- `us6000qw60_IU_PET_BHZ.mseed`
- `ak0219neiszm_AK_CHN_BHZ.mseed`
- `background_AK_CHN_BHZ.mseed`

Corresponding metadata are stored as JSON files. The metadata include recording times, station information, and, for the earthquake recordings, event information used for travel-time calculations.

## 4. Methodology

### 4.1 Data acquisition and metadata

Waveform and event information are obtained using Python and ObsPy through FDSN data services. Station metadata are used to retrieve station coordinates for the theoretical arrival-time calculations.

Recording start times are retained so that predicted arrival times can be expressed in seconds relative to the beginning of each waveform.

### 4.2 Waveform inspection

The initial inspection examines:

- Sampling frequency and number of samples.
- Recording duration.
- Waveform amplitude and signal structure.
- Raw waveform visualizations.
- Changes in signal characteristics over time.

This stage provides context for selecting appropriate preprocessing and detection parameters.

### 4.3 Detrending and bandpass filtering

The waveforms are detrended to remove constant and linear trends. A bandpass filter between 1 and 10 Hz is then applied to the waveforms used for the principal energy and STA/LTA analyses.

The filtering restricts the analysis to a selected frequency band. Its effectiveness depends on the signal characteristics and the frequency content of both the seismic arrivals and background noise.

The current analysis uses waveform counts for its principal detector inputs. The reported amplitudes should not be interpreted as calibrated ground displacement or velocity.

### 4.4 RMS energy analysis

The initial detector calculates rolling root mean square (RMS) amplitude over short waveform windows. RMS is defined as

\[
\operatorname{RMS}(x)=
\sqrt{\frac{1}{N}\sum_{i=1}^{N}x_i^2}
\]

where \(x_i\) represents a waveform sample and \(N\) is the number of samples in the window.

RMS provides a measure of signal amplitude that is less sensitive to sign changes than a simple arithmetic mean. An increase in RMS can indicate a period of elevated waveform activity.

The initial workflow includes 10-second RMS windows and additional shorter-window analysis.

### 4.5 Robust statistical thresholding

The energy-based detector estimates a threshold from the distribution of RMS measurements using the median and median absolute deviation.

For RMS measurements \(R_i\), the median absolute deviation is

\[
\operatorname{MAD} =
\operatorname{median}
\left(
|R_i-\operatorname{median}(R)|
\right)
\]

A robust variability estimate can be calculated as

\[
\sigma_{\mathrm{robust}}
\approx 1.4826\,\operatorname{MAD}
\]

The initial implementation uses the threshold

\[
T =
\operatorname{median}(R)
+4\sigma_{\mathrm{robust}}
\]

Consecutive windows above the threshold are grouped into candidate high-energy intervals.

An important limitation is that the initial threshold is estimated using the complete recording, including the earthquake signal and its coda. Consequently, the event itself can influence the baseline and threshold. The detected interval is therefore treated as a candidate region rather than a confirmed event.

### 4.6 Classic STA/LTA triggering

The second detection approach implements the classic Short-Term Average/Long-Term Average algorithm.

STA represents recent signal energy over a short window, while LTA estimates the longer-term signal level. A high STA/LTA ratio indicates that recent energy has increased relative to the longer-term average.

The current implementation uses the following parameters:

| Parameter | Value |
|---|---:|
| Short-term average window | 1 second |
| Long-term average window | 20 seconds |
| Trigger-on threshold | 3.5 |
| Trigger-off threshold | 1.0 |
| Preprocessing | Detrending and 1–10 Hz bandpass filtering |

The long-term average must first accumulate sufficient samples before triggers are considered.

Intervals are generated using the onset and offset thresholds. For each interval, the implementation records its start time, end time, duration, and peak STA/LTA ratio.

The detector is designed to identify candidate transients. It does not independently determine whether each transient is an earthquake, a local disturbance, or instrumental noise.

### 4.7 Theoretical P- and S-wave arrival times

For the two earthquake recordings, theoretical travel times are calculated using ObsPy's TauP implementation and the `iasp91` Earth model.

The calculation uses:

- Earthquake latitude and longitude.
- Earthquake source depth.
- Recording-station coordinates.
- Epicentral angular distance.
- Waveform start time and earthquake origin time.

Theoretical arrival times are converted to seconds relative to waveform start:

\[
t_{\mathrm{arrival,relative}} =
t_{\mathrm{origin}}
+t_{\mathrm{travel}}
-t_{\mathrm{waveform,start}}
\]

The resulting estimates are compared with the candidate STA/LTA intervals.

If an interval contains a predicted P or S arrival, the interval is marked as overlapping that theoretical arrival. This is a timing-consistency check, not an independently verified phase pick.

### 4.8 Combined evaluation

A single evaluation table is generated for all three recordings. It includes:

- Recording type and waveform filename.
- Station and sampling frequency.
- Number of candidate intervals.
- Strongest candidate STA/LTA ratio.
- Predicted P- and S-wave arrival times, where applicable.
- Whether candidate intervals contain the predicted arrivals.
- Whether one candidate interval contains both arrivals.
- Detector parameters and interpretation notes.

The background control is evaluated for trigger counts and peak ratios only. Theoretical earthquake arrival checks are not applied to it because it is not associated with a specified target earthquake.

## 5. Results

### 5.1 Initial RMS-based analysis

The initial energy-based detector was applied to the 660-second Kamchatka waveform.

| Measurement | Preliminary result |
|---|---:|
| Sampling frequency | 40 Hz |
| Recording duration | 660 seconds |
| Candidate high-energy interval | 80–230 seconds after waveform start |
| Baseline median RMS | 322,592.52 counts |
| Robust variability estimate | 420,600.69 counts |
| Detection threshold | 2,004,995.28 counts |
| Windows above threshold | 15 of 66 |
| Peak RMS in candidate interval | 11,574,393.47 counts |

The detector identified one broad high-energy interval. Its duration and boundaries depend on the RMS windowing and thresholding method.

These results demonstrate the operation of the energy-based analysis but do not establish that the entire interval corresponds exclusively to earthquake phases. The threshold is estimated from the same recording being analysed.

### 5.2 Theoretical arrival-time comparison

The preliminary STA/LTA evaluation produced the following results:

| Measurement | Kamchatka | Alaska Peninsula |
|---|---:|---:|
| Predicted P arrival | 78.86 s | 79.02 s |
| Predicted S arrival | 93.28 s | 93.59 s |
| P-associated trigger start | 77.72 s | 76.36 s |
| Trigger start relative to predicted P | −1.13 s | −2.66 s |
| Candidate intervals | 7 | 15 |
| Same trigger contains P and S | Yes | Yes |

The P-associated trigger in the Kamchatka recording spans approximately 77.72–106.75 seconds. In the Alaska recording, it spans approximately 76.36–106.00 seconds.

In both cases, one candidate interval contains the theoretical P- and S-wave arrival times. This is consistent with the detector responding to increased waveform activity around the expected arrivals.

However, these overlaps do not establish exact arrival-picking accuracy. The trigger boundaries are controlled by the STA/LTA thresholds and can begin before the theoretical P arrival.

### 5.3 Comparison across all three recordings

| Recording | Sampling frequency | Candidate intervals | Strongest peak STA/LTA ratio |
|---|---:|---:|---:|
| Kamchatka earthquake | 40 Hz | 7 | 19.83 |
| Alaska Peninsula earthquake | 50 Hz | 15 | 19.79 |
| Background control | 50 Hz | 10 | 17.46 |

The background-control recording produced ten candidate intervals. Its strongest interval spans approximately 580.88–582.48 seconds after recording start, with a peak STA/LTA ratio of approximately 17.46.

The waveform around this interval was observed to contain irregular oscillations, a pronounced spike, and smaller subsequent oscillations. Quantitative analysis of the filtered signal produced the following measurements:

| Window | RMS amplitude | Peak absolute amplitude |
|---|---:|---:|
| Earlier background, 560–570 s | 10.08 counts | 29.50 counts |
| Before trigger, 575–580.88 s | 9.51 counts | 83.29 counts |
| Trigger, 580.88–582.48 s | 83.73 counts | 400.05 counts |
| After trigger, 582.48–587 s | 20.96 counts | 79.15 counts |

The trigger-window RMS is approximately 8.8 times the RMS in the immediately preceding comparison window. This confirms that the detector identified a pronounced transient relative to its surroundings.

A USGS earthquake-catalog query returned no catalogued events of magnitude 0 or greater within 300 km of the station during the specified 06:19–06:30 UTC search interval on 5 August 2021. This result does not prove that the transient was non-seismic: smaller or uncatalogued events and non-earthquake sources remain possible.

### 5.4 Interpretation of the combined results

The preliminary findings support three observations:

1. **Energy-based detection identifies broad high-energy intervals.** The RMS-based detector found one candidate interval in the Kamchatka recording.
2. **STA/LTA triggers overlap expected earthquake arrivals in both selected earthquake recordings.** A candidate interval in each recording contained the theoretical P- and S-wave arrival times.
3. **Background transients can produce strong triggers.** The background control generated ten candidate intervals, and its strongest STA/LTA ratio was substantial compared with the ratios in the earthquake recordings.

The third observation is particularly important. The maximum STA/LTA ratio in the background control was 17.46, while the maximum ratios in the two earthquake recordings were approximately 19.83 and 19.79. These values overlap sufficiently that the peak ratio alone cannot reliably distinguish the recordings' signal sources.

The results motivate further validation using larger datasets, independent event labels, and additional signal features.

## 6. Software Architecture and Project Structure

The project is organized into acquisition, waveform-processing, detection, and evaluation modules.

```text
SeismoSignal-Detection/
├── src/
│   └── seismosignal/
│       ├── __init__.py
│       ├── config.py
│       ├── download_data.py
│       ├── inspect_waveform.py
│       ├── inspect_arrivals.py
│       ├── process_waveform.py
│       ├── analyze_arrival_energy.py
│       ├── detect_events.py
│       ├── detect_sta_lta.py
│       ├── evaluate_sta_lta.py
│       └── download_control.py
├── data/
│   ├── raw/                 # Downloaded waveforms and metadata
│   └── processed/           # Generated analysis tables
├── reports/
│   └── figures/             # Generated visualizations
├── notebooks/               # Space for exploratory analysis
├── tests/                   # Space for automated tests
├── requirements.txt
├── .gitignore
└── README.md
```

Raw waveform files and generated processed tables are excluded from version control. The figures and source scripts are retained in the repository.

## 7. Technologies and Tools

- **Python:** Core implementation and analysis.
- **ObsPy:** Seismic waveform handling, FDSN data access, and theoretical travel-time calculations.
- **NumPy:** Numerical operations and waveform calculations.
- **pandas:** Interval tables and combined evaluation results.
- **SciPy:** Scientific signal-processing functionality.
- **Matplotlib:** Waveform plots, energy visualizations, and detector diagnostics.
- **EarthScope FDSN services:** Access to seismic waveform and station metadata.
- **USGS earthquake catalog:** External catalog check for the background-control transient.
- **Git and GitHub:** Version control and project publication.

## 8. Reproducibility

### 8.1 Environment

The project uses Python and the dependencies specified in `requirements.txt`. Run commands from the repository root.

Install the listed dependencies in an appropriate Python environment:

```bash
python -m pip install -r requirements.txt
```

The exact environment and package versions should be recorded when preparing a final reproducibility release.

### 8.2 Running the analyses

The main processing and evaluation modules can be run with:

```bash
python -m src.seismosignal.process_waveform
python -m src.seismosignal.detect_events
python -m src.seismosignal.detect_sta_lta
python -m src.seismosignal.detect_sta_lta data/raw/ak0219neiszm_AK_CHN_BHZ.mseed
python -m src.seismosignal.detect_sta_lta data/raw/background_AK_CHN_BHZ.mseed
python -m src.seismosignal.evaluate_sta_lta
```

The acquisition scripts can be used to retrieve the required recordings and metadata. Review their configuration and requested time intervals before rerunning them.

The evaluation script expects the three waveform files, their corresponding JSON metadata, and the interval CSV and summary JSON files generated by the detector.

### 8.3 Generated outputs

Important outputs include:

- `data/processed/window_rms.csv`
- `data/processed/sta_lta_evaluation.csv`
- `data/processed/sta_lta_candidate_intervals.csv`
- `data/processed/ak0219neiszm_AK_CHN_BHZ_sta_lta_intervals.csv`
- `data/processed/background_AK_CHN_BHZ_sta_lta_intervals.csv`
- `reports/figures/raw_vs_filtered_waveform.png`
- `reports/figures/window_rms.png`
- `reports/figures/background_AK_CHN_BHZ_sta_lta_detection.png`
- `reports/figures/background_peak_zoom.png`

Some filenames correspond to the original single-waveform pipeline, while others use the newer per-waveform naming convention.

Raw recordings and generated processed data are excluded from Git tracking. To reproduce the evaluation, download the corresponding recordings and regenerate the required intermediate outputs before running the combined evaluation script.

## 9. Limitations

This project is an exploratory prototype. Its present results should be interpreted in light of the following limitations.

### Dataset size and representativeness

The STA/LTA comparison contains only two earthquake recordings and one background-control recording. This sample is too small to establish performance across different earthquake magnitudes, distances, geological settings, instruments, or noise conditions.

### Uncertain background labels

The background-control recording has not been independently verified as event-free. Candidate intervals in this recording cannot automatically be labelled false positives.

### Threshold sensitivity

The STA/LTA trigger thresholds are fixed parameters selected for experimentation. Their performance may change with noise levels, station characteristics, and filtering choices.

The RMS threshold is estimated from the full recording, meaning that strong event-related activity can influence the estimated baseline and threshold.

### Theoretical arrival uncertainty

Predicted P- and S-wave times are calculated using a theoretical Earth model and available event and station metadata. They are reference estimates rather than independently verified phase picks.

### Instrument response and physical units

The principal detector uses filtered waveform counts. The analysis does not yet establish calibrated physical ground-motion units through a complete instrument-response correction and validation workflow.

### Performance metrics

Precision, recall, false-positive rate, missed-event rate, and generalization performance have not been established. The current results should not be summarized as a validated detection accuracy percentage.

### Operational applicability

The detector is not an operational earthquake early-warning system. It has not been validated for real-time deployment, network-scale monitoring, or safety-critical use.

## 10. Future Work

The following extensions would strengthen the project scientifically.

1. **Expand the dataset:** Evaluate a larger and more diverse collection of earthquake and background recordings.
2. **Verify event labels:** Compare candidate triggers with catalogued events and independently annotated waveform arrivals.
3. **Improve baseline estimation:** Investigate adaptive noise estimates and thresholds that are less influenced by the event itself.
4. **Study parameter sensitivity:** Evaluate alternative STA/LTA windows, trigger-on thresholds, trigger-off thresholds, and frequency bands.
5. **Quantify performance:** Calculate precision, recall, false-trigger rate, and detection delay using independently labelled data.
6. **Investigate signal characteristics:** Compare amplitude, duration, spectral content, and waveform morphology across earthquake-associated and background triggers.
7. **Address instrument response:** Correct for instrument response where appropriate and document the physical units of processed signals.
8. **Improve automated testing:** Add tests for interval generation, waveform handling, metadata validation, and evaluation-table generation.
9. **Assess generalization:** Evaluate the detector on recordings from stations and earthquakes not used during parameter selection.
10. **Explore additional methods:** Compare STA/LTA with alternative signal-processing methods and, if a sufficiently labelled dataset becomes available, machine-learning approaches.

## 11. Conclusion

SeismoSignal-Detection implements a preliminary seismic signal-analysis pipeline combining waveform processing, RMS-based energy analysis, robust thresholding, classic STA/LTA triggering, and theoretical arrival-time comparison.

The initial Kamchatka analysis identified one broad high-energy interval. In the subsequent evaluation, both the Kamchatka and Alaska earthquake recordings contained candidate intervals spanning their theoretically predicted P- and S-wave arrivals.

The background-control recording also produced ten candidate intervals, including a pronounced transient whose peak STA/LTA ratio was comparable in scale to those observed in the earthquake recordings. This finding demonstrates the need for event validation beyond a simple energy-ratio threshold.

The project provides a foundation for systematic investigation of seismic event detection. Its principal next step is not merely to increase the number of triggers or tune thresholds, but to establish reliable event labels, expand the evaluation dataset, and measure performance using independent recordings.

**The current results are preliminary and demonstrate a functioning experimental pipeline, not a validated earthquake-detection system.**

---

## Author

**Spraha Vats**
Btech, Civil engineering, IIT Delhi
Independent Research Project — SeismoSignal-Detection

Interests: Seismic signal processing, scientific computing, data-driven event detection, and the application of computational methods to civil and geophysical engineering problems.

**Repository:** [github.com/sprahavats/SeismoSignal-Detection](https://github.com/sprahavats/SeismoSignal-Detection)
