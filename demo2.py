from rich.console import Console
import time

from rich.progress import SpinnerColumn, track
from rich.align import Align

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

# some time to appreciate the splash screen
for i in track(range(1,100)):
    time.sleep(0.2)
    pass