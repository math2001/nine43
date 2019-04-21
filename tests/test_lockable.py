import pytest
import server.types

async def test_lockable():
    val_lockable = server.types.Lockable([])
    async with val_lockable as val:
        val.append(2)

    async with val_lockable as val:
        assert val == [2]

    with pytest.raises(RuntimeError):
        async with val_lockable:
            async with val_lockable:
                pass