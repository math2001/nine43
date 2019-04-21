import attr
import net

@attr.s(auto_attribs=True)
class Member:

    """ A player waiting in the lobby """

    stream: net.JSONStream
    username: str