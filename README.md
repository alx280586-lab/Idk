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

## Development Tasks

- Implement production-grade NEXRAD Level II decoders
- Integrate real-time lightning, storm tracks, and polygon warning feeds
- Expand WebGL shaders for volumetric slicing and dynamic 3D tilts
- Add automated tests for smoothing kernels and detection algorithms
