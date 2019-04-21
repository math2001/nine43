import logging
import json
import trio
from utils import truncate_middle
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

BUFSIZE = 4096


class ConnectionClosed(Exception):
    pass

class JSONStream:
    """ A wrapper around a trio.Stream """

    def __init__(self, stream: trio.abc.Stream):
        self._stream = stream

        self._write_cap = trio.CapacityLimiter(1)

        # blocks reading from stream and _read_buf at the same time
        self._read_cap = trio.CapacityLimiter(1)

        self._read_buf = bytearray()

    async def read(self) -> Message:
        async with self._read_cap:
            log.debug(f"Acquired reading semaphore")
            i = self._read_buf.find(b'\n')
            while i == -1:
                try:
                    data = await self._stream.receive_some(BUFSIZE)
                except trio.BrokenResourceError:
                    raise ConnectionClosed("stream closed suddenly while reading")

                if not data:
                    raise ConnectionClosed("stream closed while reading")

                self._read_buf += data

                i = self._read_buf.find(b'\n')
                log.debug(f"Adding to buffer {data}")

            i += 1

            line = str(self._read_buf[:i], encoding='utf-8')
            self._read_buf[:i] = []

        log.debug(f"(release read semaphore) Parsing line: {line!r}")

        if line.strip() == "":
            raise ValueError(f"Invalid empty value: {line!r}")

        try:
            obj= cast(Message, json.loads(line))
        except ValueError:
            log.exception(f"Invalid JSON: {line!r}")
            raise

        if not isinstance(obj, dict):
            raise ValueError(f"should be dict, got {type(obj)} in {obj}")

        log.debug(f"Read {obj!r}")
        return obj

    async def write(self, obj: Message) -> None:
        log.debug(f"Sending {obj}")
        if not isinstance(obj, dict):
            raise ValueError(f"should send dict, got {obj!r}")

        async with self._write_cap:
            log.debug(f"Sending {obj}")
            try:
                await self._stream.send_all(bytes(json.dumps(obj) + '\n', encoding='utf-8'))
            except trio.BrokenResourceError:
                raise ConnectionClosed(f"stream closed while writing")

    async def aclose(self) -> None:
        log.info(f"closing stream {self}")
        with trio.move_on_after(1) as cancel_scope:
            await self._write_cap.acquire()
            log.debug("Got write semaphore")
            await self._read_cap.acquire()
            log.debug("Got read semaphore")

        if cancel_scope.cancelled_caught:
            log.warning("Forcefully closing stream after 1 second, "
                        "semaphore weren't acquired")

        await self._stream.aclose()
        log.debug('Stream closed, releasing semaphores')
        self._write_cap.release()
        self._read_cap.release()

    def __str__(self) -> str:
        return f"JSONStream({truncate_middle(repr(self._stream), 20)})"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, o: Any) -> bool:
        return (
            isinstance(o, JSONStream)
            and self._stream is o._stream
            and self._read_buf == o._read_buf
        )