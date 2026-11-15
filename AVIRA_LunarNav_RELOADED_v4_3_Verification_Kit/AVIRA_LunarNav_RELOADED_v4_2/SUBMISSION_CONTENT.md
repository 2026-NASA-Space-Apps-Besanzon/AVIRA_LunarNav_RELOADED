# NASA Space Apps Challenge 2026 — Submission working draft

**Team:** AVIRA_LunarNav_RELOADED  
**Challenge:** Lunar Landing Site Navigator  
**Project:** AVIRA LunarNav RELOADED — Explainable Lunar Mission Window Explorer

## Project summary (edit after verifying live NASA results)
AVIRA LunarNav RELOADED is an interactive lunar landing-site scenario navigator. It is designed to make the relationships between lunar surface lighting, direct-to-Earth geometry and mission schedule changes understandable to scientists, mission engineers and educators. Users can compare two southern polar sites, choose dates, examine animated 3D observer geometry, explore sampled sunlight and Earth visibility, screen operational constraints, stress-test communication faults and investigate alternative dates. The application uses a NASA JPL Horizons API client for real ephemerides when available and includes explicitly labeled synthetic demonstration mode. Terrain-dependent horizons require independently verified site-specific masks. The prototype is an early-stage planning aid, not a safe-landing certification.

## Problem addressed
Lunar south-pole missions face severe sunlight and line-of-sight constraints. Existing science portals provide rich raw data, but rapid side-by-side mission screening and schedule resilience analysis can be difficult for non-specialists.

## Main technical idea
Constraint-first window analysis with a transparent rationale: discard candidates that violate specified minimum sunlight, Earth availability, joint visibility or maximum blackout constraints; then rank feasible candidates according to sampled joint visibility and blackout length. Demonstrate sensitivity to assumed terrain mask and landing delay.

## Technologies
Python, Streamlit, Plotly 3D animation, pandas, NumPy, requests; optional scikit-learn Isolation Forest numerical outlier exploration; pytest.

## NASA resources
- NASA JPL Horizons observer ephemerides: https://ssd.jpl.nasa.gov/horizons/
- NASA JPL Horizons API documentation: https://ssd-api.jpl.nasa.gov/doc/horizons.html
- LRO terrain references: https://quickmap.lroc.asu.edu/ and https://trek.nasa.gov/moon/

**Before claiming actual NASA data was used, run NASA LIVE mode and preserve a real ephemeris export and provenance manifest.** Do not cite synthetic mode as NASA dataset use. Only cite LOLA terrain if an actual NASA/LOLA-derived mask is supplied and its provenance can be verified.

## Use of Super Intelligence (SI) and AI disclosure
AI-assisted programming, architecture brainstorming, debugging, test creation and writing were used. Optional Isolation Forest highlights statistical outliers in observed angle samples; it is NOT a trained landing-safety, lunar anomaly or mission-success prediction model. Mission pass/fail explanations are reproducible deterministic rules, not an LLM verdict. No generated NASA logos or identifiers are used. Any later AI-generated visual assets need the required visible disclosures/watermarks.

## Limitations
Geometric or uploaded-mask horizon only; left-edge sample-weighted estimates, not guaranteed continuous windows. No full LOS ray-tracing to Earth, antenna link budget, radiation/thermal analyses, landing obstacle or slope hazards. Synthetic animation terrain is not measured NASA data.

## Suggested 7-slide (maximum) deck
1. Name, team, challenge and the mission planning problem.
2. Why lunar south-pole sunlight and Earth visibility matter.
3. Product interface: choose site, date and constraints.
4. Scientific method: NASA/JPL ephemerides, site-specific terrain masks, sampled windows.
5. Live 3D geometry and comparative charts — actual verified screenshots.
6. Mission date shift and failure scenario demonstration — actual measured numbers.
7. Impact, engineering limitations, sources and a credible roadmap.

## Final submission checklist
- [ ] Verify NASA event/team/project page is accessible.
- [ ] Run the project locally with NASA LIVE mode and capture source-backed outputs.
- [ ] Run `python -m pytest -q`; test Streamlit UI and plot animation.
- [ ] Provide publicly accessible GitHub final project and a demo video <=30 seconds OR a <=7-slide presentation.
- [ ] Give high-level summary, detailed description, sources, SI disclosures, NASA dataset references.
- [ ] Use English and comply with NASA content/media rules.
- [ ] Click Submit for Judging and verify confirmation (Save Progress alone is not submission).
