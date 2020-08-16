import os
import typer
from dotenv import load_dotenv
from .base import new_project
from .utils import coro
import os
from decouple import config

app = typer.Typer()

config = {}


@app.callback()
def read_config(env_path: str = None):
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv(os.path.join(os.getcwd(), 'config.env'))

    config = dict(os.environ)


@app.command()
@coro
async def init(dsn: str = config.get('DB_URL'), schemaTable: str = config.get('SCHEMA_TABLE'), schemaRow: str = config.get('SCHEMA_ROW')):
    print(config)
    await new_project(dsn, schemaTable, schemaRow)
