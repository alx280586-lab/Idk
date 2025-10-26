# Synthetic WebGL Radar Simulator

The Synthetic WebGL Radar Simulator is a browser-only atmospheric laboratory that reproduces the look and behavior of professional NEXRAD products. It ships as a self-contained HTML/JavaScript experience that renders a 24-hour synthetic meteorological day in roughly two and a half minutes of real time. From initialization through shutdown, every pixel on screen is generated locally in the browser using WebGL 2 and carefully tuned shader programs.

Upon loading the application, users are greeted with a stylized boot splash before being dropped into a map-centered console modeled after National Weather Service workstations. A static shaded basemap of the continental United States anchors the display while radar products, warning polygons, and diagnostic overlays animate above it. The interface stays lightweight: a compact top bar shows site information and simulated UTC time, a timeline ribbon enables scrubbing through the day, and a collapsible drawer offers granular control over physics, rendering, and analysis layers.

The simulation advances on an accelerated internal clock where one simulated minute equals one-tenth of a real second. A dedicated scheduler maintains synchronization between the 30 Hz physics loop and the 60 Hz renderer, interpolating between consecutive frames to ensure smooth visuals even when the user scrubs or changes playback speed. Users can pause, resume, fast-forward, or rewind via keyboard shortcuts or the UI controls, with shader parameters updating instantly to reflect any toggled option.

Synthetic storms form over a procedurally generated environment that evolves throughout the day. Beneath the radar textures lives a pair of temperature and dewpoint grids that govern convective potential. Diurnal heating, moisture advection, terrain influences, and coastal boundaries all contribute to when and where storms ignite. The system seeds discrete supercells along drylines, squall lines along fronts, tropical cyclones along the Gulf, and winter precipitation across colder sectors, crafting a meteorological narrative that feels both varied and plausible.

Each storm object carries metadata for intensity, rotation, hydrometeor composition, and lifecycle stage. Reflectivity derives from Gaussian kernels blended with procedural noise to create filamentary detail, while bounded weak echo regions, hook echoes, hail spikes, and bright bands appear naturally as storm parameters evolve. The engine maintains synchronized float textures for reflectivity, radial velocity, spectrum width, correlation coefficient, differential reflectivity, and specific differential phase, ensuring coherent behavior across all radar products.

Dual-polarization signatures play a central role in realism. ZDR arcs outline supercell inflow, CC minima reveal tornado debris signatures, and KDP spikes highlight extreme rainfall. Spectrum width blooms within turbulent cores, and velocity data honors Nyquist folding with optional dealiasing for advanced users. Multi-tilt compositing blends low, mid, and high scans so the user can inspect vertical storm structure, while beam geometry modeling introduces range broadening, attenuation, and earth-curvature overshoot.

Warning logic mirrors operational National Weather Service practices. GPU-accelerated feature extraction locates storm objects, evaluates gate-to-gate velocity differences, and estimates hail probability, rainfall accumulation, and debris confidence. A decision tree issues Tornado, Severe Thunderstorm, Flash Flood, Winter, Marine, and other warnings, escalating to PDS or Emergency levels when thresholds are met. Polygons animate with distinctive colors and border styles, respecting overlay blending so multiple alerts remain readable when stacked.

Interactivity extends beyond playback controls. Users can toggle storm tracks, gust fronts, and diagnostic vectors, view time-series charts of CAPE and shear, or open storm info cards that summarize lifecycle metrics. An AI analyst module running in a Web Worker produces periodic text briefings and discussions that translate raw data into meteorological storytelling. Educational annotations label features like hook echoes and rear-inflow notches, turning the simulator into a teaching aid for radar interpretation.

Rendering prioritizes both fidelity and performance. All radar layers reside in 16-bit float textures, color tables match official NEXRAD palettes, and fragment shaders apply gamma-corrected lookups with adjustable brightness and contrast. Range rings, azimuth lines, lightning flashes, and subtle noise animations lend authenticity without sacrificing frame rate. If performance dips, the engine can dynamically reduce internal resolution while preserving UI responsiveness.

The project architecture favors modularity for future extensions. ES modules divide responsibilities across atmospheric physics (`src/atmo.js`), radar synthesis (`src/radar.js`), rendering (`src/renderer.js`), warning intelligence (`src/alerts.js`), UI bindings (`src/ui.js`), analyst commentary (`src/analyst.js`), and shared color/texture utilities. `main.js` orchestrates initialization, event routing, and the master loop. Configuration defaults live in structured constants so researchers can tweak color tables, storm seeding rates, or warning thresholds without spelunking through unrelated code.

Running the simulator requires only opening `index.html` in a modern browser with WebGL 2 support. No external assets or network requests are needed; textures, palettes, and basemap data are embedded. Developers experimenting locally can serve the project via a static file server for convenience, but the experience remains entirely client-side. Keyboard shortcuts mirror professional radar tools—`R` for reflectivity, `V` for velocity, `C` for correlation coefficient, and so on—with Shift-modified keys enabling split-pane comparisons.

Quality assurance features include deterministic replay, logging of random seeds and configuration hashes, and a debug overlay that surfaces frame times, memory usage, and storm counts. A MediaRecorder-based capture tool exports still frames or animated clips with warnings burned in, making it straightforward to share simulated events or incorporate them into training materials. The logging console supports CSV export for post-event analysis of warning performance and storm statistics.

Accessibility and user comfort receive dedicated attention. Color-blind palettes, high-contrast text, scalable UI components, and optional atmospheric audio create an inclusive experience. The control drawer’s tabs let users declutter the display or dive deep into physics tweaks without disrupting rendering. Tooltips, legends, and inline help explain jargon so learners can climb the radar meteorology curve at their own pace.

Beyond its immediate visual appeal, the simulator offers a sandbox for experimentation. Instructors can disable diurnal heating to showcase nocturnal storm behavior, students can amplify false-alarm rates to study warning verification metrics, and enthusiasts can script custom atmospheric scenarios by adjusting configuration constants. Because everything runs locally, the simulator doubles as a reliable demonstration platform in classrooms, outreach events, or offline environments.

Future improvements could incorporate WebGPU backends, volumetric lighting, multi-radar mosaics, or real-time collaboration features. The current foundation is intentionally extensible: adding new radar products, analysis overlays, or hazard types primarily involves authoring additional shaders and decision logic while reusing existing UI patterns. Contributions are welcomed, and the modular design aims to make onboarding new developers straightforward.

Whether you are a meteorology student, severe weather enthusiast, or graphics engineer, the Synthetic WebGL Radar Simulator invites you to explore a richly detailed, scientifically grounded representation of convective weather. Pause a tornadic storm to inspect its debris signature, fast-forward a tropical cyclone’s landfall, or simply let the day unfold and observe the emergent choreography of atmosphere and radar. Everything you see is simulated in-browser, yet the experience aspires to capture the awe of watching real storms evolve across the American landscape.

## Launching the simulator locally

You now have two ways to run the simulator: open the bundled offline build directly from disk, or serve the ES module sources over HTTP for iterative development.

### Option A — Open the offline bundle

1. Download or clone the repository and ensure the `dist/offline-bundle.js` file sits next to `index.html`.
2. Double-click `index.html` (or drag it into a browser window). The inline bootstrapper detects the `file://` protocol and loads the offline bundle automatically.
3. If you see an “Offline bundle missing” warning, verify the `dist` directory shipped with the download. You can regenerate the bundle manually with `python3 scripts/build_offline_bundle.py` after pulling new changes.

### Option B — Serve over HTTP (recommended for development)

Modern browsers enforce CORS checks for module scripts loaded from the local file system, so the development workflow still benefits from a tiny static web server.

1. From the repository root, start a local server:
   - **Python 3:** `python3 -m http.server 8080`
   - **Node.js (using npx):** `npx serve .`
   - **Docker users:** `docker run --rm -it -v "$PWD":/srv -p 8080:8080 pierrezemb/gostatic`
2. Open your browser to the reported address, such as `http://localhost:8080/`.
3. When the boot splash appears, configure the simulated day length and optional fast-forwarding, then start the run.

If you need to host the simulator elsewhere, deploy the contents of this repository to any static hosting provider. No backend components are required. GitHub Pages works out of the box—the bootstrapper trusts any hostname ending in `github.io`, so publishing the repo to your `<user>.github.io` site will load the live ES module build without additional configuration.

### Rebuilding the offline bundle

Whenever you update files under `src/`, rerun `python3 scripts/build_offline_bundle.py` to refresh `dist/offline-bundle.js`. The script performs a lightweight transformation that converts the ES modules into a single browser-friendly script, ensuring the offline experience stays in sync with the source modules.

### Allowing custom hostnames

The frontend validates `window.location.hostname` against `INSIGHTS_WHITELIST` before loading the WebGL runtime. Common local development hosts—`localhost`, `127.0.0.1`, `0.0.0.0`, and `[::1]`—are permitted automatically, and `github.io` domains are accepted for GitHub Pages deployments. To run behind a different proxy or vanity domain, expose an allow list before the inline bootstrap script executes:

```html
<script>
  window.RADAR_ALLOWED_HOSTS = ["weatherlab.test", "staging.radar.local"];
  window.RADAR_ALLOWED_HOST_PATTERNS = [".internal.wx"];
</script>
```

Alternatively, add comma-separated `data-allowed-hosts` or `data-allowed-patterns` attributes to the `<script id="bootstrap-script">` tag in `index.html`.
