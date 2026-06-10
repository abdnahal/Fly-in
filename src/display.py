import pygame
from typing import Dict, List
from drone import Drone
from hub import Hub


class display():
    def __init__(self, hubs: Dict[str, Hub], connections: Dict[str, tuple],
                 drones: List[Drone], path: List[str]):
        self.hubs = hubs
        self.connections = connections
        pygame.init()
        self.screen = pygame.display.set_mode((1800, 1200))
        self.backgroud = pygame.image.load(
            "background-sky.jpg"
        ).convert_alpha()
        self.backgroud = pygame.transform.scale(self.backgroud, (1800, 1200))
        self.hub = pygame.image.load("morocco.png").convert_alpha()
        self.drone = pygame.image.load("drone.png").convert_alpha()
        self.path = path
        self.drones = drones

    def _hub_center(self, hub_name: str) -> tuple[float, float]:
        hub_w, hub_h = self.hub.get_size()
        x, y = self.hubs[hub_name].coord
        return (x * 70 + hub_w // 2, y * 70 + hub_h // 2)

    def _build_route_points(self, drone: Drone) -> List[tuple[float, float]]:
        return [self._hub_center(hub_name) for hub_name in drone.path]

    def display_hubs(self) -> None:
        self.screen.fill('white')
        self.screen.blit(self.backgroud, (0, 0))
        hub_w, hub_h = self.hub.get_size()
        for key in self.connections:
            parts = key.split('-')
            x, y = self.hubs[parts[0]].coord
            i, j = self.hubs[parts[1]].coord
            pos1 = (x * 70 + hub_w // 2 + 300, y * 70 + hub_h // 2 + 200)
            pos2 = (i * 70 + hub_w // 2 + 300, j * 70 + hub_h // 2 + 200)
            pygame.draw.line(self.screen, 'green', pos1, pos2, 3)
        for key in self.hubs.keys():
            x, y = self.hubs[key].coord
            pos = (x * 70 + hub_w // 2 + 300, y * 70 + hub_h // 2 + 200)
            pygame.draw.circle(
                self.screen,
                self.hubs[key].color, pos, 30)
            self.screen.blit(self.hub, (x * 70 + 300, y * 70 + 200))

    def display_drones(self) -> int:
        finished = sum([1 for drone in self.drones
                        if drone.segment_index == len(drone.path) - 1])
        if finished == len(self.drones):
            return 1
        for drone in self.drones:
            route_points = self._build_route_points(drone)
            if drone.segment_index < len(route_points) - 1:
                start = drone.path[drone.segment_index]
                end = drone.path[drone.segment_index + 1]
                current = [f"{start}-{end}"
                           if f"{start}-{end}" in self.connections.keys()
                           else f"{end}-{start}"]
                drone.current = current[0]
                conn = self.connections[drone.current[0]]
                if conn[1] < conn[0] or drone.state == "running":
                    start_x, start_y = route_points[drone.segment_index]
                    end_x, end_y = route_points[drone.segment_index + 1]
                    drone_x = start_x + (end_x - start_x) * drone.t
                    drone_y = start_y + (end_y - start_y) * drone.t
                    self.screen.blit(self.drone, (int(drone_x) + 260,
                                                  int(drone_y) + 170))
                    drone.state = "running"
                    if drone.t == 0.0:
                        self.connections[drone.current[0]] = (conn[0],
                                                              conn[1] + 1)
                    drone.t += drone.speed
                    if drone.t >= 1.0:
                        drone.state = "waiting"
                        drone.t = 0.0
                        drone.turns += 1
                        drone.segment_index += 1
                        self.connections[drone.current[0]] = (conn[0],
                                                              conn[1] - 1)
                        print(f"{drone.id}-{drone.path[drone.segment_index]}")
                else:
                    x, y = route_points[drone.segment_index]
                    self.screen.blit(self.drone, (x+260, y+170))
            else:
                x, y = route_points[-1]
                self.screen.blit(self.drone, (x+260, y+170))
        return 0

    def _display(self) -> None:
        if not self.path or len(self.path) < 1:
            return

        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.display_hubs()
            if self.display_drones() == 1:
                break
            clock.tick(60)
            pygame.display.flip()

        pygame.quit()
