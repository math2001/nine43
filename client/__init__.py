import trio
from client.scenemanager import manage_scenes

async def run() -> None:
    async with trio.open_nursery() as nursery:
        await manage_scenes(nursery)