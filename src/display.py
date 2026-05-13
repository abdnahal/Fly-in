import pygame
from typing import Dict, List
from drone import Drone


class display():
    def __init__(self, hubs: Dict[str, Dict], connections: Dict[str, Dict],
                 drones: List[Drone], path: List[str]):
        self.hubs = hubs
        self.connections = connections
        pygame.init()
        self.screen = pygame.display.set_mode((1400, 800))
        self.backgroud = pygame.image.load(
            "jimmy-butler-wtf.png"
        ).convert_alpha()
        self.backgroud = pygame.transform.scale(self.backgroud, (1400, 800))
        self.hub = pygame.image.load("morocco.png").convert_alpha()
        self.drone = pygame.image.load("drone.png").convert_alpha()
        self.path = path
        self.drones = drones

    def _hub_center(self, hub_name: str) -> tuple[float, float]:
        hub_w, hub_h = self.hub.get_size()
        x, y = self.hubs[hub_name].coord
        return (x * 70 + hub_w // 2, y * 70 + hub_h // 2)

    def _build_route_points(self) -> List[tuple[float, float]]:
        return [self._hub_center(hub_name) for hub_name in self.path]

    def get_drone(self):
        for drone in self.drones:
            yield drone

    def display_hubs(self):
        self.screen.fill('white')
        self.screen.blit(self.backgroud, (0, 0))
        hub_w, hub_h = self.hub.get_size()
        for key in self.connections:
            parts = key.split('-')
            x, y = self.hubs[parts[0]].coord
            i, j = self.hubs[parts[1]].coord
            pos1 = (x * 70 + hub_w // 2, y * 70 + hub_h // 2)
            pos2 = (i * 70 + hub_w // 2, j * 70 + hub_h // 2)
            pygame.draw.line(self.screen, 'green', pos1, pos2, 3)
        for key in self.hubs.keys():
            x, y = self.hubs[key].coord
            pos = (x * 70 + hub_w // 2, y * 70 + hub_h // 2)
            pygame.draw.circle(
                self.screen,
                self.hubs[key].color, pos, 50)
            self.screen.blit(self.hub, (x * 70, y * 70))

    def display_drones(self):
        route_points = self._build_route_points()
        for drone in self.drones:
            print(drone.path[drone.segment_index])
        finished = sum([1 for drone in self.drones
                        if drone.segment_index == len(route_points) - 1])
        if finished == len(self.drones):
            for drone in self.drones:
                drone.segment_index = 0
            return
        for drone in self.drones:
            if drone.segment_index < len(route_points) - 1:
                start_x, start_y = route_points[drone.segment_index]
                end_x, end_y = route_points[drone.segment_index + 1]
                drone_x = start_x + (end_x - start_x) * drone.t
                drone_y = start_y + (end_y - start_y) * drone.t
                self.screen.blit(self.drone, (int(drone_x), int(drone_y)))
                drone.t += drone.speed
                if drone.t >= 1.0:
                    drone.t = 0.0
                    drone.turns += 1
                    drone.segment_index += 1
                    print(drone.path[drone.segment_index])
            else:
                self.screen.blit(self.drone, route_points[-1])

    def _display(self):
        if not self.path or len(self.path) < 2:
            return

        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.display_hubs()
            self.display_drones()
            clock.tick(60)
            pygame.display.flip()

        pygame.quit()
