import pygame
from typing import Dict, List
from .drone import Drone
from .hub import Hub
from .simulator import Simulator


class display:
    def __init__(
        self,
        hubs: Dict[str, Hub],
        connections: Dict[str, tuple],
        drones: List[Drone],
        path: List[str],
        sim: Simulator
    ):
        self.hubs = hubs
        self.connections = connections
        pygame.init()
        self.screen = pygame.display.set_mode((1800, 1200))
        self.backgroud = pygame.image.load(
            "background-sky.jpg").convert_alpha()
        self.backgroud = pygame.transform.scale(self.backgroud, (1800, 1200))
        self.drone = pygame.image.load("drone.png").convert_alpha()
        self.path = path
        self.drones = drones
        self.schedule = sim.schedule
        self.sim = sim

    def _hub_center(self, hub_name: str) -> tuple[float, float]:
        x, y = self.hubs[hub_name].coord
        return (x * 70, y * 70)

    def _build_route_points(self, drone: Drone) -> List[tuple[float, float]]:
        return [self._hub_center(hub_name) for hub_name in drone.path]

    def display_hubs(self) -> None:
        self.screen.fill("white")
        self.screen.blit(self.backgroud, (0, 0))
        for key in self.connections:
            parts = key.split("-")
            x, y = self.hubs[parts[0]].coord
            i, j = self.hubs[parts[1]].coord
            pos1 = (x * 70 + 300, y * 70 + 200)
            pos2 = (i * 70 + 300, j * 70 + 200)
            pygame.draw.line(self.screen, "green", pos1, pos2, 3)
        for key in self.hubs.keys():
            x, y = self.hubs[key].coord
            pos = (x * 70 + 300, y * 70 + 200)
            try:
                pygame.draw.circle(self.screen, self.hubs[key].color, pos, 30)
            except ValueError:
                pygame.draw.circle(self.screen, "white", pos, 30)

    def _loc_xy(self, loc: tuple) -> tuple[float, float]:
        """Screen center for a location: a zone, or an edge's midpoint."""
        if loc[0] == "zone":
            return self._hub_center(loc[1])
        ax, ay = self._hub_center(loc[1])
        bx, by = self._hub_center(loc[2])
        return ((ax + bx) / 2, (ay + by) / 2)

    def _build_timeline(self) -> List[Dict[str, tuple]]:
        """Per-turn location of every drone, parsed from the schedule.

        Move tokens come in two shapes:
          * ``D3-bottleneck``        -> drone D3 is now IN zone bottleneck
          * ``D3-start-bottleneck``  -> drone D3 is in flight on the edge
        A drone with no token this turn keeps its previous location.
        """
        cur: Dict[str, tuple] = {
            d.id: ("zone", d.path[0]) for d in self.drones
        }
        timeline: List[Dict[str, tuple]] = [dict(cur)]
        for line in self.schedule:
            for tok in line.split():
                parts = tok.split("-")
                did = parts[0]
                if len(parts) == 2:               # arrived in a zone
                    cur[did] = ("zone", parts[1])
                elif len(parts) == 3:             # in flight on a-b
                    cur[did] = ("edge", parts[1], parts[2])
            timeline.append(dict(cur))
        return timeline

    def _draw_frame(self, timeline: List[Dict[str, tuple]],
                    turn: int, alpha: float) -> None:
        """Render one interpolated frame between turn and turn+1."""
        self.display_hubs()
        nxt = min(turn + 1, len(timeline) - 1)
        for d in self.drones:
            ax, ay = self._loc_xy(timeline[turn][d.id])
            bx, by = self._loc_xy(timeline[nxt][d.id])
            x = ax + (bx - ax) * alpha
            y = ay + (by - ay) * alpha
            self.screen.blit(self.drone, (int(x) + 260, int(y) + 170))

    def _display(self) -> None:
        if not self.schedule:
            return
        timeline = self._build_timeline()
        clock = pygame.time.Clock()
        frames_per_turn = 30            # ~0.5s per turn at 60 FPS
        running = True
        turn = 0
        while running and turn < len(timeline) - 1:
            for f in range(frames_per_turn):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                if not running:
                    break
                self._draw_frame(timeline, turn, f / frames_per_turn)
                clock.tick(60)
                pygame.display.flip()
            turn += 1
        # hold the final frame until the window is closed
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self._draw_frame(timeline, len(timeline) - 1, 0.0)
            clock.tick(60)
            pygame.display.flip()
            if all(self.sim._is_done(d) for d in self.drones):
                break
        pygame.quit()
