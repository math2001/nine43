from client.utils import *
from client.const import *
from client.resman import *
from client.gui.types import *
from client.gui.button import Button
import client.gui.text as text

class Modal(GuiItem):

    def __init__(self, title: str, content: str, ok: str,
        on_ok: Callable[[], None], width: int):

        self._on_ok = on_ok

        self._btn_ok = Button(ok, self._on_ok)
        self._width = width

        with fontedit(get_font(MONO), strong=True) as font:
            title_height = text.height(font, width - 20, title)
            self._title_surf = pygame.Surface((width - 20, title_height))
            text.render(self._title_surf, font, title)

        with fontedit(get_font(MONO)) as font:
            content_height = text.height(font, width - 20, content)
            self._content_surf = pygame.Surface((width - 20, content_height))
            text.render(self._content_surf, font, content)

        self.rect = pygame.Rect(0, 0, width,
            title_height + content_height + self._btn_ok.rect.height + 30)

        self.visible = False

    def moved(self) -> None:
        """ Must be called after the Modal's rect has been moved in order to
        reposition the buttons
        """
        self._btn_ok.rect.bottomright = self.rect.bottomright
        self._btn_ok.rect.bottom -= 10
        self._btn_ok.rect.left -= 10

    def handle_event(self, e: Event) -> bool:
        if not self.visible:
            return False

        self._btn_ok.handle_event(e)
        return False

    def render(self, screen: Screen) -> None:
        if not self.visible:
            return
 
        pygame.draw.rect(screen.surf, pygame.Color("white"), self.rect, 1)
        bg = self.rect.inflate(-2, -2)
        bg.center = self.rect.center
        pygame.draw.rect(screen.surf, pygame.Color("black"), bg)

        r1 = screen.surf.blit(self._title_surf, (self.rect.left + 10,
            self.rect.top + 10))
        r2 = screen.surf.blit(self._content_surf, (self.rect.left + 10,
            self.rect.top + 10 + self._title_surf.get_height()))

        self._btn_ok.render(screen)

