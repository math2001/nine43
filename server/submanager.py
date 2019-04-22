from server.types import *

async def submanager(
    stackch: RecvCh[Tuple[Member, ...]],
    memberch: SendCh[Member]) -> None:
    pass