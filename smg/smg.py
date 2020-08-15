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
    import os
    global env = os.environ


@app.command()
@coro
async def init(dsn: str = env.get('DB_URL'), schemaTable: str = env.get('SCHEMA_TABLE'), schemaRow: str = env.get('SCHEMA_ROW')):
    await new_project(dsn, schemaTable, schemaRow)
