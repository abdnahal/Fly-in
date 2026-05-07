from hub import Hub
from typing import List, Dict, Tuple
import heapq
import math


class PathFinder:
    def __init__(self, adjacency: Dict[str, Tuple], hubs: Dict[str, Dict]):
        self.adjacency = adjacency
        self.hubs = hubs

    def _heuristic(self, zone_a: Dict[str, Dict],
                   zone_b: Dict[str, Dict]) -> float:
        return math.sqrt((zone_a['coord'][0] - zone_b['coord'][0]) ** 2 +
                         (zone_a['coord'][1] - zone_b['coord'][1]) ** 2)

    def astar(self, start: Dict[str, Dict], end: Dict[str, Dict]) -> List[Hub]:
        heap = heapq(self._heuristic(start, end), 0,
                     self.adjacency.keys().tolist()[0])
        g_score, counter = 0
        came_from = set()
        while heap:
            