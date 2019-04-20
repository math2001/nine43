""" A voting system to choose the world

This should be implemented in a much cleaner way I think: letting the user
know whether or not their vote has been taken into account isn't clean nor exact
"""

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
        await player.stream.write({
            "type": "vote",
            "input": "ignored"
        })
        return
    await votesch.send(resp['index'])
    await player.stream.write({
        "type": "vote",
        "input": "considered"
    })


async def get_chosen_world(
        votesch: RecvCh[int],
        nworlds: int,
        nvotes: int
    ) -> List[int]:
    """ Returns a list of the most popular worlds
    """

    # each index corresponds to the world in the worlds dicts. The number
    # represents the number of votes it received.
    votes: List[int] = [0 for _ in range(nworlds)]
    for _ in range(nvotes):
        index = await votesch.receive()
        if index != -1:
            votes[index] += 1

    maximum = max(votes)
    indexes: List[int] = []
    i = -1
    while i is not None:
        try:
            i = votes.index(maximum, i + 1)
        except ValueError:
            i = None
        else:
            indexes.append(i)

    return indexes

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

    indexes = await get_chosen_world(votes_getch, len(worlds), len(group))
    return worlds[random.choice(indexes)]
