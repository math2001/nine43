import logging
import net
import trio
from server.types import Member
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def initiate_conn(
        rawstream: trio.abc.Stream,
        memberch: SendCh[Member]
    ) -> None:

    log.debug("initiating stream")

    stream = net.JSONStream(rawstream)

    with trio.move_on_after(120) as cancel_scope:
        # request log in infos
        try:
            await stream.write({"type": "log in"})
        except net.ConnectionClosed:
            return log.exception("initiating conn: asking infos")

        try:
            msg = await stream.read()
        except net.ConnectionClosed:
            return log.exception("initiating conn; reading response")

        if msg['type'] != "log in":
            return log.warning("initiating conn: invalid type %s", msg)

        if 'username' not in msg:
            return log.warning("initiating conn: no 'username' %s", msg)

        member = Member(stream, msg['username'])

        try:
            await stream.write({"type": "log in update", "state": "accepted"})
        except net.ConnectionClosed:
            return log.exception("initiating conn: sending 'accept' update")

        log.info("conn initialized %s", member)


    if cancel_scope.cancelled_caught:
        return log.warning("initiating conn: dropping after timeout %s", stream)

    # copy the username, because once it's sent on the channel, I shouldn't
    # access member
    username = member.username
    await memberch.send(member)
    log.info("member '%s' sent", username)

async def initiator(
        connch: RecvCh[trio.abc.Stream],
        memberch: SendCh[Member]
    ) -> None:

    log.info("initiator started")

    async with memberch:
        async with trio.open_nursery() as nursery:
            async for conn in connch:
                nursery.start_soon(initiate_conn, conn, memberch)

            log.debug("connch closed. %d tasks left in nursery",
                len(nursery.child_tasks))

        log.critical("closing memberch")

    log.info("initiator stopped")