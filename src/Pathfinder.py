from hub import Hub
from drone import Drone
from typing import List, Dict, Tuple
import heapq
import math
import copy


class PathFinder:
    def __init__(self, adjacency: Dict[str, Tuple], hubs: Dict[str, Dict],
                 drones: List[Drone]):
        self.adjacency = adjacency
        self.hubs = hubs
        self.drones = drones

    def _heuristic(self, zone_a: Tuple[int],
                   zone_b: Tuple[int]) -> float:
        return math.sqrt((zone_a[0] - zone_b[0]) ** 2 +
                         (zone_a[1] - zone_b[1]) ** 2)

    def _path(self, end: Hub, came_from: Dict[str, str]):
        node = end.name
        path = []
        while node:
            path.append(node)
            node = came_from[node]
        return path[::-1]

    def astar(self, start: Hub, end: Hub, zones: Dict[str, Hub]) -> List[Hub]:
        heap = []
        heapq.heappush(heap, (self._heuristic(start.coord, end.coord),
                              0, start.name))
        g_score = {hub: float("inf") for hub in zones.keys()}
        f_score = {hub: float("inf") for hub in zones.keys()}
        g_score[start.name] = 0
        f_score[start.name] = g_score[start.name] + heap[0][0]
        came_from = {}
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
                    h = self._heuristic(zones[neighbor[0]].coord,
                                        end.coord)
                    f_score[neighbor[0]] = g + h
                    heapq.heappush(heap, (f_score[neighbor[0]], count,
                                          neighbor[0]))
                    count += 1
        return None

    def get_paths(self, start: Hub, end: Hub) -> List[List[str]]:
        paths = []
        counter = 0
        hubs = copy.deepcopy(self.hubs)
        # paths_req = self.drones / 5 if self.drones >= 5 else 1
        while 1:
            path = self.astar(start, end, hubs)
            if path is None:
                return paths
            if path not in paths:
                paths.append(path)
                for i, hub in enumerate(path):
                    if i == 0 or i == len(path) - 1:
                        continue
                    hubs[hub].cost += 2
                counter = 0
            else:
                counter += 1
            if len(paths) >= 5 or len(paths) == self.drones:
                return paths
            if counter >= 100:
                break
        return paths
