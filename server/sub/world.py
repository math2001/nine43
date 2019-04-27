from server.types import *


async def world(group: Group, chosen_world: World) -> Result:

    """
    World is the map, it manages player movements and updates.
    """
