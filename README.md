
# AVIRA LunarNav RELOADED — Lunar Landing Site Navigator

**NASA Space Apps Challenge 2026 | Besançon, France | 14–15 November 2026**

- **Challenge:** Lunar Landing Site Navigator
- **NASA Space Apps team:** https://www.spaceappschallenge.org/2026/find-a-team/avira_lunarnav_reloaded/
- **Local event:** Besançon, France (virtual participation from India)
- **Repository:** https://github.com/2026-NASA-Space-Apps-Besanzon/AVIRA_LunarNav_RELOADED
- **Project status:** Working Python/Streamlit research and educational prototype; not flight-qualified.

## Team Members

| Name | GitHub |
|---|---|
| Rahul Ashokrao Dhapatkar | [@raddy23](https://github.com/raddy23) |

## The Problem

Near the Moon's south pole, low Sun angles, lunar terrain and changing Earth visibility make it difficult to identify suitable landing sites and mission dates.

For example, a planned lunar landing may be delayed by several days. The originally selected site may then encounter different illumination or communication conditions. Engineers need to understand which mission constraints are violated and whether alternative dates or locations perform better.

## Our Solution

**AVIRA LunarNav RELOADED** is an interactive, explainable lunar mission-window screening prototype.

Our approach is:

**INPUT → DETECT → EXPLAIN → RECOVER → VERIFY**

1. **Input:** Select candidate lunar sites, UTC mission date, schedule changes and engineering thresholds.
2. **Detect:** Analyze sampled Sun/Earth geometry, sunlight availability, Earth-visibility windows, communication blackouts and illustrative battery reserve.
3. **Explain:** Identify constraint failures and present transparent PASS, FAIL or UNKNOWN screening outcomes.
4. **Recover:** Compare candidate landing sites or alternative mission dates.
5. **Verify:** Display assumptions, scientific limitations, data provenance and repeatable test evidence.

### Implemented Features

- Interactive Python/Streamlit dashboard
- NASA/JPL Horizons API integration for Sun and Earth observer ephemerides
- Offline synthetic demonstration mode
- Two-site and date-shift comparisons
- Sun/Earth elevation and visibility graphs
- Communication-window and blackout analysis
- Illustrative solar-energy and battery-reserve models
- Engineering constraint analysis and sensitivity testing
- Fault-injection scenarios
- Interactive procedural 3D lunar observation-geometry visualization
- CSV and reproducibility/provenance export features
- Optional exploratory machine-learning outlier analysis
- Automated Python tests

## Prototype Results

The working application was tested on Windows using Python 3.12.

**Automated testing:** 49 tests passed, 0 failed, 2 deprecation warnings.

### Example Scenario Comparison

Evaluation period: **15–20 November 2026 (120 hours)**.

| Metric | Candidate A | Candidate B |
|---|---:|---:|
| Coordinates | 89.5°S, 0°E | 89.5°S, 90°E |
| Sun geometric visibility | 120 h | 120 h |
| Earth geometric visibility | 62 h | 54 h |
| Joint Sun/Earth visibility | 62 h | 54 h |
| Joint visibility percentage | 51.67% | 45.00% |
| Longest Earth blackout | 58 h | 66 h |
| Illustrative minimum battery reserve | 0% | 0% |
| Overall result | CONSTRAINTS NOT MET | CONSTRAINTS NOT MET |

**Result interpretation:** Candidate A has eight more hours of sampled joint visibility than Candidate B under the displayed configuration. However, neither candidate meets the configured communication-blackout and battery-reserve constraints.

The prototype therefore explains the failures instead of incorrectly declaring either location safe.

**Scientific qualification:** These are observed application outputs. The live-mode response has not yet been independently cross-validated against saved raw NASA/JPL Horizons data. This is not a certified lunar landing-site recommendation.

## Existing Solutions and Our Differentiation

NASA/JPL Horizons, NASA Moon Trek and LROC QuickMap already provide important lunar ephemeris, mapping and visualization capabilities.

Our intended contribution is to connect lunar geometry with **explainable engineering decisions, mission-delay analysis, constraint failures, alternative scenario exploration and evidence-aware validation**.

Our differentiating workflow is:

**Detect a failure → Explain its cause → Explore alternatives → Verify the evidence.**

We do not claim that lunar ephemerides, terrain mapping or site ranking are new technologies. Superiority over existing professional tools has not been independently benchmarked.

## NASA Data and Resources Used

1. **NASA/JPL Horizons:** https://ssd.jpl.nasa.gov/horizons/
   - API documentation: https://ssd-api.jpl.nasa.gov/doc/horizons.html
   - The prototype's live mode requests Sun and Earth observer ephemerides for candidate lunar locations.

2. **NASA Moon Trek:** https://trek.nasa.gov/moon/
   - Lunar exploration and terrain reference.

3. **LROC QuickMap:** https://quickmap.lroc.asu.edu/
   - Lunar mapping and imagery reference.

4. **NASA Lunar Reconnaissance Orbiter / LOLA:** https://lola.gsfc.nasa.gov/
   - Reference for future real-terrain/horizon integration.

**Data validation status:** The application displays a JPL Horizons live-data mode. Independent preservation and verification of raw Horizons results are still pending. The procedural 3D landscape is not a NASA LOLA terrain model.

## Use of AI / SI Tools (Required Disclosure)

OpenAI ChatGPT assisted with software architecture, Python implementation, unit-test development, documentation, analysis, troubleshooting and presentation preparation.

AI image-generation tools were used to create conceptual lunar imagery and landing animations for the presentation. These are labeled as **AI-generated conceptual visualizations**, not NASA photography, real lunar terrain or validated landing simulations.

The optional scikit-learn Isolation Forest performs exploratory numerical outlier detection; it is not a mission-safety prediction model.

The project remains an independent team prototype, and AI-assisted results require human review and scientific validation.

## Deliverables

- **Source code:** https://github.com/2026-NASA-Space-Apps-Besanzon/AVIRA_LunarNav_RELOADED
- **Project demonstration (7 slides):** TO BE ADDED — upload the final presentation and insert its public URL.
- **Application:** Python/Streamlit prototype, tested locally on Windows.
- **Screenshots and 3D visualization:** Upload to the `images/` or `docs/` directory.
- **Source and results evidence:** Upload test evidence, sample exports and validated NASA data provenance when available.

The local URL `http://localhost:8501` is not publicly accessible and must not be submitted as a public demo URL.

## How to Run

### Requirements

- Python 3.12 (64-bit)
- Windows, Linux or another supported development environment
- Internet connection for live NASA/JPL Horizons requests
- Project Python source files and `requirements.txt`

### Install dependencies

```powershell
py -3.12 -m venv C:\nasaenv
C:\nasaenv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
```

### Run tests

```powershell
C:\nasaenv\Scripts\python.exe -m pytest -q
```

Observed Windows test result:

```text
49 passed, 2 warnings
```

### Launch the application

```powershell
C:\nasaenv\Scripts\python.exe -m streamlit run app.py
```

Open `http://localhost:8501`.

**Windows note:** On one Windows environment, Application Control blocked a PyArrow DLL. A modified no-PyArrow version of the application was used to display result tables successfully. If necessary, run the corrected version once it is uploaded alongside the source:

```powershell
C:\nasaenv\Scripts\python.exe -m streamlit run AVIRA_LunarNav_RELOADED_app_no_pyarrow.py
```

Do not disable Windows security controls.

## Scientific Limitations

- This is an early-stage decision-support and educational prototype, **not a flight-qualified landing-safety system**.
- Real terrain blocking requires validated site-specific lunar terrain and horizon data.
- Sun elevation does not by itself establish electrical power production.
- Direct-to-Earth geometric visibility does not prove RF link performance.
- Battery reserves are based on simplified engineering assumptions.
- Sampled event times have limited time resolution.
- Synthetic example data must not be represented as verified NASA measurements.
- An overall screening failure must not be overridden by a higher relative score.

## Sources and Credits

- NASA/JPL Horizons: https://ssd.jpl.nasa.gov/horizons/
- NASA Moon Trek: https://trek.nasa.gov/moon/
- LROC QuickMap: https://quickmap.lroc.asu.edu/
- NASA LOLA: https://lola.gsfc.nasa.gov/
- Python: https://www.python.org/
- Streamlit: https://streamlit.io/
- Plotly: https://plotly.com/python/
- pandas: https://pandas.pydata.org/
- NumPy: https://numpy.org/
- scikit-learn: https://scikit-learn.org/
- pytest: https://docs.pytest.org/
- OpenAI ChatGPT and AI image-generation tools (disclosed above)

---

## Final Submission Checklist

- [x] Project description prepared in English
- [x] Team details completed
- [x] AI/SI usage disclosed
- [x] Working application demonstrated in browser
- [x] 49 automated tests passed
- [ ] Upload the complete Python source, tests and assets to this repository
- [ ] Upload final seven-slide presentation and add public demo link
- [ ] Verify public links without GitHub login
- [ ] Submit the official NASA Space Apps Project Page
- [ ] Confirm the "Submit for Judging" success message

**Deadline:** Sunday, 15 November 2026, 23:59 CET (Paris time).

**Team:** AVIRA_LunarNav_RELOADED  
**Participant:** Rahul Ashokrao Dhapatkar  
**Local event:** Besançon, France (virtual participation from India)
