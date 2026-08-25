# Fly-In

A drone routing and simulation project in Python.

## Project summary

This project asks you to design a system that routes multiple drones from a start zone to an end zone through a graph of connected zones while respecting movement rules, capacities, and timing constraints. The goal is to move all drones to the destination in as few simulation turns as possible while keeping the system valid and efficient.

The project is not just about finding a path. It is about building a valid, constrained simulation engine that handles:

- multiple drones moving simultaneously,
- zone and connection capacity rules,
- restricted zones with extra movement cost,
- collision avoidance and deadlock prevention,
- route optimization,
- visual feedback of the simulation,
- a clean, testable, object-oriented Python implementation.

## What you need to do

## Running the visualizers

Run a simulation with colored terminal output:

```bash
python3 -m fly_in maps/easy/01_linear_path.txt --visual terminal
```

Useful terminal options are `--no-color` for plain output and `--delay 0.5` to
pause between turns. The default visualization mode is `terminal`.

Save the assignment-format movements to an output file with:

```bash
python3 -m fly_in maps/easy/01_linear_path.txt --output moves.txt --no-color
```

The file contains one space-separated movement line per turn, without the
internal `turn N:` log prefix. Waiting turns are preserved as blank lines.

Run the same simulation in the coordinate-based Pygame visualizer:

```bash
python3 -m fly_in maps/challenger/01_the_impossible_dream.txt --visual pygame --delay 0.2
```

Install Pygame with `make install` or `python3 -m pip install pygame`. The
Pygame module is loaded only when that mode is selected, so terminal mode also
works in headless environments.

### 1. Build a valid Python 3.10+ project

Your implementation must:

- be written in Python 3.10 or later,
- follow the flake8 style rules,
- use type hints throughout,
- pass mypy without errors,
- include docstrings for functions and classes,
- handle exceptions gracefully,
- clean up resources correctly with context managers,
- avoid crashes during evaluation.

### 2. Use object-oriented design

The project must be fully object-oriented. This is a key requirement and will be checked during peer review.

You should model at least:

- the drone fleet,
- zones and their metadata,
- connections/edges,
- the map/graph,
- the parser,
- the simulation engine,
- the pathfinding logic,
- visualization code.

### 3. Parse the map file correctly

The input file describes the network of zones and connections. Your parser must:

- read the number of drones from the first line with nb_drones:
- accept exactly one start_hub and one end_hub,
- accept unique zone names,
- accept valid integer coordinates,
- accept optional metadata inside brackets,
- reject invalid syntax clearly with an explicit error message,
- reject duplicate connections,
- reject invalid zone types,
- reject invalid capacity values,
- ignore comments beginning with #.

### 4. Implement the routing logic

Your solution must schedule paths for all drones while:

- distributing drones across multiple routes when needed,
- using waiting strategically when movement is blocked,
- avoiding path conflicts and deadlocks,
- respecting zone capacities and connection capacities,
- planning for movement cost and turn scheduling,
- adapting to different map structures.

The algorithm should take into account:

- path length,
- zone type cost,
- capacity limits,
- disjoint and overlapping routes,
- turn order and scheduling,
- eventual scalability for larger numbers of drones.

### 5. Simulate the movement turn by turn

The simulation is discrete and runs in turns.

At each simulation turn, each drone may:

- move to an adjacent connected zone if capacity allows,
- move toward a restricted zone through a connection, if the zone requires two turns,
- stay in place if needed,
- wait if blocked.

Important rule: a drone moving into a restricted zone must reach that destination in the next turn and cannot wait extra turns on the connection.

### 6. Provide visual feedback

The implementation must provide some kind of visual representation of movement, such as:

- colored terminal output,
- graphical display,
- or both.

This is not just cosmetic. It helps users understand the routing behavior, congestion, and simulation flow.

### 7. Produce a valid simulation output

The simulation output must be step-by-step and follow the assignment format.

Each turn is represented by one line. A line contains all movements for that turn, separated by spaces.

Movement syntax:

- D<ID>-<zone>
- D<ID>-<connection>

Examples:

- D1-hubA
- D3-corridorB
- D7-tunnelC

Rules:

- drones that do not move in a turn are omitted,
- drones that reach the end zone are considered delivered and no longer tracked,
- the simulation ends when all drones have reached the end zone.

### 8. Test your project

You are expected to create small test programs to validate functionality, even though they are not part of the final graded submission.

Use pytest or unittest and cover edge cases such as:

- invalid input parsing,
- blocked zones,
- capacity overflow,
- restricted zone movement,
- simultaneous movement scheduling,
- deadlocks or blocked paths.

## Important subject rules and mechanics

### Zone and connection syntax

Example map format:

```text
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

Important syntax rules:

- connection names cannot contain dashes in zone names,
- metadata is optional and enclosed in brackets,
- metadata can appear in any order,
- comments start with # and are ignored,
- zones and connections must be defined consistently.

### Zone types

Valid zone types are:

- normal: default, movement cost = 1 turn
- blocked: inaccessible, cannot be entered
- restricted: movement cost = 2 turns
- priority: movement cost = 1 turn, should be preferred by the route planner

### Zone metadata

Optional metadata includes:

- zone=<type> (default: normal)
- color=<value> (default: none)
- max_drones=<number> (default: 1)

### Connection metadata

Optional metadata includes:

- max_link_capacity=<number> (default: 1)

This means the same connection can support multiple drones at the same time only if its capacity allows it.

## Capacity rules

These are essential and must be respected at all times.

### Zone occupancy

- By default, a zone can contain at most one drone at any given turn.
- A zone with max_drones=N may contain up to N drones simultaneously.
- The start zone is a special exception: all drones may begin there together.
- The end zone is a special exception: multiple drones can arrive and be considered delivered there.
- Two drones may not enter the same zone on the same turn unless the zone capacity allows it.
- A drone may not move into a zone that would exceed its maximum capacity.

### Connection occupancy

- A connection can carry at most max_link_capacity drones at the same time.
- If a connection is full, drones cannot move through it together.

### Capacity timing rule

A very important behavioral rule:

- drones moving out of a zone free space for that same turn,
- a zone must have available capacity after those departures before another drone can enter,
- movement must be evaluated turn by turn with valid scheduling.

## Movement / turn mechanics

Each movement has a cost determined by the destination zone type:

- normal -> 1 turn
- restricted -> 2 turns
- priority -> 1 turn
- blocked -> impossible to enter

The simulation proceeds in discrete turns. A drone can:

- move to an adjacent zone,
- move along a connection toward a restricted zone,
- wait in place.

For restricted zones:

- the drone occupies the connection during transit,
- it must arrive at the destination during the next turn,
- it cannot wait on the connection for an empty space.

This is one of the easiest places to get the logic wrong.

## What to be aware of

### 1. No graph libraries

Libraries such as networkx are forbidden. Build your own graph logic.

### 2. No shortcuts on type safety

This project requires strict typing. Use mypy and avoid untyped defects.

### 3. Handle bad input safely

Invalid data must trigger a clear parsing error. This includes:

- invalid zone types,
- invalid capacity numbers,
- duplicate connections,
- missing start/end hubs,
- names with invalid syntax,
- malformed metadata.

### 4. Avoid deadlocks and invalid scheduling

A route that looks valid on paper can still fail if:

- multiple drones try to enter the same zone at once,
- a zone becomes temporarily full,
- a connection is saturated,
- a restricted-zone move blocks the next turn schedule,
- waiting is not coordinated correctly.

### 5. Optimization matters

The objective is to minimize total simulation turns. The fewer turns, the better the score.

### 6. Visual output is required

Even if the algorithm is good, the project should still provide readable runtime feedback to show where drones move and where congestion happens.

## Makefile requirements

Your project should include a Makefile with at least these rules:

- install
- run
- debug
- clean
- lint

The lint target must run:

```bash
flake8 .
mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
```

A stricter variant is optional:

```bash
flake8 .
mypy . --strict
```

## Scoring and performance goals

The performance of the solution is judged by the total number of simulation turns needed to move every drone from the start to the end.

Lower turn counts are better. A valid simulation must:

- respect all capacity constraints,
- avoid conflicts,
- route all drones without invalid movement,
- finish with all drones delivered.

Secondary criteria may include:

- number of drones moved per turn,
- average turns per drone,
- total path cost,
- quality of visual representation.

The subject provides benchmark targets such as:

- Easy maps: under 10 turns
- Medium maps: 10-30 turns
- Hard maps: under 60 turns
- Optional challenger maps: target can be as low as 45 turns or below

Examples from the assignment include:

- Linear path with 2 drones: target <= 6 turns
- Simple fork with 3 drones: target <= 6 turns
- Basic capacity with 4 drones: target <= 8 turns
- Dead end trap with 5 drones: target <= 15 turns
- Circular loop with 6 drones: target <= 20 turns
- Priority puzzle with 4 drones: target <= 12 turns
- Maze nightmare with 8 drones: target <= 45 turns
- Capacity hell with 12 drones: target <= 60 turns
- Ultimate challenge with 15 drones: target <= 35 turns

This is a useful optimization target to compare your implementation against.

## Submission and peer-review expectations

Your work will be reviewed not only by running the code but also by explaining it.

You should be prepared to justify:

- your design choices,
- your pathfinding strategy,
- your capacity management,
- your simulation scheduling,
- your object-oriented structure,
- your visual output,
- your testing and validation.

It is important to be able to explain how your code works, not just that it runs.

## Practical advice

To succeed, focus on these priorities:

1. Implement the parser carefully.
2. Model the graph and capacities explicitly.
3. Keep the simulation turn-based and deterministic.
4. Respect restricted-zone timing rules.
5. Build a route planner that accounts for congestion.
6. Validate edge cases with tests.
7. Add visualization to make the behavior understandable.
8. Keep the project clean and explainable.

## Final goal

The final project should be a complete drone routing simulator that can read a map, compute valid routes, coordinate drone movement under constraints, render the simulation clearly, and do so efficiently enough to meet the subject's performance expectations.

The key idea is simple: the solution must be valid, scalable, and optimized — but also understandable and reviewable.
