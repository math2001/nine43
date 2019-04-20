""" Tests conversion of connection to a player

That involves the lobby and the server. Creating a connection should result
in a <Player> poping out on the server side.
"""

import string
import trio
import trio.testing
import net
from t import *
import server.lobby


def new_stream_pair() -> Tuple[net.JSONStream, net.JSONStream]:
    left, right = trio.testing.memory_stream_pair()
    return net.JSONStream(left), net.JSONStream(right)

async def test_lobby_groups():

    group_size = 3
    player_number = 6

    conn_sendch, conn_getch = trio.open_memory_channel(0) # type: trio.abc.SendChannel, trio.abc.ReceiveChannel
    group_sendch, group_getch = trio.open_memory_channel(0) # type: trio.abc.SendChannel, trio.abc.ReceiveChannel

    groups: List[List[server.lobby.Player]] = []
    group: List[server.lobby.Player] = []


    with trio.move_on_after(2) as out:
            
        async with trio.open_nursery() as nursery:

            server.lobby.new_lobby(nursery, conn_getch, group_sendch, group_size)

            for i in range(player_number):

                left, right = new_stream_pair()
                await left.write({"type": "log in", "username": string.ascii_letters[i]})

                group.append(server.lobby.Player(right, string.ascii_letters[i]))

                await conn_sendch.send(right)

                if len(group) == group_size:
                    groups.append(group.copy())
                    group.clear()

            with trio.move_on_after(2) as sub:
                for group in groups:
                    assert (await group_getch.receive()) == group

            assert sub.cancelled_caught is False, \
                "Awaiting group_getch took too long"

            await conn_sendch.aclose()

    assert out.cancelled_caught is False,\
            "Awaiting nursery (probably lobby) took too long"
    # some players are left in the lobby if player_number % group_size != 0

    # we could check what happens when we close conn_sendch, ie. we close the
    # server (lobby should close as well), but who cares? When the server goes
    # down, everything goes down.