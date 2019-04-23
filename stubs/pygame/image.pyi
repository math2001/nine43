import io
from typing import *
from pygame.surface import Surface

@overload
def load(filename: str) -> Surface:
    ...

@overload
def load(filobj: io.FileIO, hint: str="") -> Surface:
    ...

def save(surf: Surface, name: str) -> None:
    ...

def get_extended() -> bool:
    ...

# TODO: check format
def tostring(s: Surface, format: int, flipped: bool=False) -> str:
    ...

def fromstring(string: str, size: Tuple[int, int], format: int, flipped: bool=False) -> Surface:
    ...

def frombuffer(string: str, size: Tuple[int, int], format: int) -> Surface:
    ...
