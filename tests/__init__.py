import trio.testing
import net
from typings import *

def new_stream_pair() -> Tuple[net.JSONStream, net.JSONStream]:
    left, right = trio.testing.memory_stream_pair()
    return net.JSONStream(left), net.JSONStream(right)