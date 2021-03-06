import logging
import pygame
import net
import client.gui as gui
from client.resman import *
from client.types import *
from client.const import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

STATE_WAITING_INPUT = 0, "Type your username and press enter!"
STATE_WAITING_SERVER = 10, "Waiting for server response..."
STATE_REFUSED = 20, "Connection refused"
STATE_ACCEPTED = 30, "Going to lobby!"


async def submit_username(
    username: str, stream: net.JSONStream, sendch: SendCh[Message]
) -> None:
    """ Submits the username and waits for the server to accept

    it sends one value on the channel and then closes it.

    - {"type": "accepted"} if the server accepted
    - {"type": "log in update", "state": "refused", "message": <server message>}
    - {"type": "log in update", "state": "accepted"}
    """

    # TODO: retry if it's only a temporary error
    try:
        await stream.write({"type": "log in", "username": username})
    except net.ConnectionClosed as e:
        return await sendch.send({"type": "error", "error": e})

    try:
        resp = await stream.read()
    except net.ConnectionClosed as e:
        log.exception("failed to read username response")
        return await sendch.send({"type": "error", "error": e})

    if "type" not in resp:
        return await sendch.send({"type": "error", "error": f"no type {resp}"})

    if resp["type"] != "log in update":
        return await sendch.send({"type": "error", "error": f"invalid type {resp}"})

    if resp["state"] == "accepted":
        await sendch.send({"type": "accepted"})
        return await sendch.aclose()
    elif resp["state"] == "refused":
        return await sendch.send({"type": "refused", "message": resp["message"]})
    else:
        return await sendch.send({"type": "error", "error": f"invalid type in {resp}"})


class Username(Scene):
    def __init__(self, nursery: Nursery, screen: Screen, pdata: SimpleNamespace):
        super().__init__(nursery, screen, pdata)

        self.pdata.username = ""
        self.resp_sendch, self.resp_recvch = trio.open_memory_channel[Message](0)
        self.request_sent = trio.Event()

        assert hasattr(self.pdata, "stream")

        self.state = STATE_WAITING_INPUT

        self.modal = gui.Modal(
            title="Error",
            content=f"Internal error. Please report at {ISSUES}",
            ok="OK",
            on_ok=self.hide_modal,
            width=450,
            screen=self.screen,
        )

    def hide_modal(self) -> None:
        self.modal.visible = False
        self.state = STATE_WAITING_INPUT

    def handle_event(self, e: Event) -> bool:
        self.modal.handle_event(e)

        if self.state[0] != STATE_WAITING_INPUT[0]:
            return False

        if e.type != pygame.KEYDOWN:
            return False

        if e.key == pygame.K_BACKSPACE:
            if len(self.pdata.username) > 0:
                self.pdata.username = self.pdata.username[:-1]

        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):

            self.scene_nursery.start_soon(
                submit_username,
                self.pdata.username,
                self.pdata.stream,
                self.resp_sendch,
            )
            self.state = STATE_WAITING_SERVER

        elif e.unicode:
            self.pdata.username += e.unicode

        else:
            return False
        return True

    def update(self) -> None:
        if self.state[0] != STATE_WAITING_SERVER[0]:
            return

        try:
            resp = self.resp_recvch.receive_nowait()
        except trio.WouldBlock:
            return

        log.debug(f"server response: {resp}")

        if resp["type"] == "accepted":
            self.state = STATE_ACCEPTED
            self.going = False
            # the channel is being closed at the other end, but I can't be
            # bothered to do some wonky logic to wait for it. Who cares...
            return
        elif resp["type"] == "refused":
            self.modal.alter(
                content=f"LOL. Can't even join. \n\n{resp['message']}", title="Refused"
            )
            self.modal.visible = True
        elif resp["type"] == "error":
            log.error(f"Errored while sending username {resp}")
            msg = (
                f"Errored while sending username: \n\n{resp['message']}\n\n"
                f"Please report at {ISSUES}"
            )
            self.modal.alter(content=msg)
            self.modal.visible = True
        else:
            log.error(f"Unknown behaviour while sending username {resp}")
            msg = (
                f"Unknown behaviour while sending username: \n\n{resp}\n\n"
                f"Please report at {ISSUES}"
            )
            self.modal.alter(content=msg)
            self.modal.visible = True
        self.state = STATE_REFUSED

    def render(self) -> None:
        # render the username
        start = [self.screen.rect.centerx - 50, self.screen.rect.centery]

        with fontedit(MONO, origin=True) as font:
            rect = font.render_to(self.screen.surf, start, self.pdata.username)

        if self.state == STATE_WAITING_INPUT:
            # render the cursor
            start[0] += rect.width
            end = start[0] + 5, start[1]
            pygame.draw.line(self.screen.surf, pygame.Color("white"), start, end, 2)

        with fontedit(MONO, fgcolor=pygame.Color("grey")) as font:
            rect = font.get_rect(self.state[1])
            rect.midbottom = self.screen.rect.midbottom
            rect.top -= 20
            font.render_to(self.screen.surf, rect, None)

        self.modal.render()

    def next_scene(self) -> str:
        return "lobby"

    def finish(self) -> None:
        self.scene_nursery.start_soon(self.pdata.stream.aclose)
