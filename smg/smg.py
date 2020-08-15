import os
import typer
from dotenv import load_dotenv
from .base import new_project
from .utils import coro

app = typer.Typer()


@app.callback()
def read_config(env_path: str = None):
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv(os.path.join(os.getcwd(), 'config.env'))


@app.command()
@coro
async def init(dsn: str = os.getenv('DB_URL'), schemaTable: str = os.getenv('SCHEMA_TABLE'), schemaRow: str = os.getenv('SCHEMA_ROW')):
    await new_project(dsn, schemaTable, schemaRow)
