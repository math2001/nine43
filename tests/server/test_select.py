import trio
import trio.testing
import server.sub.select as select
from typings import *

async def _check_votes_result(
        votes: List[int],
        answers: List[int],
        nworlds: int) -> None:
    """ A util function to test the return value of chosen world

    answers is plural because there can be more than one answer: when sevaral
    worlds get the same amount of vote, one gets choosen randomly
    """

    votes_sendch, votes_getch = trio.open_memory_channel[int](0)

    async def send_votes(votesch: SendCh[int]) -> None:
        for vote in votes:
            await votesch.send(vote)

    async def check_decision() -> None:
        i = await select.get_chosen_world(votes_getch, nworlds, len(votes))
        assert i in answers

    with trio.move_on_after(2) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_votes, votes_sendch)
            nursery.start_soon(check_decision)

    assert cancel_scope.cancelled_caught is False, \
            "Sending vote/checking decision timed out"


async def test_get_chosen_world() -> None:
    with trio.move_on_after(2) as cancel_scope:
        await _check_votes_result([1, 2, 1, 2, 3, 4, -1], [1, 2], 5)
        # await _check_votes_result([1, 2, 3, 1], [1], 3)
        # await _check_votes_result([1, 2, 3, 1], [1], 3)
        # await _check_votes_result([1, 2, 3, 4], [1, 2, 3, 4], 4)
        # await _check_votes_result([-1, -1], [1, 2, 3, 4, 5], 5)
    assert cancel_scope.cancelled_caught is False, \
            "checking votes timed out"
    
