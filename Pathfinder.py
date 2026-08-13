from hub import Hub
from typing import List, Dict, Tuple, Optional
import heapq
import math
import copy


class PathFinder:
    """Computes routing paths across the hub network.

    Uses the A* algorithm combined with path penalties to find multiple
    candidate routes from start to end hub to help optimize drone flow
    and reduce congestion.

    Attributes:
        adjacency: Mapping from zone name to a list of connection
            endpoints and capacities.
        hubs: Dictionary of raw or simulated hub/zone configurations.
        drones: Total number of drones to optimize paths for.
    """

    def __init__(
        self, adjacency: Dict[str, List[Tuple[str, int]]],
        hubs: Dict[str, Hub],
        drones: int
    ):
        """Initialize the PathFinder instance.

        Args:
            adjacency: Mapping from zone name to a list of tuples containing
                neighboring zones and capacities.
            hubs: Mapping of zone name to Hub instances.
            drones: Number of drones in the simulation.
        """
        self.adjacency = adjacency
        self.hubs = hubs
        self.drones = drones

    def _heuristic(
        self, zone_a: Tuple[int, int], zone_b: Tuple[int, int]
    ) -> float:
        """Calculate the straight-line (Euclidean) distance between
        two zone coordinates.

        Args:
            zone_a: Coordinate of the first zone (x, y).
            zone_b: Coordinate of the second zone (x, y).

        Returns:
            The Euclidean distance between the two coordinates.
        """
        return math.sqrt((zone_a[0] - zone_b[0]) ** 2 + (
            zone_a[1] - zone_b[1]) ** 2)

    def _path(
        self, end: Hub, came_from: Dict[str, Optional[str]]
    ) -> List[str]:
        """Reconstruct the path from the end zone back to the start zone.

        Args:
            end: The destination Hub.
            came_from: Dictionary mapping each zone back to its predecessor.

        Returns:
            The reconstructed list of zone names in start-to-end order.
        """
        node: Optional[str] = end.name
        path: List[str] = []
        while node:
            path.append(node)
            node = came_from[node]
        return path[::-1]

    def astar(
        self, start: Hub, end: Hub, zones: Dict[str, Hub]
    ) -> Optional[List[str]]:
        """Run the A* search algorithm to find the lowest-cost path from
        start to end hub.

        The path cost incorporates specific zone traversal costs (such as
        blocked or restricted).

        Args:
            start: The start Hub.
            end: The destination Hub.
            zones: Current mapping of zone names to Hubs (which may contain
                path penalties).

        Returns:
            A list of zone names representing the path if found,
            otherwise None.
        """
        heap: List[Tuple[float, int, str]] = []
        heapq.heappush(heap, (self._heuristic(start.coord, end.coord), 0,
                              start.name))
        g_score = {hub: float("inf") for hub in zones.keys()}
        f_score = {hub: float("inf") for hub in zones.keys()}
        g_score[start.name] = 0
        f_score[start.name] = g_score[start.name] + heap[0][0]
        came_from: Dict[str, Optional[str]] = {}
        came_from[start.name] = None
        # seen = set()
        count = 1
        while heap:
            f, _, current = heapq.heappop(heap)
            if current == end.name:
                return self._path(end, came_from)
            if f > f_score[current]:
                continue
            for neighbor in self.adjacency[current]:
                g = g_score[current] + zones[current].cost
                if g < g_score[neighbor[0]]:
                    came_from[neighbor[0]] = current
                    g_score[neighbor[0]] = g
                    if zones[neighbor[0]].cost == 0.8:
                        h: float = 0
                    else:
                        h = self._heuristic(zones[neighbor[0]].coord,
                                            end.coord)
                    f_score[neighbor[0]] = g + h
                    heapq.heappush(heap, (f_score[neighbor[0]], count,
                                          neighbor[0]))
                    count += 1
        return None

    def get_paths(self, start: Hub, end: Hub) -> List[List[str]]:
        """Find up to 5 alternative candidate paths between start and end.

        This method iteratively runs A* and applies penalties (increasing
        Hub cost) to zones on the chosen paths to encourage the discovery
        of diverse alternative routes.

        Args:
            start: The starting Hub.
            end: The destination Hub.

        Returns:
            A list of paths, where each path is a list of zone names.
        """
        paths: List[List[str]] = []
        hubs = copy.deepcopy(self.hubs)
        for _ in range(100):
            path = self.astar(start, end, hubs)
            if path is None:
                return paths
            if path not in paths:
                paths.append(path)
                for i, hub in enumerate(path):
                    if i == 0 or i == len(path) - 1:
                        continue
                    hubs[hub].cost += 2
            if len(paths) >= 5 or len(paths) == self.drones:
                return paths
        return paths
