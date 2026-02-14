# LTE and 5G Scenarios Simulation with Omnet++

## Python project (UV)

The simulation logic lives in the `app` package and is managed with [UV](https://docs.astral.sh/uv/).

- **Setup:** From the project root run `uv sync` to create the virtual environment and install dependencies.
- **Run main pipeline:** `uv run run-all` or `uv run python -m app.run_all`
- **Run other scripts:** `uv run python -m app.clean_all`, `uv run python -m app.viz.graphs`, etc.

**App layout:**
- `app/core/` – coordinates, geometry, SINR computation, errors
- `app/helpers/` – helper, helper_ned, helper_xml, general_functions
- `app/solvers/` – ga, gwo; `app/solvers/ilp/` – ILP solvers
- `app/scenarios/five_g/` – 5G ILP configs; `app/scenarios/lte/` – LTE scenario helpers
- `app/viz/` – graphs, plot_SNR_map, comp_comput_performance
- `app/` (root) – run_all, run_simulations, gen_ilp_info, clean_all, sinrMapGen, sinrTEstCode

Dependencies are declared in `pyproject.toml`. The old `Functions/` directory can be kept for reference or removed; the canonical code is under `app/`.

**Code behaviour:** See [docs/CODE_BEHAVIOUR.md](docs/CODE_BEHAVIOUR.md) for an overview of the code behaviour: architecture, main pipeline, sequence diagrams, and data flow (Mermaid diagrams).

## Versions
**Operational Systems:** Lubuntu 18.04 and Ubuntu 18.04.5

**Omnet++:** 5.6.2

**INET-Framework:** 4.2.2

**SimuLTE:** 1.2.0

**Simu5G:** 1.1.0
