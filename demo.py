from datetime import datetime

from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from textual import layout

from textual.app import App
from textual.widget import Widget

from yahoo_fin import stock_info as si

class Stock_Prices(Widget):
    def on_mount(self):
        self.set_interval(60, self.refresh)

    def render(self):

        SPY_data = "SPY: " + str(round(si.get_live_price("SPY"), 2))
        layout = Layout()
        layout.ratio = 2
        layout.split_row(
            Layout(name="left"),
            Layout(Panel(Align.center(SPY_data, vertical="middle")), name="middle"),
            Layout(name="right")
        )
        return Align.center(layout, vertical="middle")


class ClockApp(App):
    async def on_mount(self):
        await self.view.dock(Stock_Prices())


ClockApp.run()