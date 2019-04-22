import pygame
import attr
from typings import *

__all__ = ['Screen', 'Scene', 'Font']

Font = pygame.freetype.Font

@attr.s(auto_attribs=True)
class Screen:

    surf: Any
    rect: Any

class Scene:

    def __init__(self, nursery: Nursery, screen: Screen):
        self.nursery = nursery
        self.screen = screen
        self.going = True

    def update(self) -> None:
        pass

    def render(self) -> None:
        pass

    def close(self) -> None:
        self.going = False

    def debug_text(self) -> str:
        return ""

    def next_scene_name(self) -> str:
        return ""

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.debug_text()})"