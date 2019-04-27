from client.const import *
from client.resman import *
from client.gui.types import *
from client.gui.button import Button
import client.gui.text as text


class Modal(GuiItem):
    def __init__(
        self,
        title: str,
        content: str,
        ok: str,
        on_ok: Callable[[], None],
        width: int,
        screen: Screen,
    ):

        self._on_ok = on_ok
        self.screen = screen

        self._btn_ok = Button(ok, self._on_ok, self.screen)
        self.alter(title, content, width, ok)

        self.visible = False

    def moved(self) -> None:
        """ Must be called after the Modal's rect has been moved in order to
        reposition the buttons
        """
        self._btn_ok.rect.bottomright = self.rect.bottomright
        self._btn_ok.rect.bottom -= 10
        self._btn_ok.rect.left -= 10

    def alter(
        self, title: str = "", content: str = "", width: int = 0, ok: str = ""
    ) -> None:
        if title:
            self._title = title
        if content:
            self._content = content
        if width:
            self._width = width
        if ok:
            self._ok = ok

        prev_center: Optional[Tuple[int, int]] = None

        with fontedit(MONO, strong=True) as font:
            title_height = text.height(font, self._width - 20, self._title)
            self._title_surf = pygame.Surface((self._width - 20, title_height))
            text.render(self._title_surf, font, self._title)

        with fontedit(MONO) as font:
            content_height = text.height(font, self._width - 20, self._content)
            self._content_surf = pygame.Surface((self._width - 20, content_height))
            text.render(self._content_surf, font, self._content)

        self.rect = pygame.Rect(
            0,
            0,
            self._width,
            title_height + content_height + self._btn_ok.rect.height + 30,
        )

        self._btn_ok.alter(self._ok)

        self.rect.center = self.screen.rect.center
        self.moved()

    def handle_event(self, e: Event) -> bool:
        if not self.visible:
            return False

        self._btn_ok.handle_event(e)

        # capture every single event
        return True

    def render(self) -> None:
        if not self.visible:
            return

        pygame.draw.rect(self.screen.surf, pygame.Color("white"), self.rect, 1)
        bg = self.rect.inflate(-2, -2)
        bg.center = self.rect.center
        pygame.draw.rect(self.screen.surf, pygame.Color("black"), bg)

        r1 = self.screen.surf.blit(
            self._title_surf, (self.rect.left + 10, self.rect.top + 10)
        )
        r2 = self.screen.surf.blit(
            self._content_surf,
            (self.rect.left + 10, self.rect.top + 10 + self._title_surf.get_height()),
        )

        if DEBUG:
            pygame.draw.rect(self.screen.surf, pygame.Color("red"), r1, 1)
            pygame.draw.rect(self.screen.surf, pygame.Color("red"), r2, 1)

        self._btn_ok.render()
