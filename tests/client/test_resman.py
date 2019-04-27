from client.resman import get_font, fontedit


def test_get_font() -> None:
    first = get_font("FiraMono-Medium")
    second = get_font("FiraMono-Medium")
    assert first is second, "getting same font return different object"


def test_fontedit() -> None:

    out = get_font("FiraMono-Medium")
    original = out.origin
    out.origin = True

    with fontedit(get_font("FiraMono-Medium"), origin=False) as font:
        assert font.origin == False, "font attribute hasn't been set in context manager"

    assert (
        out.origin == True
    ), "font attribute hasn't been restored properly"

    # restore to original value because get_font() always returns the same object, so this
    # might affect other tests
    out.origin = original
