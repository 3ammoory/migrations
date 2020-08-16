import os
import typer
from dotenv import load_dotenv
from .base import new_project
from .utils import coro
import os
from decouple import config

app = typer.Typer()


@app.callback()
def read_config(env_path: str = None):
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv(os.path.join(os.getcwd(), 'config.env'))
    setattr(app, 'env', os.environ)


@app.command()
@coro
async def init(dsn: str = app.env.get('DB_URL'), schemaTable: str = app.env.get('SCHEMA_TABLE'), schemaRow: str = app.env.get('SCHEMA_ROW')):
    possible_vals = [(name, val)
                     for name, val in os.environ.items() if name.lower().startswith('s')]
    print(possible_vals)
    await new_project(dsn, schemaTable, schemaRow)
