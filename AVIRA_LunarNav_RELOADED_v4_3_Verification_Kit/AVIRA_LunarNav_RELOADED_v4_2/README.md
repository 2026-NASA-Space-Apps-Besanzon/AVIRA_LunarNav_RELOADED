# AVIRA LunarNav RELOADED

**NASA Space Apps Challenge 2026 — Lunar Landing Site Navigator**  
Independent science/engineering prototype. Not NASA-endorsed or flight-qualified.

## Features
- Retrieves **actual Sun and Earth observer ephemerides** at lunar coordinates from the **NASA/JPL Horizons API** when the machine has internet access.
- Compares two candidate sites or dates, including ±14-day launch/landing schedule shifts.
- Interactive **3D lunar observation geometry** showing Sun/Earth directions. Terrain is **procedural illustration**, not NASA LOLA elevation.
- Elevation charts, sampled sunlight, Earth visibility, simultaneous visibility, window tables, CSV export.
- **Mission Decision Lab**: configurable constraints, sampled max blackout duration, transparent rule-based explanations and scenario ranking.
- **Best/nominal/worst stress analysis**: adjust horizon clearance margins; explicitly labeled user-defined sensitivity, NOT NASA uncertainty.
- **Fault injection**: model an 8-hour hypothetical communication interruption for embedded/mission resilience analysis.
- **Terrain-aware option**: upload an azimuth-indexed horizon CSV derived from NASA LOLA DEM; app then checks Sun and Earth against local horizon elevations.
- Optional exploratory Isolation Forest ML outlier detection; deliberately not a safety model.
- **Clearly labeled synthetic offline demonstration mode**; never claim its data are NASA observations.

## Launch on Windows
1. Install [Python 3.11 or 3.12](https://www.python.org/downloads/) and select **Add python.exe to PATH**.
2. Extract this ZIP, then double-click `START_WINDOWS.bat`.
3. Open the Streamlit local URL, usually `http://localhost:8501`.
4. Select **NASA JPL Horizons (LIVE)** if internet is available. The first query can take time.

Alternatively:
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m pytest -q
```

## Modes and provenance

**LIVE** sends observer queries to `https://ssd.jpl.nasa.gov/api/horizons.api`, with center `coord@301`, `SITE_COORD` (east longitude, latitude, height km), Sun target `10`, Earth target `399`, azimuth/elevation quantity `4`, airless horizon. A data-source banner is visible. Results are available only if NASA responds successfully.

**SYNTHETIC DEMO** produces mathematically constructed examples. The app visibly labels them as synthetic and exports synthetic-labelled CSV. **Never cite those values as real scientific results.**

For validation, export two live scenarios and compare sample rows directly against the Horizons web interface using identical inputs. Some Horizons output settings can vary; if the parser rejects a response, do not substitute synthetic mode as authentic data.

## Scientific limitations

By default horizon checks use the local geometric tangent plane, **not lunar terrain**. For terrain-aware screening, upload a verified azimuth-indexed horizon CSV extracted from lunar topography. The app does NOT include a pre-downloaded NASA DEM and does not automatically verify its provenance. Real crater walls may block the Sun or Earth even with a positive elevation. The 3D terrain illustration is synthesized; it is NOT a LOLA DEM. Solar exposure does not equate to electric power. Link geometry does not establish RF link budget. Sampled intervals are discrete (uncertainty ~one step). This is a non-flight-qualified screening and educational tool, not a certified mission planner.

## Terrain mask input (advanced)

The **Surface & fault-tolerance lab** accepts a CSV with columns:

```csv
azimuth_deg,elevation_deg
0,2.0
30,3.0
60,5.0
90,4.0
120,1.0
150,2.0
180,1.0
210,1.0
240,2.0
270,3.0
300,2.0
330,2.0
```

The values above are **fabricated format examples** and are NOT NASA measured terrain. A real mask must come from one of the applicable NASA LOLA terrain elevation models, with site coordinates and projection verified independently. Azimuth 0° is local north; 90° east. Missing/invalid profiles fail closed. The `terrain.py` module provides an optional `derive_horizon_dem` helper for meter-projected LOLA GeoTIFFs if `rasterio` is installed; you must supply correctly transformed projected x/y site coordinates and inspect the DEM's scale/datum. The derivation is a limited-distance approximation, NOT a fully validated geodetic terrain solver.

## Engineering test plan

Run `python -m pytest -q`. Automated tests cover:

- **Best case**: uninterrupted solar and Earth visibility.
- **Worst case**: complete loss of solar illumination and Earth contact.
- **Mixed case**: partial blackout violating a maximum outage constraint.
- **Terrain case**: obstructed Sun but unobstructed Earth due to different azimuths.
- **Sensitivity case**: more conservative clearance never improves measured joint visibility.
- **Fault case**: 8-hour injected communications outage lowers windows appropriately.
- **Data faults**: missing/duplicated timestamps, nonfinite angles, negative thresholds and bad terrain CSV are rejected.
- **NASA interface**: mocked Horizons CSV checks parser, request parameters and incomplete response handling.

### Remaining scientific milestones
Obtain and ingest verified NASA LOLA south-pole topographic tiles; confirm map-to-body frame conventions; compare live NASA Horizons rows with independent official outputs; implement event-edge interpolation/adaptive sampling; add independent RF link budget and solar panel orientation models; perform end-to-end web UI testing and actual local operation. This software is **not flight-qualified**.

## Official data sources
- NASA JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- NASA/JPL Horizons system: https://ssd.jpl.nasa.gov/horizons/
- NASA LRO/LOLA south-pole elevation: https://pgda.gsfc.nasa.gov/products/90
- LROC QuickMap: https://quickmap.lroc.asu.edu/
- NASA Moon Trek: https://trek.nasa.gov/moon/

## AI/ML disclosure (edit to match your actual use)
Coding and design assistance from OpenAI ChatGPT (AI) was used to accelerate software implementation, documentation, test drafting and interface prototyping; the competition team must confirm original authorship and compliance with the organizers’ SI guidance. Optional scikit-learn Isolation Forest is used only for **exploratory** numerical outlier detection, not mission risk certification. User/team must independently validate code and sources and disclose SI usage on the submission page. The 3D illustration uses Plotly-generated mathematical geometry rather than AI image synthesis. No NASA logos are included.

## License and collaboration
Code supplied as a prototype for the team to review, test and adapt. External packages retain their own licenses. Verify the applicable NASA competition rules before submitting, especially originality and SI disclosures.

---
## v3 upgrades & judging demonstration

See [RELEASE_NOTES_v3.md](RELEASE_NOTES_v3.md) and [SUBMISSION_CONTENT.md](SUBMISSION_CONTENT.md).

### Suggested 90-second technical walkthrough (for private/local presentation)
1. Set **NASA JPL Horizons (LIVE)** and two southern-pole sites; check console output and data-source notice.
2. Compare sunlight, Earth visibility, joint windows, longest Earth blackout and transparent constraint checks.
3. Show the animated 3D Sun/Earth arrows; explain that relief is illustrative, not LOLA terrain.
4. In the mission-delay explorer, compare three date offsets and explain why one passes/fails engineering limits.
5. Inject an eight-hour radio-availability fault to demonstrate resilient screening.
6. Export the reproducibility manifest and show UTC coordinates, NASA data source and horizon model.

### How to run automated tests
```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

### Data-source and safety note
Do not submit synthetic demonstration numbers as observations. Genuine NASA JPL data is fetched **only after successful access** in LIVE mode. No actual LOLA GeoTIFF is bundled, and independently sourced site-specific horizon masks must include citation and coordinate/datum verification. Anomalies from optional Isolation Forest are numerical outliers, not proven real-world mission hazards.

## v4 tested release — POWER & EVIDENCE GATES

**Open `OFFLINE_SYNTHETIC_3D_PREVIEW.html` directly in a browser** to view the standalone animated 3D diagram and interactive charts, without Python, Streamlit, or network access. **ALL preview numbers are SYNTHETIC**, generated using mathematical demonstration signals, and must not be included as real NASA observations.

In the main Python app (`START_WINDOWS.bat`), v4 also includes a horizontal solar-array and battery energy balance. Configurable engineering inputs: array area, load, battery capacity, initial state-of-charge, and minimum reserve. Panel efficiency, solar flux, charge and discharge efficiencies are declared assumptions. Inputs are not validated flight hardware values; the resulting energy output is a what-if study, *not* a lander thermal/power subsystem analysis. Battery-unsafe scenarios cannot win the local recommendation screening. A synthetic scenario never becomes an official scientific PASS.

**Release validation performed inside build environment:** 45 automated Python unit tests passed, Python source compiled, and an offline interactive Plotly HTML preview was generated. Actual Streamlit server launch and NASA Horizons live ephemeris verification have **NOT** passed end-to-end in this environment (Streamlit module and NASA network access unavailable). Install the dependencies and validate on the target Windows machine. A PNG screenshot/recording from running the app is still required for judging evidence.

### End-to-end acceptance checklist on Windows
1. Run `python -m pytest -q` and confirm all tests pass.
2. Double-click `START_WINDOWS.bat` and verify the Streamlit dashboard appears.
3. Select `SYNTHETIC DEMO (OFFLINE)`, move date, site and constraints and check that metrics/3D/chart update. Check for the **DEMO ONLY** data gate.
4. Enter zero sunlight/high load and verify battery reserve breach and no false safe recommendation.
5. Switch to `NASA JPL Horizons (LIVE)` and query two sites; if the request fails, capture the error rather than substituting synthetic values.
6. In live mode, compare at least three sample rows with official Horizons outputs using identical `CENTER`, `SITE_COORD`, UTC dates and `QUANTITIES`.
7. If using LOLA-derived terrain masks, verify each site's azimuth grid, datum, elevation units, coverage and source citation.
8. Export the manifest/CSV, confirm provenance, capture a screen recording and test the public links in an incognito browser.

**Submission note:** The official NASA project guide states the judged demo must be **30 seconds or less** for video or **no more than seven slides**. A separate longer video can be used as a supplementary technical walkthrough if linked as such and allowed by the platform.

## v4.1 — capture actual NASA data for submission evidence

Run `GET_NASA_DATA_WINDOWS.bat` on an internet-connected computer or run
`python CAPTURE_NASA_DATA.py --date 2026-11-15 --days 2 --step-hours 2`.
This queries two candidate lunar sites, Sun and Earth, and saves original Horizons
response text, request URLs/parameters, CSV outputs, interactive graphical HTML
charts and a `NASA_DATA_MANIFEST.json`. **The command fails without silently
substituting synthetic values if NASA is inaccessible or its output is unparseable.**
The chart uses a **geometric 0° horizon**, not LOLA terrain. All site coordinates
are demonstration *candidate* coordinates, not asserted actual landing sites.
The actual 3D Streamlit dashboard can be run separately using `START_WINDOWS.bat`
and selecting `NASA JPL Horizons (LIVE)`.

An authentic NASA-data submission claim is supported only after this command
succeeds and its saved responses are inspected. If it fails, the offline preview
remains SYNTHETIC and must not be described as NASA-derived.
