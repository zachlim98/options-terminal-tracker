import getpass
from rich import table

from selenium import webdriver
from rich.console import Console
from rich.table import Table
from rich.progress import track

import rich.box
from rich.console import group
from rich.panel import Panel
from rich.align import Align

from textual import events
from textual.app import App
from textual.widget import Reactive, Widget
from textual.widgets import Header, Footer, Static
from textual.views import WindowView

from textual_inputs import TextInput, IntegerInput

class Scraper:

    def __init__(self, driver_path=rf"/home/{getpass.getuser()}/Documents/", driver_type="Firefox"):
        if driver_type=="Firefox":
            self.webdriver = driver_path + "geckodriver"
            op = webdriver.FirefoxOptions()
            op.add_argument('--headless')
            self.driver = webdriver.Firefox(executable_path=self.webdriver, options=op)
        elif driver_type=="Chrome":
            self.webdriver = driver_path + "chromedriver"
            op = webdriver.ChromeOptions()
            op.add_argument('--headless')
            self.driver = webdriver.Chrome(executable_path=self.webdriver, options=op)
        
    def etf_scrape(self):
        self.driver.get("https://www.barchart.com/options/iv-rank-percentile/etfs?orderBy=optionsImpliedVolatilityPercentile1y&orderDir=desc")

        ticker_name = [self.driver.find_element_by_xpath(f"/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/div/div[6]/div/div[2]/div/div/ng-transclude/table/tbody/tr[{i}]/td[1]/div/span[2]/a").text for i in track(range(1,101), description="Downloading Ticker Name...")]
        ticker_last = [self.driver.find_element_by_xpath(f"/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/div/div[6]/div/div[2]/div/div/ng-transclude/table/tbody/tr[{i}]/td[3]/div/span/span/span").text for i in track(range(1,101), description="Downloading Last Price...")]
        ticker_optvol = [self.driver.find_element_by_xpath(f"/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/div/div[6]/div/div[2]/div/div/ng-transclude/table/tbody/tr[{i}]/td[6]/div/span/span/span").text for i in track(range(1,101), description="Downloading Option Vol...")]
        ticker_impr = [self.driver.find_element_by_xpath(f"/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/div/div[6]/div/div[2]/div/div/ng-transclude/table/tbody/tr[{i}]/td[8]/div/span/span/span").text for i in track(range(1,101), description="Downloading IV Rank...")]
        ticker_impp = [self.driver.find_element_by_xpath(f"/html/body/main/div/div[2]/div[2]/div/div[2]/div/div/div/div[6]/div/div[2]/div/div/ng-transclude/table/tbody/tr[{i}]/td[9]/div/span/span/span").text for i in track(range(1,101), description="Downloading IV Percentile...")]

        return list(zip(ticker_name, ticker_last, ticker_optvol, ticker_impr, ticker_impp))

class Renderer:

    def __init__(self):
        self.console = Console()
    
    def last_color(self, text) -> str:
        if float(text) < 30:
            return f"[bright_green]{str(text)}[/]"
        elif float(text) > 30 and float(text) < 50:
            return f"[orange1]{str(text)}[/]"
        else:
            return f"[bright_red]{str(text)}[/]"

    def dte_color(self, text) -> str:
        if float(text) <= 21:
            return f"[bright_red]{str(text)}[/]"
        else:
            return f"{str(text)}"

    def screener_table(self, data, table_type="ETF") -> Table:
        table = Table(title=f"Screened {table_type}")
        col_name = ["Ticker", "Last", "Volume", "IV Rank", "IV Perc"]

        for i in range(len(col_name)):
            table.add_column(col_name[i])

        for i in range(0,11):
            table.add_row(data[i][0], self.last_color(data[i][1]),data[i][2],data[i][3],data[i][4])

        return table

    def trades_table(self, data) -> Table:
        table = Table(title = "Trades")
        col_name = ["Ticker", "Trade Price", "Stock BE" , "DTE"]

        for i in range(len(col_name)):
            table.add_column(col_name[i])
        
        for i in range(len(data)):
            table.add_row(data[i][0], data[i][1], data[i][2], self.dte_color(data[i][3]))
        
        return table

class MyApp(App):
    """An example of a very simple Textual App"""

    show_info = Reactive(False)

    async def on_load(self, event: events.Load) -> None:
        """Bind keys with the app loads (but before entering application mode)"""
        await self.bind("b", "view.toggle('sidebar')", "Toggle sidebar")
        await self.bind("g", "view.toggle('intro')", "Enter Info")
        await self.bind("s", "view.toggle('screener')", "View Screener")
        await self.bind("r", "refresh", "Refresh Screener")
        await self.bind("q", "quit", "Quit")
        await self.bind("enter", "submit", "Submit")

    async def on_mount(self, event: events.Mount) -> None:
        """Create and dock the widgets."""

        self.open_date = TextInput(
            name="opendate",
            placeholder="dd MMM YYYY",
            title="Open Date",
        )

        self.ticker = TextInput(
            name="ticker",
            placeholder="Stock Ticker",
            title="Ticker",
        )

        self.strike_price = IntegerInput(
            name="strike_price",
            placeholder="Strike",
            title="Strike",
        )

        self.trade_price = IntegerInput(
            name="trade_price",
            placeholder="Trd Price",
            title="Trade Prices",
        )

        self.exp_date = TextInput(
            name="exp_date",
            placeholder="dd MMM YYYY",
            title="Expiration",
        )

        self.output = Static(
            renderable=Panel(
                "",
                title="Report",
                border_style="blue",
                box=rich.box.SQUARE
            )
        )

        self.body = WindowView(Panel("Hi there! Welcome to Terminal Options!"))

        self.screen = Static(Panel("", box=rich.box.SQUARE, title="Screener", border_style="red"))

        # Header / footer / dock
        await self.view.dock(Header(), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(self.output, edge="left", size=50, name="sidebar")
        await self.view.dock(self.screen, edge="right", size=50, name="screener")

        await self.view.dock(self.body, name="intro")
        await self.view.dock(self.open_date, self.ticker, self.strike_price, self.trade_price, self.exp_date, edge="top", name="form")
                

    async def action_submit(self) -> None:
        formatted = f"""
Ticker: {self.ticker.value}
Strike: {self.strike_price.value}
Trade Price: {self.trade_price.value}
Exp: {self.exp_date.value}
        """
        await self.output.update(
            Panel(
                formatted,
                title="Report",
                border_style="blue",
                box=rich.box.SQUARE
            )
        )

    async def action_refresh(self) -> None:
        new_scrap = Scraper()
        new_render = Renderer()
        table_view = new_render.screener_table(new_scrap.etf_scrape())
        await self.screen.update(Static(Panel(Align(table_view, align="center"), box=rich.box.SQUARE, title="Screener", border_style="red")))

MyApp.run(title="OpShell", log="textual.log")