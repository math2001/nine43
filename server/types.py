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