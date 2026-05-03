from hub import Hub
from typing import List
from collections import defaultdict


class PathFinder:
    def __init__(self, connections: List[set]):
        self.connections = connections

    def astar(self) -> List[Hub]:
