from client.utils import *
from client.const import *
from client.resman import *
from client.gui.types import *

# stolen from the pygame docs, and slightly adapted
# https://devdocs.io/pygame/ref/freetype#pygame.freetype.Font.render_to

def height(font: Font, width: int, text: str) -> int:
    lines = text.splitlines()
    words: List[str] = []
    for line in lines:
        words += line.split(' ')
        words.append('\n')
    del words[-1]

    line_height = font.get_sized_height() + 2
    print(line_height)
    x, y = 0, line_height

    with fontedit(font, origin=True) as font:
        space = font.get_rect(' ')
        for word in words:
            if word == '\n':
                x, y = 0, y + line_height
                continue

            bounds = font.get_rect(word)

            if x + bounds.x + bounds.width >= width:
                x, y = 0, y + line_height

            if x + bounds.x + bounds.width >= width:
                raise ValueError(f"word {word!r} too long for width {width}")

            x += bounds.x + space.width

    # for some reason, get_sized_descender returns a negative number
    # add some extra to y so that we can see what's bellow the baseline on 
    # the last line (bottom of j for example)
    return y - font.get_sized_descender(font.size) + 4

def render(surf: pygame.Surface, font: Font, text: str) -> None:
    lines = text.splitlines()
    words: List[str] = []
    for line in lines:
        words += line.split(' ')
        words.append('\n')
    del words[-1]

    width, height = surf.get_size()
    line_height = font.get_sized_height() + 2
    x, y = 0, line_height

    with fontedit(font, origin=True) as font:
        space = font.get_rect(' ')
        for word in words:
            if word == '\n':
                x, y = 0, y + line_height
                continue

            bounds = font.get_rect(word)

            if x + bounds.x + bounds.width >= width:
                x, y = 0, y + line_height * 2

            if x + bounds.x + bounds.width >= width:
                raise ValueError(f"word {word!r} too long for width {width}")

            # if y - bounds.y + bounds.height >= height:
            #     print(word)
            #     raise ValueError(f"text {text!r} too long for height {height}")

            font.render_to(surf, (x, y), word, pygame.Color('white'))
            x += bounds.width + space.width