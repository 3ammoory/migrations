import os
import typer
from dotenv import load_dotenv
from .base import new_project
from .utils import coro

load_dotenv()

env = os.environ
app = typer.Typer()


@app.command()
@coro
async def init(dsn: str = env.get('DB_URL'), schemaTable: str = env.get('SCHEMA_TABLE'), schemaRow: str = env.get('SCHEMA_ROW')):
    await new_project(dsn, schemaTable, schemaRow)
