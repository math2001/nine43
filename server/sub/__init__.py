"""
A sub the independent game phase of the server ie. the world choice, game
and end scene.

This means the server will spin up multiple instance of this class (one
per group of player).

After this, the players, if they are still here, can rejoin the lobby.
"""

import server.lobby as lobby
from typings import *

def new_sub(nursery: Nursery, group: Tuple[lobby.Player, ...]) -> None:
    pass