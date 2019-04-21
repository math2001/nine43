import logging
import net
import trio
from server.types import Member
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

async def initiate_conn(
        socketstream: trio.SocketStream,
        memberch: SendCh[Member]
    ) -> None:

    log.debug("initiating stream %s", socketstream)

    stream = net.JSONStream(socketstream)

    try:
        msg = await stream.read()
    except net.ConnectionClosed as e:
        return log.exception("initiating conn: connection closed")

    if msg['type'] != "log in":
        return log.warning("initiating conn: invalid type %s", msg)

    if 'username' not in msg:
        return log.warning("initiating conn: no 'username' %s", msg)

    member = Member(stream, msg['username'])
    log.info("conn initialized %s", member)
    await memberch.send(member)

async def initiator(
        connch: RecvCh[trio.SocketStream],
        memberch: SendCh[Member]
    ) -> None:

    log.info("initiator started")

    async with trio.open_nursery() as nursery:
        async for conn in connch:
            nursery.start_soon(initiate_conn, conn, memberch)
                
    log.info("memberch closed")