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
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def load_worlds_metadata() -> List[Dict[str, str]]:
    return [
        {
            "name": "default",
            "description": "don't worry. be happy."
        }
    ]

async def new_sub(group: Tuple[lobby.Player, ...]) -> None:
    log.info("[sub] select")
    try:
        worldname = await select.select(group, load_worlds_metadata())
    except Exception as e:
        return log.exception("sub crashed: select failed")

    log.info("[sub] world '%s'", worldname)
    result = await world.world(group, worldname)

    log.info("[sub] fin")
    await fin.fin(group, result)

    # TODO: loop back, but change lobby first (see note at the top of lobby.py)