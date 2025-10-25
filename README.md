# Procedural Country Simulator

A replayable grand-strategy style simulation where you manage every aspect of a nation in a procedurally generated world. Guide your country's economy, politics, society, military, and diplomacy while AI-controlled nations pursue their own agendas.

## Features

- **Procedural world generation:** Each run builds a new world map with unique countries, climates, and resource distributions.
- **Interlocking systems:** Economic, political, military, diplomatic, and societal models influence each other, producing emergent gameplay.
- **Dynamic AI countries:** Computer-controlled nations react to global tension, ideology, and their own circumstances to craft alliances, wage wars, or reform.
- **Automation options:** Delegate economy, diplomacy, or military management to AI ministers for a high-level experience, or micromanage every decision.
- **Full world map:** Render the entire generated world as an ASCII map highlighting ownership and the player's territory.
- **Save/Load support:** Manual saves plus automatic yearly autosaves keep long campaigns secure.

## Requirements

The simulator targets Python 3.11+ and relies only on the standard library, making it easy to run in most environments.

## Getting Started

Create and activate a virtual environment (optional but recommended), then install any optional tooling you prefer. Run the game with:

```bash
python -m simulator.game
```

Useful command-line options:

- `--seed <int>`: Generate the world from a known seed for repeatable scenarios.
- `--countries <int>`: Number of countries (including the player) to spawn. Defaults to 6.
- `--load <filename>`: Load a saved game from the `saves/` directory instead of starting anew.

## Gameplay Overview

1. **Choose your country** from the list of generated nations.
2. **Review your situation** using the summary screen, and adjust tax rates or budget allocations.
3. **Navigate diplomacy** by managing relations, forging alliances, or imposing embargoes.
4. **Direct the military** through doctrine choices and offensive operations.
5. **Pass the year** to watch AI powers respond and global events unfold.

The ASCII map updates every turn, showing global control and highlighting your territory. Use automation toggles to let computer ministers handle subsystems while you focus on high-level strategy.

## Saving and Loading

Manual saves are stored under `saves/<filename>.json`. An autosave is created after every turn. To resume a campaign, run:

```bash
python -m simulator.game --load autosave.json
```

## Development Notes

- Game state is serialized to JSON for portability and easy inspection.
- Systems are split into modules under `simulator/` so new mechanics (e.g., climate change, espionage depth) can be added incrementally.
- The `WorldMap.render()` method renders a full global map using ASCII characters, ensuring the world layout is always visible.

Contributions, tweaks, and balance adjustments are welcome!
