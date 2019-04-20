import random
from typings import *
import server.lobby as lobby


async def gather_votes(player: lobby.Player, votesch: SendCh[int]) -> None:
    pass

async def get_chosen_world(
        votesch: RecvCh[int],
        worlds: List[Dict[str, str]],
        nvotes: int
    ) -> int:
    # each index corresponds to the world in the worlds dicts. The number
    # represents the number of votes it received.
    votes: List[int] = [0 for _ in worlds]

    for _ in range(nvotes):
        index = await votesch.receive()
        if index is not None:
            votes[index] += 1

    maximum = max(votes)
    indexes: List[int] = []
    i = 0
    while i != -1:
        i = votes.index(maximum)
        indexes.append(i)

    return random.choice(indexes)

async def select(group: Tuple[lobby.Player, ...], worlds: List[Dict[str, str]]) -> Dict[str, str]:
    msg = {
        "type": "select world",
        "worlds": worlds
    }

    votes_sendch, votes_getch = trio.open_memory_channel[int](0)

    async with trio.open_nursery() as nursery:
        for player in group:
            nursery.start_soon(player.stream.write, msg)

        for player in group:
            nursery.start_soon(gather_votes, player, votes_sendch)

        i = await get_chosen_world(votes_getch, worlds, len(group))
        return worlds[i]
