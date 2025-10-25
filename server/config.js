/**
 * Setup & Deployment Notes
 * -------------------------
 * 1. Copy `.env.example` to `.env` and update the placeholders with
 *    any required API keys or custom endpoints. NWS products are
 *    available without authentication, but commercial providers may
 *    require keys.
 * 2. Local development: `cd ..` (project root) and run `npm install`,
 *    then `npm run dev` to start the backend (Express) and frontend
 *    (Vite) together. The server listens on the PORT defined below.
 * 3. Production: build the frontend with `npm run build`, host the
 *    static assets (e.g., in S3 or a CDN), and deploy this Express
 *    service to your infrastructure. Update `CLIENT_ORIGIN` to match
 *    the production domain so CORS remains permissive.
 * 4. Radar tiles: If you host processed tiles yourself, point the
 *    `RADAR_TILE_BASE_URL` and related env vars to your tile service.
 *    Otherwise, configure the provided NOAA / NWS endpoints.
 */

import 'dotenv/config';

export const PORT = process.env.PORT ?? 4000;
export const CLIENT_ORIGIN = process.env.CLIENT_ORIGIN ?? 'http://localhost:5173';
export const RADAR_TILE_BASE_URL =
  process.env.RADAR_TILE_BASE_URL ?? 'https://opengeo.ncep.noaa.gov/geoserver/conus/{product}/wms';
export const RADAR_PRODUCTS = {
  reflectivity: process.env.RADAR_PRODUCT_REFLECTIVITY ?? 'conus_bref_qcd',
  velocity: process.env.RADAR_PRODUCT_VELOCITY ?? 'conus_vel_max',
  correlationCoefficient: process.env.RADAR_PRODUCT_CC ?? 'conus_cc',
  echoTops: process.env.RADAR_PRODUCT_ECHOTOPS ?? 'conus_etop35'
};
export const WARNINGS_URL =
  process.env.NWS_WARNINGS_URL ?? 'https://api.weather.gov/alerts/active?status=actual&message_type=alert';
export const WARNINGS_UPDATE_INTERVAL_MS = Number(
  process.env.WARNINGS_UPDATE_INTERVAL_MS ?? 60_000
);
export const RADAR_FRAME_COUNT = Number(process.env.RADAR_FRAME_COUNT ?? 12);
export const RADAR_FRAME_INTERVAL_MINUTES = Number(
  process.env.RADAR_FRAME_INTERVAL_MINUTES ?? 5
);
