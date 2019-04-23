import abc
from client.types import *

NORMAL = 'normal'
HOVER = 'hover'
CLICKED = 'clicked'
DEBUG = False

class GuiItem(abc.ABC):

    @abc.abstractmethod
    def render(self) -> None:
        pass

    @abc.abstractmethod
    def handle_event(self, event: Event) -> bool:
        pass

    def repr(self) -> str:
        return ""

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return f"gui.{self.__class__.__name__}({self.state}{self.repr()})"