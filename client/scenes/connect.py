import logging
import net
from client.resman import *
from client.types import *
from client.const import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


async def open_connection(
    host: str, port: int, streamch: SendCh[net.JSONStream]
) -> None:

    """ open connection with server.

    1. open connection
    2. send on channel
    3. wait for 'log in' message from server
    4. close channel
    """

    raw = await trio.open_tcp_stream(host, port)
    stream = net.JSONStream(raw)

    log.info(f"connection open {stream}")

    await streamch.send(stream)

    async def wait_for_login(stream: net.JSONStream) -> None:
        """ reads until the server says to log in """
        resp = await stream.read()
        if resp != {"type": "log in"}:
            log.error(f"invalid resp {resp}")
            await wait_for_login(stream)

    log.debug(f"waiting for 'log in' request {stream}")

    await wait_for_login(stream)

    log.debug(f"closing streamch {stream}")
    await streamch.aclose()


class Connect(Scene):

    """ Connect to the server

    TODO: read from a file/allow the user to type in their own host:port
    """

    host = "localhost"
    port = PORT

    def __init__(self, nursery: Nursery, screen: Screen, pdata: SimpleNamespace):
        super().__init__(nursery, screen, pdata)

        stream_sendch, self.stream_recvch = trio.open_memory_channel[net.JSONStream](0)

        self.scene_nursery.start_soon(
            open_connection, self.host, self.port, stream_sendch
        )

        self.state = 0, f"Connecting to {self.host}:{self.port}..."

    def update(self) -> None:
        if self.state[0] == 0:
            try:
                self.pdata.stream = self.stream_recvch.receive_nowait()
            except trio.WouldBlock:
                pass
            else:
                self.state = 10, "Waiting for server instructions..."

        elif self.state[0] == 10:
            try:
                msg = self.stream_recvch.receive_nowait()
            except trio.WouldBlock:
                pass
            except trio.EndOfChannel:
                self.going = False
            else:
                raise ValueError(f"streamch should have been closed, got " f"{msg!r}")

    def render(self) -> None:
        with fontedit(MONO) as font:
            rect = font.get_rect(self.state[1])
            rect.center = self.screen.rect.center
            font.render_to(self.screen.surf, rect, None)

    def next_scene(self) -> str:
        return "username"

    def finish(self) -> None:
        if self.state[0] >= 10:
            # we have a stream open
            self.scene_nursery.start_soon(self.pdata.stream.aclose)
