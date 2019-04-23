from typing import *
from pygame.color import ValidColor
from pygame.surface import Surface
from pygame.rect import Rect

__all__ = ["rect", "polygon", "circle", "ellipse", "arc", "line", "lines", "aaline", "aalines"]

Point = Union[Tuple[int, int], List[int]]
PointList = Union[Tuple[Point, ...], List[Point]]

def rect(surf: Surface,
    color: ValidColor,
    rect: Rect,
    width: int=1) -> None:
    ...
    
def polygon(surf: Surface,
    color: ValidColor,
    pointlist: PointList,
    width: int=1) -> None: ...

def circle(surf: Surface,
    color: ValidColor,
    pos: Point,
    radius: int,
    width: int=1) -> None: ...

def ellipse(surf: Surface,
    color: ValidColor,
    rect: Rect,
    width: int=1) -> None: ...

def arc(surf: Surface,
    color: ValidColor,
    rect: Rect,
    start: float,
    end: float,
    width: int=1) -> None: ...

def line(surf: Surface,
    color: ValidColor,
    start: Point,
    end: Point,
    width: int=1) -> None: ...

def lines(surf: Surface,
    color: ValidColor,
    pointlist: PointList,
    width: int=1) -> None: ...

def aaline(surf: Surface,
    color: ValidColor,
    start: Point,
    end: Point,
    width: int=1) -> None: ...

def aalines(surf: Surface,
    color: ValidColor,
    pointlist: PointList,
    width: int=1) -> None: ...
