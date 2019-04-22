""" Simplistic resource manager that only loads each resource once
"""

import pygame
import pygame.freetype
from client.types import *
from typings import *

_resources: Dict[str, Any] = {
    "images": {},
    "fonts": {},
}

def get_image(name: str) -> pygame.Surface:
    if name in _resources['images']:
        return _resources['images'][name]

    return pygame.image.load_alpha(f'./client/resources/images/{name}.png').convert_alpha()

def get_font(name: str) -> Font:
    if name in _resources['fonts']:
        return _resources['fonts'][name]

    font = pygame.freetype.Font(f'./client/resources/fonts/{name}.ttf', size=20)
    # some sane defaults
    font.fgcolor = 255, 255, 255
    return font