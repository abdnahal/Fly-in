import pygame
from typing import Dict


class display():
    def __init__(self, hubs: Dict[str, Dict], connections: Dict[str, Dict]):
        self.hubs = hubs
        self.connections = connections
        pygame.init()
        self.screen = pygame.display.set_mode((1400, 1000))
        self.backgroud = pygame.image.load("jimmy-butler-wtf.png")
        self.backgroud.convert_alpha()
        self.backgroud = pygame.transform.scale(self.backgroud, (1400, 1000))
        self.hub = pygame.image.load("morocco.png").convert_alpha()

    def display_hubs(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.fill('white')
            self.screen.blit(self.backgroud, (0, 0))
            for key in self.hubs.keys():
                x, y = self.hubs[key]['coord']
                self.screen.blit(self.hub, (x * 70, y * 70))
            hub_w, hub_h = self.hub.get_size()
            for key in self.connections:
                parts = key.split('-')
                x, y = self.hubs[parts[0]]['coord']
                i, j = self.hubs[parts[1]]['coord']
                pos1 = (x * 70 + hub_w // 2, y * 70 + hub_h // 2)
                pos2 = (i * 70 + hub_w // 2, j * 70 + hub_h // 2)
                pygame.draw.line(self.screen, 'green', pos1, pos2, 3)
            pygame.display.flip()
