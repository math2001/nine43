from client.const import *
from client.resman import *
from client.gui.types import *

# stolen from the pygame docs, and slightly adapted
# https://devdocs.io/pygame/ref/freetype#pygame.freetype.Font.render_to


def split_words(text: str) -> List[str]:
    lines = text.splitlines()
    words: List[str] = []
    for i, line in enumerate(lines):
        words += line.split(" ")
        if i < len(lines) - 1:
            words.append("\n")

    return words


def height(font: Font, width: int, text: str) -> int:
    words = split_words(text)

    line_height = font.get_sized_height() + 2
    x, y = 0, line_height

    with fontedit(font, origin=True) as font:
        space = font.get_rect(" ")
        for word in words:
            if word == "\n":
                x, y = 0, y + line_height
                continue

            bounds = font.get_rect(word)

            if x + bounds.x + bounds.width >= width:
                print("new line")
                x, y = 0, y + line_height

            if x + bounds.x + bounds.width >= width:
                raise ValueError(f"word {word!r} too long for width {width}")

            x += bounds.x + bounds.width + space.width

    # font size can be a tuple with (width, height) or an integer
    size: int = 0
    if isinstance(font.size, tuple):
        size = font.size[0]
    else:
        size = font.size

    # for some reason, get_sized_descender returns a negative number
    # add some extra to y so that we can see what's bellow the baseline on
    # the last line (bottom of j for example)
    return y - font.get_sized_descender(size) + 4


def render(surf: pygame.Surface, font: Font, text: str) -> None:
    words = split_words(text)

    width, height = surf.get_size()
    line_height = font.get_sized_height() + 2
    x, y = 0, line_height

    with fontedit(font, origin=True) as font:
        space = font.get_rect(" ")
        for word in words:
            if word == "\n":
                x, y = 0, y + line_height
                continue

            bounds = font.get_rect(word)

            if x + bounds.x + bounds.width >= width:
                x, y = 0, y + line_height

            if x + bounds.x + bounds.width >= width:
                raise ValueError(f"word {word!r} too long for width {width}")

            # if y - bounds.y + bounds.height >= height:
            #     raise ValueError(f"text {text!r} too long for height {height}")

            font.render_to(surf, (x, y), word, pygame.Color("white"))
            x += bounds.x + bounds.width + space.width
