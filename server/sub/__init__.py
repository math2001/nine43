"""
A sub the independent game phase of the server ie. the world choice, game
and end scene.

This means the server will spin up multiple instance of this class (one
per group of player).

After this, the players, if they are still here, can rejoin the lobby.
"""

import server.lobby as lobby
import server.sub.select as select
import server.sub.world as world
from typings import *

def load_worlds_metadata():
    return [
        {
            "name": "default",
            "description": "don't worry. be happy."
        }
    ]

async def new_sub(group: Tuple[lobby.Player, ...]) -> None:
    worldname = await select.select(group, worlds)
    result = await world.world(group, worldname)
    await fin.fin(group, result)

    # TODO: loop back, but change lobby first (see note at the top of lobby.py)