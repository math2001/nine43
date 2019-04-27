from typing import *

__all__ = ["raises"]

# TODO: return Tuple[type, any exception, traceback]
# TODO: it's *args, not err
def raises(type: type, err: str = "") -> ContextManager[Tuple[type, Any, Any]]: ...
