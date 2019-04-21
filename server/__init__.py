import os
import errno
import logging
import trio
import net

import server.initiator as initiator
import server.lobby as lobby
import server.submanager as submanager
from server.types import Member
from typings import *

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

async def run(port: int) -> None:
    """ The overarching piece of the server.

    It'll manage monitoring it.

    network ->  initiator -> lobby -> submanager :: spawns subs -> back to lobby
         connch        memberch  groupch                     memberch

    Note: initiator -> lobby and subs -> lobby isn't the same channel, just a 
    combination of 2 different channels: they are independent.

    """

    log.debug("starting server on port %d", port)

    async with trio.open_nursery() as nursery:

        conn_sendch, conn_recvch = trio.open_memory_channel[trio.abc.Stream](0)

        member_sendch, member_recvch = trio.open_memory_channel[Member](0)

        group_sendch, group_recvch = trio.open_memory_channel[Tuple[Member, ...]](0)

        nursery.start_soon(accept_conns, port, conn_sendch)

        nursery.start_soon(initiator.initiator, conn_recvch, member_sendch)

        nursery.start_soon(lobby.lobby, member_recvch, group_sendch, GROUP_SIZE)

        nursery.start_soon(submanager.submanager, group_recvch, member_sendch.clone())
