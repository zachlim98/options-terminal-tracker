import getpass

from selenium import webdriver
from rich.console import Console
from rich.table import Table
from rich.progress import track

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
    
    def last_color(self, text):
        if float(text) < 30:
            return f"[bright_green]{str(text)}[/]"
        elif float(text) > 30 and float(text) < 50:
            return f"[orange1]{str(text)}[/]"
        else:
            return f"[bright_red]{str(text)}[/]"

    def screener_table(self, data, table_type="ETF"):
        table = Table(title=f"Screened {table_type}")
        col_name = ["Ticker", "Last", "Volume", "IV Rank", "IV Perc"]

        for i in range(0,5):
            table.add_column(col_name[i])

        for i in range(0,11):
            table.add_row(data[i][0], self.last_color(data[i][1]),data[i][2],data[i][3],data[i][4])

        self.console.print(table)

def main():
    # Create the root menu
    console = Console()
    main_loop = console.input("""Please choose [bold green]1[/] to screen or [bold green]2[/] to display the data or [bold red]q[/] to quit: """)

    while main_loop != "q":
        if main_loop == "1":
            console.print("Collecting [bold green]data[/] now...")
            new_scrap = Scraper()
            new_render = Renderer()
            new_render.screener_table(new_scrap.etf_scrape())
            main()
    exit()

main()