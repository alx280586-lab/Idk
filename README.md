# Weather Radar Visualization Tool

An interactive web application that displays live radar products and National Weather Service (NWS) warnings on top of a Leaflet map. The stack consists of a Node.js/Express backend for data aggregation and a React/Vite frontend for visualization.

## Features

- Toggleable radar layers: reflectivity, velocity, correlation coefficient, and echo tops.
- Animated time slider for radar loops with play/pause controls.
- Real-time warning list with clickable entries that fly the map to the affected polygon.
- Color-coded polygons for tornado, severe thunderstorm, flash flood, and other warnings.
- Legends and “last updated” timestamps for each radar product.
- Mobile-friendly layout with semitransparent overlays.

## Project Structure

```
.
├── client/        # React + Vite front-end (Leaflet map)
├── server/        # Express backend that proxies NWS data
├── package.json   # Root scripts for installing/running both apps
└── README.md
```

## Getting Started

1. **Install dependencies**

   ```bash
   npm install
   ```

   This runs the server and client installs (`npm install` inside each folder).

2. **Configure environment variables**

   ```bash
   cp server/.env.example server/.env
   ```

   - Adjust the radar product layer names or tile service URLs if you host your own radar imagery.
   - `CLIENT_ORIGIN` should match your frontend URL (defaults to `http://localhost:5173`).

3. **Run the development servers**

   ```bash
   npm run dev
   ```

   - Express backend: `http://localhost:4000`
   - Vite frontend: `http://localhost:5173`

4. **Build for production**

   ```bash
   npm run build
   ```

   - Deploy `client/dist` to a static host or CDN.
   - Deploy the Express server (container, VM, serverless) and set environment variables to point at your production origins and data feeds.

## Data Sources & Configuration

- **Radar products**: Defaults point to NOAA’s `opengeo.ncep.noaa.gov` WMS services. Swap `RADAR_TILE_BASE_URL` and `RADAR_PRODUCT_*` env vars to match other services (e.g., MRMS, IDP).
- **Warnings**: The server requests GeoJSON from `https://api.weather.gov/alerts/active`. You can replace `NWS_WARNINGS_URL` with other feeds that return GeoJSON polygons.
- **Caching/Tiling**: The backend exposes a skeleton for building time-based WMS requests. For production, consider pre-processing Level II/III data into tiled layers or using a commercial tiling service for performance.

## Deployment Notes

- Use HTTPS in production and configure CORS via `CLIENT_ORIGIN`.
- Add request throttling, caching, and retries on the backend for resilience against upstream outages.
- Integrate with a queuing or job system if you plan to decode Level II radar volumes and render custom tiles.
- Monitor the NWS API usage guidelines and rate limits (https://weather-gov.github.io/api/) before going live.

## Testing

- Unit tests and integration tests can be added under `server/` and `client/` respectively. For now, run the dev server and verify interactive behavior manually.
