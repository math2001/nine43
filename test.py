from trio import *

async def read(chan):
    async for item in chan:
        print(item)
    print("chan closed?")

async def main():
    send, get = open_memory_channel(0) # type: abc.SendChannel, abc.ReceiveChannel
    async with open_nursery() as nursery:
        nursery.start_soon(read, get)
        await send.send("Hello")
        await send.send("World")
        await send.send("I love trio")
        await send.aclose()
    print("Should be done")

run(main)