import logging
import net
from client.resman import get_font
from client.types import *
from client.utils import *
from client.const import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

class Connect(Scene):

    """ Connect to the server

    TODO: read from a file/allow the user to type in their own host:port
    """

    host = "localhost"
    port = PORT

    def __init__(self, nursery: Nursery, screen: Screen):
        super().__init__(nursery, screen)

        self.scene_nursery.start_soon(self.open_connection)
        self.state = f"Connecting to {self.host}:{self.port}..."

    async def open_connection(self) -> None:
        raw = await trio.open_tcp_stream(self.host, self.port)
        # we can overwrite the current state of the object because these are
        # atomic operations
        self.stream = net.JSONStream(raw)

        self.state = "Waiting for server instructions..."

        async def wait_for_login() -> None:
            """ reads until the server says to log in """
            resp = await self.stream.read()
            if resp != {'type': 'log in'}:
                log.error(f"invalid resp {resp}")
                await wait_for_login()

        await wait_for_login()
        self.going = False

    def render(self) -> None:
        with fontedit(get_font(MONO)) as font:
            rect = font.get_rect(self.state)
            rect.center = self.screen.rect.center
            font.render_to(self.screen.surf, rect, None)

    def next_scene(self) -> Tuple[str, Dict[str, Any]]:
        return 'username', {'stream': self.stream}