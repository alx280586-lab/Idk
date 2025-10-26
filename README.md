# Synthetic Radar Simulator

A playful yet meteorologically-inspired desktop simulator that renders an entire
day of synthetic radar data across the continental United States.  The
application is implemented with Python 3.10+, PyQt6, matplotlib, cartopy, NumPy
and SciPy and showcases classic radar signatures such as hook echoes, velocity
couplets, tornado debris signatures and more.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python radar_simulator.py
```

The simulator launches immediately and paints the CONUS map with the first radar
frame of the 24-hour cycle.

## Controls

* **Play/Pause** – animates the day using five-minute timesteps.
* **Skip ±1 hour** – jump forward/backward.
* **Time slider** – scrub through the 24-hour archive.
* **Product dropdown** – choose between reflectivity, velocity, dual-pol fields,
  spectrum width and composite reflectivity.
* **Brightness/Contrast** – fine tune any product.
* **Clutter filter / Dual-pol QC / Velocity dealiasing** – toggle simplified
  quality-control steps.
* **Hour spin box** – jump instantly to any UTC hour.
* **Active warnings list** – shows automatic warning polygons.
* Keyboard shortcuts: `Space` play/pause, `←` previous hour, `→` next hour.

The status bar displays the simulated UTC time, active storm count and number of
warnings.

## Radar science highlights

* **Beam broadening** – gaussian smoothing increases with range to mimic the
  radar beam widening and softening fine details.
* **Hook echoes & TVS** – supercells generate curved high-dBZ appendages and
  gate-to-gate velocity couplets.  Severe couplets inject a tornado debris
  signature by lowering correlation coefficient and boosting spectrum width.
* **Bow echoes** – fast moving lines with rear inflow notches and powerful
  outbound velocities.
* **Hail cores** – reflectivity exceeding 60 dBZ co-located with depressed ZDR,
  low CC and high KDP.
* **Outflow boundaries** – thin expanding rings that perturb reflectivity and
  velocity fields.
* **Dual-pol story** – warm rain increases ZDR and KDP, debris lowers CC,
  spectrum width climbs wherever turbulence abounds.
* **Warning engine** – heuristic detectors feed a rule engine that emits
  Tornado, PDS, Emergency, Severe Hail, Flash Flood, Damaging Wind and seasonal
  warnings.  Polygons are rendered directly on the map with descriptive labels.

## Configuration

All tunable parameters live in `config.yaml`, including the grid resolution,
thresholds for detectors, colours and default ranges for each radar product.
Feel free to tweak the YAML and relaunch the simulator – the world resets with a
fresh set of synthetic storms every run.

## Project structure

* `radar_simulator.py` – entry point
* `ui_main.py` – PyQt6 GUI and interaction logic
* `storm_generator.py` – synthesises storm evolution and radar fields
* `detectors.py` – feature detection heuristics (TVS, hail, flooding, etc.)
* `warnings.py` – rule engine that emits warning polygons and re-exports stdlib
  warning helpers
* `renderer.py` – matplotlib/cartopy rendering utilities
* `config.yaml` – simulator configuration
* `requirements.txt` – dependency list

Have fun exploring a fully synthetic day in the life of the U.S. severe weather
machine!
