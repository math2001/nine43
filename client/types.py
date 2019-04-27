import logging
import abc
import pygame
import attr
from typings import *
from types import SimpleNamespace

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

Font = pygame.freetype.Font
Event = pygame.event.EventType


class Screen:
    def __init__(self, surf: pygame.Surface):
        self.surf = surf
        self.rect = surf.get_rect()


class Scene(abc.ABC):
    def __init__(self, nursery: Nursery, screen: Screen, pdata: SimpleNamespace):
        self.scene_nursery = nursery
        self.screen = screen
        self.pdata = pdata
        self.going = True
        self._state = -1, ""

    def update(self) -> None:
        pass

    def render(self) -> None:
        pass

    def close(self) -> None:
        """ close current scene to let others run """
        self.going = False

    @abc.abstractmethod
    def finish(self) -> None:
        """ gracefully close *everything* because the app is closing """

    def debug_text(self) -> str:
        return ""

    @abc.abstractmethod
    def next_scene(self) -> str:
        return ""

    def handle_event(self, e: pygame.event.EventType) -> bool:
        return False

    def __str__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.debug_text()})"

    @property
    def state(self) -> Tuple[int, str]:
        return self._state

    @state.setter
    def state(self, val: Tuple[int, str]) -> None:
        self._state = val
        log.info(f"[{self.__class__.__name__}] {self._state[0]} {self._state[1]}")
