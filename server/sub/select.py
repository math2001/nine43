""" A voting system to choose the world

This should be implemented in a much cleaner way I think: letting the user
know whether or not their vote has been taken into account isn't clean nor exact,
because it can't check whether the vote is valid (not out of range).

It should also handle timeouts.
"""

import logging
import random
from typings import *
from server.types import Member
import server.lobby as lobby

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

async def gather_vote(player: Member, votesch: SendCh[int]) -> None:
    log.debug("waiting for vote from %s", player)
    resp = await player.stream.read()
    log.debug("got response from %s: %s", player, resp)

    if resp['type'] != 'vote':
        log.warning("gather vote: invalid type %s", resp)
        await votesch.send(-1)
        await player.stream.write({
            "type": "vote",
            "input": "ignored"
        })
        return

    log.debug("send vote on channel: %d", resp['index'])
    await votesch.send(resp['index'])
    log.debug("send confirmation")
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
        log.debug("Got vote for %d", index)
        if index != -1:
            votes[index] += 1

    # make sure no one sends more votes on this channel
    await votesch.aclose()

    maximum = max(votes)
    indexes: List[int] = []
    i = -1
    while True:
        try:
            i = votes.index(maximum, i + 1)
        except ValueError:
            return indexes
        else:
            indexes.append(i)

async def select(
        group: Tuple[Member, ...],
        worlds: Tuple[Dict[str, str], ...]
    ) -> Dict[str, str]:


    msg = {
        "type": "select world",
        "worlds": worlds
    }

    votes_sendch, votes_recvch = trio.open_memory_channel[int](0)

    async with trio.open_nursery() as nursery:
        log.debug("sending worlds")
        for player in group:
            nursery.start_soon(player.stream.write, msg)
        log.debug('waiting for votes')
        for player in group:
            nursery.start_soon(gather_vote, player, votes_sendch)

        indexes = await get_chosen_world(votes_recvch, len(worlds), len(group))
    return worlds[random.choice(indexes)]
