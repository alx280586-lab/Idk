# NextGen Radar Visualization Engine

An ultra-advanced interactive weather radar system inspired by [supercell-wx](https://github.com/dpaulat/supercell-wx). The engine ingests high quality NEXRAD Level II/III radar data, applies multi-scale Gaussian smoothing, and renders professional-grade visualizations with WebGL acceleration.

## Features

- **Data ingestion** for live HTTP streams and historical archives
- **Radar decoding** for reflectivity, velocity, correlation coefficient, spectrum width, ZDR, KDP, and more
- **Derived fields** including storm-relative motion, composite reflectivity, VIL, and hail probability
- **Advanced smoothing** with configurable multi-scale Gaussian convolution and adaptive blending
- **Storm analysis** covering mesocyclone detection, hook echo recognition, and hail core estimation
- **OpenGL/WebGL rendering** with customizable color tables, frame caching, and time-loop playback
- **Geospatial overlays** for states, counties, roads, rivers, and cities with CRS transformation
- **Professional UI** leveraging a templated dashboard featuring real-time warning banners and counters
- **FastAPI service** exposing live products, frame history, overlays, and texture streaming endpoints
- **Modular architecture** suitable for desktop or web deployment with an extensible API surface

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[development]
uvicorn nextgen_radar.server.api:create_app --reload
```

Open `http://127.0.0.1:8000` and serve the `templates/dashboard.html` with your preferred static file host or integrate with a modern frontend framework.

### Decoding Level-II radar with ToolsUI (Easy Mode)

NEXRAD Level-II archives use proprietary BZip2 blocks that cannot be decompressed with standard utilities. The easiest way to prepare data for this project is to use **Unidata's NetCDF-Java ToolsUI** application, which bundles the official Level-II decoder.

1. Download `toolsUI-<version>.jar` from the [NetCDF-Java release page](https://downloads.unidata.ucar.edu/netcdf-java/latest/).
2. Launch the converter directly from the command line:

   ```bash
   java -jar toolsUI-<version>.jar UI
   ```

3. In the ToolsUI window choose **Feature Types → Radar Level II to NetCDF**.
4. Select your raw Level-II (`*.gz` or `*.ar2v`) file as the input and choose an output location ending in `.nc`.
5. Press **Convert**. The resulting NetCDF file is immediately compatible with xarray and the rest of the NextGen Radar processing pipeline.

Tips:

- ToolsUI runs anywhere Java is available (Windows, macOS, Linux) and requires no additional Python setup.
- Store converted volumes in a directory referenced by `FileRadarSource` to enable historical playback.
- For batch conversions you can supply multiple files to the **Radar Level II to NetCDF** tool; ToolsUI queues them automatically.

### Integrating converted data

Once a Level-II file has been converted, copy it into a directory such as `data/decoded/`. Update your configuration to point a `FileRadarSource` at that directory. The built-in decoder will ingest the NetCDF payload and expose all supported tilts and derived products.

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
