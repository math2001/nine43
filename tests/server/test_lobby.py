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
from server.types import *


def new_stream_player(username: str) -> Tuple[Player, Player]:
    left, right = trio.testing.memory_stream_pair()
    return (
        Player(net.JSONStream(left), username),
        Player(net.JSONStream(right), username),
    )


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
    # close playerch
    # ensure user I get's closed nicely (how?)
    """

    player_sendch, player_recvch = trio.open_memory_channel[Player](0)
    group_sendch, group_recvch = trio.open_memory_channel[Group](0)
    quit_sendch, quit_recvch = trio.open_memory_channel[Any](0)

    async def send(
        client_end: Player, player: Player, playerch: SendCh[Player]
    ) -> None:
        with trio.move_on_after(1) as cancel_scope:
            await playerch.send(player)
            assert await client_end.stream.read() == {
                "type": "lobby",
                "message": "welcome",
            }

        assert (
            cancel_scope.cancelled_caught is False
        ), f"lobby welcome message took to long for {player}"

    groups_event = trio.Event()
    groups: List[Group] = []

    async def send_sequence(
        playerch: SendCh[Player], seq: trio.testing.Sequencer, quitch: RecvCh[Player]
    ) -> None:

        a_left, a_right = new_stream_player(username="a")
        b_left, b_right = new_stream_player(username="b")
        c_left, c_right = new_stream_player(username="c")
        d_left, d_right = new_stream_player(username="d")
        e_left, e_right = new_stream_player(username="e")
        f_left, f_right = new_stream_player(username="f")
        g_left, g_right = new_stream_player(username="g")
        h_left, h_right = new_stream_player(username="h")
        i_left, i_right = new_stream_player(username="i")

        groups.append(Group((b_right, c_right, d_right)))
        groups.append(Group((e_right, g_right, h_right)))
        groups.append(Group((i_left,)))
        groups_event.set()

        async with seq(0):
            await send(a_left, a_right, playerch)
            await send(b_left, b_right, playerch)
            await a_left.stream.aclose()
            assert await quitch.receive() == a_right
            await send(c_left, c_right, playerch)
            await send(d_left, d_right, playerch)

            await send(e_left, e_right, playerch)

        async with seq(2):
            await send(f_left, f_right, playerch)
            await f_left.stream.aclose()
            assert await quitch.receive() == f_right
            await send(g_left, g_right, playerch)
            await send(h_left, h_right, playerch)
            await send(i_left, i_right, playerch)

        async with seq(4):
            await playerch.aclose()
            print("closed channel")

    async def check_groupch(
        groupch: RecvCh[Group], seq: trio.testing.Sequencer
    ) -> None:

        await groups_event.wait()
        first = groups[0]
        second = groups[1]
        i_left = groups[2].players[0]

        async with seq(1):
            assert await groupch.receive() == groups[0]

        async with seq(3):
            assert await groupch.receive() == groups[1]
            print("recieved")

        async with seq(5):
            with pytest.raises(trio.EndOfChannel):
                resp = await groupch.receive()
                assert (
                    False
                ), f"read from groupch returned {resp!r}, should raise trio.EndOfChannel"

            with pytest.raises(net.ConnectionClosed):
                msg = await i_left.stream.read()
                assert (
                    False
                ), f"read returned message: {msg!r}. Should have raised net.ConnectionClosed"

    seq = trio.testing.Sequencer()

    with trio.move_on_after(3) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_sequence, player_sendch, seq, quit_recvch)
            nursery.start_soon(check_groupch, group_recvch, seq)

            nursery.start_soon(lobby.lobby, player_recvch, group_sendch, 3, quit_sendch)

    assert cancel_scope.cancelled_caught is False, "lobby test took to long"


async def test_watch_close() -> None:
    left, right = new_stream_player(username="a")
    sendch, recvch = trio.open_memory_channel[Player](0)

    async def monitor(
        client_end: Player, server_end: Player, ch: RecvCh[Player]
    ) -> None:

        with pytest.raises(trio.WouldBlock):
            ch.receive_nowait()

        await client_end.stream.aclose()
        assert await ch.receive() == server_end

    async with trio.open_nursery() as nursery:
        nursery.start_soon(lobby.watch_close, right, sendch)
        nursery.start_soon(monitor, left, right, recvch)
