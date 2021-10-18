import datetime
import os
import pickle
import time

import easygui as g
import rich.box
from rich import print
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import track
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from textual import events
from textual.app import App
from textual.widget import Widget
from textual.widgets import Footer, Header, Placeholder, Static

from yahoo_fin import stock_info as si

class Trade:
    """
    Trade objects will hold all the basic variables of an options trade - specifically a Cash-Secured Put.
    The basic variables to create a new trade object are:
    @parem: Open Date: DD MMM YYYY
    @parem: Ticker: AAA or BB
    @parem: Strike Price: 00.00
    @parem: Trade Price: 00.00
    @parem: Expiration Date: DD MMM YYYY
    """

    def __init__(self, open_date: str, ticker: str, strike_price : float, trade_price: float, exp_date: str) -> None:
        self.open_date = datetime.datetime.strptime(open_date, "%d %b %Y")
        self.ticker = ticker
        self.strike_price = strike_price
        self.trade_price = trade_price
        self.exp_date = datetime.datetime.strptime(exp_date, "%d %b %Y")
        self.roll_count = 0
        self.pnl = 0
        # Additional calculated variables as follow
        self.dte = (datetime.datetime.now() - self.exp_date).days
        self.breakeven = self.strike_price - self.trade_price

    def roll_trade(self, roll_price : float, exp_date: str, strike_price = None) -> None:
        """
        Allows users to manage trade by rolling forward in duration or rolling up and down in time.
        Rolling almost always involves duration so expiration date is non-optional.
        """
        if strike_price == "":
            self.strike_price = self.strike_price
        else:
            self.strike_price = strike_price
        self.roll_count += 1
        self.trade_price += roll_price
        self.exp_date = datetime.datetime.strptime(exp_date, "%d %b %Y")
        self.dte = (datetime.datetime.now() - self.exp_date).days
        self.breakeven = self.strike_price - self.trade_price

    def close_trade(self, close_price: float) -> float:
        """
        Allows users to close a trade and returns the profit and loss from the trade
        """
        self.roll_count += 1 
        self.pnl = (self.trade_price - close_price)*100 - 0.70*(self.roll_count*2)

        return self.pnl

class Account:
    """
    Main object that will handle all trade and account operations. Trade objects will never be directly accessed
    and must be accessed through an Account object.
    @parem: Deposits: 00.00 (initial monetary deposits)
    @parem: Current Value: 00.00 (initial + PnL)
    @parem: Open Trades: Dict of saved trades
    """

    def __init__(self, deposits: float, curr_value: float, open_trades: dict) -> None:
        self.base = deposits
        self.value = curr_value
        self.open_trades = open_trades
        pass

    def add_value(self, top_up):
        """
        If one deposits additional amounts
        """
        self.base += top_up

    def new_trade(self, open_date: str, ticker: str, strike_price : float, trade_price: float, exp_date: str) -> None:
        """
        Opens new Trade object and adds trade to the Account dictionary of open trades
        """
        new_trade = Trade(open_date, ticker, strike_price, trade_price, exp_date) 
        self.open_trades[ticker + " " + str(open_date)] = new_trade

    def roll_trade(self, trade_name: str, roll_price: float, exp_date: str, strike_price = None) -> None:
        """
        Higher level function that uses Trade.roll_trade
        """
        trade = self.open_trades.get(trade_name)
        trade.roll_trade(roll_price, exp_date, strike_price)
        pass

    def close_trade(self, trade_name, close_price: float) -> None:
        """
        Closes trade, removes the trade from Account dictionary and updates pnl
        """
        trade = self.open_trades.get(trade_name)
        pnl = trade.close_trade(close_price)
        self.value += pnl
        del self.open_trades[trade_name]

    def render_table(self):
        """
        Prepares open trades dictionary in the form that can be taken by a Rich.Table function to 
        render a table
        """
        open_date = [self.open_trades[key].open_date.strftime("%d %b %Y") for key in self.open_trades]
        ticker_name = [str(self.open_trades[key].ticker) for key in self.open_trades]
        trd_price = [str(self.open_trades[key].trade_price) for key in self.open_trades] 
        stock_be = [str(self.open_trades[key].breakeven) for key in self.open_trades]
        dte = [str(abs(self.open_trades[key].dte)) for key in self.open_trades]

        return list(zip(open_date, ticker_name, trd_price, stock_be, dte))

    @staticmethod
    def save_acc(account, filename):
        """
        Method that saves the current account to a pickle file for continuity
        """
        data = {}
        data["trades"] = account.open_trades
        data["balances"] = {'base_val' : account.base, "curr_val" : account.value}

        with open(filename+".pickle", 'wb') as handle:
            pickle.dump(data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load_acc(filename):
        """
        Method that opens a previously saved file
        """
        with open(filename, "rb") as handle:
            data = pickle.load(handle)

        trades = data["trades"]
        bal = data["balances"]

        account = Account(bal["base_val"], bal["curr_val"], trades)

        return account

class Renderer:
    """
    Interface between screener and account objects and terminal GUI. Contains functions that allows for information 
    from screener or accounts to be translated to renderable objects to be used by Rich and Textual
    """
    def __init__(self):
        self.console = Console()
    
    def color_text(self, text: str, col_type: str) -> str:
        """
        Function that colors text based on various criteria
        @parem: col_type = ["afford", "dte", "posneg"]
        """
        if col_type == "afford":
            if float(text) < 30:
                return f"[bright_green]{str(text)}[/]"
            elif float(text) > 30 and float(text) < 50:
                return f"[orange1]{str(text)}[/]"
            else:
                return f"[bright_red]{str(text)}[/]"
        elif col_type == "dte":
            if float(text) <= 21:
                return f"[bright_red]{str(text)}[/]"
            else:
                return f"{str(text)}"
        elif col_type == "posneg":
            if float(text) < 0:
                return f"[bright_red]{str(text)}[/]"
            else:
                return f"[bright_green]{str(text)}[/]"

    def screener_table(self, data, table_type="ETF") -> Table:
        """
        Function that returns a table object from screener information
        """
        table = Table(title=f"Screened {table_type}")
        col_name = ["Ticker", "Last", "Volume", "IV Rank", "IV Perc"]

        for i in range(len(col_name)):
            table.add_column(col_name[i])

        for i in range(0,11):
            table.add_row(data[i][0], self.color_text(data[i][1], "afford"),data[i][2],data[i][3],data[i][4])

        return table

    def trades_table(self, data) -> Table:
        """
        Function that returns a table object from account trade information
        """
        table = Table(title = "Trades")
        col_name = ["Date", "Ticker", "Trade Price", "Stock BE" , "DTE"]

        for i in range(len(col_name)):
            table.add_column(col_name[i])
        
        for i in range(len(data)):
            table.add_row(data[i][0], data[i][1], data[i][2], data[i][3], self.color_text(data[i][4], "dte"))
        
        return table

    def gain_loss_table(self, data) -> Table:
        """
        Function that returns a table object from gainers and losers
        """

        table = Table(title=f"Losers and Gainers")
        col_name = ["Losers", "% Change", "Gainers", "% Change"]

        for i in range(len(col_name)):
            table.add_column(col_name[i])

        for i in range(len(data)):
            table.add_row(data[i][0], self.color_text(data[i][1], "posneg"), data[i][2], self.color_text(data[i][3], "posneg"))

        return table

class Prompts():
    """
    Umbrella class to hold easygui prompts
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def on_load() -> Account:
        """
        Function that allows users to choose if they have an account,
        If yes account, choose file. Otherwise, create new account and fill in basic info.
        """
        if g.buttonbox(msg="Do you have an account?", choices=["Yes", "No"]) == "Yes":
            account = Account.load_acc(g.fileopenbox(msg="Please select your account file"))

        else:
            account_info = g.multenterbox(msg="Please fill in the basic information for your account",
            fields=["Deposit Amount", "Current Value"])
            if account_info is None: # we NEED to load an account, so re-open the load function
                return Prompts.on_load()
            else:
                account = Account(account_info[0], account_info[1], {})

        return account

    @staticmethod
    def open_trade(account) -> None:
        """
        Function that provides the GUI for opening new trades in an account
        """
        fieldValues = g.multenterbox(msg="Enter trade information", title="Trade Information", 
        fields=["Open Date", "Ticker", "Strike", "Trade Price", "Expiration Date"])

        account.new_trade(fieldValues[0], fieldValues[1], float(fieldValues[2]), float(fieldValues[3]), fieldValues[4])

    @staticmethod
    def edit_trade(account) -> None:
        """
        Function that provides the GUI for editing trades in an account
        """
        trdname = g.choicebox("Pick an item", "ITEM PICKER", choices=list(account.open_trades.keys()))

        if trdname not in account.open_trades:
            g.msgbox(msg="Trade not found. Please try again.")
        else:
            choiceValues = g.buttonbox(msg="Close or Roll Trade?", choices=["Close", "Roll"])
            if choiceValues == "Roll":
                fieldValues = g.multenterbox(msg="Enter updated trade information", title="Trade Editor",
                fields=["Roll Price", "Expiration Date", "Strike (Optional)"], values=[0,0,""])
                if (fieldValues is None):
                    pass
                else:
                    account.roll_trade(trdname, float(fieldValues[0]), str(fieldValues[1]), 
                    float(fieldValues[2]) if fieldValues[2] != "" else fieldValues[2])
            elif choiceValues == "Close":
                fieldValues = g.multenterbox(msg="Enter closing trade information", title="Closing Trade",
                fields=["Close Price"], values=[0])
                if (fieldValues is None):
                    pass
                else:
                    account.close_trade(trdname, float(fieldValues[0]))

class MyFooter(Footer):
    """
    Child class of parent class Footer to customize the style of the footer
    """
    def __init__(self) -> None:
        super().__init__()

    def make_key_text(self) -> Text:
        """Create text containing all the keys."""
        text = Text(
            style="blue on white",
            no_wrap=True,
            overflow="ellipsis",
            justify="left",
            end="",
        )
        for binding in self.app.bindings.shown_keys:
            key_display = (
                binding.key.upper()
                if binding.key_display is None
                else binding.key_display
            )
            hovered = self.highlight_key == binding.key
            key_text = Text.assemble(
                (f" {key_display} ", "reverse" if hovered else "default on default"),
                f" {binding.description} ",
                meta={"@click": f"app.press('{binding.key}')", "key": binding.key},
            )
            text.append_text(key_text)
        return text

class Stock_Prices(Widget):

    def __init__(self, data, name = None) -> None:
        super().__init__(name=name)
        self.tg = data[2].loc[0:4]
        self.tl = data[3].loc[0:4]

    def on_mount(self):
        self.set_interval(60, self.refresh)        

    def render(self):
        
        new_render = Renderer()
        
        #prepare top gainers and losers for render
        data_tgtl = list(zip(self.tl.loc[:,"Symbol"], self.tl.loc[:, "% Change"], self.tg.loc[:,"Symbol"], self.tg.loc[:, "% Change"]))

        layout = Layout()
        layout.split_row(
            Layout(name="left"),
            Layout(name="middle"),
            Layout(Panel(Align.center(new_render.gain_loss_table(data_tgtl), vertical="middle")))
        )
        return layout

class MyApp(App):
    """
    Main app class to display all the elements through render and to allow for 
    user interaction through prompts. Child class from textual app class
    """

    async def on_load(self, event: events.Load) -> None:

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

        # Load stock data
        load_list = [si.get_futures, si.get_market_status, si.get_day_gainers, si.get_day_losers]

        self.data_list = []

        for i in track(range(len(load_list)),description="Loading data"):
            self.data_list.append(load_list[i]())

        """Bind keys with the app load"""
        await self.bind("b", "view.toggle('screener')", "Toggle screener")
        await self.bind("q", "quit", "Quit")
        await self.bind("i", "item", "New Trade")
        await self.bind("e", "edit", "Roll/Close Trade")
        await self.bind("s", "save", "Save Account")

    async def on_mount(self, event: events.Mount) -> None:
        """Create and dock the widgets."""

        # Loads the account
        self.account = Prompts.on_load()

        # Prepare the screener
        self.screener = Static(
            renderable=Panel(
                "",
                border_style="blue",
                box=rich.box.SQUARE
            )
        )
        self.screener.visible = False

        # Prepare the trade report body
        new_render = Renderer()
        self.trades_table = Static(renderable=Panel(Align(
                new_render.trades_table(self.account.render_table())
            , align="center", vertical="middle"
        ), title="Full Report"))

        # Header / footer / sidebar docking
        await self.view.dock(Header(style="blue on white"), edge="top")
        await self.view.dock(MyFooter(), edge="bottom")
        await self.view.dock(self.screener, edge="left", size=60, name="screener")

        # Dock the remaining views in the remaining space
        await self.view.dock(Stock_Prices(self.data_list), self.trades_table,  edge="top")

    async def action_item(self) -> None:
        """
        async function to add trades and update render table
        """
        Prompts.open_trade(self.account)

        new_render = Renderer()
        await self.trades_table.update(
                Panel(
                    Align(
                    new_render.trades_table(self.account.render_table()),
        align="center", vertical="middle"),
        title="Full Report", border_style="red"))

    async def action_edit(self) -> None:
        """
        async action function to edit/close trades and update render table
        """

        Prompts.edit_trade(self.account)

        new_render = Renderer()
        await self.trades_table.update(
                Panel(
                    Align(
                    new_render.trades_table(self.account.render_table()),
        align="center", vertical="middle"),
        title="Full Report", border_style="red"))

    async def action_save(self) -> None:
        """
        async action function to save trades
        """

        while True:
            filename = g.enterbox("Choose a file name to save your account")

            if os.path.isfile(filename+".pickle"):
                if g.ynbox("File already exists. Overwrite?"):
                    Account.save_acc(self.account,filename)
                    break
                else:
                    continue
            else:
                Account.save_acc(self.account, filename)
                break


time.sleep(2)

# run the main app
MyApp.run(title="OpShell v1.0", log="textual.log")