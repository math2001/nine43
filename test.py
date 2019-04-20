import trio
from t import *

async def read(chan: trio.abc.ReceiveChannel[str]) -> None:
    async for item in chan:
        print(item)
    print("chan closed?")

async def main() -> None:
    send, get = trio.open_memory_channel[str](0)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(read, get)
        await send.send("Hello")
        await send.send("World")
        await send.send("I love trio")
        await send.aclose()
    print("Should be done")

trio.run(main)