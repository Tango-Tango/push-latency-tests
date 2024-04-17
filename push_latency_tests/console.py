import logging

import rich.traceback
from rich.console import Console
from rich.logging import RichHandler

console = Console()
error_console = Console(stderr=True)

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=error_console)],
)

rich.traceback.install(show_locals=True)
