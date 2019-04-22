"""
A sub the independent game phase of the server ie. the world choice, game
and end scene.

This means the server will spin up multiple instance of this class (one
per group of player).

After this, the players, if they are still here, can rejoin the lobby.
"""

import logging
import server.lobby as lobby
import server.sub.select as select
import server.sub.world as world
from server.types import Member
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def load_worlds_metadata() -> Tuple[Dict[str, str], ...]:
    return (
        {
            "name": "default",
            "description": "don't worry. be happy."
        },
    )

async def new_sub(group: Tuple[Member, ...]) -> None:
    log.info("[sub] select")
    try:
        chosen_world = await select.select(group, load_worlds_metadata())
    except Exception as e:
        return log.exception("sub crashed: select failed")

    log.info("[sub] world '%s'", chosen_world['name'])
    result = await world.world(group, chosen_world)

    log.info("[sub] fin")
    await fin.fin(group, result)