import attr
import net
from typings import *
from utils import truncate_middle

@attr.s(auto_attribs=True, str=False, repr=False)
class Player:

    """ A player waiting in the lobby """

    stream: net.JSONStream
    username: str

    def __eq__(self, o: Any) -> bool:
        return isinstance(o, Player) \
            and o.stream is self.stream \
            and o.username == self.username

    def __str__(self) -> str:
        return f"Player({self.username!r}, {truncate_middle(repr(self.stream), 20)})"

    def __repr__(self) -> str:
        return str(self)

class Lockable(Generic[T]):

    def __init__(self, val: T):
        self._val = val
        self._cap = trio.CapacityLimiter(1)

    async def acquire(self) -> T:
        await self._cap.acquire()
        return self._val

    def release(self) -> None:
        self._cap.release()

    async def __aenter__(self) -> T:
        await self.acquire()
        return self._val

    def val(self) -> T:
        return self._val

    async def __aexit__(self, *exc: Any) -> None:
        self.release()