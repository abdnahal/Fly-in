from typing import Dict, List, Tuple


class Hub:
    def __init__(self, name: str, coord: Tuple[int], connections: List[Hub]):
        self.name = name
        self.connections = connections
        self.coord = coord