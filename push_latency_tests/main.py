import logging
import sys

import typer

from .console import console, error_console

logger = logging.getLogger("stillhouse_cli")

app = typer.Typer()


@app.command()
def hello():
    console.print("Hello, World!")


@app.callback()
def main(log_level: str = "info"):
    """
    A tool to interface with the Stillhouse API.
    """
    logger.setLevel(logging.getLevelName(log_level.upper()))


if __name__ == "__main__":
    app()
