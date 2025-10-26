# NextGen Radar Visualization Engine

An ultra-advanced interactive weather radar system inspired by [supercell-wx](https://github.com/dpaulat/supercell-wx). The engine ingests high quality NEXRAD Level II/III radar data, applies multi-scale Gaussian smoothing, and renders professional-grade visualizations with WebGL acceleration.

## Features

- **Automated Level-II ingestion** directly from NOAA's AWS bucket with zero manual decoding
- **Radar decoding** for reflectivity, velocity, correlation coefficient, spectrum width, ZDR, KDP, and more
- **Derived fields** including storm-relative motion, composite reflectivity, VIL, and hail probability
- **Advanced smoothing** with configurable multi-scale Gaussian convolution and adaptive blending
- **Storm analysis** covering mesocyclone detection, hook echo recognition, and hail core estimation
- **OpenGL/WebGL rendering** with customizable color tables, frame caching, and time-loop playback
- **Geospatial overlays** for states, counties, roads, rivers, and cities with CRS transformation
- **Professional UI** inspired by supercell-wx with pixel-perfect radar textures, looping controls, and live warning banners
- **FastAPI service** exposing live products, frame history, overlays, and texture streaming endpoints
- **Modular architecture** suitable for desktop or web deployment with an extensible API surface

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[development]
python scripts/run_nextgen.py --station KTLX
```

Open `http://127.0.0.1:8000` after the server starts. The API streams live textures to the dashboard located at `templates/dashboard.html`. "Serving" the HTML simply means opening that file through any lightweight static host (an editor's Live Server button or `python -m http.server` both work) so the browser can request frames, warnings, and overlays from the FastAPI app.

> **Note:** Installation pulls in [MetPy](https://unidata.github.io/MetPy/) and [Siphon](https://unidata.github.io/siphon/) so Level-II volumes stream in from AWS, decode in pure Python, and land in xarray without any extra tooling.

### Configure live ingest

The helper script uses Siphon to locate the latest Level-II scans and MetPy to decode them into xarray datasets automatically:

```bash
python scripts/run_nextgen.py --station KFDR --storage ./radar-cache --interval 60
```

- `--station` / `--stations` accepts one or more four-letter NEXRAD sites (e.g. `--station KTLX KFDR`) so you can watch multiple radars at once.
- `--storage` determines where Level-II files are cached (they're automatically decompressed and reused).
- `--interval` controls how often the AWS feed is polled for new volumes.
- `--archive-days` sets how far back in the archive to search when booting.

The ingest manager automatically converts each volume into reflectivity, velocity, dual-pol, and derived fields, then pushes pixel-perfect textures to the WebGL renderer.

### How the MetPy + Siphon ingest works

1. **Siphon** queries the NOAA AWS catalog for each configured station and picks the newest Level-II scan without requiring manual downloads.
2. **MetPy's `Level2File`** decodes the binary volume into reflectivity, velocity, dual-pol moments, and differential phase entirely in Python.
3. **xarray** wraps each decoded moment so the smoothing pipeline, derived product calculators, and renderer can work with labeled arrays instantly.

### Bring your own archives (optional)

Already have decoded NetCDF archives? Point a `FileRadarSource` at the directory and the decoder will ingest them alongside the live feed. Mixed workflows are supported so you can blend historical playback with the streaming radar tiles.

### Live NWS warnings and polygons

This project now queries the official [api.weather.gov](https://api.weather.gov) alerts feed to obtain live warning polygons.

- `GET /warnings` returns the active alert list, warning counts, and the highest-priority headline for the dashboard overlay. Use query parameters such as `zone=ILZ013`, `event=Tornado Warning`, or `point=41.87,-87.62` to filter results.
- `scripts/render_dashboard.py` fetches the same feed when generating a static dashboard preview so the bottom-right warning counter and top-left banner reflect real data whenever connectivity is available.

Each `StormWarning` includes the simplified warning code (`TOR`, `SVR`, `FFW`, etc.), severity, expiration time, and the polygon vertices (latitude/longitude pairs) suitable for GIS overlays.

## Development Tasks

- Implement production-grade NEXRAD Level II decoders
- Integrate real-time lightning, storm tracks, and polygon warning feeds
- Expand WebGL shaders for volumetric slicing and dynamic 3D tilts
- Add automated tests for smoothing kernels and detection algorithms
