import string
import trio
import trio.testing
import server.initiator as initiator
import net
from server.types import Member
from typings import *

def mem_pair() -> Tuple[net.JSONStream, trio.abc.Stream]:
    left, right = trio.testing.memory_stream_pair()
    client = net.JSONStream(left)
    return client, right

async def test_username() -> None:

    conn_sendch, conn_recvch = trio.open_memory_channel[trio.abc.Stream](0)
    member_sendch, member_recvch = trio.open_memory_channel[Member](0)

    conns = {
        "slow": mem_pair(),
        "quick": mem_pair(),
        "average": mem_pair(),
        "late": mem_pair()
    }

    async def got_login_request(client: net.JSONStream) -> None:
        with trio.move_on_after(2) as cancel_scope:
            assert await client.read() == {"type": "log in"}

        assert cancel_scope.cancelled_caught is False, \
                "waiting for log in request from server took to long"

    async def got_accepted(client: net.JSONStream) -> None:
        with trio.move_on_after(2) as cancel_scope:
            assert await client.read() == {
                "type": "log in update",
                "state": "accepted"
            }

        assert cancel_scope.cancelled_caught is False, \
                "waiting for log in acception from server took to long"
        

    async def client1(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:

        client, right = conns["slow"]

        async with seq(0):
            await connch.send(right)

        async with seq(2):
            await got_login_request(client)

        async with seq(5):
            await client.write({"type": "log in", "username": "slow"})
            await got_accepted(client)

    async def client2(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns["quick"]

        async with seq(1):
            await connch.send(right)
            await got_login_request(client)
            await client.write({"type": "log in", "username": "quick"})
            await got_accepted(client)

    async def client3(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns['average']

        async with seq(3):
            await connch.send(right)
            await got_login_request(client)

        async with seq(4):
            await client.write({"type": "log in", "username": "average"})
            await got_accepted(client)

    async def client4(connch: SendCh[trio.abc.Stream], seq: Seq) -> None:
        client, right = conns['late']

        async with seq(6):
            await connch.send(right)
            await got_login_request(client)
            await client.write({"type": "log in", "username": "late"})
            await got_accepted(client)

    async def get_members(memberch: RecvCh[Member]) -> None:
        order = ['quick', 'average', 'slow', 'late']

        i = 0
        async for member in memberch:
            assert member.username == order[i]
            assert member.stream == net.JSONStream(conns[order[i]][1])
            i += 1

    async def wait_for_all_clients(
            connch: SendCh[trio.abc.Stream],
            seq: Seq
        ) -> None:
        async with connch:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(client1, connch, seq)
                nursery.start_soon(client2, connch, seq)
                nursery.start_soon(client3, connch, seq)
                nursery.start_soon(client4, connch, seq)

    async def monitor(
            connch: SendCh[trio.abc.Stream],
            memberch: RecvCh[Member]) -> None:

        seq = trio.testing.Sequencer()

        with trio.move_on_after(100) as cancel_scope:

            async with trio.open_nursery() as nursery:
                nursery.start_soon(wait_for_all_clients, connch, seq)
                nursery.start_soon(get_members, memberch)

        assert cancel_scope.cancelled_caught is False, \
                "clients took too long"
        
    with trio.move_on_after(2) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(initiator.initiator, conn_recvch, member_sendch)
            nursery.start_soon(monitor, conn_sendch, member_recvch)

    assert cancel_scope.cancelled_caught is False, \
            "initator and/or monitor took too long to finish"
    