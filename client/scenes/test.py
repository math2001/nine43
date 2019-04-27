import pygame
import client.gui as gui
from client.resman import *
from client.types import *
from client.const import *

content = "Show for the first time! hello to the whole world, one heck of a line here"


class Test(Scene):
    def __init__(self, nursery: Nursery, screen: Screen, pdata: SimpleNamespace):
        super().__init__(nursery, screen, pdata)

        self.button = gui.Button(
            text="Show popup?", on_click=self.show_modal, screen=self.screen
        )
        self.button.rect.center = self.screen.rect.center

        self.modal = gui.Modal(
            title="Hello world",
            content=content,
            ok="Done",
            on_ok=self.hide_modal,
            width=400,
            screen=self.screen,
        )
        self.modal.rect.center = self.screen.rect.center
        self.modal.moved()

        self.count = 0

    def handle_event(self, e: Event) -> bool:
        if self.modal.handle_event(e):
            return True
        return self.button.handle_event(e)

    def render(self) -> None:
        self.button.render()
        self.modal.render()

    def show_modal(self) -> None:
        self.count += 1
        self.modal.visible = True
        self.button.alter(text=f"Show popup ({self.count})")
        # self.modal.alter(content=f'Showed for {self.count}th time')
        self.modal.rect.center = self.screen.rect.center
        self.button.rect.center = self.screen.rect.center
        # self.modal.moved()

    def next_scene(self) -> str:
        return ""

    def finish(self) -> None:
        pass

    def hide_modal(self) -> None:
        self.modal.visible = False
