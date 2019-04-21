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
            # print('waiting for memberch', client_end)
            await memberch.send(member)
            # print('waiting for confirmation', client_end)
            assert await client_end.stream.read() == {"type": "lobby", "message": "welcome"}
            # print('got confirmation', client_end)

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

        # await send(e_left, e_right, memberch)
        # await send(f_left, f_right, memberch)
        # await f_left.stream.aclose()
        # await send(g_left, g_right, memberch)

        # await send(h_left, h_right, memberch)
        # await send(i_left, i_right, memberch)

        print('closing channel')
        await memberch.aclose()
        print('[done] send sequence: channel closed')

    async def check_groupch(
            groupch: RecvCh[Tuple[Member, ...]],
            seq: trio.testing.Sequencer
        ) -> None:

        await groups_event.wait()
        first = groups[0]
        second = groups[1]
        i_left = groups[1][0]

        print('waiting for first group')
        assert await groupch.receive() == groups[0]
        print('waiting for second group')
        # assert await groupch.receive() == groups[1]

        print('asserting close connection')

        # with pytest.raises(net.ConnectionClosed):
        #     print('reading to get "closed"')
        #     msg = await i_left.stream.read()
        #     print(f"got something while expecting close {msg!r}")

        print('[done] check groupch: connection closed')

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
        print('monitor finished')

    with trio.move_on_after(3) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(monitor, member_sendch, group_recvch)
            nursery.start_soon(lobby.lobby, member_recvch, group_sendch, 3)


    assert cancel_scope.cancelled_caught is False, \
            "lobby test took to long"
    

@pytest.mark.skip
# type: ignore
async def test_lobby_groups() -> None:

    group_size = 3
    player_number = 7

    
    conn_sendch, conn_recvch = trio.open_memory_channel[net.JSONStream](0)
    group_sendch, group_recvch = trio.open_memory_channel[Tuple[Member, ...]](0)

    groups: List[Tuple[Member, ...]] = []
    group: List[Member] = []
    
    # streams that will still be waiting in the lobby (because they aren't
    # enough). This happens when player_number % group_size != 0

    extra_client_streams: List[net.JSONStream] = []

    with trio.move_on_after(3) as out:
            
        async with trio.open_nursery() as nursery:

            lobby.new_lobby(nursery, conn_recvch, group_sendch, group_size)

            for i in range(player_number):

                left, right = tests.new_stream_pair()
                if i >= player_number - (player_number % group_size):
                    extra_client_streams.append(left)

                await left.write(cast(Message, {"type": "log in", "username": string.ascii_letters[i]}))

                group.append(Member(right, string.ascii_letters[i]))

                await conn_sendch.send(right)

                if len(group) == group_size:
                    groups.append(tuple(group))
                    group.clear()

            with trio.move_on_after(2) as sub:
                for expected in groups:
                    assert await group_recvch.receive() == expected

            assert sub.cancelled_caught is False, \
                "Awaiting group_recvch took too long"

            await conn_sendch.aclose()

    assert out.cancelled_caught is False,\
            "Awaiting nursery (probably lobby) took too long"

    with trio.move_on_after(2) as cancel_scope:
        for stream in extra_client_streams:
            with pytest.raises(net.ConnectionClosed):
                await stream.read()

    assert cancel_scope.cancelled_caught is False, \
            "extra client streams should have been closed by the lobby " \
            "(took too long to raise error trying to read it)"

    with trio.move_on_after(2) as cancel_scope:
        with pytest.raises(trio.EndOfChannel):
            await group_recvch.receive()

    assert cancel_scope.cancelled_caught is False,\
            "group get channel blocked for too long (should have been closed)"

    # Note that the other connection that the lobby has *given* to the server
    # should still be open.