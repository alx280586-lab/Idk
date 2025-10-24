# SPC Forecaster Simulation

A browser-based meteorological forecasting game inspired by Storm Prediction Center operations. Each session generates a brand-new synoptic setup, simulated Skew-T sounding, hodograph, and verification storyline. The game is self-contained in static HTML/CSS/JS so it can be hosted directly on GitHub Pages.

## Features

- **Procedural atmospheric scenarios** with dynamic overview text and environmental metrics.
- **Interactive Skew-T and hodograph** rendered on canvas with regenerating sounding profiles.
- **Forecast desk** where you choose categorical risks, hazard probabilities, and craft SPC-style discussions.
- **Event simulation timeline** summarizing how convection evolves after your outlook.
- **Post-event recap** including long-form narrative, damage summary table, and detailed event deep-dive reports.
- **Verification scoring** that compares your forecast to the simulated outcome.

## Getting Started

1. Clone or download this repository.
2. Open `index.html` in any modern browser.
3. Click **Generate New Scenario** to receive fresh atmospheric data.
4. Analyze the sounding, hodograph, and environment metrics.
5. Issue your convective outlook and discussion.
6. Advance the simulation and study the recap to see how you performed.

No build tools or external dependencies are required.

## GitHub Pages

To host on GitHub Pages, enable Pages on your repository and point it to the `main` branch (or a `gh-pages` branch) with the root directory. The static assets will load the fully playable experience.

## License

Released into the public domain (CC0). Modify and extend freely.
