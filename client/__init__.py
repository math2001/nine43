import logging
import trio
import pygame
import pygame.freetype
from client.resman import *
from client.types import *
from client.const import *
from client.scenes.connect import Connect
from client.scenes.username import Username
from client.scenes.lobby import Lobby
from client.scenes.test import Test

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

MAX_FPS = 60.0


def get_screen() -> Screen:
    return Screen(pygame.display.set_mode((500, 500)))


def show_debug(screen: Screen, scene: Scene, fps: float) -> None:
    with fontedit(MONO) as font:
        rect = font.get_rect(f"{scene!r} {fps:.2f} fps")
        rect.bottomright = screen.rect.bottomright
        font.render_to(screen.surf, rect, None, bgcolor=pygame.Color("black"))


async def scene_manager(game_nursery: Nursery) -> None:

    log.info("start client")

    pygame.init()
    pygame.freetype.init()

    pygame.key.set_repeat(300, 50)
    screen = get_screen()

    scenes: Dict[str, type] = {
        "username": Username,
        "connect": Connect,
        "lobby": Lobby,
        "test": Test,
    }

    scene_name = "connect"

    clock = pygame.time.Clock()

    debug = True
    pdata = SimpleNamespace()

    going = True
    while going:

        log.info(f"new scene {scene_name!r}")

        async with trio.open_nursery() as nursery:
            if scene_name not in scenes:
                raise ValueError(f"Unknown scene {scene_name!r}")

            scene = scenes[scene_name](nursery, screen, pdata)

            while scene.going:

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        log.info("quiting")
                        scene.close()
                        scene.finish()
                        going = False

                    elif scene.handle_event(e):
                        continue  # event handled

                    if e.type == pygame.KEYDOWN and e.key == pygame.K_F2:
                        debug = not debug

                screen.surf.fill(pygame.Color("black"))
                scene.update()
                scene.render()

                if debug:
                    show_debug(screen, scene, clock.get_fps())

                clock.tick(MAX_FPS)

                pygame.display.flip()
                await trio.sleep(0)

            if going:
                scene.close()
                pdata = scene.pdata
                scene_name = scene.next_scene()

            # scene should be closed in less that 2 seconds
            nursery.cancel_scope.deadline = trio.current_time() + 2

    print("Bye")


async def run() -> None:
    async with trio.open_nursery() as nursery:
        await scene_manager(nursery)
