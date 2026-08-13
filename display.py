import pygame
from typing import Dict, List
from drone import Drone
from hub import Hub
from simulator import Simulator


class display:
    def __init__(
        self,
        hubs: Dict[str, Hub],
        connections: Dict[str, tuple],
        drones: List[Drone],
        path: List[List[str]],
        sim: Simulator
    ):
        self.hubs = hubs
        self.connections = connections
        pygame.init()
        width, height = 1500, 700
        self.screen = pygame.display.set_mode((width, height))
        self.backgroud = pygame.image.load(
            "background-sky.jpg").convert_alpha()
        self.backgroud = pygame.transform.scale(
            self.backgroud, (width, height))

        # Fit the map to the window: derive a uniform scale and a centring
        # offset from the hub coordinate bounds, so a map of any size (a
        # handful of zones, or the 50+ of the challenger map) stays fully on
        # screen instead of running off the fixed 1500x700 canvas. The scale
        # is capped at 70 so small maps keep their familiar spacing.
        margin = 90
        xs = [h.coord[0] for h in hubs.values()] or [0]
        ys = [h.coord[1] for h in hubs.values()] or [0]
        self._min_x, max_x = min(xs), max(xs)
        self._min_y, max_y = min(ys), max(ys)
        span_x = (max_x - self._min_x) or 1
        span_y = (max_y - self._min_y) or 1
        avail_w = width - 2 * margin
        avail_h = height - 2 * margin
        self._scale = min(avail_w / span_x, avail_h / span_y, 70)
        self._off_x = (width - span_x * self._scale) / 2
        self._off_y = (height - span_y * self._scale) / 2

        # Size the hub circles and drone sprite to the scale so dense maps
        # stay legible; both are clamped to their original sizes for small
        # maps (radius 30 and an 80px sprite at the un-shrunk scale of 70).
        self._radius = max(6, min(30, int(self._scale * 30 / 70)))
        drone_size = max(16, min(80, int(self._scale * 80 / 70)))
        self._drone_half = drone_size / 2
        drone_img = pygame.image.load("drone.png").convert_alpha()
        self.drone = pygame.transform.scale(
            drone_img, (drone_size, drone_size))

        # Label font scales with the map so hub/connection names stay
        # legible on dense maps and don't overpower small ones.
        label_size = max(12, min(22, int(self._scale * 22 / 70)))
        self._font = pygame.font.Font(None, label_size)

        self.path = path
        self.drones = drones
        self.schedule = sim.schedule
        self.sim = sim

    def _hub_center(self, hub_name: str) -> tuple[float, float]:
        x, y = self.hubs[hub_name].coord
        return (self._off_x + (x - self._min_x) * self._scale,
                self._off_y + (y - self._min_y) * self._scale)

    def _build_route_points(self, drone: Drone) -> List[tuple[float, float]]:
        return [self._hub_center(hub_name) for hub_name in drone.path]

    def _draw_label(self, text: str, cx: float, cy: float) -> None:
        """Draw centred text with a light halo so names stay readable."""
        main = self._font.render(text, True, (20, 20, 20))
        halo = self._font.render(text, True, (255, 255, 255))
        rect = main.get_rect(center=(int(cx), int(cy)))
        for ox, oy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            self.screen.blit(halo, (rect.x + ox, rect.y + oy))
        self.screen.blit(main, rect)

    def display_hubs(self) -> None:
        self.screen.fill("white")
        self.screen.blit(self.backgroud, (0, 0))
        fh = self._font.get_height()
        for key in self.connections:
            parts = key.split("-")
            pos1 = self._hub_center(parts[0])
            pos2 = self._hub_center(parts[1])
            pygame.draw.line(self.screen, "green", pos1, pos2, 3)
            mx = (pos1[0] + pos2[0]) / 2
            my = (pos1[1] + pos2[1]) / 2
            self._draw_label(key, mx, my - fh / 2)
        for key in self.hubs.keys():
            pos = self._hub_center(key)
            try:
                pygame.draw.circle(
                    self.screen, self.hubs[key].color, pos, self._radius)
            except ValueError:
                pygame.draw.circle(self.screen, "white", pos, self._radius)
            self._draw_label(key, pos[0], pos[1] + self._radius + fh / 2 + 2)

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
            self.screen.blit(
                self.drone,
                (int(x - self._drone_half), int(y - self._drone_half)))

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
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            running = False
                if not running:
                    break
                self._draw_frame(timeline, turn, f / frames_per_turn)
                clock.tick(60)
                pygame.display.flip()
            turn += 1
