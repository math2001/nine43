from contextlib import contextmanager
from client.types import *
from typings import *

@contextmanager
def fontedit(font: Font, **kwargs: Dict[str, Any]) -> Iterator[Font]:
    """ Applies some settings to a font, and then removes them """
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
