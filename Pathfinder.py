from hub import Hub
from typing import List, Dict, Tuple
from collections import deque


class PathFinder:
    def __init__(self, adjacency: Dict[str, Tuple], hubs: Dict[str, Dict]):
        self.adjacency = adjacency
        self.hubs = hubs

    def astar(self) -> List[Hub]:
        came_from = deque([])
        seen = []
        current = self.adjacency.keys()[0]
        came_from.append(current)
        while came_from:
            current = self.adjacency[current]