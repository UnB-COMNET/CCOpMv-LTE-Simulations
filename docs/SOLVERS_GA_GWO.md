# GA and GWO Solvers: Pseudocode and Computational Complexity

This document describes the Genetic Algorithm (GA) and Progressive Grey Wolf Optimizer (PGWO / GWO) solvers used for eNB placement, with pseudocode and complexity analysis based on the main problem parameters.

---

## Main parameters (notation)

| Symbol | Meaning | Typical / default | Worst case |
|--------|--------|-------------------|------------|
| **M**  | Number of regions (sectors) on the map | e.g. 100 (from `size_x`, `size_y`, `size_sector`) | - |
| **T**  | Number of time slices | e.g. 12 (`num_slices`) | - |
| **\|A\|** | Number of antennas at a given time | Sparse: 5-20 | O(M) (antenna in every region) |
| **P**  | GA population size | 100 | - |
| **G**  | GA generations per slice (or until stop) | 100 (or until `saturate_30`) | 100 (no early stop) |
| **P_c** | GA connections sub‑population size | 100 | - |
| **G_c** | GA connections sub‑generations | 10 | - |
| **W**  | GWO pack size (number of wolves) | 300 (`pack_size`) | - |
| **I**  | GWO max iterations per run | 200 (`max_iter`) | - |
| **D**  | GWO max dimension (max antennas added per slice) | 10 (`max_dimension`) | - |

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
3.  ga_instance.run()   // WORST CASE: runs full G generations (no early stop)
                        // Evaluates fitness() for each individual in each generation
                        // Total fitness calls: O(G · P)
4.  solution, solution_fitness, solution_idx := ga_instance.best_solution()
5.  antennas_regions := indices m where solution[m] > 0
6.  RETURN antennas_regions, connection_results[solution_idx]
```

```text
Algorithm: fitness(solution, solution_idx)   // CALLED O(G · P) TIMES per slice

1.  antennas_regions := { m : solution[m] > 0 };  |A| := |antennas_regions|
2.  IF any m with antennas_last_result[m]=1 has solution[m]!=1 THEN RETURN (0, None)
3.  map_of_service := get_map_of_service(antennas_regions, snr_map_mn)   // O(|A| · M)
                     // For each region, find best antenna: M regions × |A| antennas
4.  Check backhaul: every antenna (except first) must have a neighbor within min_dis   // O(|A|²)
                    // Check all antenna pairs for connectivity
5.  IF not connected THEN RETURN (0, None)
6.  users_regions := { n : users_t_m[0][n] > 0 };  |U| := |users_regions| ≤ M
7.  base_connections_genome := [map_of_service[n].antenna for n in users_regions]  // O(|U|)
8.  (connect_solution, connect_fitness) := run_genetic_connections(...)  // NESTED GA!
                    // Runs FULL inner GA: O(P_c · G_c) fitness evaluations
                    // Each inner fitness: O(|U|) = O(M) in worst case
                    // Total for inner GA: O(P_c · G_c · M)
9.  Compute antennas_score, coverage_score, eccentricity_score, norm_metric_score  // O(M)
10. RETURN combined_fitness, connect_dict

// TOTAL COST PER CALL: O(|A| · M + |A|² + P_c · G_c · M)
// WORST CASE: |A| = O(M) → O(M² + P_c · G_c · M)
```

```text
Algorithm: run_genetic_connections   // INNER GA (nested within fitness())

Input: base_genome (length |users_regions| ≤ M), fitness_func=fitness_connections, gene_space=antennas_regions
Output: connection solution (which antenna serves each user region), fitness

1.  population := P_c copies of base_genome  // Chromosome length: |U| ≤ M
2.  FOR gen := 0 TO G_c-1 DO  // WORST CASE: full G_c generations
3.      FOR each individual in population (P_c individuals) DO
4.          fitness_connections(individual)  // O(|U|) = O(M) worst case
                // Check: users assigned to valid antennas, capacity constraints
5.      Select, crossover, mutate
6.  RETURN best_solution, best_fitness

// TOTAL COST: O(P_c · G_c · M)
```

- **get_map_of_service(antennas_regions, metric_map_mn)**: for each region, compare all antennas to find the best one based on SNR metric. Cost **O(|A| · M)** (M regions × |A| antennas). In worst case |A| = O(M), giving O(M²).
- **run_genetic_connections**: inner GA with **P_c** individuals, **G_c** generations, chromosome length |U| ≤ M; **fitness_connections** is **O(M)** per evaluation. **Critically: this inner GA runs to completion EVERY time fitness() is called.**

### 1.3 Complexity (GA)

#### Detailed breakdown:

1. **Per fitness() call** (lines 1-10 of fitness algorithm):
   - get_map_of_service: **O(|A| · M)**
   - Backhaul check: **O(|A|²)**
   - Inner GA (run_genetic_connections): **O(P_c · G_c · M)**
   - Scoring computations: **O(M)**
   - **Total: O(|A| · M + |A|² + P_c · G_c · M)**
   - **Worst case** (|A| = O(M)): **O(M² + P_c · G_c · M)**

2. **Per slice** (one run_genetic call):
   - Number of fitness() calls: **G generations × P individuals** = **O(G · P)** in worst case (no early stopping)
   - Each fitness call: **O(M² + P_c · G_c · M)** worst case
   - **Per slice total: O(G · P · (M² + P_c · G_c · M))**
   - Since typically M ≥ P_c · G_c (M ~ 100, P_c · G_c ~ 1000), we get: **O(G · P · M²)**

3. **Total over T slices**:
   - **Time: O(T · G · P · M²)**  
   - With defaults G=100, P=100: **O(T · M²)** with constant factor ~10⁴
   - Note: if P_c · G_c ≫ M, complexity becomes **O(T · G · P · P_c · G_c · M)**

**Space**: O(M²) for distance and SNR maps, O(P · M) for outer population, O(P_c · M) for inner connections GA; total **O(M² + P·M)**.

**Key worst-case assumptions**: 
- Full G generations run (no early convergence)
- |A| grows to O(M) (antenna in many/most regions)
- Inner GA runs P_c · G_c full evaluations for every outer fitness call

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
2.  FOR t := 0 TO T-1 DO  // T slices
3.      users_t_m_current := users_t_m[t..T-1]
4.      antennas_regions := { m : antennas_map[m] > 0 };  |A| := |antennas_regions|
5.      users_regions := { n : users_t_m_current[0][n] > 0 }
6.      dimension := |antennas_regions|
7.      _wolf := Wolf(antennas_regions, users_regions, dimension, scenario, ...)
8.      set _wolf positions from region centers; _wolf.updateFitness(...)
9.      IF _wolf.fitness = -∞ THEN  // Current antennas insufficient
10.         dimension := 1
11.         WHILE dimension ≤ D DO  // WORST CASE: try all D dimensions
12.             solution := run_gwo(scenario, antennas_regions, users_regions, W, dimension, I, fitness_func, seed_base)
                            // Full GWO run: O(I · W · fitness_cost)
13.             seed_base += W
14.             IF solution.fitness ≠ -∞ THEN  // Feasible solution found
15.                 FOR each position in solution.position DO
16.                     r := coord2Region(position); antennas_map[r] := 1
17.                 results[t] := { m : antennas_map[m] > 0 }; BREAK
18.             IF dimension = D THEN RETURN None   // infeasible even with max antennas
19.             dimension += 1
20.     ELSE results[t] := antennas_regions  // Current antennas already sufficient
21. write result file; RETURN results

// WORST CASE PER SLICE: run_gwo called D times (dimensions 1,2,...,D)
// BEST CASE PER SLICE: no GWO runs needed (line 20) or early success (line 17)
```

```text
Algorithm: run_gwo (single GWO run for a fixed dimension d)

Input: scenario, antennas_regions, users_regions, pack_size W, wolf_dimension d, max_iter I, fitness_func, seed_base
Output: best wolf (alpha)

1.  population := [ Wolf(...) for i in 0..W-1 ]  // Initialize W wolves
2.  FOR i := 0 TO W-1 DO  // Initial fitness evaluation
3.      population[i].updateFitness(antennas_regions, users_regions)  // O(fitness_cost)
4.  population := sort(population by fitness descending)  // O(W log W)
5.  alpha, beta, delta := copy(population[0]), copy(population[1]), copy(population[2])
6.  FOR iter := 0 TO I-1 DO  // WORST CASE: full I iterations (no early stop)
7.      a := 2*(1 - iter/I)
8.      FOR n := 0 TO W-1 DO  // Update each wolf
9.          Xnew := copy(population[n])
10.         FOR j := 0 TO d-1 DO  // Update each dimension (d coordinates)
11.             Compute A1,A2,A3, C1,C2,C3 (random vectors)  // O(1) per dimension
12.             X1[j] := alpha.position[j] - A1.*|C1.*alpha.position[j] - X[j]|
13.             X2[j] := beta.position[j]  - A2.*|C2.*beta.position[j]  - X[j]|
14.             X3[j] := delta.position[j] - A3.*|C3.*delta.position[j] - X[j]|
15.             Xnew.position[j] := (X1[j] + X2[j] + X3[j]) / 3
16.             Clamp Xnew.position[j] to [0, size_x] x [0, size_y]
              // Total position update: O(d)
17.         Xnew.updateFitness(antennas_regions, users_regions)  // O(fitness_cost)
18.         IF Xnew.fitness >= population[n].fitness THEN population[n] := Xnew
19.     population := sort(population by fitness descending)  // O(W log W)
20.     alpha, beta, delta := copy(population[0..2])
21. RETURN alpha

// TOTAL FITNESS EVALUATIONS: W (initial) + I · W (iterations) = O(I · W)
// TOTAL COST: O(I · W · (d + fitness_cost) + I · W log W) = O(I · W · fitness_cost)
//   (assuming fitness_cost ≫ d and fitness_cost ≫ log W)
```

```text
Algorithm: fitness_pgwo2 (and check_constraints)  // CALLED O(I · W) TIMES per run_gwo

1.  check_constraints(wolf_position, antennas_regions, users_regions, scenario):
2.      wolf_antennas := [ coord2Region(wolf_position[i]) for i ]  // O(d)
3.      IF duplicate or overlap with installed THEN RETURN False  // O(d) or O(|A|)
4.      antennas_regions' := wolf_antennas ∪ antennas_regions;  |A'| := |antennas_regions'|
5.      IF any antenna in forbidden region THEN RETURN False  // O(|A'|)
6.      Backhaul check: every antenna (except first) has neighbor within min_dis   // O(|A'|²)
                       // Check all pairs of antennas for connectivity constraint
7.      connections, map_of_service := get_dict_of_connections(...)  // O(|A'| · M)
                       // Calls get_map_of_service: O(|A'| · M)
                       // Then assigns users to antennas checking capacity: O(|U| · |A'|) ≤ O(M · |A'|)
8.      IF connections = None THEN RETURN False  // Capacity/coverage constraints violated
9.      RETURN (connections, antennas_regions', map_of_service)
10. IF check_constraints succeeds THEN 
11.     compute coverage (sum over M regions) and WMSE (sum over users)  // O(M)
12.     score := 10000*(1/sqrt(wmse))*sum_eta_m/M  // O(1)
13. ELSE score := -∞
14. RETURN score

// TOTAL COST PER CALL: O(|A'|² + |A'| · M + M) 
// WORST CASE: |A'| = |A| + d ≤ M → O(M² + M²) = O(M²)
```

- **get_dict_of_connections** uses **get_map_of_service** (O(|A| · M)) and sorts/assigns users to antennas checking capacity constraints (O(|U| · |A|)); total cost **O(|A| · M)** with |A| ≤ M, |U| ≤ M. In worst case |A| = O(M), giving O(M²).

### 2.3 Complexity (GWO)

#### Detailed breakdown:

1. **Per fitness_pgwo2() call** (lines 1-14 of fitness algorithm):
   - Backhaul check: **O(|A'|²)** where |A'| = |A| + d (existing + new antennas)
   - get_dict_of_connections: **O(|A'| · M)**
   - Coverage/WMSE computation: **O(M)**
   - **Total: O(|A'|² + |A'| · M + M)**
   - **Worst case** (|A'| = O(M)): **O(M²)**

2. **Per run_gwo(d)** call (single dimension):
   - Initial fitness evaluations: **W** wolves × fitness_cost = **O(W · M²)**
   - Main loop: **I iterations** × **W wolves** × (position update + fitness)
     - Position update per wolf: **O(d)** where d ≤ D = 10 (negligible)
     - Fitness evaluation per wolf: **O(M²)** worst case
   - Sorting per iteration: **O(W log W)** (negligible compared to fitness)
   - **Total per run_gwo: O(I · W · M²)**

3. **Per slice** (pgwo_solver, lines 2-21):
   - **Best case**: Current antennas sufficient → no GWO runs → **O(M²)** (single fitness check)
   - **Worst case**: Need to try dimensions 1, 2, ..., D sequentially
     - run_gwo called D times (once per dimension)
     - Each run_gwo: **O(I · W · M²)**
     - **Per slice worst case: O(D · I · W · M²)**

4. **Total over T slices**:
   - **Time (worst case): O(T · D · I · W · M²)**  
   - With defaults D=10, I=200, W=300: **O(T · M²)** with constant factor = D·I·W = 6×10⁵
   - **Time (best case): O(T · M²)** (no new antennas needed)

**Space**: O(M²) for distance and SNR maps, O(W · D) for wolf positions (negligible: 300×10×2coords = 6000 vs M² ~ 10⁴), total **O(M²)**.

**Key worst-case assumptions**:
- Every slice requires D full dimension attempts (no early feasible solution)
- Each run_gwo runs full I iterations (no early convergence)
- |A| grows to O(M) eventually (many antennas deployed)
- W wolves all evaluated every iteration

---

## 3. Summary and comparison

| Solver | Time complexity (worst case) | Main parameters | Constant factor |
|--------|------------------------------|-----------------|------------------|
| **GA** | **O(T · G · P · M²)** | T slices, G generations, P population, M regions | G·P ~ 10⁴ |
| **GWO** | **O(T · D · I · W · M²)** | T slices, D max dimension, I iterations, W pack size, M regions | D·I·W ~ 6×10⁵ |

### Key observations:

1. **Common M² term**: Both algorithms have O(M²) cost per fitness evaluation, arising from:
   - Distance matrix and SNR map storage: O(M²) space accessed per evaluation
   - get_map_of_service / get_dict_of_connections: O(|A| · M) where |A| = O(M) worst case
   - Backhaul connectivity checks: O(|A|²) where |A| = O(M) worst case

2. **GA multiplier (G · P)**:
   - Outer GA evaluates fitness G·P times per slice (generations × population)
   - Each fitness call triggers a FULL inner GA with P_c·G_c·M overhead
   - Total: O(G·P·M²) assuming M dominates P_c·G_c
   - Worst case if P_c·G_c ≫ M: O(G·P·P_c·G_c·M)

3. **GWO multiplier (D · I · W)**:
   - Progressive strategy: try dimensions 1, 2, ..., D until feasible
   - Worst case: all D dimensions attempted
   - Each dimension: I iterations × W wolves = I·W fitness evaluations
   - Much larger constant factor than GA (6×10⁵ vs 10⁴)
   - Best case: O(I·W·M²) if dimension 1 succeeds or antennas already sufficient

4. **Practical complexity**:
   - GA: ~10⁴ · T · M² operations
   - GWO: ~6×10⁵ · T · M² operations (worst), ~10³ · T · M² (best)
   - For typical M=100, T=12: GA ~10⁸ operations, GWO ~10¹⁰ operations (worst)

### Worst-case justification from pseudocode:

- **GA**: 
  - T slices (line 3 of ga_solver)
  - G generations per slice (line 3 of run_genetic, no early stop)
  - P fitness evaluations per generation (implicit in GA framework)
  - Each fitness: O(M²) for maps + O(P_c·G_c·M) for inner GA (line 8 of fitness)
  - Inner GA runs P_c·G_c full evaluations (lines 2-6 of run_genetic_connections)

- **GWO**:
  - T slices (line 2 of pgwo_solver)  
  - D dimension attempts per slice worst case (line 11-19 of pgwo_solver)
  - I · W fitness evaluations per dimension (lines 6-17 of run_gwo)
  - Each fitness: O(|A'|² + |A'|·M) = O(M²) worst case (lines 6-7 of fitness_pgwo2)
