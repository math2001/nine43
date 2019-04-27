import pytest
import server.types
from typings import *


async def test_lockable() -> None:
    val_lockable = server.types.Lockable[List[int]]([])
    async with val_lockable as val:
        val.append(2)

    async with val_lockable as val:
        assert val == [2]

    with pytest.raises(RuntimeError):
        async with val_lockable:
            async with val_lockable:
                pass
