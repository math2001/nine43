from server.types import *

async def submanager(
    stackch: RecvCh[Tuple[Player, ...]],
    playerch: SendCh[Player]) -> None:
    pass