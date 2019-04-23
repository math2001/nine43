from client.const import *
from client.resman import *
from client.gui.types import *

class Button(GuiItem):

    def __init__(self, text: str, on_click: Callable[[], None], screen: Screen) -> None:
        self._state = NORMAL
        self.on_click = on_click
        self.screen = screen
        self.alter(text)

    def handle_event(self, event: Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(event.pos):
                self._state = HOVER
                return True
            self._state = NORMAL
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self._state = CLICKED
                self.on_click()
                return True
            self._state = NORMAL
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(event.pos):
                self._state = HOVER
                return True
            self._state = NORMAL
        return False

    def render(self) -> None:
        with fontedit(MONO)) as font:
            rect = font.get_rect(self._text)
            rect.center = self.rect.center
            font.render_to(self.screen.surf, rect, None)
            if self._state == NORMAL:
                pygame.draw.rect(self.screen.surf,
                    pygame.Color("white"), self.rect, 1)
            elif self._state in (HOVER, CLICKED):
                pygame.draw.rect(self.screen.surf,
                    pygame.Color("white"), self.rect, 2)


    def alter(self, text: str="") -> None:
        if text:
            self._text = text

        self.rect = get_font(MONO).get_rect(self._text).inflate((20, 20))
