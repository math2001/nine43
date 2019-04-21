import string
import trio
import trio.testing
import net
import tests
import server.sub.select as select
from server.types import Member
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
        indexes = await select.get_chosen_world(votes_getch, nworlds, len(votes))
        assert indexes == answers

    with trio.move_on_after(2) as cancel_scope:
        async with trio.open_nursery() as nursery:
            nursery.start_soon(send_votes, votes_sendch)
            nursery.start_soon(check_decision)

    assert cancel_scope.cancelled_caught is False, \
            "Sending vote/checking decision timed out"


async def test_get_chosen_world() -> None:
    with trio.move_on_after(2) as cancel_scope:
        await _check_votes_result([1, 2, 1, 2, 3, 4, -1], [1, 2], 5)
        await _check_votes_result([1, 2, 3, 1], [1], 4)
        await _check_votes_result([0, 2, 3, 1], [0, 1, 2, 3], 4)
        await _check_votes_result([1, 2, 3, 4], [1, 2, 3, 4], 5)
        await _check_votes_result([-1, -1], [0, 1, 2, 3, 4], 5)

    assert cancel_scope.cancelled_caught is False, \
            "checking votes timed out"
    

async def _check_conversation(
        worlds: Tuple[Dict[str, str], ...],
        votes: Tuple[int, ...]) -> None:
    """ util function for conversation test """

    players: List[Member] = []
    ends: List[net.JSONStream] = []

    for i in range(len(votes)):
        left, right = tests.new_stream_pair()
        players.append(Member(right, string.ascii_letters[i]))
        ends.append(left)

    async def sel() -> None:
        await select.select(tuple(players), worlds)
        print("done with select")
        # we ignore the result of the votes, this isn't the purpose of this test

    async def send_votes(votes: Tuple[int, ...]) -> None:
        for i, vote in enumerate(votes):
            print("doing vote", i)
            assert await ends[i].read() == {
                "type": "select world",
                # convert into a list because when the JSON is decoded,
                # it's decoded as a list, not a tuple
                "worlds": list(worlds)
            }

            await ends[i].write({
                "type": "vote",
                "index": vote
            })

            print('waiting for confirmation')
            msg = await ends[i].read()
            if vote == -1:
                assert msg == {"type": "vote", "input": "ignored"}
            else:
                assert msg == {"type": "vote", "input": "considered"}

    async with trio.open_nursery() as nursery:
        nursery.start_soon(sel)
        nursery.start_soon(send_votes, votes)


async def test_conversation() -> None:
    """ Ensure that the server sends the correct messages to the client """
    worlds = (
        {"a": "a"},
        {"b": "b"},
        {"c": "c"}
    )

    with trio.move_on_after(2) as cancel_scope:
        await _check_conversation(worlds, (0, 1, 1, 2, 0))
        await _check_conversation(worlds, (0, 1, 1, 2, 2, 2))

    assert cancel_scope.cancelled_caught is False, \
            "check confirmation timed out"
    