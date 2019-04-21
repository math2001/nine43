""" The lobby of the whole server

Only once instance of the lobby will be running at any time (always the
same one).

In essence, it receives connections from the server, stacks them and sends
them in group of N back to the server.

Path of a player from the server back to the server:

Server -> group_players -> Server
     memberch         groupch

Remember: when you send something through a channel, you *give up its
          ownership*.

"""

import logging
import trio
import net
from server.types import Member, Lockable
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def watch_close(
        member: Member,
        member_leftch: SendCh[Member]
    ) -> None:
    log.debug(f"watching connection close {member}")
    try:
        msg = await member.stream.read()
    except net.ConnectionClosed:
        log.warning(f"{member} left the lobby")
        await member_leftch.send(member)
        return
    log.error(f"recieved message while watching close: {msg}")

async def remove_member_when_leaves(
        member_leftch: RecvCh[Member],
        stacklk: Lockable[List[Member]]
    ) -> None:

    log.debug("ready to remove member from stack as they leave...")

    async for member in member_leftch:
        async with stacklk as stack:
            stack.remove(member)

async def add_new_members(
        memberch: RecvCh[Member],
        stacklk: Lockable[List[Member]],
        groupch: SendCh[Tuple[Member, ...]],
        group_size: int
    ) -> None:

    member_left_sendch, member_left_recvch = trio.open_memory_channel[Member](0)

    while True:
        log.debug('looping!')
        final_stack: Tuple[Member, ...] = ()

        async with trio.open_nursery() as nursery:
            nursery.start_soon(remove_member_when_leaves, member_left_recvch, stacklk)
            # we don't use len(stack) because we'd need to acquire it every
            # single time. Since we already acquire it at the bottom of the
            # loop, which just cache it.

            need_more_members = True
            while need_more_members:
                log.info("waiting for new members on memberch")
                try:
                    member = await memberch.receive()
                except trio.EndOfChannel as e:
                    log.info("memberch closed", exc_info=e)
                    return nursery.cancel_scope.cancel()

                log.debug(f"got new member {member}")

                async with stacklk as stack:
                    log.info(f"add {member} to the stack")
                    stack.append(member)
                    # TODO: move into an extra nursery (not the existing
                    # one because it gets canceled)
                    await member.stream.write({"type": "lobby", "message": "welcome"})
                    nursery.start_soon(watch_close, member, member_left_sendch)
                    if len(stack) == group_size:
                        log.debug("caching and clearing stack")
                        final_stack = tuple(stack)
                        stack.clear()
                        need_more_members = False

            nursery.cancel_scope.cancel()

        if len(final_stack) != group_size:
            log.critical("stack length is different than the expected stack length!")
            log.critical(f"Got {len(final_stack)}, should have {group_size}")

        log.info(f"sending stack (cancel nursery) {final_stack}")
        await groupch.send(final_stack)
        log.debug("stack sent!")

async def lobby(
        memberch: RecvCh[Member],
        groupch: SendCh[Tuple[Member, ...]],
        group_size: int
    ) -> None:

    log.info("start lobby")

    stacklk = Lockable[List[Member]]([])

    async with groupch:
        await add_new_members(memberch, stacklk, groupch, group_size)

    log.debug('closing connections; acquiring stack')
    async with stacklk as stack:
        log.info(f"closing {len(stack)} member(s) from stack...")
        with trio.move_on_after(2) as cancel_scope:
            async with trio.open_nursery() as nursery:
                for member in stack:
                    log.debug(f"closing {member}")
                    nursery.start_soon(member.stream.aclose)
            log.debug("closed all members left on the stack!")

        if cancel_scope.cancelled_caught:
            log.warning("forcefully closed members in stack after timeout")

    log.info("lobby done: closed all members from stack")