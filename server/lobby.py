""" The lobby could be written a lot more cleanly using a select

It would make the main function "sync", and much more maintainable
"""

import logging
import net
from server.types import *

# from .shit_lobby import lobby

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


async def lobby(
    playerch: RecvCh[Player],
    groupch: SendCh[Group],
    group_size: int,
    quitch: SendCh[Player],
) -> None:

    # this is a local quitch, used to keep track of the stack
    quit_sendch, quit_recvch = trio.open_memory_channel[Player](0)

    create_more_stacks = True
    stack: List[Player] = []
    async with trio.open_nursery() as parent:
        while create_more_stacks:
            # this nursery is used exclusively for watch_close tasks:
            # all other task are start_soon on parent.
            # a new nursery like this is spawned once per stack.
            async with trio.open_nursery() as nursery:
                # select from quit and new
                while len(stack) < group_size:
                    player, ch, still_open = await select(quit_recvch, playerch)
                    if ch == quit_recvch:
                        if not still_open:
                            # remember: this is the local quit channel
                            # the quit channel should never be closed while the
                            # lobby is running.
                            raise RuntimeError(
                                "quit channel was closed "
                                "unexpectedly. Please report."
                            )
                        log.info(f"{player} left the lobby ({len(stack)} - 1)")
                        log.debug(f"{stack}")
                        # tell the server a player left. Spawns on a different
                        # nursery because this task is independent of the stack:
                        # even if the stack is finished (which means this
                        # nursery will be closed) this task should keep running
                        parent.start_soon(quitch.send, player)

                        stack.remove(player)

                        # send the new stack to the players
                        # copy the stack, it can loop on it without worrying.
                        parent.start_soon(stack_changed, tuple(stack), group_size)

                    elif ch == playerch and still_open:
                        log.info(f"{player} joined the lobby ({len(stack)} + 1)")
                        log.debug(f"{stack}")

                        stack.append(player)

                        # spawn watch
                        nursery.start_soon(watch_close, player, quit_sendch.clone())

                        parent.start_soon(
                            player.stream.write, {"type": "lobby", "message": "welcome"}
                        )

                        # same as above
                        parent.start_soon(stack_changed, tuple(stack), group_size)
                    elif ch == playerch and not still_open:
                        log.info("stopping lobby (playerch closed)")
                        # we can't close these streams because there are still
                        # watchers monitoring it. The nursery should be cancelled
                        # and then we can close
                        parent.start_soon(close_all, stack)
                        parent.start_soon(groupch.aclose)
                        create_more_stacks = False
                        nursery.cancel_scope.cancel()
                    else:
                        raise RuntimeError(
                            f"Invalid select result {player} " f"{ch} {still_open}"
                        )

                # if we haven't stopped the loop, it means that the stack is
                # full
                if create_more_stacks:

                    log.info(f"stack full ({len(stack)}): {stack}")

                    # cancel the watchers
                    nursery.cancel_scope.cancel()

                    parent.start_soon(groupch.send, Group(tuple(stack)))

                    # clear the stack
                    stack.clear()

        log.debug("lobby main loop exited, waiting for parent nursery to close")
    log.info("lobby finished")


async def close_all(players: List[Player]) -> None:
    log.info(f"closing stack {players}")
    async with trio.open_nursery() as nursery:
        for player in players:
            nursery.start_soon(player.stream.aclose)
        nursery.cancel_scope.deadline = trio.current_time() + 3

    if nursery.cancel_scope.cancelled_caught:
        log.warning("timed out closing all players")


async def stack_changed(stack: Tuple[Player, ...], group_size: int) -> None:
    return
    async with trio.open_nursery() as nursery:
        for player in stack:
            nursery.start_soon(
                player.stream.write,
                {
                    "type": "lobby update",
                    # same here, we pass a copy of the tuple, so that we can
                    # keep looping freely without worrying about what .write is
                    # doing with the list
                    "players": tuple(stack),
                    "group_size": group_size,
                },
            )


async def watch_close(player: Player, quitch: SendCh[Player]) -> None:
    """ sends player on quitch as soon as its stream is closed

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
        await quitch.send(player)
        # it's safe to close the channel because each time, we are given a
        # clone, not the original.
        await quitch.aclose()
        return

    log.error(f"recieved message while watching close: {msg}")


async def select(a: RecvCh[T], b: RecvCh[T]) -> Tuple[T, RecvCh[T], bool]:
    """ A good enough select
    returns 
        - value captured
        - channel that received
        - channel still open

    TODO: use an internal channel to make it a bit cleaner
    TODO: accept a variable amount of channels
    TODO: test this function independently
    """

    sendch, recvch = trio.open_memory_channel[T](0)

    result: Optional[T] = None
    still_open = True
    channel = None

    async def _fetch_and_cancel(ch: RecvCh[T], nursery: Nursery) -> None:
        nonlocal result, still_open, channel

        try:
            result = await ch.receive()
        except trio.EndOfChannel:
            still_open = False
            result = None

        channel = ch
        nursery.cancel_scope.cancel()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(_fetch_and_cancel, b, nursery)
        nursery.start_soon(_fetch_and_cancel, a, nursery)

    return result, channel, still_open  # type: ignore
