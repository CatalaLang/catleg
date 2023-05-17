# `catdev` entry point
import asyncio
from pathlib import Path

import typer

from catala_devtools_fr.cli_util import set_basic_loglevel

from catala_devtools_fr.find_changes import find_changes

app = typer.Typer()


@app.command()
def diff(file: Path):
    with open(file, "r") as f:
        asyncio.run(find_changes(f, file_path=file))


if __name__ == "__main__":
    set_basic_loglevel()

    app()
