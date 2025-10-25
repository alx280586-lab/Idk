# StormFront: The Chase

This repository contains an advanced suite of Roblox scripts for the **StormFront: The Chase** experience—an ultra-realistic storm chasing sandbox driven by layered thermodynamics and physically reactive tornadoes. The scripts are structured as ModuleScripts that can be placed under a ServerScriptService container.

## Modules

- `AtmosphericModel.lua` – Generates a high-resolution domain of thermodynamic conditions (CAPE, CIN, helicity, theta-e gradients, storm motion) with outflow boundary detection for realistic mesoscale setups.
- `StormManager.lua` – Spawns storm cells along boundaries, evolves them through full life cycles, and promotes tornadogenesis using localized atmospheric samples.
- `StormCell.lua` – Encapsulates individual storm behavior, including mesocyclone intensity, hail, lightning, and tornado handoff logic.
- `TornadoSystem.lua` – Builds a multi-segment vortex that breathes, ropes out, and emits debris based on EF-scale pressure drops and tangential winds.
- `Instrumentation.lua` – Provides formatted chaser-style readouts and localized sampling helpers for UI or probe devices.
- `init.server.lua` – Example bootstrap script wiring the systems together with richer logging to trace the simulation.

Each module focuses on a specific aspect of the storm simulation pipeline so you can expand or replace pieces independently.
