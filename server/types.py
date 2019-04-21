import attr
import net
from typings import *

@attr.s(auto_attribs=True)
class Member:

    """ A player waiting in the lobby """

    stream: net.JSONStream
    username: str

    def __eq__(self, o: Any) -> bool:
        return isinstance(o, Member) \
            and o.stream is self.stream \
            and o.username == self.username

class Lockable(Generic[T]):

    def __init__(self, val: T):
        self._val = val
        self._cap = trio.CapacityLimiter(1)

    async def __aenter__(self) -> T:
        await self._cap.acquire()
        return self._val

    def val(self) -> T:
        return self._val

    async def __aexit__(self, *exc: Any) -> None:
        self._cap.release()