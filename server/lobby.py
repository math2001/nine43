""" The lobby of the whole server

Only once instance of the lobby will be running at any time (always the
same one).

In essence, it recieves connections from the server, stacks them and sends
them in group of N back to the server.

Path of a player from the server back to the server:

Server -> group_players -> Server
     memberch         groupch

Remember: when you send something through a channel, you *give up its
          ownership*.

"""

import net
import trio
import logging
from server.types import Member
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def lobby(
        memberch: RecvCh[Member],
        groupch: SendCh[Tuple[Member, ...]],
        group_size: int
    ) -> None:

    log.info("start lobby")

    async with groupch:
        stack: List[Member] = []
        log.debug("waiting for new players to group...")
        async for player in playerch:
            log.info("new player %s", player)
            stack.append(player)
            if len(stack) == group_size:
                await groupch.send(tuple(stack))
                stack.clear()

    # playerch has been closed, close groupch and
    # close the connections with the players still in the lobby
    async with trio.open_nursery() as nursery:
        for player in stack:
            nursery.start_soon(player.stream.aclose)


