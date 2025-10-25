# StormScope GR-2 Analyst Simulator

StormScope is a synthetic radar analysis environment inspired by GR2Analyst. The
application renders multi-tilt radar fields, derived products, and automatically
issues SPC-style severe weather alerts from simulated data.

## Features

- Real-time synthetic Level-II style radar volumes (reflectivity, velocity,
  dual-polarization variables, spectrum width)
- Derived products such as echo tops, VIL, normalized rotation, and hail size
  estimates
- Automatic storm detection with warning generation for severe thunderstorm,
  tornado, tornado emergency, and flash flood scenarios
- PyQt6 desktop interface with interactive product selection and time controls

## Running

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # coming soon; install PyQt6 and matplotlib manually if needed
python main.py
```

## Project Structure

```
stormscope/
  analysis/          # Storm detection and warning logic
  data/              # Synthetic radar generation and product derivations
  gui/               # PyQt6 widgets and windows
  simulation/        # Clock and simulation coordination
  visualization/     # Matplotlib canvases and view components
main.py              # Application entry point
```

The code is organized for extensibility. Modules expose clear APIs, making it
straightforward to plug in new radar products, add additional visualizations, or
integrate more sophisticated forecast logic.
