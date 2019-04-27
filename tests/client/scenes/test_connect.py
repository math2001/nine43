import pygame
import trio
from client.types import *
from client.scenes.connect import Connect, STATE_WAITING_FOR_SERVER, STATE_CONNECTING


async def run_scene(
    nursery: Nursery, portch: RecvCh[int], events: Dict[str, trio.Event]
) -> None:
    screen = Screen(pygame.Surface((500, 500)))

    scene = Connect(
        nursery, screen, SimpleNamespace(host="localhost", port=await portch.receive())
    )

    while scene.going:

        scene.update()

        if scene.state[0] == STATE_WAITING_FOR_SERVER[0]:
            assert events["got_conn"].is_set()
        else:
            assert scene.state[0] == STATE_CONNECTING[0]

        # to allow for cancellation
        await trio.sleep(0)

    # the scene should have exited (set scene.going to False)
    assert scene.next_scene() == "username"


async def server(portch: SendCh[int], events: Dict[str, trio.Event]) -> None:
    # open a genuine tcp server, it's the only scene that's actually going to need it.
    # after, we'll just pass memory streams into pdata.

    def get_handler(nursery: Nursery) -> Callable[[trio.abc.Stream], Awaitable[None]]:
        async def handler(stream: trio.abc.Stream) -> None:
            events["got_conn"].set()
            await stream.send_all(b'{"type": "log in"}\n')
            nursery.cancel_scope.cancel()

        return handler

    async with trio.open_nursery() as nursery:
        listeners: List[trio.SocketListener] = await nursery.start(  # type: ignore
            trio.serve_tcp, get_handler(nursery), 0
        )

        sockname = listeners[0].socket.getsockname()
        if isinstance(sockname, tuple):
            port = sockname[1]
        else:
            raise ValueError(
                f"failed to determine port of socket from sockname {sockname!r}"
            )
        await portch.send(port)


async def test_connect() -> None:
    events = {"got_conn": trio.Event()}
    port_send, port_recv = trio.open_memory_channel[int](0)

    with trio.move_on_after(2) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(run_scene, nursery, port_recv, events)
            nursery.start_soon(server, port_send, events)

    assert cancel_scope.cancelled_caught is False, f"connect timed out after 2 seconds"
