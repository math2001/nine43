import logging
import net
import trio
from server.types import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


async def initiator(
    connch: RecvCh[trio.abc.Stream], playerch: SendCh[Player], quitch: RecvCh[Player]
) -> None:

    log.info("initiator started")

    usernameslk = Lockable[List[str]]([])

    async with playerch:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(release_usernames, quitch, usernameslk)
            async for conn in connch:
                nursery.start_soon(initiate_conn, conn, playerch, usernameslk)

            log.debug(
                "connch closed. %d tasks left in nursery", len(nursery.child_tasks)
            )

    log.info("initiator finished")


async def release_usernames(
    quitch: RecvCh[Player], usernameslk: Lockable[List[str]]
) -> None:

    async for player in quitch:
        log.debug(f"removing {player.username!r} from list of usernames")
        async with usernameslk as usernames:
            usernames.remove(player.username)
    log.info("quit channel closed")


async def get_username(
    stream: net.JSONStream, usernameslk: Lockable[List[str]]
) -> Optional[str]:

    msg = await stream.read()

    if msg["type"] != "log in":
        log.warning("initiating conn: invalid type %s", msg)
        return None

    if "username" not in msg:
        log.warning("initiating conn: no 'username' %s", msg)
        return None

    usernames = await usernameslk.acquire()
    if msg["username"] in usernames:
        log.info(f"username taken: {msg['username']!r}")
        await stream.write(
            {"type": "log in update", "state": "refused", "message": "username taken"}
        )
        usernameslk.release()
        return await get_username(stream, usernameslk)
    else:
        usernames.append(msg["username"])
        usernameslk.release()

    log.debug(f"got username {msg['username']!r}")
    return msg["username"]


async def initiate_conn(
    rawstream: trio.abc.Stream,
    playerch: SendCh[Player],
    usernameslk: Lockable[List[str]],
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
            if username is None:
                return log.info("connection dropped")

            player = Player(stream, username)

            log.debug(f"{username!r} accepted")

            await stream.write({"type": "log in update", "state": "accepted"})

        except net.ConnectionClosed as e:
            log.warning("connection dropped", exc_info=e)

            # remove username from the list of usernames
            if username is not None:
                async with usernameslk as usernames:
                    try:
                        usernames.remove(username)
                    except ValueError:
                        pass
            return

        log.info("conn initialized %s", player)

    if cancel_scope.cancelled_caught:
        return log.warning("initiating conn: dropping after timeout %s", stream)

    # copy the username, because once it's sent on the channel, I shouldn't
    # access player
    username = player.username
    await playerch.send(player)
    log.info("player '%s' sent", username)
