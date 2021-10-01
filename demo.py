from rich import print
from rich.panel import Panel, Text
title = Text.assemble(("Options Terminal Console", "bold blue underline"), justify="center")
para = "Welcome to [blue]Options Terminal Console[/] - the premier options management system, right within your console!"

print(Panel(Text.from_markup(para), title=title))