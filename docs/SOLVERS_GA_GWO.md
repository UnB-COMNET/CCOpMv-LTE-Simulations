# GA and GWO Solvers: Pseudocode and Computational Complexity

This document describes the Genetic Algorithm (GA) and Progressive Grey Wolf Optimizer (PGWO / GWO) solvers used for eNB placement, with pseudocode and complexity analysis based on the main problem parameters.

---

## Main parameters (notation)

| Symbol | Meaning | Typical / default |
|--------|--------|-------------------|
| **M**  | Number of regions (sectors) on the map | e.g. 100 (from `size_x`, `size_y`, `size_sector`) |
| **T**  | Number of time slices | e.g. 12 (`num_slices`) |
| **P**  | GA population size | 100 |
| **G**  | GA generations per slice (or until stop) | 100 (or until `saturate_30`) |
| **P_c** | GA connections sub‑population size | 100 |
| **G_c** | GA connections sub‑generations | 10 |
| **W**  | GWO pack size (number of wolves) | 300 (`pack_size`) |
| **I**  | GWO max iterations per run | 200 (`max_iter`) |
| **D**  | GWO max dimension (max antennas added per slice) | 10 (`max_dimension`) |

---

## 1. Genetic Algorithm (GA) — `app.solvers.ga`

### 1.1 High-level idea

- The problem is solved **per time slice**: for slice `t`, we maintain a binary chromosome of length **M** (one gene per region: 1 = antenna, 0 = no antenna).
- Constraints: backhaul connectivity (distance ≤ `min_dis`), SINR coverage, max users per antenna, and “antenna once installed cannot be removed” across slices.
- For each slice, a **GA** evolves a population of chromosomes; the **fitness** of a chromosome combines: number of antennas (fewer is better), coverage, eccentricity, and a nested **GA for user–antenna connections**. The best solution is kept as the antenna mask for the next slice.

### 1.2 Pseudocode

```text
Algorithm: GA solver (ga_solver)

Input: num_regions M, users_t_m[0..T-1][0..M-1], distance_mn[M][M], snr_map_mn[M][M],
       first_antenna_region, num_slices T, min_dis, min_sinr_w, max_users_per_antenna_m[M], result_dir
Output: antennas_regions_byslice[0..T-1], connections_dict_byslice[0..T-1]

1.  Precompute center_section (region with minimum mean distance).
2.  antennas_last_result[0..M-1] := 0 except antennas_last_result[first_antenna_region] := 1.
3.  FOR t := 0 TO T-1 DO
4.      users_t_m_current := users_t_m[t..T-1]   // remaining slices from t
5.      (antennas_regions, connections_dict) := run_genetic(antennas_last_result, fitness_func, callback)
6.      antennas_last_result[m] := 1 if m in antennas_regions else 0, for all m
7.      antennas_regions_byslice[t] := antennas_regions
8.      connections_dict_byslice[t] := connections_dict
9.  write_file_result(...)
10. RETURN antennas_regions_byslice, connections_dict_byslice
```

```text
Algorithm: run_genetic (single-slice GA)

Input: base_genome[0..M-1], fitness_func, on_generation_callback
Output: antennas_regions (indices where solution[m]=1), connections_dict

1.  population := create_population(base_genome, population_size P)   // P copies of base_genome
2.  ga_instance := GA(num_generations=G, num_parents_mating=4, fitness_func=fitness_func,
                     initial_population=population, gene_space={0,1}, ...)
3.  ga_instance.run()   // run until G generations or stop_criteria (e.g. saturate_30)
4.  solution, solution_fitness, solution_idx := ga_instance.best_solution()
5.  antennas_regions := indices m where solution[m] > 0
6.  RETURN antennas_regions, connection_results[solution_idx]
```

```text
Algorithm: fitness(solution, solution_idx)   // cost per chromosome evaluation

1.  antennas_regions := { m : solution[m] > 0 }
2.  IF any m with antennas_last_result[m]=1 has solution[m]!=1 THEN RETURN (0, None)
3.  map_of_service := get_map_of_service(antennas_regions, snr_map_mn)   // O(|A|² · M)
4.  Check backhaul: every antenna (except first) must have a neighbor within min_dis   // O(|A|²)
5.  IF not connected THEN RETURN (0, None)
6.  users_regions := { n : users_t_m[0][n] > 0 }
7.  base_connections_genome := [map_of_service[n].antenna for n in users_regions]
8.  (connect_solution, connect_fitness) := run_genetic_connections(base_connections_genome, fitness_connections, gene_space=antennas_regions)
9.  Compute antennas_score, coverage_score, eccentricity_score, norm_metric_score
10. RETURN combined_fitness, connect_dict
```

```text
Algorithm: run_genetic_connections

Input: base_genome (length |users_regions|), fitness_func=fitness_connections, gene_space=antennas_regions
Output: connection solution (which antenna serves each user region), fitness

1.  population := P_c copies of base_genome
2.  Run GA with G_c generations, population size P_c, gene_space = antennas_regions
3.  RETURN best_solution, best_fitness
```

- **get_map_of_service(antennas_regions, metric_map_mn)**: for each pair of antennas and each region, compare metric; build “best antenna per region”. Cost **O(|A|² · M)** with |A| ≤ M.
- **run_genetic_connections**: inner GA with **P_c** individuals, **G_c** generations, chromosome length ≤ M; **fitness_connections** is **O(M)** per evaluation.

### 1.3 Complexity (GA)

- **Per slice**: one `run_genetic`:
  - Up to **G** generations × **P** individuals × (fitness cost).
  - Fitness: **O(M²)** (get_map_of_service + backhaul) + **O(P_c · G_c · M)** (inner GA run once per outer fitness call).
  - So per slice: **O(G · P · (M² + P_c · G_c · M))** = **O(G · P · M²)** when M dominates.
- **Total over T slices**:
  - **Time: O(T · G · P · M²)**  
  - With default P=100, G=100: **O(T · M²)** in practice (constants 10⁴).

**Space**: O(M²) for distance and SNR maps, O(P · M) for population, O(P_c · M) for connections GA; total **O(M² + P·M)**.

---

## 2. Progressive Grey Wolf Optimizer (PGWO / GWO) — `app.solvers.gwo`

### 2.1 High-level idea

- Again the problem is solved **per time slice**. For each slice we start from the current antenna set. If the current set already satisfies the constraints (fitness ≠ −∞), we keep it. Otherwise we run **GWO** with **increasing dimension** d = 1, 2, …, up to **D**: each wolf encodes **d** new (x,y) positions (new antennas); we search until a feasible solution is found or d reaches D.
- **GWO** maintains a pack of **W** wolves. Each wolf has a **position** = list of d coordinates (d = dimension). The objective is to maximize a **fitness** (coverage and/or WMSE-based). In each iteration, every wolf is updated toward alpha, beta, and delta (best three wolves); then fitness is re-evaluated and the pack is re-sorted.

### 2.2 Pseudocode

```text
Algorithm: PGWO solver (pgwo_solver)

Input: scenario (MapChess), num_regions M, users_t_m[0..T-1][0..M-1], distance_mn, snr_map_mn,
       antennasmap_m[M], first_antenna_region, num_slices T, min_dis, min_sinr_w,
       max_users_per_antenna_m[M], result_dir, max_dimension D, pack_size W, max_iter I
Output: results[0..T-1] (antennas_regions per slice)

1.  antennas_map[0..M-1] := 0; antennas_map[first_antenna_region] := 1
2.  FOR t := 0 TO T-1 DO
3.      users_t_m_current := users_t_m[t..T-1]
4.      antennas_regions := { m : antennas_map[m] > 0 }
5.      users_regions := { n : users_t_m_current[0][n] > 0 }
6.      dimension := |antennas_regions|
7.      _wolf := Wolf(antennas_regions, users_regions, dimension, scenario, ...)
8.      set _wolf positions from region centers; _wolf.updateFitness(...)
9.      IF _wolf.fitness = -∞ THEN
10.         dimension := 1
11.         WHILE dimension ≤ D DO
12.             solution := run_gwo(scenario, antennas_regions, users_regions, W, dimension, I, fitness_func, seed_base)
13.             seed_base += W
14.             IF solution.fitness ≠ -∞ THEN
15.                 FOR each position in solution.position DO
16.                     r := coord2Region(position); antennas_map[r] := 1
17.                 results[t] := { m : antennas_map[m] > 0 }; BREAK
18.             IF dimension = D THEN RETURN None   // infeasible
19.             dimension += 1
20.     ELSE results[t] := antennas_regions
21. write result file; RETURN results
```

```text
Algorithm: run_gwo (single GWO run for a fixed dimension d)

Input: scenario, antennas_regions, users_regions, pack_size W, wolf_dimension d, max_iter I, fitness_func, seed_base
Output: best wolf (alpha)

1.  population := [ Wolf(antennas_regions, users_regions, d, scenario, seed_base+i, i, fitness_func) for i in 0..W-1 ]
2.  population := sort(population by fitness descending)
3.  alpha, beta, delta := copy(population[0]), copy(population[1]), copy(population[2])
4.  FOR iter := 0 TO I-1 DO
5.      a := 2*(1 - iter/I)
6.      FOR n := 0 TO W-1 DO
7.          Xnew := copy(population[n])
8.          FOR j := 0 TO d-1 DO
9.              Compute A1,A2,A3, C1,C2,C3 (vectors of length 2d, random)
10.             X1[j] := alpha.position[j] - A1.*|C1.*alpha.position[j] - X[j]|
11.             X2[j] := beta.position[j]  - A2.*|C2.*beta.position[j]  - X[j]|
12.             X3[j] := delta.position[j] - A3.*|C3.*delta.position[j] - X[j]|
13.             Xnew.position[j] := (X1[j] + X2[j] + X3[j]) / 3
14.             Clamp Xnew.position[j] to [0, size_x] x [0, size_y]
15.         Xnew.updateFitness(antennas_regions, users_regions)
16.         IF Xnew.fitness >= population[n].fitness THEN population[n] := Xnew
17.     population := sort(population by fitness descending)
18.     alpha, beta, delta := copy(population[0..2])
19. RETURN alpha
```

```text
Algorithm: fitness_pgwo2 (and check_constraints)

1.  check_constraints(wolf_position, antennas_regions, users_regions, scenario):
2.      wolf_antennas := [ coord2Region(wolf_position[i]) for i ]
3.      IF duplicate or overlap with installed THEN RETURN False
4.      antennas_regions := wolf_antennas ∪ antennas_regions
5.      IF any antenna in forbidden region THEN RETURN False
6.      Backhaul check: every antenna (except first) has neighbor within min_dis   // O(|A|²)
7.      connections, map_of_service := get_dict_of_connections(antennas_regions, users_regions, users_t_m[0], snr_map_mn, ...)
8.      IF connections = None THEN RETURN False
9.      RETURN (connections, antennas_regions, map_of_service)
10. IF check_constraints THEN compute coverage and WMSE; score := 10000*(1/sqrt(wmse))*sum_eta_m/M
11. ELSE score := -∞
12. RETURN score
```

- **get_dict_of_connections** uses **get_map_of_service** and sorts/assigns users to antennas; cost **O(|A|² · M)** with |A| ≤ M.

### 2.3 Complexity (GWO)

- **Per run_gwo(d)**:
  - **I** iterations × **W** wolves × (update d coordinates + one fitness).
  - Position update: **O(d)** per wolf; d ≤ D.
  - Fitness (check_constraints + get_dict_of_connections + score): **O(M²)**.
  - So per run: **O(I · W · (d + M²))** = **O(I · W · M²)**.
- **Per slice (worst case)**: we run run_gwo for dimension 1, 2, …, **D** until feasible: **O(D · I · W · M²)**.
- **Total over T slices**:
  - **Time: O(T · D · I · W · M²)**  
  - With D=10, I=200, W=300: **O(T · M²)** with a large constant (~6·10⁵).

**Space**: O(M²) for maps, O(W · D) for wolf positions; total **O(M² + W·D)**.

---

## 3. Summary and comparison

| Solver | Time complexity | Main parameters |
|--------|------------------|-----------------|
| **GA** | **O(T · G · P · M²)** | T slices, G generations, P population, M regions |
| **GWO** | **O(T · D · I · W · M²)** | T slices, D max dimension, I iterations, W pack size, M regions |

- Both depend on **T** (number of slices) and **M²** (region count and pairwise/distance and SNR structures).
- GA adds a factor **G · P** (generations × population) per slice; GWO adds **D · I · W** (dimension × iterations × wolves) per slice in the worst case (each slice needing a full dimension sweep).
- The **M²** term comes from: (1) distance matrix and SNR map of size M×M, and (2) get_map_of_service / get_dict_of_connections over antenna sets of size O(M) and M regions.

The pseudocode above justifies these complexities: each per-slice GA run does O(G·P) fitness evaluations each O(M²) (+ inner GA O(P_c·G_c·M)); each per-slice GWO does at most D runs of O(I·W) fitness evaluations each O(M²).
