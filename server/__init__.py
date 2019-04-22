import os
import errno
import logging
import trio
import net

import server.initiator as initiator
import server.lobby as lobby
import server.submanager as submanager
from server.types import Player
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

PORT = 9999
SLEEP_TIME = 0.1
stack_SIZE = 2

# straight from trio's source code. The thing is that their default handler
# closes the connection as soon as the handler is done, which I don't want
# because it prevents delegation
async def _handle_one_listener(
    nursery: Nursery,
    ln: trio.SocketListener,
    connch: SendCh[trio.abc.Stream]) -> None:

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
                nursery.start_soon(connch.send, stream)


async def accept_conns(port: int, connch: SendCh[trio.abc.Stream]) -> None:
    listeners = await trio.open_tcp_listeners(port)
    async with trio.open_nursery() as nursery:
        for ln in listeners:
            nursery.start_soon(_handle_one_listener, nursery, ln, connch)

async def run() -> None:
    """ The overarching piece of the server.

    It'll manage monitoring it.

    network ->  initiator -> lobby -> submanager :: spawns subs -> back to lobby
         connch        playerch  stackch                     playerch

    Note: initiator -> lobby and subs -> lobby isn't the same channel, just a 
    combination of 2 different channels: they are independent.

    """

    log.debug("starting server on port %d", PORT)

    async with trio.open_nursery() as nursery:

        conn_sendch, conn_recvch = trio.open_memory_channel[trio.abc.Stream](0)

        player_sendch, player_recvch = trio.open_memory_channel[Player](0)

        stack_sendch, stack_recvch = trio.open_memory_channel[Tuple[Player, ...]](0)

        nursery.start_soon(accept_conns, PORT, conn_sendch)

        nursery.start_soon(initiator.initiator, conn_recvch, player_sendch)

        nursery.start_soon(lobby.lobby, player_recvch, stack_sendch, stack_SIZE)

        nursery.start_soon(submanager.submanager, stack_recvch, player_sendch.clone())
