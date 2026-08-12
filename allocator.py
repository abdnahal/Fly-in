from typing import Dict, List, Tuple

from .hub import Hub
from .drone import Drone
from .simulator import Simulator


class Allocator:
    """Assign each drone to a path so the fleet clears in the fewest turns.

    The pathfinder yields several candidate routes from start to goal. How
    the fleet is *distributed* across those routes dominates the turn count,
    because the map's real bottlenecks are shared:

      * one drone per turn can be injected through the start gate, and
      * restricted-zone links carry only one drone every two turns.

    Concentrating every drone on the single cheapest path throttles them
    through one restricted chain; spreading them over too many long paths
    wastes turns on detours. The sweet spot is to use the *K* cheapest paths
    and interleave drones round-robin, for the K that minimises makespan.

    Rather than hard-code K, this allocator tries each K and scores it with
    the real :class:`Simulator`, so it adapts to any map topology.

    Attributes:
        assignment: One path (list of zone names) per drone id, produced by
            :meth:`allocate`.
        turns: Simulated turn count of the chosen assignment.
    """

    def __init__(
        self,
        hubs: Dict[str, Hub],
        connections: Dict[str, Tuple[float, int]],
        paths: List[List[str]],
        nb_drones: int,
    ) -> None:
        """Build an allocator.

        Args:
            hubs: Zone-name to :class:`Hub` mapping (capacity/zone metadata).
            connections: Connection name to ``(capacity, used)`` mapping.
            paths: Candidate start-to-goal routes from the pathfinder.
            nb_drones: Number of drones to route.
        """
        self.hubs = hubs
        self.connections = connections
        self.paths = paths
        self.nb_drones = nb_drones
        self.assignment: List[List[str]] = []
        self.turns: int = 0

    def _path_cost(self, path: List[str]) -> int:
        """Turn cost of traversing ``path`` (restricted zones cost 2)."""
        cost = 0
        for zone in path[1:]:
            hub = self.hubs[zone]
            restricted = hub.metadata.get("zone") == "restricted"
            cost += 2 if restricted else 1
        return cost

    def _interleave(self, chosen: List[List[str]]) -> List[List[str]]:
        """Spread drones round-robin over ``chosen`` paths by drone id."""
        count = len(chosen)
        return [chosen[i % count] for i in range(self.nb_drones)]

    def _simulate(self, assignment: List[List[str]]) -> int:
        """Return the turn count the simulator needs for ``assignment``."""
        drones = [Drone(i, [], assigned=assignment[i])
                  for i in range(self.nb_drones)]
        turns: int = Simulator(self.hubs, self.connections,
                               drones).calculate_turns()
        return turns

    def allocate(self) -> List[List[str]]:
        """Compute and store the best per-drone path assignment.

        Returns:
            The chosen assignment (one path per drone id). Also cached on
            :attr:`assignment`, with its score on :attr:`turns`.
        """
        if not self.paths or self.nb_drones <= 0:
            self.assignment = []
            self.turns = 0
            return self.assignment

        ranked = sorted(self.paths, key=self._path_cost)

        best_turns = -1
        best_assignment: List[List[str]] = []
        for k in range(1, len(ranked) + 1):
            assignment = self._interleave(ranked[:k])
            turns = self._simulate(assignment)
            if best_turns == -1 or turns < best_turns:
                best_turns = turns
                best_assignment = assignment

        self.assignment = best_assignment
        self.turns = best_turns
        return self.assignment
