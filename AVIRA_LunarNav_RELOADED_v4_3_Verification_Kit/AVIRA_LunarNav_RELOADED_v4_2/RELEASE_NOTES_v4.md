# AVIRA LunarNav RELOADED v4 — November 14, 2026

## New
- Fixed-horizontal-array electrical production and sampled battery state-of-charge integration (declared assumptions).
- Minimum battery reserve screening for alternatives; battery-unsafe scenarios cannot be winners.
- Evidence quality gating: synthetic data results cannot be represented as scientific passes.
- Machine-readable per-scenario energy metrics, battery assumptions, and source-quality notes in provenance JSON.
- Offline standalone 3D interactive HTML technical preview with embedded Plotly JS. Clearly marked synthetic.
- Added 16 focused tests for battery/quality edge cases (45 tests total).

## Verified in this release
- `python -m pytest -q`: 45 passed
- `python -m compileall -q .`: passed
- `python make_offline_preview.py`: produced 3D HTML with embedded JS; preview's HTML file generated successfully.

## NOT YET VERIFIED
- Actual JPL Horizons connection and independent JPL output cross-check (network blocked in build environment).
- Streamlit launch and browser end-to-end operation (Streamlit unavailable in build environment).
- Actual NASA LOLA elevation in 3D; uploaded per-site terrain masks are an option but no official raster data is bundled.
- Mission-safe power/communications certification (model only estimates geometry and simplified assumptions).

## Primary objective
Convert the challenge's lunar lighting/communications constraints into explainable testable pass/fail/unknown-style engineering screening, including date shifts, blackouts and battery-survival scenarios, without misleading scientific claims.
