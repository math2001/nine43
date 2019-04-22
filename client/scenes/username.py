import pygame
from client.resman import get_font
from client.types import Scene
from client.utils import *

class Username(Scene):

    def update(self) -> None:
        pass

    def render(self) -> None:
        with fontedit(get_font('FiraMono')) as font:
            font.render_to(self.screen.surf,
                self.screen.rect.center, "Hello, world!")

