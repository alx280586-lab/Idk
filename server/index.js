/**
 * Weather Radar Visualization Backend
 * ------------------------------------
 * Setup:
 *   1. From the repo root run `npm install` to install both server and
 *      client dependencies. Duplicate `server/.env.example` into
 *      `server/.env` and tweak endpoints if needed.
 *   2. Start development servers via `npm run dev`. Express will run on
 *      `http://localhost:4000` by default and proxy data to the client.
 * Configuration:
 *   - RADAR_TILE_BASE_URL, RADAR_PRODUCT_* env vars point to NOAA/NWS
 *     services. Swap these out for commercial feeds or your own tile
 *     server if required.
 *   - NWS_WARNINGS_URL defaults to the public Weather.gov alerts API.
 * Deployment:
 *   - Build the frontend `npm run build` and host the generated
 *     `client/dist` folder via a static host or CDN.
 *   - Deploy this Express server (e.g., container, serverless) and set
 *     `CLIENT_ORIGIN` to your production domain so CORS is configured.
 */

import express from 'express';
import cors from 'cors';

import { CLIENT_ORIGIN, PORT } from './config.js';
import radarRouter from './routes/radarRoutes.js';
import warningsRouter from './routes/warningsRoutes.js';

const app = express();

app.use(cors({ origin: CLIENT_ORIGIN, credentials: false }));
app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.use('/api/radar', radarRouter);
app.use('/api/warnings', warningsRouter);

app.use((err, _req, res, _next) => {
  console.error('Unhandled server error:', err);
  res.status(500).json({ message: 'Internal server error', details: err.message });
});

app.listen(PORT, () => {
  console.log(`Weather radar backend listening on port ${PORT}`);
});
