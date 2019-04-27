from typing import Any, List, Optional, Sequence, Text, Tuple, Union, overload
from pygame.bufferproxy import BufferProxy
from pygame.rect import Rect

_RgbaInput = Sequence[float]
_ColorInput = Union[_RgbaInput, int]
_RgbaOutput = Tuple[int, int, int, int]

class Surface(object):
    _pixels_address: int
    @overload
    def __init__(
        self,
        width_height: Tuple[float, float],
        flags: int = ...,
        depth: int = ...,
        masks: Optional[_RgbaInput] = ...,
    ) -> None: ...
    @overload
    def __init__(
        self,
        width_height: Tuple[float, float],
        flags: int = ...,
        surface: Surface = ...,
    ) -> None: ...
    def blit(
        self,
        source: Surface,
        dest: Union[Sequence[float], Rect],
        area: Optional[Rect] = ...,
        special_flags: int = ...,
    ) -> Rect: ...
    @overload
    def convert(self, surface: Surface) -> Surface: ...
    @overload
    def convert(self, depth: int, flags: int = ...) -> Surface: ...
    @overload
    def convert(self, masks: _RgbaInput, flags: int = ...) -> Surface: ...
    @overload
    def convert(self) -> Surface: ...
    @overload
    def convert_alpha(self, surface: Surface) -> Surface: ...
    @overload
    def convert_alpha(self) -> Surface: ...
    def copy(self) -> Surface: ...
    def fill(
        self, color: _ColorInput, rect: Optional[Rect] = ..., special_flags: int = ...
    ) -> Rect: ...
    def scroll(self, dx: int = ..., dy: int = ...) -> None: ...
    @overload
    def set_colorkey(self, color: _ColorInput, flags: int = ...) -> None: ...
    @overload
    def set_colorkey(self, color: None) -> None: ...
    def get_colorkey(self) -> Optional[_RgbaOutput]: ...
    @overload
    def set_alpha(self, value: int, flags: int = ...) -> None: ...
    @overload
    def set_alpha(self, value: None) -> None: ...
    def get_alpha(self) -> Optional[int]: ...
    def lock(self) -> None: ...
    def unlock(self) -> None: ...
    def mustlock(self) -> bool: ...
    def get_locked(self) -> bool: ...
    def get_locks(self) -> Tuple[Any, ...]: ...
    def get_at(self, x_y: Sequence[int]) -> _RgbaOutput: ...
    def set_at(self, x_y: Sequence[int], color: _ColorInput) -> None: ...
    def get_at_mapped(self, x_y: Sequence[int]) -> int: ...
    def get_palette(self) -> List[_RgbaOutput]: ...
    def get_palette_at(self, index: int) -> _RgbaOutput: ...
    def set_palette(self, palette: List[_RgbaInput]) -> None: ...
    def set_palette_at(self, index: int, color: _RgbaInput) -> None: ...
    def map_rgb(self, color: _RgbaInput) -> int: ...
    def unmap_rgb(self, mapped_int: int) -> _RgbaOutput: ...
    def set_clip(self, rect: Optional[Rect]) -> None: ...
    def get_clip(self) -> Rect: ...
    def subsurface(self, rect: Rect) -> Surface: ...
    def get_parent(self) -> Surface: ...
    def get_abs_parent(self) -> Surface: ...
    def get_offset(self) -> Tuple[int, int]: ...
    def get_abs_offset(self) -> Tuple[int, int]: ...
    def get_size(self) -> Tuple[int, int]: ...
    def get_width(self) -> int: ...
    def get_height(self) -> int: ...
    def get_rect(self, **kwargs: Union[int, Tuple[int, int]]) -> Rect: ...
    def get_bitsize(self) -> int: ...
    def get_bytesize(self) -> int: ...
    def get_flags(self) -> int: ...
    def get_pitch(self) -> int: ...
    def get_masks(self) -> _RgbaOutput: ...
    def set_masks(self, color: _RgbaInput) -> None: ...
    def get_shifts(self) -> _RgbaOutput: ...
    def set_shifts(self, color: _RgbaInput) -> None: ...
    def get_losses(self) -> _RgbaOutput: ...
    def get_bounding_rect(self, min_alpha: int = ...) -> Rect: ...
    def get_view(self, kind: Text = ...) -> BufferProxy: ...
    def get_buffer(self) -> BufferProxy: ...
