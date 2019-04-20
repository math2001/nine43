""" The lobby

To make the loop back easier (fin to lobby), the server itself should ask the
clients for their username, not the lobby.
"""

import attr
import net
import trio
import logging
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

@attr.s(auto_attribs=True)
class Player:

    """ A player waiting in the lobby """

    stream: net.JSONStream
    username: str

async def initiate_player(
        stream: net.JSONStream,
        playerch: trio.abc.SendChannel[Player]
    ) -> None:

    log.debug("initiating player %s", stream)

    try:
        msg = await stream.read()
    except net.ConnectionClosed as e:
        return log.exception("initiating player: connection closed")

    if msg['type'] != "log in":
        return log.warning("initiating player: invalid type %s", msg)

    if 'username' not in msg:
        return log.warning("initiating player: no 'username' %s", msg)

    player = Player(stream, msg['username'])
    log.info("player initialized %s", player)
    await playerch.send(player)

async def initiate_players(
        connch: trio.abc.ReceiveChannel[net.JSONStream],
        playerch: trio.abc.SendChannel[Player]
    ) -> None:

    async with playerch:
        async with trio.open_nursery() as nursery:
            log.debug('waiting for streams on conn channel...')
            async for stream in connch:
                log.debug("new stream in conn ch")
                nursery.start_soon(initiate_player, stream, playerch)
            log.info("conn channel closed, with %d tasks left",
                     len(nursery.child_tasks))

            if len(nursery.child_tasks) > 0:
                log.info("waiting for initialization to be finished")
                await trio.sleep(2)

            if len(nursery.child_tasks) > 0:
                log.warning("hard cancelling player initialization")
                nursery.cancel_scope.cancel()

async def group_players(
        playerch: trio.abc.ReceiveChannel[Player],
        groupch: trio.abc.SendChannel[Tuple[Player, ...]],
        group_size: int
    ) -> None:
    """ Stacks players in groups of group_size and sends them on group channel
    """

    async with groupch:
        stack: List[Player] = []
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

def new_lobby(
        nursery: Nursery,
        connch: trio.abc.ReceiveChannel[net.JSONStream],
        groupch: trio.abc.SendChannel[Tuple[Player, ...]],
        group_size: int
    ) -> None:

    """The lobby of the whole server
    
    Only once instance of the lobby will be running at any time (always the
    same one).

    In essence, it recieves connections from the server, stacks them and sends
    them in group of N back to the server.

    Path of a player from the server back to the server:

    Server -> initiate_players -> group_players -> Server
         connch             playerch         groupch

    Remember: when you send something through a channel, you *give up its
              ownership*.

    """

    log.info("start lobby")

    player_sendch, player_getch = trio.open_memory_channel[Player](0)

    nursery.start_soon(initiate_players, connch, player_sendch)
    nursery.start_soon(group_players, player_getch, groupch, group_size)
