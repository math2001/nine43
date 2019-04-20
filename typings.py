""" Watch it's typingS, with an s.

Just to make sure you're awake
"""

import trio
from typing import *
from trio_typing import *

Message = Dict[str, Any]
RecvCh = trio.abc.ReceiveChannel
SendCh = trio.abc.SendChannel