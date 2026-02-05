Model Design
============

# 1. Design Goals

- Encode the game rules in data-first models.
- Keep models serializable to JSON for autosave.
- Separate static map topology from dynamic game state.

# 2. Core Entities

## 2.1 GameState

- id: string
- seed: int
- turn: int
- phase: string (player_turn | map_phase | cpu_turn)
- active_side: string (player | cpu)
- remaining_commands: int
- map: MapState
- nations: list[Nation]
- units: list[Unit]
- leaders: list[Leader]
- logs: list[LogEntry]
- difficulty: DifficultyConfig
- rule_params: RuleParams

Notes:
- Owns the full mutable state required for autosave.

## 2.2 MapState

- cities: list[City]
- roads: list[Road]

Notes:
- Graph topology. Cities and roads are stable identities; ownership is dynamic.

## 2.3 City

- id: string
- name: string
- position: tuple[int, int]
- size_cap: int
- production: int
- population: int
- owner_nation_id: string
- stationed_unit_ids: list[string]
- occupation: OccupationState | null

Notes:
- population grows each turn by size_cap * 0.10, up to size_cap.
- occupation is active when non-owner units are present.

## 2.4 Road

- id: string
- a_city_id: string
- b_city_id: string
- length: int

Notes:
- Undirected edge between cities.

## 2.5 Nation

- id: string
- name: string
- side: string (player | cpu)
- city_ids: list[string]
- leader_ids: list[string]
- color_index: int

## 2.6 Unit

- id: string
- owner_nation_id: string
- leader_id: string | null
- city_id: string
- soldiers: int

Notes:
- Unit is removed when soldiers reaches 0.

## 2.7 Leader

- id: string
- name: string
- owner_nation_id: string | null
- atk_bonus: float
- occ_bonus: float

Notes:
- owner_nation_id is null when unassigned.

## 2.8 OccupationState

- city_id: string
- invader_nation_id: string
- durability: float

Notes:
- durability starts at City.population and decreases by occupation_value each map phase.

## 2.9 LogEntry

- id: string
- turn: int
- category: string (battle | spawn | move | occupation)
- message: string
- data: dict

# 3. Rule Parameter Models

## 3.1 DifficultyConfig

- name: string
- cpu_commands_per_turn: int
- player_commands_per_turn: int
- population_growth_rate: int
- cpu_growth_curve: string

Notes:
- cpu_growth_curve points to a rule set in RuleParams.

## 3.2 RuleParams

- battle_round_limit: int (default 5)
- battle_base_divisor: int (default 10)
- battle_rng_min: float (default -0.10)
- battle_rng_max: float (default 0.10)
- multi_unit_bonus_per_unit: float (default 0.10)
- city_spawn_interval: int
- enemy_unit_base: int
- enemy_unit_growth: float
- enemy_leader_bonus_growth: float

Notes:
- These are tunables for difficulty and balance.

# 4. Relationships and Invariants

- City.owner_nation_id must match a Nation.id.
- Unit.city_id must match a City.id.
- Unit.owner_nation_id must match a Nation.id.
- If Unit.leader_id is set, Leader.owner_nation_id must match Unit.owner_nation_id.
- Nation.city_ids is derived from City ownership and should be recomputed on load.
- Nation.leader_ids is derived from Leader ownership and should be recomputed on load.
- City.stationed_unit_ids is derived from Unit.city_id and should be recomputed on load.

# 5. Derived Values and Rules

- Command counts are read from DifficultyConfig and do not change mid-game.
- population increases by size_cap * 0.10 each map phase until size_cap.
- recruiting creates a Unit with soldiers equal to City.population, then sets population to 0.
- battle damage per round:
  - base = total_soldiers / battle_base_divisor
  - leader bonus = base * atk_bonus
  - unit count bonus = base * (multi_unit_bonus_per_unit * (unit_count - 1))
  - random factor = uniform(battle_rng_min, battle_rng_max)
  - total damage = (base + leader bonus + unit count bonus) * (1 + random factor)

# 6. Save / Load

- Serialize GameState as a JSON root.
- Stable ids are required for City, Road, Unit, Leader, Nation, LogEntry.
- Derived lists (Nation.city_ids, etc.) are recomputed on load to avoid drift.

# 7. Turn Progression (Model-Level)

- player_turn:
  - command loop (move | recruit)
  - battle resolution
- map_phase:
  - occupation resolution (player side)
  - new city discovery
  - population growth
- cpu_turn:
  - command loop
  - battle resolution
- map_phase (cpu):
  - occupation resolution (cpu side)

# 8. Open Items

- Occupation completion threshold.
- CPU target selection rules (unit movement priorities).
