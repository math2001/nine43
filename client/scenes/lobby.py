import logging
import pygame
import net
from client.resman import *
from client.types import *
from client.const import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Lobby(Scene):

    def __init__(self,
        nursery: Nursery,
        screen: Screen,
        stream: net.JSONStream,
        username: str):
        super().__init__(nursery, screen)
        self.stream = stream
        self.username = username

    def render(self) -> None:
        with fontedit(MONO) as font:
            rect = font.get_rect(f"Waiting for other people to join the lobby")
            rect.centerx = self.screen.rect.centerx
            rect.top = 100
            font.render_to(self.screen.surf, rect, None)

            rect = font.get_rect(f"Hold tight {self.username}")
            rect.center = self.screen.rect.center
            font.render_to(self.screen.surf, rect, None)
            

    def next_scene(self) -> Tuple[str, Dict[str, Any]]:
        return 'select', {'stream': self.stream, 'username': self.username}

    def finish(self) -> None:
        self.scene_nursery.start_soon(self.stream.aclose)
