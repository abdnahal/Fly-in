from typing import List
from random import choice


class Drone:
    def __init__(self, drone_id: int, path: List[str]):
        self.id = drone_id
        self.path = path
        self.segment_index = 0
        self.t = choice([0.0, 0.1, 0.2, 0.06, 0.05, 0.25])
        self.speed = choice([0.01, 0.02, 0.008, 0.015, 0.0025])
        self.turns = 0
