# AVIRA LunarNav RELOADED v2 — Engineering release notes

## Problem
Lunar south-pole landings encounter varying solar availability and direct-to-Earth geometry. Evaluating schedule and candidate changes manually makes it hard to compare power and communications screening trade-offs.

## Actual deliverables
1. Streamlit interactive site/date comparison with NASA/JPL Horizons client (online) and clearly synthetic demo mode.
2. Plotly interactive 3D Sun/Earth vectors, terrain illustration, and play/pause animation.
3. Mission Decision Lab: required sunlight, Earth visibility, simultaneous visibility, longest Earth blackout and four screening constraints.
4. Best/nominal/worst geometric horizon clearance sensitivity screening.
5. Hypothetical communications outage fault-injection scenario.
6. Optional azimuth-elevation terrain profile CSV, with shape/range validation and interpolation.
7. Optional Isolation Forest numerical outlier detection (exploratory only).
8. CSV export, source notes, setup scripts and automated scientific edge-case tests.

## Verified locally in build environment
- 18 unit tests passed (mocked NASA API response included).
- All Python modules passed syntax compilation.

## NOT verified here / not implemented
- No real NASA response downloaded/validated in this build environment.
- No end-to-end Streamlit browser test (Streamlit unavailable locally).
- No authentic NASA LOLA DEM bundled, no genuine NASA terrain shown in the 3D panel.
- No tested AI model for physical risk prediction, no true solar electrical generation model, no verified radio-link margin, no flight safety certification.
- Clearance stress range is user-selected, not a statistical confidence bound.
- Event times and percentage results are sampled, not sub-sample rise/set predictions.

## Baseline provenance
JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html
LOLA south-pole terrain: https://pgda.gsfc.nasa.gov/products/90
NASA/ASU lunar QuickMap: https://quickmap.lroc.asu.edu/

## NASA Space Apps SI statement
ChatGPT assisted source generation, code revisions, test design, and documentation. The approach must be understood, independently validated and disclosed by the team. Scientific computations and deterministic screening are not inherently AI/ML; the optional Isolation Forest module is an ML demonstration only.
