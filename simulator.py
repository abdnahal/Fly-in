from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from hub import Hub
from drone import Drone


class Simulator:
    """Turn-by-turn drone-flow simulator.

    Given a fleet of drones (each already carrying an assigned ``path`` from
    the start zone to the end zone) the simulator advances every drone one
    step per discrete turn while respecting all movement constraints, and
    reports how many turns the whole fleet needs to reach the goal.

    Constraints enforced each turn:
      * Zone capacity: a zone holds at most ``max_drones`` drones (default 1).
        The unique start and end zones are treated as unbounded.
      * Connection capacity: a link carries at most ``max_link_capacity``
        drones simultaneously (default taken from ``connections``).
      * Restricted zones cost two turns: the drone occupies the connection
        for the transit turn and *must* land in the zone on the next turn.
      * Free-then-fill: drones leaving a zone free its capacity within the
        same turn, so a chain of drones can shift forward together.

    Attributes:
        schedule: One string per turn, each listing that turn's moves in the
            ``D<ID>-<zone>`` / ``D<ID>-<connection>`` output format.
        turns: Total number of simulation turns once :meth:`calculate_turns`
            has run (``0`` beforehand).
    """

    def __init__(
        self,
        hubs: Dict[str, Hub],
        connections: Dict[str, Tuple[float, int]],
        drones: List[Drone],
    ) -> None:
        """Build a simulator.

        Args:
            hubs: Mapping of zone name to its :class:`Hub` (for capacity and
                zone-type metadata).
            connections: Mapping of connection name ``"a-b"`` to a
                ``(capacity, used)`` tuple, as produced by
                ``ConfigParser.get_connections``.
            drones: Fleet to route; each drone must expose ``id`` and a
                ``path`` list of zone names from start to goal.
        """
        self.hubs = hubs
        self.connections = connections
        self.drones = drones
        self.schedule: List[str] = []
        self.turns: int = 0

        self._unbounded: set[str] = set()
        for drone in drones:
            if drone.path:
                self._unbounded.add(drone.path[0])
                self._unbounded.add(drone.path[-1])

        self._idx: Dict[str, int] = {}
        self._inflight: Dict[str, bool] = {}
        self._flight: Dict[str, Optional[str]] = {}
        self._occ: Dict[str, int] = defaultdict(int)

    def _conn_key(self, a: str, b: str) -> str:
        """Return the stored connection key for the ``a``/``b`` link."""
        if f"{a}-{b}" in self.connections:
            return f"{a}-{b}"
        return f"{b}-{a}"

    def _conn_cap(self, conn: str) -> float:
        """Maximum drones allowed on ``conn`` at once (``inf`` if unknown)."""
        entry = self.connections.get(conn)
        return entry[0] if entry is not None else float("inf")

    def _zone_cap(self, name: str) -> float:
        """Maximum drones a zone may hold simultaneously."""
        if name in self._unbounded:
            return float("inf")
        hub = self.hubs.get(name)
        if hub is None:
            return 1.0
        cap = hub.metadata.get("max_drones", 1)
        return float(cap)

    def _zone_type(self, name: str) -> str:
        """Zone type of ``name`` (``normal`` when unspecified)."""
        hub = self.hubs.get(name)
        if hub is None:
            return "normal"
        zone = hub.metadata.get("zone", "normal")
        return str(zone)

    def _is_done(self, drone: Drone) -> bool:
        """True once ``drone`` has landed in its goal zone."""
        return (
            not self._inflight[drone.id]
            and self._idx[drone.id] == len(drone.path) - 1
        )

    def _init_state(self) -> None:
        """Reset all drones to the start of their path."""
        self.schedule = []
        self.turns = 0
        self._occ = defaultdict(int)
        for drone in self.drones:
            self._idx[drone.id] = 0
            self._inflight[drone.id] = False
            self._flight[drone.id] = None
            if drone.path:
                self._occ[drone.path[0]] += 1

    # -- core loop -------------------------------------------------------

    def _step(self) -> List[str]:
        """Advance the simulation by one turn.

        Returns:
            The move tokens produced this turn (empty if nothing moved,
            which signals a deadlock).
        """
        moves: List[str] = []
        leaving: Dict[str, int] = defaultdict(int)
        entering: Dict[str, int] = defaultdict(int)
        conn_used: Dict[str, int] = defaultdict(int)

        # A) Drones mid-flight toward a restricted zone must land this turn.
        #    Their destination slot was reserved when the flight started, so
        #    occupancy needs no update here -- only the connection is used.
        landed: set[str] = set()
        for drone in self.drones:
            did = drone.id
            if not self._inflight[did]:
                continue
            src_i = self._idx[did]
            dest = drone.path[src_i + 1]
            conn = self._flight[did]
            if conn is not None:
                conn_used[conn] += 1
            self._idx[did] = src_i + 1
            self._inflight[did] = False
            self._flight[did] = None
            landed.add(did)
            moves.append(f"{did}-{dest}")

        # B) Drones sitting in a zone try to advance one step. Process the
        #    ones closest to the goal first so leaders free space for
        #    followers within the same turn (chain-shift). Drones that just
        #    landed in step A have already used their move for this turn.
        movers = [
            d
            for d in self.drones
            if d.id not in landed and not self._inflight[d.id]
            and not self._is_done(d)
        ]
        movers.sort(key=lambda d: self._idx[d.id], reverse=True)

        for drone in movers:
            did = drone.id
            i = self._idx[did]
            cur = drone.path[i]
            nxt = drone.path[i + 1]
            conn = self._conn_key(cur, nxt)

            if conn_used[conn] >= self._conn_cap(conn):
                continue
            avail = self._zone_cap(nxt) - self._occ[nxt] - entering[nxt]
            avail += leaving[nxt]
            if avail <= 0:
                continue

            # Commit: reserve the link and both zones' bookkeeping.
            conn_used[conn] += 1
            leaving[cur] += 1
            entering[nxt] += 1

            if self._zone_type(nxt) == "restricted":
                # Two-turn move: leave now, ride the link, land next turn.
                self._inflight[did] = True
                self._flight[did] = conn
                moves.append(f"{did}-{conn}")
            else:
                self._idx[did] = i + 1
                moves.append(f"{did}-{nxt}")

        for zone, count in leaving.items():
            self._occ[zone] -= count
        for zone, count in entering.items():
            self._occ[zone] += count

        return moves

    def calculate_turns(self, max_turns: int = 100000) -> int:
        """Run the full simulation and return the number of turns used.

        The turn-by-turn move log is also recorded in :attr:`schedule`.

        Args:
            max_turns: Safety cap; the loop stops early if a turn makes no
                progress (deadlock) or this many turns elapse.

        Returns:
            Total number of simulation turns to deliver every drone.
        """
        self._init_state()
        while not all(self._is_done(d)
                      for d in self.drones) and self.turns < max_turns:
            moves = self._step()
            if not moves:
                break  # no drone could move -> deadlock, stop counting
            self.schedule.append(" ".join(moves))
            self.turns += 1
        return self.turns
