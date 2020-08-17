import os
import typer
from dotenv import load_dotenv
from .base import new_project, make_migrations
from .utils import coro, getenv
from typing import List

app = typer.Typer()
config_path = ''


@app.callback()
def set_config_path(path: str = None):
    config_path = path


@ app.command()
@ coro
async def init(dsn: str = getenv('DB_URL', path), schemaTable: str = getenv('SCHEMA_TABLE', path), schemaRow: str = getenv('SCHEMA_ROW', path)):
    await new_project(dsn, schemaTable, schemaRow)


@app.command()
def makemigrations(sql_files: List[str] = typer.Argument(None), public: bool = False):
    make_migrations(sql_files, public)
