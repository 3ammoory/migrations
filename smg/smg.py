import os
import typer
from dotenv import load_dotenv
from .utils import new_project

app = typer.Typer()
env = os.environ


@app.callback()
def read_config(env_path: str = None):
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()


@app.command()
def init(dsn: str = env.get('DB_URL'), schemaTable: str = env.get('SCHEMA_TABLE'), schemaRow: str = env.get('SCHEMA_ROW')):
