import trio
from typings import *

def show(msg: Dict[str, Any]) -> None:
    print(msg['hello'])

async def read(chan: RecvCh[str]) -> Dict[str, Any]:
    async for item in chan:
        print(item)
    print("chan closed?")
    return {"hello world": "test"}

async def read_forever(chan: RecvCh[str]) -> None:
    msg = await read(chan)
    print(msg['hello'])
    # show(msg)

async def main() -> None:
    send, get = trio.open_memory_channel[str](0)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(read_forever, get)
        await send.send("Hello")
        await send.send("World")
        await send.send("I love trio")
        await send.aclose()
    print("Should be done")

trio.run(main)