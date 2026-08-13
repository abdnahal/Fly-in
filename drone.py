from typing import List, Optional
from random import choice


class Drone:
    """Represents an individual drone operating in the network.

    A drone carries an assigned route from the start zone to the goal zone.
    It tracks its current location index, visual interpolation properties
    (like speed and progress parameter t), and scheduling details.

    Attributes:
        id: Unique string identifier of the drone (e.g., "D1").
        path: Ordered list of zone/hub names representing the route this
            drone travels.
        segment_index: Current segment/leg of the route.
        t: Animation parameter indicating current position on a path segment.
        speed: Rate of progress for visualization animation.
        turns: Number of simulator turns elapsed.
        current: A string representation of the current connection/segment.
        state: State descriptor of the drone (e.g., "waiting", "flying").
    """

    def __init__(
        self, drone_id: int, paths: List[List[str]],
        assigned: Optional[List[str]] = None
    ):
        """Initialize a Drone instance.

        Args:
            drone_id: Numeric identifier for the drone.
            paths: A list of default candidate paths to choose from if
                no specific assignment is given.
            assigned: An optional predefined path to assign to the drone.
        """
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
