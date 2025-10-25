/**
 * Frontend Setup Instructions
 * ---------------------------
 * 1. Install dependencies from the project root via `npm install`.
 * 2. Run `npm run dev` to start the Vite dev server with hot reload and
 *    the Express backend proxy.
 * 3. Configure backend endpoints (e.g., `RADAR_TILE_BASE_URL`) in
 *    `server/.env`. The frontend consumes `/api/*` routes exposed by the
 *    backend, so no direct API keys are required here.
 * 4. Production build: `npm run build` and host the generated
 *    `client/dist` folder with any static host. Update backend CORS to
 *    allow the production origin.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App.jsx';
import './styles/app.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
