""" Tests conversion of connection to a player

That involves the lobby and the server. Creating a connection should result
in a <Player> poping out on the server side.
"""

import string
import pytest
import trio
import trio.testing
import net
import tests
import server.lobby as lobby
from typings import *
from server.types import *

def new_stream_member(username: str) -> Tuple[Member, Member]:
    left, right = trio.testing.memory_stream_pair()
    return Member(net.JSONStream(left), username), Member(net.JSONStream(right), username)

async def test_lobby() -> None:
    """ integration test

    # send user A
    # send user B
    # user A closes its connection
    # send user C
    # send user D
    # check on group_recvch (should have (B, C, D))
    # send user E
    # send user F
    # user F quits
    # send user G
    # send user H
    # check on group_recvch (should have (E, G, H))
    # send user i
    # close memberch
    # ensure user I get's closed nicely (how?)
    """


    member_sendch, member_recvch = trio.open_memory_channel[Member](0)
    group_sendch, group_recvch = trio.open_memory_channel[Tuple[Member, ...]](0)

    async def send(
            client_end: Member,
            member: Member,
            memberch: SendCh[Member],
        ) -> None:
        with trio.move_on_after(1) as cancel_scope:
            await memberch.send(member)
            assert await client_end.stream.read() == {"type": "lobby", "message": "welcome"}

        assert cancel_scope.cancelled_caught is False, \
                f"lobby welcome message took to long for {member}"


    groups_event = trio.Event()
    groups: List[Tuple[Member, ...]] = []

    async def send_sequence(
            memberch: SendCh[Member],
            seq: trio.testing.Sequencer
        ) -> None:

        a_left, a_right = new_stream_member(username="a")
        b_left, b_right = new_stream_member(username="b")
        c_left, c_right = new_stream_member(username="c")
        d_left, d_right = new_stream_member(username="d")
        e_left, e_right = new_stream_member(username="e")
        f_left, f_right = new_stream_member(username="f")
        g_left, g_right = new_stream_member(username="g")
        h_left, h_right = new_stream_member(username="h")
        i_left, i_right = new_stream_member(username="i")


        groups.append((b_right, c_right, d_right))
        groups.append((e_right, g_right, h_right))
        groups.append((i_left, ))
        groups_event.set()

        await send(a_left, a_right, memberch)
        await send(b_left, b_right, memberch)
        await a_left.stream.aclose()
        await send(c_left, c_right, memberch)
        await send(d_left, d_right, memberch)

        await send(e_left, e_right, memberch)
        await send(f_left, f_right, memberch)
        await f_left.stream.aclose()
        await send(g_left, g_right, memberch)

        await send(h_left, h_right, memberch)
        await send(i_left, i_right, memberch)

        await memberch.aclose()

    async def check_groupch(
            groupch: RecvCh[Tuple[Member, ...]],
            seq: trio.testing.Sequencer
        ) -> None:

        await groups_event.wait()
        first = groups[0]
        second = groups[1]
        i_left = groups[2][0]

        assert await groupch.receive() == groups[0]
        assert await groupch.receive() == groups[1]

        with pytest.raises(trio.EndOfChannel):
            resp = await groupch.receive()
            assert False, \
                f"read from groupch returned {resp!r}, should raise trio.EndOfChannel"


        with pytest.raises(net.ConnectionClosed):
            msg = await i_left.stream.read()
            assert False, \
                f"read returned message: {msg!r}. Should have raised net.ConnectionClosed"


    async def monitor(
            memberch: SendCh[Member],
            groupch: RecvCh[Tuple[Member, ...]]
        ) -> None:

        # right is the part that is send to the server, and left the part that
        # is acting as the client.
        seq = trio.testing.Sequencer()
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_sequence, member_sendch, seq)
            nursery.start_soon(check_groupch, groupch, seq)

    with trio.move_on_after(3) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(monitor, member_sendch, group_recvch)
            nursery.start_soon(lobby.lobby, member_recvch, group_sendch, 3)


    assert cancel_scope.cancelled_caught is False, \
            "lobby test took to long"
    
