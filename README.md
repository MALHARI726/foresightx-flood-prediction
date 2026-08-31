# foresightx-flood-prediction
3. AI based Multi - source Flood Risk Prediction and early warning system*

## Flood GIS Demo Safe-Route Mode

The **Flood GIS Map** now includes a **Demo Safe-Route Mode** built with Leaflet.

- Demo mode is restricted to **Mumbai and Pune**.
- You can simulate **rainfall, water depth, road blockage, and river/drain overflow**.
- ForesightX scores the predefined demo evacuation corridors against the simulated flood conditions.
- The map displays **only the safest corridor** in green, plus the start point, evacuation point, and simulated flood zones.
- The demo is intentionally a **visual simulation**, not turn-by-turn navigation. Real evacuation decisions should use current road-closure and official emergency information.
- Leaflet + OpenStreetMap tiles are used for the GIS visualization; no routing library is required.

