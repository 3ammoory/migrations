import os
import typer
from dotenv import load_dotenv
from .base import new_project
from .utils import coro, getenv

app = typer.Typer()


@ app.command()
@ coro
async def init(dsn: str = getenv('DB_URL'), schemaTable: str = getenv('SCHEMA_TABLE'), schemaRow: str = getenv('SCHEMA_ROW')):
    await new_project(dsn, schemaTable, schemaRow)
