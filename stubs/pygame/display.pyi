from typing import *
from pygame.surface import Surface
from pygame.rect import Rect

def set_mode(resolution: Tuple[int, int]=(0,0), flags: int=0, depth: int=0) -> Surface:
    ...

def flip() -> None: ...

@overload
def update() -> None: ...

@overload
def update(r: Rect) -> None: ...

@overload
def update(rs: List[Rect]) -> None: ...