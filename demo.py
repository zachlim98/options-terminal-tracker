from datetime import datetime

from rich.align import Align
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box

from textual import events
from textual.app import App
from textual.widget import Widget

from yahoo_fin import stock_info as si

from rich.progress import track

class demo_Render():

    def render_table(self, data):
        table = Table(title="")
        col_name = ["Losers", "% Change", "Gainers", "% Change"]

        for i in range(len(col_name)):
            table.add_column(col_name[i])

        for i in range(len(data)):
            table.add_row(data[i][0], str(data[i][1]), data[i][2], str(data[i][3]))

        return table

    @staticmethod
    def color_text(text):

        return f"[chartreuse2]{text}" if float(text.removesuffix("%")) > 0 else f"[deep_pink4]{text}"


class Stock_Prices(Widget):

    def __init__(self, data, account, name = None) -> None:
        super().__init__(name=name)
        self.account = account
        self.tg = data[2].loc[0:4]
        self.tl = data[3].loc[0:4]
        self.futs = data[0].loc[0:3]
        self.status = data[1]
        self.pnl = float(self.account.value) - float(self.account.base)
        self.pnlp = round(self.pnl/self.account.value * 100, 2)

    def on_mount(self):
        self.set_interval(20, self.refresh)        

    def render(self):
        
        new_render = demo_Render()
        
        #prepare top gainers and losers for render
        data_tgtl = list(zip(self.tl.loc[:,"Symbol"], self.tl.loc[:, "% Change"], self.tg.loc[:,"Symbol"], self.tg.loc[:, "% Change"]))

        mkt_formatted = f"""
        [bold]Market[/]: [underline]{self.status}[/]
        [blue3 bold]ES[/]: {self.futs.iloc[0,2]} (""" + new_render.color_text(self.futs.iloc[0,5]) + f""")
        [orange4 bold]YM[/]: {self.futs.iloc[1,2]} (""" + new_render.color_text(self.futs.iloc[1,5]) + f""")
        [hot_pink3 bold]NQ[/]: {self.futs.iloc[2,2]} (""" + new_render.color_text(self.futs.iloc[2,5]) + f""")
        [gold3 bold]VXX[/]: {round(si.get_live_price("VXX"),2)}
        """

        if self.pnl > 0:
            acc_formatted = f"""
            [bold]Total value[/]: {self.account}  
            [bold]Deposit amt[/]: {self.account.base}
            [bold]P&L[/]: [chartreuse2]{self.pnl}[/]
            [bold]P&L % [/]: [chartreuse2]{self.pnlp}[/]
            """
        else:
            acc_formatted = f"""
            [bold]Total value[/]: {self.account}  
            [bold]Deposit amt[/]: {self.account.base}
            [bold]P&L[/]: [deep_pink4]{self.pnl}[/]
            [bold]P&L % [/]: [deep_pink4]{self.pnlp}[/]
            """

        layout = Layout()
        layout.split_row(
            Layout(Panel(Align.center(mkt_formatted, vertical="middle"), title="Market update", border_style="red")),
            Layout(Panel(Align.center(acc_formatted, vertical="middle"), border_style="yellow", title="My account")),
            Layout(Panel(Align.center(new_render.render_table(data_tgtl), vertical="middle"), 
            border_style="blue", title="Losers and Gainers",
            box=box.DOUBLE))
        )
        return layout


class ClockApp(App):

    async def on_load(self, event: events.Load):
        
                # create new console object to pretty print
        console = Console()

        # print colored splashscreen
        console.print("""

        ______   .______   [red]  _______. __    __   _______  __       __      [/]
        /  __  \  |   _  \  [orange4] /       ||  |  |  | |   ____||  |     |  |     [/]
        |  |  |  | |  |_)  | [yellow]|   (----`|  |__|  | |  |__   |  |     |  |     [/]
        |  |  |  | |   ___/  [green] \   \    |   __   | |   __|  |  |     |  |     [/]
            |  `--'  | |  |   [blue].----)   |   |  |  |  | |  |____ |  `----.|  `----.[/]
            \______/  | _|   [violet]|_______/    |__|  |__| |_______||_______||_______|[/]

        A [bold]W200[/] Project by [underline]Zachary[/]

        """, justify="center")

        load_list = [si.get_futures, si.get_market_status, si.get_day_gainers, si.get_day_losers]

        self.data_list = []

        for i in track(range(len(load_list)),description="Loading data"):
            self.data_list.append(load_list[i]())

    async def on_mount(self):
        await self.view.dock(Stock_Prices(self.data_list))


ClockApp.run()