import os
import errno
import logging
import trio
import net
from typing import *
from trio_typing import *
from server.lobby import new_lobby

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

SLEEP_TIME = 0.1
GROUP_SIZE = 2

# straight from trio's source code. The thing is that their default handler
# closes the connection as soon as the handler is done, which I don't want
# because it prevents delegation
async def _handle_one_listener(
    nursery: Nursery,
    ln: trio.abc.Listener,
    conn_sendch: trio.abc.SendChannel) -> None:

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


async def accept_conns(port: int, conn_sendch: trio.abc.SendChannel) -> None:
    listeners = await trio.open_tcp_listeners(port)
    async with trio.open_nursery() as nursery:
        for ln in listeners:
            nursery.start_soon(_handle_one_listener, nursery, ln, conn_sendch)


async def server(port, nursery: Nursery) -> None:
    """ The overarching piece of the server.

    It'll manage monitoring it.
    """

    conn_sendch, conn_getch = trio.open_memory_channel(0) # type: trio.abc.SendChannel, trio.abc.ReceiveChannel
    group_sendch, group_getch = trio.open_memory_channel(0) # type: trio.abc.SendChannel, trio.abc.ReceiveChannel

    nursery.start_soon(accept_conns, port, conn_sendch)

    new_lobby(nursery, conn_getch, group_sendch, GROUP_SIZE)

async def run():
    async with trio.open_nursery() as nursery:
        server(9999, nursery)
