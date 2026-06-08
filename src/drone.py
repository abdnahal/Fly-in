from typing import List
from random import choice


class Drone:
    def __init__(self, drone_id: int, paths: List[str]):
        self.id = f"D{drone_id}"
        self.path = choice(paths)
        self.segment_index = 0
        self.t = choice([0.0, 0.1, 0.2, 0.06, 0.05, 0.25])
        self.speed = choice([0.01, 0.02, 0.009, 0.015, 0.021, 0.025])
        self.turns = 0
        self.current = f"{self.path[0]}-{self.path[1]}"
        self.state = "waiting"
