from typing import *

def get_focused() -> bool: ...
def get_pressed() -> bool: ...
def get_mods() -> int: ...
def set_mods() -> None: ...
@overload
def set_repeat() -> None: ...
@overload
def set_repeat(delay: int, interval: int) -> None: ...

def get_repeat() -> Tuple[int, int]: ...
def name(key: int) -> str: ...
