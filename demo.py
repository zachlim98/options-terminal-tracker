from rich.panel import Panel
from textual.app import App
from textual import events
from textual.reactive import Reactive
from textual.views import WindowView
from textual.widget import Widget
from textual.widgets import Button, ButtonPressed, Header, Footer, Placeholder
from random import randint
from textual.message import Message

from rich.console import Group

class WindowChange(Message):
    def can_replace(self, message: Message) -> bool:
        return isinstance(message, WindowChange)

class Intro(Widget):
    def render(self) -> Panel:
        return Panel("Hi there!!")

class GoodNight(Widget):
    def render(self) -> Panel:
        return Panel("Goodnight!")

class DynamicButtons(App):
    """The Calculator Application"""

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("q", "quit", "Quit")
        await self.bind("r", "reload_events")

    async def on_mount(self, event: events.Mount) -> None:
        """Create and dock the widgets."""
        # A scrollview to contain the markdown file
        self.body = WindowView(Intro())

        # Header / footer / dock
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")

        # Dock the body in the remaining space
        await self.view.dock(self.body, edge="top")

    async def action_reload_events(self) -> None:
        await self.body.update(GoodNight())

DynamicButtons.run(title="DynamicButtonsTest")