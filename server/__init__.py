import os
import errno
import logging
import trio
import net
from typings import *
import server.lobby as lobby
import server.sub as sub

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

PORT = 9999
SLEEP_TIME = 0.1
GROUP_SIZE = 2

# straight from trio's source code. The thing is that their default handler
# closes the connection as soon as the handler is done, which I don't want
# because it prevents delegation
async def _handle_one_listener(
    nursery: Nursery,
    ln: trio.SocketListener,
    conn_sendch: SendCh[net.JSONStream]) -> None:

    async with ln:
        while True:
            try:
                stream = await ln.accept()
            except OSError as exc:
                # the system is too busy
                if exc.errno in [errno.EMFILE, errno.ENFILE, errno.ENOMEM,
                                 errno.ENOBUFS]:
                    log.error(
                        "accept returned %s (%s); retrying in %s seconds",
                        errno.errorcode[exc.errno],
                        os.strerror(exc.errno),
                        SLEEP_TIME,
                        exc_info=True
                    )
                    await trio.sleep(SLEEP_TIME)
                else:
                    raise
            else:
                nursery.start_soon(conn_sendch.send, net.JSONStream(stream))


async def accept_conns(port: int, conn_sendch: SendCh[net.JSONStream]) -> None:
    listeners = await trio.open_tcp_listeners(port)
    async with trio.open_nursery() as nursery:
        for ln in listeners:
            nursery.start_soon(_handle_one_listener, nursery, ln, conn_sendch)


async def start_subs(groupch: RecvCh[Tuple[lobby.Player, ...]]) -> None:
    async with trio.open_nursery() as nursery:
        async for group in groupch:
            nursery.start_soon(sub.new_sub, group)

async def server(port: int, nursery: Nursery) -> None:
    """ The overarching piece of the server.

    It'll manage monitoring it.
    """

    conn_sendch, conn_getch = trio.open_memory_channel[net.JSONStream](0)
    group_sendch, group_getch = trio.open_memory_channel[Tuple[lobby.Player, ...]](0)

    nursery.start_soon(accept_conns, port, conn_sendch)

    lobby.new_lobby(nursery, conn_getch, group_sendch, GROUP_SIZE)

    nursery.start_soon(start_subs, group_getch)

async def run() -> None:
    log.debug("starting server on port %d", PORT)
    async with trio.open_nursery() as nursery:
        await server(PORT, nursery)
