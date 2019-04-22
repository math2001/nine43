""" The lobby of the whole server

Only once instance of the lobby will be running at any time (always the
same one).

In essence, it receives connections from the server, stacks them and sends
them in group of N back to the server.

Path of a player from the server back to the server:

Server -> group_players -> Server
     playerch         groupch

Replayer: when you send something through a channel, you *give up its
          ownership*.

"""

import logging
import trio
import net
from server.types import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

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

    Note: this watch close could be implemented to watch *all* streams on the
    stack. Might be a better idea...
    """
    log.debug(f"watching connection close {player}")
    try:
        msg = await player.stream.read()
    except net.ConnectionClosed:
        log.warning(f"{player} left the lobby")
        await player_leftch.send(player)
        return
    log.error(f"recieved message while watching close: {msg}")

async def remove_player_when_leaves(
        player_leftch: RecvCh[Player],
        stacklk: Lockable[List[Player]]
    ) -> None:

    log.debug("ready to remove player from stack as they leave...")

    async for player in player_leftch:
        async with stacklk as stack:
            stack.remove(player)

async def add_new_players(
        parent: Nursery,
        playerch: RecvCh[Player],
        stacklk: Lockable[List[Player]],
        groupch: SendCh[Group],
        group_size: int
    ) -> None:

    player_left_sendch, player_left_recvch = trio.open_memory_channel[Player](0)

    while True:
        log.debug('looping!')
        final_stack: Tuple[Player, ...] = ()

        async with trio.open_nursery() as nursery:
            nursery.start_soon(remove_player_when_leaves, player_left_recvch, stacklk)
            # we don't use len(stack) because we'd need to acquire it every
            # single time. Since we already acquire it at the bottom of the
            # loop, which just cache it.

            need_more_players = True
            while need_more_players:
                log.info("waiting for new players on playerch")
                try:
                    player = await playerch.receive()
                except trio.EndOfChannel as e:
                    log.info("playerch closed", exc_info=e)
                    return nursery.cancel_scope.cancel()

                log.debug(f"got new player {player}")

                async with stacklk as stack:
                    log.info(f"add {player} to the stack")
                    stack.append(player)

                    parent.start_soon(player.stream.write, {"type": "lobby", "message": "welcome"})
                    nursery.start_soon(watch_close, player, player_left_sendch)
                    if len(stack) == group_size:
                        log.debug("caching and clearing stack")
                        nursery.cancel_scope.cancel()
                        final_stack = tuple(stack)
                        stack.clear()
                        need_more_players = False


        if len(final_stack) != group_size:
            log.critical("stack length is different than the expected stack length!")
            log.critical(f"Got {len(final_stack)}, should have {group_size}")

        log.info(f"sending stack (cancel nursery) {final_stack}")
        parent.start_soon(groupch.send, Group(players=final_stack))
        log.debug("stack sent!")

async def lobby(
        playerch: RecvCh[Player],
        groupch: SendCh[Group],
        group_size: int
    ) -> None:

    log.info("start lobby")

    stacklk = Lockable[List[Player]]([])

    async with groupch:
        async with trio.open_nursery() as nursery:
            await add_new_players(nursery, playerch, stacklk, groupch, group_size)
            if len(nursery.child_tasks) > 0:
                log.warning(f"{len(nursery.child_tasks)} tasks left in lobby "
                            f"parent nursery. Closing in 2")

                await trio.sleep(2)
                if len(nursery.child_tasks) > 0:
                    log.critical(f"force cancel {len(nursery.child_tasks)} tasks")
                    nursery.cancel_scope.cancel()

    log.debug('closing connections; acquiring stack')
    async with stacklk as stack:
        log.info(f"closing {len(stack)} player(s) from stack...")
        with trio.move_on_after(2) as cancel_scope:
            async with trio.open_nursery() as nursery:
                for player in stack:
                    log.debug(f"closing {player}")
                    nursery.start_soon(player.stream.aclose)
            log.debug("closed all players left on the stack!")

        if cancel_scope.cancelled_caught:
            log.warning("forcefully closed players in stack after timeout")

    log.info("lobby done: closed all players from stack")