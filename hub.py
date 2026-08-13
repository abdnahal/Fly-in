from typing import Dict, Any


class Hub:
    """Represents a hub (or zone) in the drone flight network.

    A hub holds coordinate and metadata properties. It manages cost
    calculations for pathfinding based on its zone type (e.g., normal,
    blocked, restricted, priority) and holds representation color details
    for the visualization display.

    Attributes:
        hub: Dictionary containing raw hub configuration data.
        name: The unique string identifier/name of the hub.
        coord: A 2-tuple (x, y) representing the coordinate of the hub.
        metadata: Metadata dictionary holding extra attributes like zone
            type or capacity.
        start: True if this is the designated starting hub.
        end: True if this is the designated ending/goal hub.
        cost: Routing weight/cost for pathfinding based on the zone type.
        color: Visual display color name for drawing this hub.
    """

    def __init__(self, name: str, hub: Dict[str, Any],
                 start: bool, end: bool):
        """Initialize a Hub instance.

        Args:
            name: Unique name/identifier of the hub.
            hub: Raw dictionary containing configuration (coordinates,
                metadata).
            start: Flag indicating if this hub is the start zone.
            end: Flag indicating if this hub is the end/goal zone.
        """
        self.hub = hub
        self.name = name
        self.coord = hub["coord"]
        self.metadata = hub.get("metadata", {})
        self.start = start
        self.end = end
        if name == "start" or name == "goal":
            self.cost: float = 0
        elif "zone" in self.metadata.keys():
            if self.metadata["zone"] == "blocked":
                self.cost = float("inf")
            elif self.metadata["zone"] == "priority":
                self.cost = 0.8
            else:
                self.cost = 2 if self.metadata["zone"] == "restricted" else 1
        else:
            self.cost = 1
        if self.metadata.get("color"):
            self.color = self.metadata["color"]
        else:
            self.color = "White"
