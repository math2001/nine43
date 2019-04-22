import pygame
from client.types import Scene

class Username(Scene):

    def update(self) -> None:
        pass

    def render(self) -> None:
        pygame.draw.circle(
            self.screen.surf,
            pygame.Color('white'),
            self.screen.rect.center,
            250, 1
        )

    async def aclose(self) -> None:
        pass