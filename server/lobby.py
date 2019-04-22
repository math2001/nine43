""" The lobby could be written a lot more cleanly using a select

It would make the main function "sync", and much more maintainable
"""

import logging
import net  
from typings import *
from server.types import *

from .shit_lobby import lobby

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def watch_close(
        player: Player,
        player_leftch: SendCh[Player]
    ) -> None:
    """ sends player on player_leftch as soon as its stream is closed

    The only way to check if a TCP connection closed by the other end is to
    read from it, and check for errors.

    This doesn't consume any message because it is cancelled before it gets a
    chance to read anything (this is managed by the function add_new_players)

    Therefore: this only works if NO MESSAGE IS BEING SENT TO THE STREAM
    """
    log.debug(f"watching connection close {player}")
    try:
        msg = await player.stream.read()
    except net.ConnectionClosed:
        log.warning(f"{player} left the lobby")
        await player_leftch.send(player)
        return

    log.error(f"recieved message while watching close: {msg}")

async def select(a: RecvCh[T], b: RecvCh[T]) -> Tuple[T, RecvCh[T], bool]:
    """ A good enough select
    returns 
        - value captured
        - channel that received
        - channel still open
    """

    sendch, recvch = trio.open_memory_channel[T](0)

    result = "default value. Raise error!"
    still_open = True
    channel = None

    async def _fetch_and_cancel(ch: RecvCh[T], nursery: Nursery) -> None:
        nonlocal result, still_open, channel

        try:
            result = await ch.receive()
        except trio.EndOfChannel:
            still_open = False
            result = ""

        channel = ch
        nursery.cancel_scope.cancel()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(_fetch_and_cancel, b, nursery)
        nursery.start_soon(_fetch_and_cancel, a, nursery)

    return result, channel, still_open # type: ignore

# async def lobby(
#         playerch: RecvCh[Player],
#         stackch: SendCh[Tuple[Player, ...]],
#         stack_size: int
#     ) -> None:

#     async with trio.open_nursery() as parent:
#         # read from player_leftch
#         # if he left: add to player_left list
#         # read from new_playerch
#         # if there is a new one: add to new_player
#         pass
