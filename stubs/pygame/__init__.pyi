"""
Copied from https://github.com/pygame/pygame/tree/master/buildconfig/pygame-stubs
22.04.2019
"""

from typing import *

import pygame.key
import pygame.locals
import pygame.color
import pygame.bufferproxy
import pygame.event
import pygame.joystick
import pygame.draw
import pygame.display
import pygame.time
import pygame.freetype
import pygame.image

from pygame.locals import *
from pygame.rect import Rect as Rect
from pygame.surface import Surface as Surface # wtf? doesn't work otherwise


Color = pygame.color.Color
BufferProxy = pygame.bufferproxy.BufferProxy

# def __getattr__(name: str) -> Any: ...  # don't error on missing stubs

def init() -> Tuple[int, int]: ...

def quit() -> None: ...
