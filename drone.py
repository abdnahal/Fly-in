from typing import List, Optional
from random import choice


class Drone:
    def __init__(
        self, drone_id: int, paths: List[List[str]],
        assigned: Optional[List[str]] = None
    ):
        self.id = f"D{drone_id}"
        # Prefer an explicitly assigned path (deterministic routing from the
        # Allocator); fall back to a random pick only when none is given.
        self.path = assigned if assigned is not None else choice(paths)
        self.segment_index = 0
        self.t = choice([0.0, 0.1, 0.2, 0.06, 0.05, 0.25])
        self.speed = choice([0.015, 0.02, 0.013, 0.017, 0.021, 0.025])
        self.turns = 0
        self.current = f"{self.path[0]}-{self.path[1]}"
        self.state = "waiting"
