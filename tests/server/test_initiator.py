import string
import trio
import trio.testing
import server.initiator as initiator
import net
from server.types import Player
from typings import *


def new_half_stream_pair() -> Tuple[net.JSONStream, trio.abc.Stream]:
    left, right = trio.testing.memory_stream_pair()
    client = net.JSONStream(left)
    return client, right


async def check_login_request(client: net.JSONStream) -> None:
    with trio.move_on_after(2) as cancel_scope:
        assert await client.read() == {"type": "log in"}

    assert (
        cancel_scope.cancelled_caught is False
    ), "waiting for log in request from server took to long"


async def got_accepted(client: net.JSONStream) -> None:
    with trio.move_on_after(2) as cancel_scope:
        assert await client.read() == {"type": "log in update", "state": "accepted"}

    assert (
        cancel_scope.cancelled_caught is False
    ), "waiting for log in acception from server took to long"


async def test_username() -> None:

    conn_sendch, conn_recvch = trio.open_memory_channel[trio.abc.Stream](0)
    player_sendch, player_recvch = trio.open_memory_channel[Player](0)
    quit_sendch, quit_recvch = trio.open_memory_channel[Player](0)

    conns = {
        "slow": new_half_stream_pair(),
        "quick": new_half_stream_pair(),
        "average": new_half_stream_pair(),
        "late": new_half_stream_pair(),
        "average2": new_half_stream_pair(),
        "closing": new_half_stream_pair(),
        "closing2": new_half_stream_pair(),
        "closing3": new_half_stream_pair(),
        "quitter": new_half_stream_pair(),
    }

    async def client_slow(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:

        client, right = conns["slow"]

        async with seq(0):
            await connch.send(right)

        async with seq(6):
            await check_login_request(client)

        async with seq(10):
            await client.write({"type": "log in", "username": "slow"})
            await got_accepted(client)

    async def client_quick(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns["quick"]

        async with seq(1):
            await connch.send(right)
            await check_login_request(client)
            await client.write({"type": "log in", "username": "quick"})
            await got_accepted(client)

    async def client_average(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns["average"]

        async with seq(2):
            await connch.send(right)
            await check_login_request(client)

        async with seq(7):
            await client.write({"type": "log in", "username": "average"})
            await got_accepted(client)

    async def client_late(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns["late"]

        async with seq(11):
            await connch.send(right)
            await check_login_request(client)
            await client.write({"type": "log in", "username": "late"})
            await got_accepted(client)

    async def client_duplicate(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns["average2"]

        async with seq(3):
            await connch.send(right)
            await check_login_request(client)

        async with seq(8):
            await client.write({"type": "log in", "username": "average"})
            assert await client.read() == {
                "type": "log in update",
                "state": "refused",
                "message": "username taken",
            }

        async with seq(12):
            await client.write({"type": "log in", "username": "average2"})
            await got_accepted(client)

    async def client_closing_reuse(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:

        client, right = conns["closing"]

        async with seq(5):
            await connch.send(right)
            await check_login_request(client)

        async with seq(13):
            await client.write({"type": "log in", "username": "closing"})
            await got_accepted(client)

    async def client_closing_giveup(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns["closing2"]

        async with seq(4):
            await connch.send(right)
            await check_login_request(client)
            await client.aclose()

        client, right = conns["closing3"]

        async with seq(9):
            await connch.send(right)
            await check_login_request(client)
            await client.write({"type": "log in", "username": "closing"})
            await client.aclose()

    async def get_players(playerch: RecvCh[Player]) -> None:
        order = ["quick", "average", "slow", "late", "average2", "closing"]

        i = 0
        async for player in playerch:
            assert player.username == order[i]
            assert player.stream == net.JSONStream(
                conns[order[i]][1]
            ), f"{order[i]!r} stream differs"
            i += 1

    async def wait_for_all_clients(
        connch: SendCh[trio.abc.Stream], quitch: SendCh[Player]
    ) -> None:
        seq = trio.testing.Sequencer()

        async with connch, quitch:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(client_slow, connch, seq)
                nursery.start_soon(client_quick, connch, seq)
                nursery.start_soon(client_average, connch, seq)
                nursery.start_soon(client_late, connch, seq)
                nursery.start_soon(client_duplicate, connch, seq)
                nursery.start_soon(client_closing_giveup, connch, seq)
                nursery.start_soon(client_closing_reuse, connch, seq)

    async def monitor(
        connch: SendCh[trio.abc.Stream],
        playerch: RecvCh[Player],
        quitch: SendCh[Player],
    ) -> None:

        async with trio.open_nursery() as nursery:
            nursery.start_soon(wait_for_all_clients, connch, quitch)
            nursery.start_soon(get_players, playerch)

    with trio.move_on_after(2) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(
                initiator.initiator, conn_recvch, player_sendch, quit_recvch
            )
            nursery.start_soon(monitor, conn_sendch, player_recvch, quit_sendch)

    assert (
        cancel_scope.cancelled_caught is False
    ), "initator and/or monitor took too long to finish"


async def test_quitter() -> None:
    # left is a net.JSONStream, right just a trio.abc.Stream

    async def spawn(
        connch: SendCh[trio.abc.Stream],
        playerch: RecvCh[Player],
        quitch: SendCh[Player],
    ) -> None:

        left, right = new_half_stream_pair()

        await connch.send(right)
        assert await left.read() == {"type": "log in"}
        await left.write({"type": "log in", "username": "first"})
        assert await left.read() == {"type": "log in update", "state": "accepted"}

        # the initiator should spit the player out
        player = await playerch.receive()

        assert player.username == "first"
        assert player.stream == net.JSONStream(right)

        # player quits from the lobby or a sub, or anything that isn't the
        # initiator
        await quitch.send(player)

        left, right = new_half_stream_pair()

        await connch.send(right)
        assert await left.read() == {"type": "log in"}
        # notice how we use the same username. It shouldn't block, because
        # the other quitted
        await left.write({"type": "log in", "username": "first"})
        assert await left.read() == {"type": "log in update", "state": "accepted"}

        player = await playerch.receive()

        assert player.username == "first"
        assert player.stream == net.JSONStream(right)

        await conn_sendch.aclose()
        await quit_sendch.aclose()

    conn_sendch, conn_recvch = trio.open_memory_channel[trio.abc.Stream](0)
    player_sendch, player_recvch = trio.open_memory_channel[Player](0)
    quit_sendch, quit_recvch = trio.open_memory_channel[Player](0)

    async with trio.open_nursery() as nursery:
        nursery.cancel_scope.deadline = trio.current_time() + 2
        nursery.start_soon(spawn, conn_sendch, player_recvch, quit_sendch)
        nursery.start_soon(initiator.initiator, conn_recvch, player_sendch, quit_recvch)

    assert (
        nursery.cancel_scope.cancelled_caught is False
    ), f"spawn timed out after 2 seconds"


async def test_empty_username() -> None:
    conn_sendch, conn_recvch = trio.open_memory_channel[trio.abc.Stream](0)
    player_sendch, player_recvch = trio.open_memory_channel[Player](0)
    quit_sendch, quit_recvch = trio.open_memory_channel[Player](0)

    async def spawn(
        connch: SendCh[trio.abc.Stream],
        playerch: RecvCh[Player],
        quitch: SendCh[Player],
    ) -> None:
        left, right = new_half_stream_pair()
        await connch.send(right)
        await check_login_request(left)
        await left.write({"type": "log in", "username": ""})
        await got_accepted(left)

        await playerch.receive()

        await connch.aclose()
        await quitch.aclose()

    async with trio.open_nursery() as nursery:
        nursery.cancel_scope.deadline = trio.current_time() + 2
        nursery.start_soon(spawn, conn_sendch, player_recvch, quit_sendch)
        nursery.start_soon(initiator.initiator, conn_recvch, player_sendch, quit_recvch)

    assert (
        nursery.cancel_scope.cancelled_caught is False
    ), f"spawn timed out after 2 seconds"
