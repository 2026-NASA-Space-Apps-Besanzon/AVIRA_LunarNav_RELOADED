# Real NASA ephemeris evidence — no synthetic fallback

On an internet-connected Windows computer, double-click `GET_NASA_LIVE_3D_WINDOWS.bat`.
It installs dependencies; requests Sun (`10`) and Earth (`399`) ephemerides from NASA/JPL Horizons for two lunar south-polar coordinate examples; captures raw responses and exact query URLs; computes sampled geometric horizon visibility; and generates `NASA_EVIDENCE/NASA_LIVE_3D_COMPARISON.html` with interactive 3D Sun/Earth directions and graphs.

The lander and flat grey horizon in the 3D display are **schematic graphics**, not an actual mission landing simulation or NASA LOLA topography. The scientific inputs driving 3D rays and charts come from JPL only if retrieval succeeds. Without a successful download there is deliberately **no live-result HTML output**.

## Scientific limitations

- Only local horizontal azimuth/elevation, for two illustrative coordinate sites, at 2-hour sampling. Very short events can be missed; sample fractions are approximate.
- No LOLA terrain horizon, solar panel pointing, thermal modeling, RF link budget, antenna mask, lander descent trajectory, dust, or flight qualification.
- Positive Earth elevation means geometric line of sight above a flat local horizon, not guaranteed RF communications.
- The generated HTML includes a schematic lander and planar horizon that must not be cited as NASA terrain.

## NASA form link

NASA/JPL Horizons System: https://ssd.jpl.nasa.gov/horizons/
NASA/JPL Horizons API: https://ssd-api.jpl.nasa.gov/doc/horizons.html

For the NASA Data form, cite only data successfully retrieved and used and preserve raw evidence and manifest for reproducibility.
