from typing import *
from pygame.color import ValidColor
from pygame.rect import Rect
from pygame.surface import Surface
from pygame.locals import STYLE_DEFAULT

def get_error() -> str: ...
def get_version() -> Tuple[int, int, int]: ...
def init(cache_size: int = 64, resolution: int = 72) -> None: ...
def quit() -> None: ...
def was_init() -> bool: ...
def get_cache_size() -> int: ...
def get_default_resolution() -> int: ...
def set_default_resolution(res: int = 72) -> None: ...

# TODO: is size a float or an int?
def SysFont(name: str, size: int, bold: bool = False, italic: bool = False) -> Font: ...
def get_default_font() -> str: ...

Dest = Union[Tuple[int, int], Rect, List[int]]

class Font:

    name: str
    path: str
    size: Union[int, Tuple[int, int]]
    height: int
    ascender: int
    descender: int
    style: int
    underline: bool
    strong: bool
    oblique: bool
    wide: bool
    strength: float
    underline_adjustment: float
    fixed_width: bool
    fixed_sizes: int
    scalable: bool
    use_bitmap_strikes: bool
    antialiased: bool
    kerning: bool
    vertical: bool
    rotation: int
    fgcolor: ValidColor
    origin: bool
    pad: bool
    ucs4: bool
    resolution: int
    def __init__(
        self,
        file: str,
        size: int = 0,
        font_index: int = 0,
        resolution: int = 0,
        ucs4: bool = False,
    ): ...
    def render_raw_to(
        self,
        array: List[List[int]],
        text: Optional[str],
        dest: Optional[Dest] = None,
        style: int = STYLE_DEFAULT,
        rotation: int = 0,
        size: int = 0,
        invert: bool = False,
    ) -> Tuple[int, int]: ...
    def render_raw(
        self,
        text: Optional[str],
        style: int = STYLE_DEFAULT,
        rotation: int = 0,
        size: int = 0,
        invert: bool = False,
    ) -> Tuple[bytes, Tuple[int, int]]: ...
    def render_to(
        self,
        surf: Surface,
        dest: Dest,
        text: Optional[str],
        fgcolor: Optional[ValidColor] = None,
        bgcolor: Optional[ValidColor] = None,
        style: int = STYLE_DEFAULT,
        rotation: int = 0,
        size: int = 0,
    ) -> Rect: ...
    def render(
        self,
        text: Optional[str],
        fgcolor: Optional[ValidColor] = None,
        bgcolor: Optional[ValidColor] = None,
        style: int = STYLE_DEFAULT,
        rotation: int = 0,
        size: int = 0,
    ) -> Tuple[Surface, Rect]: ...
    def get_sizes(self) -> List[Tuple[int, int, int, float, float]]: ...
    def get_sized_glyph_height(self, size: int = 0) -> int: ...
    def get_sized_height(self, size: int = 0) -> int: ...
    def get_sized_descender(self, size: int = 0) -> int: ...
    def get_sized_ascender(self, size: int = 0) -> int: ...
    def get_metrics(
        self, text: str, size: int = 0
    ) -> List[Tuple[int, int, int, int, float, float]]: ...
    def get_rect(
        self, text: str, style: int = STYLE_DEFAULT, rotation: int = 0, size: int = 0
    ) -> Rect: ...
