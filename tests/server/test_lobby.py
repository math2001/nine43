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
from server.types import Member

async def test_lobby_groups() -> None:

    group_size = 3
    player_number = 7

    
    conn_sendch, conn_getch = trio.open_memory_channel[net.JSONStream](0)
    group_sendch, group_getch = trio.open_memory_channel[Tuple[Member, ...]](0)

    groups: List[Tuple[Member, ...]] = []
    group: List[Member] = []
    
    # streams that will still be waiting in the lobby (because they aren't
    # enough). This happens when player_number % group_size != 0

    extra_client_streams: List[net.JSONStream] = []

    with trio.move_on_after(3) as out:
            
        async with trio.open_nursery() as nursery:

            lobby.new_lobby(nursery, conn_getch, group_sendch, group_size)

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
                    assert await group_getch.receive() == expected

            assert sub.cancelled_caught is False, \
                "Awaiting group_getch took too long"

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
            await group_getch.receive()

    assert cancel_scope.cancelled_caught is False,\
            "group get channel blocked for too long (should have been closed)"

    # Note that the other connection that the lobby has *given* to the server
    # should still be open.