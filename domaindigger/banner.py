import pyfiglet
from rich.console import Console
from rich.text import Text
from rich.style import Style

GREEN = Style(color="#39FF14", bold=True)
CYAN = Style(color="cyan", italic=True)

console = Console()


def show_banner():
    fig = pyfiglet.figlet_format("DOMAIN", font="big")
    fig += pyfiglet.figlet_format("DIGGER", font="big")
    text = Text(fig, style=GREEN)
    text.append("made by Paras", style=CYAN)
    console.print(text)
