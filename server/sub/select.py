import logging
import random
from typings import *
import server.lobby as lobby

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

async def gather_vote(player: lobby.Player, votesch: SendCh[int]) -> None:
    resp = await player.stream.read()
    if resp['type'] != 'vote':
        log.warning("gather vote: invalid type %s", resp)
        await votesch.send(-1)
        return

    await votesch.send(resp['index'])


async def get_chosen_world(
        votesch: RecvCh[int],
        nworlds: int,
        nvotes: int
    ) -> int:
    # each index corresponds to the world in the worlds dicts. The number
    # represents the number of votes it received.
    votes: List[int] = [0 for _ in range(nworlds)]

    for _ in range(nvotes):
        index = await votesch.receive()
        if index != -1:
            votes[index] += 1

    maximum = max(votes)
    indexes: List[int] = []
    i = 0
    while i != -1:
        try:
            i = votes.index(maximum, i + 1)
        except ValueError:
            i = -1
        else:
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
            nursery.start_soon(gather_vote, player, votes_sendch)

        i = await get_chosen_world(votes_getch, len(worlds), len(group))
        return worlds[i]
