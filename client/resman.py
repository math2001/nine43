""" Simplistic resource manager that only loads each resource once
"""

import pygame
import pygame.freetype
from contextlib import contextmanager
from client.types import *

__all__ = ["get_image", "get_font", "fontedit"]

_resources: Dict[str, Any] = {"images": {}, "fonts": {}}


def get_image(name: str) -> pygame.Surface:
    if name in _resources["images"]:
        return _resources["images"][name]

    return pygame.image.load(f"./client/resources/images/{name}.png").convert_alpha()


def get_font(name: str) -> Font:
    if name in _resources["fonts"]:
        return _resources["fonts"][name]

    font = pygame.freetype.Font(f"./client/resources/fonts/{name}.ttf", size=14)
    # some sane defaults
    font.fgcolor = 255, 255, 255
    return font


@contextmanager
def fontedit(fontname: Union[str, Font], **kwargs: Any) -> Iterator[Font]:
    """ Applies some settings to a font, and then removes them """
    if isinstance(fontname, str):
        font = get_font(fontname)
    else:
        font = fontname

    defaults = {}
    for key in kwargs:
        try:
            defaults[key] = getattr(font, key)
        except AttributeError as e:
            raise AttributeError(f"Invalid parameter for font {key!r}")
        try:
            setattr(font, key, kwargs[key])
        except AttributeError:
            raise AttributeError(f"Could not set {key!r}. Probably read-only")
    yield font
    for key, value in defaults.items():
        try:
            setattr(font, key, value)
        except AttributeError:
            raise AttributeError(f"Could not reset {key!r} to its original value")
