"""
Copied from https://github.com/pygame/pygame/tree/master/buildconfig/pygame-stubs
22.04.2019
"""

from typing import Any

import pygame.event as event
import pygame.joystick as joystick
from pygame.rect import Rect

import pygame.color
import pygame.bufferproxy

Color = pygame.color.Color
BufferProxy = pygame.bufferproxy.BufferProxy

# def __getattr__(name: str) -> Any: ...  # don't error on missing stubs
