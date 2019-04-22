import logging
import trio
import pygame
import pygame.freetype
from client.types import *
from client.scenes.username import Username
from typings import *

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

MAX_FPS = 60.0

def get_screen() -> Screen:
    surf = pygame.display.set_mode((500, 500))
    rect = surf.get_rect()
    return Screen(surf, rect)

def show_debug(screen: Screen, scene: Scene, fps: float) -> None:
    text = f"{Scene!r} | {fps} fps"

def run_scene(scene: Scene, clock: Any) -> bool:
   
    return True

async def manage_scenes(game_nursery: Nursery) -> None:

    log.info("start client")

    pygame.init()
    pygame.freetype.init()

    screen = get_screen()

    scenes: Dict[str, type] = {
        "username": Username,
    }

    scene_name = "username"

    clock = pygame.time.Clock()

    debug = True

    going = True
    while going:

        log.info(f"new scene {scene_name!r}")

        async with trio.open_nursery() as nursery:
            if scene_name not in scenes:
                raise ValueError(f"Unknown scene {scene_name!r}")

            scene = scenes[scene_name](nursery, screen)

            while scene.going:

                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        log.info("quiting")
                        scene.close()
                        going = False
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_F2:
                        debug = not debug

                scene.update()
                scene.render()

                if debug:
                    show_debug(screen, scene, clock.get_fps())

                clock.tick(MAX_FPS)

                pygame.display.flip()


            if going:
                scene_name = scene.next_scene_name()

    print("Bye")