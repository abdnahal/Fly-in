# Fly-in: Drone Routing System - Complete Tutorial

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Design](#architecture--design)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Algorithm Recommendations](#algorithm-recommendations)
5. [Library Suggestions](#library-suggestions)
6. [Testing & Debugging](#testing--debugging)
7. [Optimization Strategies](#optimization-strategies)

---

## Project Overview

### Goal
Route multiple drones from a start zone to an end zone in the minimum number of simulation turns while respecting:
- Zone occupancy constraints (max_drones per zone)
- Connection capacity limits (max_link_capacity)
- Zone type movement costs (normal=1, restricted=2, priority=1)
- Blocked zones (impassable)

### Key Constraints
- **No graph libraries** (networkx, graphlib forbidden)
- **100% typesafe** (mypy strict mode)
- **Fully object-oriented**
- **Flake8 compliant**

### Input Format
```
nb_drones: N
start_hub: name x y [metadata]
end_hub: name x y [metadata]
hub: name x y [metadata]
connection: zone1-zone2 [metadata]
```

---

## Architecture & Design

### Recommended Class Structure

```python
# Core data structures
├── Zone (or Hub)
│   ├── name: str
│   ├── coord: Tuple[int, int]
│   ├── zone_type: ZoneType
│   ├── max_drones: int
│   └── metadata: Dict[str, Any]
│
├── Connection (or Edge)
│   ├── zone1: str
│   ├── zone2: str
│   ├── max_link_capacity: int
│   └── metadata: Dict[str, Any]
│
├── Graph
│   ├── zones: Dict[str, Zone]
│   ├── connections: Dict[str, Connection]
│   ├── adjacency: Dict[str, List[str]]
│   └── methods: get_neighbors(), get_path(), etc.
│
├── Drone
│   ├── drone_id: int
│   ├── current_zone: str
│   ├── destination: str
│   ├── path: List[str]
│   ├── status: DroneStatus
│   └── turns_in_transit: int
│
├── Simulation
│   ├── drones: List[Drone]
│   ├── graph: Graph
│   ├── turn: int
│   ├── zone_occupancy: Dict[str, int]
│   └── methods: step(), move_drone(), check_capacity()
│
└── ConfigParser
    ├── parse(): Dict
    └── _parse_metadata(): Dict
```

---

## Step-by-Step Implementation

### **Step 1: Parser Implementation**

**What to do:**
1. Read the configuration file line by line
2. Parse `nb_drones` directive
3. Parse zone definitions (start_hub, end_hub, hub)
4. Parse connection definitions
5. Extract and validate metadata

**Key points:**
- Use regex for metadata extraction (already fixed in your parser.py)
- Validate zone types: normal, blocked, restricted, priority
- Ensure numeric values are integers where needed
- Handle comments (#) and empty lines

**Example reference:**
```python
def _parse_metadata(self, text: str) -> Dict[str, object]:
    """Extract key=value pairs from [brackets]"""
    metadata: Dict[str, object] = {}
    match = re.search(r"\[(.*?)\]", text)
    if not match:
        return metadata
    for key, value in re.findall(
        r"([A-Za-z_][A-Za-z0-9_]*)=([^\s\]]+)", 
        match.group(1)
    ):
        metadata[key] = int(value) if value.isdigit() else value
    return metadata
```

---

### **Step 2: Build Core Data Structures**

**Zone/Hub Class:**
```python
from enum import Enum
from typing import Dict, Tuple, Any

class ZoneType(Enum):
    NORMAL = 1
    BLOCKED = float('inf')  # Inaccessible
    RESTRICTED = 2
    PRIORITY = 1

class Zone:
    def __init__(
        self, 
        name: str, 
        coord: Tuple[int, int],
        zone_type: ZoneType = ZoneType.NORMAL,
        max_drones: int = 1,
        metadata: Dict[str, Any] | None = None
    ):
        self.name = name
        self.coord = coord
        self.zone_type = zone_type
        self.max_drones = max_drones
        self.metadata = metadata or {}
```

**Connection/Edge Class:**
```python
class Connection:
    def __init__(
        self, 
        zone1: str, 
        zone2: str,
        max_link_capacity: int = 1,
        metadata: Dict[str, Any] | None = None
    ):
        self.zone1 = zone1
        self.zone2 = zone2
        self.max_link_capacity = max_link_capacity
        self.metadata = metadata or {}
```

**Graph Class:**
```python
class Graph:
    def __init__(self):
        self.zones: Dict[str, Zone] = {}
        self.connections: Dict[str, Connection] = {}
        self.adjacency: Dict[str, List[str]] = {}
        self.start_zone: str | None = None
        self.end_zone: str | None = None

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

    def add_connection(self, conn: Connection) -> None:
        key = f"{conn.zone1}-{conn.zone2}"
        self.connections[key] = conn
        # Bidirectional
        self.adjacency[conn.zone1].append(conn.zone2)
        self.adjacency[conn.zone2].append(conn.zone1)

    def get_neighbors(self, zone_name: str) -> List[str]:
        return self.adjacency.get(zone_name, [])

    def is_blocked(self, zone_name: str) -> bool:
        return self.zones[zone_name].zone_type == ZoneType.BLOCKED
```

**Drone Class:**
```python
from enum import Enum

class DroneStatus(Enum):
    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"  # Multi-turn movement
    DELIVERED = "delivered"

class Drone:
    def __init__(self, drone_id: int, start_zone: str):
        self.drone_id = drone_id
        self.current_zone = start_zone
        self.destination: str | None = None
        self.path: List[str] = []
        self.status = DroneStatus.WAITING
        self.turns_in_transit = 0
        self.total_turns = 0
```

---

### **Step 3: Implement Pathfinding**

**Recommended Algorithms (in order of priority):**

#### **Option A: BFS (Best for unweighted paths)**
```python
def bfs(start: str, end: str, graph: Graph) -> List[str] | None:
    """Breadth-first search - finds shortest path by number of hops"""
    from collections import deque
    
    queue: deque = deque([(start, [start])])
    visited: set = {start}
    
    while queue:
        node, path = queue.popleft()
        
        if node == end:
            return path
        
        for neighbor in graph.get_neighbors(node):
            if (neighbor not in visited and 
                not graph.is_blocked(neighbor)):
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    return None
```

#### **Option B: Dijkstra (For weighted paths with movement costs)**
```python
def dijkstra(start: str, end: str, graph: Graph) -> List[str] | None:
    """Dijkstra's algorithm - finds lowest-cost path"""
    import heapq
    
    distances: Dict[str, float] = {z: float('inf') 
                                    for z in graph.zones}
    distances[start] = 0
    predecessors: Dict[str, str | None] = {z: None 
                                            for z in graph.zones}
    
    pq: list = [(0, start)]
    visited: set = set()
    
    while pq:
        current_dist, current = heapq.heappop(pq)
        
        if current in visited:
            continue
        visited.add(current)
        
        if current == end:
            # Reconstruct path
            path = []
            node = end
            while node is not None:
                path.append(node)
                node = predecessors[node]
            return path[::-1]
        
        for neighbor in graph.get_neighbors(current):
            if graph.is_blocked(neighbor):
                continue
            
            # Movement cost based on zone type
            cost = graph.zones[neighbor].zone_type.value
            new_dist = current_dist + cost
            
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                predecessors[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))
    
    return None
```

#### **Option C: A* (For heuristic-guided pathfinding)**
Best when you have coordinates available (Euclidean distance heuristic).

```python
def heuristic(zone1: str, zone2: str, graph: Graph) -> float:
    """Euclidean distance heuristic"""
    x1, y1 = graph.zones[zone1].coord
    x2, y2 = graph.zones[zone2].coord
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

def a_star(start: str, end: str, graph: Graph) -> List[str] | None:
    """A* pathfinding - combines Dijkstra with heuristic"""
    import heapq
    
    open_set: list = [(0, start)]
    came_from: Dict[str, str | None] = {}
    g_score: Dict[str, float] = {z: float('inf') 
                                  for z in graph.zones}
    g_score[start] = 0
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current == end:
            # Reconstruct path
            path = [current]
            while current in came_from and came_from[current]:
                current = came_from[current]
                path.append(current)
            return path[::-1]
        
        for neighbor in graph.get_neighbors(current):
            if graph.is_blocked(neighbor):
                continue
            
            cost = graph.zones[neighbor].zone_type.value
            tentative_g = g_score[current] + cost
            
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = (tentative_g + 
                          heuristic(neighbor, end, graph))
                heapq.heappush(open_set, (f_score, neighbor))
    
    return None
```

---

### **Step 4: Build Simulation Engine**

**Core Logic:**

```python
class Simulation:
    def __init__(self, graph: Graph, num_drones: int):
        self.graph = graph
        self.drones = [Drone(i, graph.start_zone) 
                       for i in range(num_drones)]
        self.turn = 0
        self.zone_occupancy: Dict[str, int] = {}
        self.connection_occupancy: Dict[str, int] = {}
        self.history: List[str] = []
        
        # Initialize occupancy
        self._reset_occupancy()
    
    def _reset_occupancy(self) -> None:
        """Reset capacity counters"""
        for zone_name in self.graph.zones:
            self.zone_occupancy[zone_name] = 0
        
    def _can_move_to_zone(
        self, 
        drone: Drone, 
        target_zone: str
    ) -> bool:
        """Check if drone can move to zone"""
        zone = self.graph.zones[target_zone]
        current_occupancy = self.zone_occupancy[target_zone]
        return current_occupancy < zone.max_drones
    
    def _can_use_connection(self, zone1: str, zone2: str) -> bool:
        """Check connection capacity"""
        key = f"{zone1}-{zone2}"
        reverse_key = f"{zone2}-{zone1}"
        
        # Get connection (works both directions)
        conn_key = (key if key in self.graph.connections 
                    else reverse_key)
        
        if conn_key not in self.graph.connections:
            return True
        
        conn = self.graph.connections[conn_key]
        occupancy = self.connection_occupancy.get(conn_key, 0)
        return occupancy < conn.max_link_capacity
    
    def step(self) -> List[str]:
        """Execute one simulation turn"""
        self.turn += 1
        movements: List[str] = []
        
        # Reset occupancy for this turn
        self._reset_occupancy()
        
        # Calculate new positions
        for drone in self.drones:
            if drone.status == DroneStatus.DELIVERED:
                continue
            
            if not drone.path:
                # Compute path if drone doesn't have one
                drone.path = self._compute_path_for_drone(drone)
            
            if drone.path and len(drone.path) > 1:
                next_zone = drone.path[1]
                
                if self._can_move_to_zone(drone, next_zone):
                    if self._can_use_connection(
                        drone.current_zone, next_zone
                    ):
                        drone.current_zone = next_zone
                        drone.path.pop(0)
                        
                        if drone.current_zone == self.graph.end_zone:
                            drone.status = DroneStatus.DELIVERED
                        
                        movements.append(
                            f"D{drone.drone_id}-{next_zone}"
                        )
                        self.zone_occupancy[next_zone] += 1
        
        self.history.append(" ".join(movements))
        return movements
    
    def _compute_path_for_drone(self, drone: Drone) -> List[str]:
        """Use pathfinding to find route"""
        # Use A* or Dijkstra
        path = dijkstra(
            drone.current_zone, 
            self.graph.end_zone, 
            self.graph
        )
        return path or [drone.current_zone]
    
    def run(self) -> Tuple[int, List[str]]:
        """Run simulation until all drones delivered"""
        max_turns = 1000  # Safety limit
        
        while any(d.status != DroneStatus.DELIVERED 
                  for d in self.drones) and self.turn < max_turns:
            self.step()
        
        return self.turn, self.history
```

---

### **Step 5: Visual Representation**

**Option A: Terminal Output (Recommended for MVP)**

```python
def print_grid(
    self, 
    graph: Graph, 
    drones: List[Drone],
    turn: int
) -> None:
    """ASCII visualization of drone positions"""
    # Find bounds
    xs = [z.coord[0] for z in graph.zones.values()]
    ys = [z.coord[1] for z in graph.zones.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    # Create grid
    grid = [[' ' for _ in range(max_x + 1)] 
            for _ in range(max_y + 1)]
    
    # Place zones
    zone_map = {}
    for zone in graph.zones.values():
        x, y = zone.coord
        symbol = self._get_zone_symbol(zone)
        grid[y][x] = symbol
        zone_map[(x, y)] = zone.name
    
    # Place drones
    for drone in drones:
        zone = graph.zones[drone.current_zone]
        x, y = zone.coord
        grid[y][x] = f"D{drone.drone_id}"
    
    print(f"\n=== Turn {turn} ===")
    for row in grid:
        print("".join(row))

def _get_zone_symbol(self, zone: Zone) -> str:
    """Symbol for zone types"""
    symbols = {
        ZoneType.NORMAL: "●",
        ZoneType.BLOCKED: "✕",
        ZoneType.RESTRICTED: "⚠",
        ZoneType.PRIORITY: "★"
    }
    return symbols.get(zone.zone_type, "●")
```

**Option B: Colored Terminal Output**

Use the `colorama` library for terminal colors.

```python
from colorama import Fore, Back, Style

def print_colored_status(self, turn: int, movements: List[str]) -> None:
    """Print colored turn summary"""
    print(f"\n{Fore.CYAN}Turn {turn}:{Style.RESET_ALL}")
    for move in movements:
        print(f"  {Fore.GREEN}{move}{Style.RESET_ALL}")
    print()
```

**Option C: Graphical Interface (Optional)**

Use `pygame` or `tkinter` for a more sophisticated display:
- Draw zones as circles/rectangles at their coordinates
- Draw connections as lines between zones
- Animate drone movements
- Show zone occupancy as labels

---

### **Step 6: Multi-Drone Scheduling**

**The Core Challenge:** Schedule multiple drones efficiently.

**Strategy 1: Greedy Pathfinding**
- Each drone computes shortest path independently
- May cause collisions; resolve with queue/wait

**Strategy 2: Conflict Resolution**
```python
def resolve_conflicts(self) -> None:
    """If multiple drones want same zone, queue them"""
    target_counts: Dict[str, List[Drone]] = {}
    
    for drone in self.drones:
        if drone.path and len(drone.path) > 1:
            target = drone.path[1]
            if target not in target_counts:
                target_counts[target] = []
            target_counts[target].append(drone)
    
    # For zones at capacity, make drones wait
    for zone, drones_wanting in target_counts.items():
        max_capacity = self.graph.zones[zone].max_drones
        if len(drones_wanting) > max_capacity:
            for drone in drones_wanting[max_capacity:]:
                # Drone waits this turn
                pass
```

**Strategy 3: Multi-Path Routing (Advanced)**
- Compute multiple disjoint paths
- Distribute drones across paths
- Use BFS to find edge-disjoint paths

---

## Algorithm Recommendations

### For Small Maps (< 10 zones, < 5 drones):
1. **BFS** for pathfinding
2. **Greedy scheduling** (first-come-first-served)
3. Simple capacity checking

### For Medium Maps (10-20 zones, 5-15 drones):
1. **Dijkstra** for weighted paths (respects movement costs)
2. **Queue-based conflict resolution**
3. **Backup path computation** if primary blocked

### For Large/Complex Maps (20+ zones, 15+ drones):
1. **A*** with Euclidean heuristic
2. **Multi-path routing** with disjoint path finding
3. **Load balancing** across alternative routes
4. **Priority queuing** for capacity-constrained zones
5. Cache pathfinding results

---

## Library Suggestions

### Required (Built-in):
- `typing` - Type hints (mandatory)
- `enum` - For ZoneType, DroneStatus
- `collections` - deque for BFS
- `heapq` - For Dijkstra/A*
- `re` - For metadata parsing

### Recommended (Install with pip):
```bash
pip install colorama  # Terminal colors
pip install mypy      # Type checking (mandatory)
pip install flake8    # Linting (mandatory)

# Optional (for visualization)
pip install pygame    # Graphics
pip install matplotlib  # Plotting routes
```

### Explicitly Forbidden:
- `networkx` - Graph library
- `graphlib` - Graph utilities
- Any other pre-built graph/pathfinding libs

---

## Testing & Debugging

### Unit Tests to Write:

```python
def test_parser_metadata_extraction():
    """Verify metadata parsing"""
    parser = ConfigParser("test.txt", {})
    assert parser.data["hubs"]["hub"]["metadata"]["zone"] == "priority"

def test_bfs_finds_path():
    """Verify BFS returns shortest path"""
    graph = Graph()
    # Add zones...
    path = bfs("start", "end", graph)
    assert path is not None
    assert path[0] == "start"
    assert path[-1] == "end"

def test_zone_capacity_constraint():
    """Verify zones respect max_drones"""
    sim = Simulation(graph, 2)
    # Try to place 3 drones in zone with max_drones=2
    # Should queue one

def test_blocked_zone_avoided():
    """Verify pathfinding avoids blocked zones"""
    graph = Graph()
    # Create path with blocked zone in middle
    path = dijkstra("start", "end", graph)
    assert "blocked_zone" not in path

def test_restricted_zone_cost():
    """Verify restricted zones cost 2 turns"""
    # Drone movement through restricted zone takes extra turn
    pass

def test_connection_capacity():
    """Verify connection max_link_capacity respected"""
    # Only N drones should traverse same connection per turn
    pass
```

### Debug Techniques:

```python
# Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Print state after each turn
for turn in range(num_turns):
    print(f"Turn {turn}: {[d.current_zone for d in drones]}")
    sim.step()

# Export path for visualization
def export_paths(self) -> Dict[int, List[str]]:
    return {d.drone_id: d.path for d in self.drones}
```

---

## Optimization Strategies

### 1. **Path Caching**
```python
path_cache: Dict[Tuple[str, str], List[str]] = {}

def get_cached_path(start: str, end: str) -> List[str] | None:
    key = (start, end)
    if key not in path_cache:
        path_cache[key] = dijkstra(start, end, graph)
    return path_cache[key]
```

### 2. **Batched Pathfinding**
Compute paths for all unrouted drones at once, before simulation step.

### 3. **Priority Zones**
Prefer priority zones in pathfinding (same cost but heuristic bonus).

### 4. **Load Balancing**
```python
def distribute_drones_across_paths(wai_drones: List[Drone]) -> None:
    """Find K edge-disjoint paths and assign drones"""
    paths = find_multiple_disjoint_paths(
        graph.start_zone, 
        graph.end_zone, 
        num_paths=len(waiting_drones)
    )
    for drone, path in zip(waiting_drones, paths):
        drone.path = path
```

### 5. **Early Termination**
If all drones reach end zone, stop simulation immediately.

### 6. **Memoization for Zone Accessibility**
```python
reachable_from: Dict[str, set] = {}

def precompute_reachability(graph: Graph) -> Dict[str, set]:
    """Which zones can reach end_zone?"""
    for zone in graph.zones:
        reachable_from[zone] = compute_reachable(zone, graph)
    return reachable_from
```

---

## Performance Targets

### Expected Results:
- **Easy maps**: < 10 turns
- **Medium maps**: 10-30 turns
- **Hard maps**: < 60 turns
- **Challenger**: < 45 turns (optional)

### Profiling:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run simulation
sim.run()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions
```

---

## Common Pitfalls to Avoid

1. ❌ **Not respecting zone occupancy** → Drones collide
2. ❌ **Letting drones get stuck** → Infinite loops
3. ❌ **No deadlock detection** → Drones wait forever
4. ❌ **Recalculating paths every turn** → O(n²) complexity
5. ❌ **Not handling restricted zones properly** → Movement stays stuck in transit
6. ❌ **Ignoring connection capacity** → Invalid simulation
7. ❌ **Using blocked zones** → Paths invalid

---

## Checklist for Completion

- [ ] Parser reads and validates all input
- [ ] Graph structure built correctly
- [ ] Zone types and costs implemented
- [ ] BFS or Dijkstra pathfinding working
- [ ] Simulation engine respect all constraints
- [ ] Multi-drone scheduling with no collisions
- [ ] Visual output (terminal + optional graphics)
- [ ] Performance meets targets
- [ ] All type hints and mypy passing
- [ ] Flake8 compliant
- [ ] Tests written and passing
- [ ] README.md with algorithm description
- [ ] Makefile with install/run/lint tasks
- [ ] Git repo clean and well-organized

---

## Next Steps

1. **Start with the parser** (already done!)
2. **Build data structures** (Zone, Connection, Graph)
3. **Implement one pathfinding algorithm** (BFS first)
4. **Build basic simulation**
5. **Add multi-drone scheduling**
6. **Implement visualization**
7. **Optimize and test**
8. **Document and submit**

Good luck! 🚁

