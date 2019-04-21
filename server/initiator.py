import logging
import net
import trio
from server.types import *
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def get_username(
        stream: net.JSONStream,
        usernameslk: Lockable[List[str]]
    ) -> Optional[str]:

    msg = await stream.read()

    if msg['type'] != "log in":
        log.warning("initiating conn: invalid type %s", msg)
        return None

    if 'username' not in msg:
        log.warning("initiating conn: no 'username' %s", msg)
        return None


    usernames = await usernameslk.acquire()
    if msg['username'] in usernames:
        log.info(f"username taken: {msg['username']!r}")
        await stream.write({
            "type": "log in update",
            "state": "refused",
            "message": "username taken"
        })
        usernameslk.release()
        return await get_username(stream, usernameslk)
    else:
        usernames.append(msg['username'])
        usernameslk.release()

    log.debug(f"got username {msg['username']!r}")
    return msg['username']


async def initiate_conn(
        rawstream: trio.abc.Stream,
        memberch: SendCh[Member],
        usernameslk: Lockable[List[str]]
    ) -> None:

    log.debug("initiating stream")

    stream = net.JSONStream(rawstream)

    with trio.move_on_after(120) as cancel_scope:

        username = None

        try:

            log.debug("asking for log in infos")

            await stream.write({"type": "log in"})

            log.debug("getting valid username")

            username = await get_username(stream, usernameslk)
            if not username:
                return log.warning("connection dropped")


            member = Member(stream, username)

            log.debug(f"{username!r} accepted")

            await stream.write({"type": "log in update", "state": "accepted"})

        except net.ConnectionClosed:
            log.exception("connection dropped")

            # remove username from the list of usernames
            if username is not None:
                async with usernameslk as usernames:
                    try:
                        usernames.remove(username)
                    except ValueError:
                        pass
            return

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

    usernameslk = Lockable[List[str]]([])

    async with memberch:
        async with trio.open_nursery() as nursery:
            async for conn in connch:
                nursery.start_soon(initiate_conn, conn, memberch, usernameslk)

            log.debug("connch closed. %d tasks left in nursery",
                len(nursery.child_tasks))

    log.info("initiator stopped")