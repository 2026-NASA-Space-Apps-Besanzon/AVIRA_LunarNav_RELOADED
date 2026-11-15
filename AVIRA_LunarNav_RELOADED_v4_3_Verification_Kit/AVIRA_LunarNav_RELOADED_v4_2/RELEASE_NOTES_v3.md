# AVIRA LunarNav RELOADED — Professional v3

## Mission
Turn NASA/JPL lunar-surface Sun/Earth ephemerides into a reproducible comparison of selected sites and date offsets. Provide explicit engineering screens, 3D animated directions and honest data-provenance labels.

## Version 3 changes (relative to v2)
- Separate optional horizon CSV file and provenance for **each** lunar site. No longer silently applies Site A horizon profile to Site B.
- Rise/set **sample bracket** messages, longest solar and direct-Earth windows, longest blackouts. Do not interpret sample intervals as exact event timestamps.
- Horizontal solar-array geometric incident-light proxy [0,1] without claiming electric power output.
- Constraint-first recommendations: candidates failing any mandatory requirement are not recommended merely for high joint visibility.
- Manual date-offset explorer for candidate A (extra Horizons API calls occur only on button click; caching enabled).
- Downloadable NASA/synthetic provenance JSON manifest: source, dates, coordinates, assumptions, masks, limitations.
- 11 new automated decision tests; total 29 passing in release environment.

## Verification level
- Unit-test suite: **29 passed**, Python modules compile.
- Full Streamlit UI: **not run in this build environment** because Streamlit is unavailable.
- NASA API integration: client implemented and tested with mocked Horizons data; actual connection could not be exercised from this offline environment.
- Actual LOLA terrain data: not embedded. Procedural 3D relief is illustrative only. Optional separately uploaded site horizon masks can represent LOLA-derived terrain if their origin is documented and validated.
- No claim of flight qualification, real electrical power analysis, RF link-budget analysis or mission safety certification.

## Quality target
9.5/10 is an aspiration for hackathon execution, **not an independently measured score or NASA evaluation**. Key remaining acceptance gates: live Horizons acquisition; independent datum/frame verification; reproducible screen capture; actual LOLA masks if feasible; public repository and NASA submission.
