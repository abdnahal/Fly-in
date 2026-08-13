*This project has been created as part of the 42 curriculum by <abdnahal>.*

# Fly-in

A drone-fleet routing and traffic simulation. Given a map of zones connected by
links, Fly-in routes a fleet of drones from a single start zone to a single end
zone in the fewest possible discrete turns, while respecting every capacity and
movement constraint on the map. The turn-by-turn plan is printed to the terminal
and replayed as a pygame animation.

## Description

The problem is a capacity-constrained, multi-agent shortest-path scheduling
problem. Each turn every drone may move one step along a connection, but:

- a zone can hold only a limited number of drones at once (`max_drones`);
- a connection can carry only a limited number of drones at once
  (`max_link_capacity`);
- some zones cost more than one turn to cross, and some are impassable.

The goal is to deliver **all** drones to the end zone in the minimum number of
turns (the *makespan*). Fly-in solves this with a three-stage pipeline —
candidate-path search, fleet allocation, and an authoritative simulator — and
then visualises the result.

## Features

- Custom A\* pathfinder (no graph libraries) that returns several diverse routes.
- Makespan-minimising allocator that distributes drones across routes and scores
  each option with the real simulator.
- Turn-by-turn simulator enforcing zone capacity, connection capacity,
  multi-turn (restricted) zones, and simultaneous chain movement.
- Robust parser with clear error messages for malformed maps.
- Animated pygame visualisation driven by the simulator's own schedule.

## Instructions

**Requirements:** Python 3.10+ and `pip`. The visualisation uses `pygame`.

### Installation

```bash
make install        # installs pygame, flake8, mypy
```

Or manually:

```bash
pip install pygame
```

### Execution

```bash
make run                            # runs the default map (file.txt)
python3 -m src <map_file>           # run on any map
python3 -m src maps/easy/02_simple_fork.txt
```

### Development

```bash
make lint     # flake8 + mypy type checking
make clean    # remove __pycache__
```

## Map File Format

A map is a plain-text file. Lines beginning with `#` are comments and blank
lines are ignored. The structure is:

```
nb_drones: <positive integer>          # must be the first line

start_hub: <name> <x> <y> [metadata]   # exactly one, first zone declared
hub:       <name> <x> <y> [metadata]   # zero or more intermediate zones
end_hub:   <name> <x> <y> [metadata]   # exactly one, last zone declared

connection: <zoneA>-<zoneB> [metadata] # undirected link between two zones
```

- `<x> <y>` are integer coordinates (used by the heuristic and the display).
- Zone names may not contain `-` (the output format uses `-` as a separator).
- `start_hub` must be the first zone and `end_hub` the last; connections follow.

### Metadata

Hub metadata (all optional, space-separated inside `[ ]`):

| Key          | Values                                         | Default  |
|--------------|------------------------------------------------|----------|
| `zone`       | `normal`, `restricted`, `priority`, `blocked`  | `normal` |
| `max_drones` | positive integer                               | `1`      |
| `color`      | any pygame colour name                         | `White`  |

Connection metadata:

| Key                 | Values           | Default |
|---------------------|------------------|---------|
| `max_link_capacity` | positive integer | `1`     |

The start and end zones are treated as having unbounded capacity.

### Zone types and movement cost

| Zone type    | Effect                                                        |
|--------------|---------------------------------------------------------------|
| `normal`     | costs 1 turn to enter                                         |
| `restricted` | costs 2 turns: the drone rides the link for one turn, then **must** land the next turn |
| `priority`   | costs 1 turn, but is preferred by the pathfinder             |
| `blocked`    | impassable — never used in any route                         |

## Algorithm and Implementation Strategy

Fly-in is built as three cooperating layers, each a separate class. The design
principle is that **the simulator is the single source of truth**: the
pathfinder and allocator only *propose*, and every proposal is scored by
actually simulating it.

### 1. Pathfinding — `PathFinder` (custom A\*)

The graph is a plain adjacency dictionary (`{zone: [(neighbour, capacity)]}`)
built by the parser — no graph library is used.

`astar()` is a standard A\* search:

- **g-score** is the accumulated traversal cost of the zones on the path.
- **h-score** (heuristic) is the Euclidean distance from a zone to the goal,
  computed from the map coordinates. Euclidean distance is admissible for a
  geometric graph, so A\* stays efficient.
- The open set is a binary heap of `(f_score, count, zone)` tuples. `count` is a
  strictly increasing counter used purely as a **tie-breaker**: when two zones
  share an `f_score`, the heap compares the counters instead of trying to
  compare zone objects, which keeps ordering deterministic.
- Lazy deletion (`if f > f_score[current]: continue`) skips stale heap entries
  instead of paying to remove them.

A single shortest path is not enough, because concentrating every drone on one
route throttles them through that route's bottleneck. `get_paths()` therefore
runs A\* repeatedly, and after each run **penalises** the interior zones of the
path just found (their cost is raised) so the next run is nudged onto a
different route. It collects up to five diverse candidate routes.

### 2. Allocation — `Allocator` (makespan minimisation)

Given the candidate routes, the allocator decides **how many drones take which
route**. It ranks the routes by cost, then tries using the *K* cheapest routes
for K = 1, 2, 3, …, distributing drones round-robin across the chosen K. Each
distribution is scored by running the real simulator, and the assignment with
the lowest simulated makespan wins. Because scoring uses the authoritative
simulator rather than an estimate, the allocator automatically adapts to each
map's true bottlenecks instead of relying on a hand-tuned formula.

### 3. Simulation — `Simulator` (authoritative schedule)

`calculate_turns()` advances the fleet one discrete turn at a time and is the
sole enforcer of every rule:

- **Zone capacity** — a zone never exceeds its `max_drones` (start/end are
  unbounded).
- **Connection capacity** — a link never carries more than `max_link_capacity`
  drones in one turn.
- **Restricted zones** — modelled as a two-phase move: the drone occupies the
  connection on the transit turn and is forced to land on the next turn.
- **Chain movement (free-then-fill)** — within a single turn, drones closer to
  the goal are processed first, so a leader vacating a zone frees the slot for
  its follower in the *same* turn. This lets a whole column shift forward at
  once, which is essential to hitting the turn targets.

The simulator records one string per turn in `schedule`, which is what both the
terminal output and the visualiser consume.

### Complexity

Let *V* = zones, *E* = connections, *D* = drones, *P* = candidate paths (≤ 5).
A single A\* run is `O(E log V)`; path generation is `O(P · E log V)`. Each
simulation is roughly `O(turns · D)`, and the allocator runs up to *P*
simulations, giving `O(P · turns · D)` overall — comfortably fast for the
benchmark maps.

## Visual Representation

Running the program opens a pygame window that animates the simulation, giving
an immediate, intuitive picture of the plan that the raw turn list cannot.

- **Zones** are drawn as circles at their map coordinates, filled with the
  `color` from each zone's metadata (green start, red goal, and so on). Colour
  lets the viewer distinguish the start, goal, bottlenecks, and special zones at
  a glance.
- **Connections** are drawn as lines between zones, so the graph topology — the
  forks, merges, and bottlenecks — is visible directly.
- **Drones** are drawn as sprites and **animated smoothly between zones**. The
  display interpolates each drone's position across ~30 frames per turn, so
  instead of teleporting once per turn the drones glide along their links. This
  makes congestion, waiting, and the two-turn restricted-zone crossings easy to
  see as they happen.
- The animation is **driven entirely by the simulator's `schedule`**, so what
  you see is exactly the plan that is printed — the visualiser has no physics of
  its own and cannot disagree with the numbers.
- When every drone has arrived, the final frame is held so the finished state
  stays on screen until the window is closed.

Because the visualisation replays the authoritative schedule, it doubles as a
verification aid: capacity violations or routing mistakes would be visible as
overlapping drones or illegal moves.

## Example

### Input — `maps/easy/02_simple_fork.txt`

```
# Easy Level 2: Simple fork with two paths
nb_drones: 4

start_hub: start 0 0 [color=green]
hub: junction 1 0 [color=yellow max_drones=2]
hub: path_a 2 1 [color=blue]
hub: path_b 2 -1 [color=blue]
end_hub: goal 3 0 [color=red max_drones=3]

connection: start-junction [max_link_capacity=2]
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

### Command

```bash
python3 -m src maps/easy/02_simple_fork.txt
```

### Expected output

```
D0-junction D1-junction
D0-path_a D1-path_b D2-junction D3-junction
D0-goal D1-goal D2-path_a D3-path_b
D2-goal D3-goal
Simulation turns: 4
```

**Reading the output:** each line is one turn. A token `D<ID>-<zone>` means that
drone arrived in that zone this turn; a token `D<ID>-<zoneA>-<zoneB>` means the
drone is in flight along that connection (used when crossing into a restricted
zone). Drones that do not move on a given turn are omitted from that line. Here
all four drones reach the goal in **4 turns**: two drones stream through the
`junction` (capacity 2) each turn and fan out across the two paths to the goal
(capacity 3).

## Resources

Classic references consulted for this project:

- Hart, Nilsson & Raphael, *A Formal Basis for the Heuristic Determination of
  Minimum Cost Paths* (1968) — the original A\* paper.
- Amit Patel, *Introduction to A\** — Red Blob Games:
  https://www.redblobgames.com/pathfinding/a-star/introduction.html
- Python `heapq` documentation:
  https://docs.python.org/3/library/heapq.html
- pygame documentation: https://www.pygame.org/docs/
- The concept of penalising found paths to obtain diverse alternatives is
  related to *k-shortest-paths* and edge-penalty route-diversification methods.

### Use of AI

AI (Claude) was used as an assistant during development, specifically for:

- **Testing and edge-case discovery** — generating adversarial map inputs to
  stress the parser (malformed metadata, duplicate hubs/connections, invalid
  capacities) and the simulator (capacity invariants, restricted-zone cadence),
  and cross-checking results against the benchmark targets.
- **Debugging** — diagnosing a display bug where all animation frames aliased a
  single state dictionary, and identifying parser error-handling gaps.
- **Documentation** — assistance drafting and structuring this README.

All core design and implementation decisions — the three-layer architecture, the
A\* pathfinder, the simulation model, and the allocation strategy — were made and
written by the author; AI was used to review, test, and document that work.



