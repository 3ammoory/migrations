import os
import typer
from dotenv import load_dotenv
from .base import new_project, make_migrations
from .utils import coro, getenv
from typing import List

app = typer.Typer()


@app.callback()
def set_config_path():
    '''
    A tool for handling migrations in
    PostgreSQL databases which contain multiple
    schemas
    '''


@ app.command()
@ coro
async def init(dsn: str = getenv('DB_URL'), schemaTable: str = getenv('SCHEMA_TABLE'), schemaRow: str = getenv('SCHEMA_ROW')):
    await new_project(dsn, schemaTable, schemaRow)


@app.command()
def makemigrations(public: bool = False):
    make_migrations(public)
