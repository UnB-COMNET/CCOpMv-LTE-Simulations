# LTE and 5G Scenarios Simulation with Omnet++
## Summary

This project focus itself in generating solutions for randomly allocated antennas in an antenna placement problem.

The algorigthms present use the solutions to also create Omnet++ configurations and then running the related simulations in order to test the found solutions.

For the used algorithms, we adapted two prominent meta-heuristics from literature to align with our unique disaster-response constraints:

- Grey Wolf Optimizer (GWO)
- Genetic Algorithm (GA)


---

### Main pipeline (run_all.py)

The main entry point orchestrates: **user generation → movement simulation (OMNeT++) → solver (ILP/GA/GWO) → config generation → network simulation (OMNeT++) → CSV export**. One process per seed; within each seed, one process per (mode, min_sinr).

---

### Data flow summary

```
Config (seeds, modes, min_sinrs, map, micro_power, ...)
    ↓
Poisson users & ues_per_slice (helpers.general_functions)
    ↓
Movement .ini (scenarios.five_g.ilp_move_users) → OMNeT++ → .sna
    ↓
MapChess + getSinrMap() (core) + get_map_ues_time (helpers.helper_xml from .sna)
    ↓
Solver (solvers.ilp / ga / gwo) → result_<mode>_<min_sinr>.txt
    ↓
Simulation .ini (ilp_sliced_ini*) + .ned (ilp_ned)
    ↓
OMNeT++ simulation → .sca / .vec
    ↓
scavetool → CSV → viz (graphs, comp_comput_performance)
```

---

### File artefacts

| Artefact | Producer | Consumer / use |
|----------|----------|-----------------|
| `ilp_move_users-<seed>.ini` | ilp_move_users | OMNeT++ (movement) |
| `ilp_move_users-<seed>.sna` | OMNeT++ | get_map_ues_time, gen_ilp_info |
| `result_<mode>_<min_sinr>.txt` | Solvers | ilp_sliced_ini*, ilp_ned |
| `ilp_<mode>_sliced_<min_sinr>.ini` | ilp_sliced_ini* | OMNeT++ (video/app) |
| `*.ned` | ilp_ned | OMNeT++ network definition |
| `*.sca`, `*.vec` | OMNeT++ | scavetool → CSV |
| CSV | get_csv (scavetool) | viz.graphs, comp_comput_performance |

---

### Usage example:

[run_all.py](/Functions/run_all.py) (main)

### Complexity analysis

Can be found in details in the [SOLVERS_GA_GWO.md](/docs/SOLVERS_GA_GWO.md) file.

## Versions
**Operational Systems:** Lubuntu 18.04 and Ubuntu 18.04.5

**Omnet++:** 5.6.2

**INET-Framework:** 4.2.2

**SimuLTE:** 1.2.0

**Simu5G:** 1.1.0

## Authors

@GiordanoSM
@julianobp
