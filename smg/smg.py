import os
import typer
from dotenv import load_dotenv
from .base2 import Migrator as mgr
from .exceptions import UnidentifiedSQLError, NoMigrationsError
from .utils import coro, getenv, check_dir
from typing import List

app = typer.Typer()


@app.callback()
def callback(public: bool = False):
    '''
    A tool for handling migrations in
    PostgreSQL databases which contain multiple
    schemas
    '''
    mgr.public = public


@ app.command()
@ coro
async def init(name: str, dsn: str = getenv('DB_URL'), schemaTable: str = getenv('SCHEMA_TABLE'), schemaRow: str = getenv('SCHEMA_ROW')):
    await mgr.new_project(dsn, schemaTable, schemaRow, name)


@app.command()
def makemigrations():
    check_dir()
    try:
        mgr.make_migrations()
    except NoMigrationsError:
        typer.secho('WARNING: 0 new migrations were found', fg='yellow')
        raise typer.Abort()
    except UnidentifiedSQLError as e:
        typer.secho(
            f'''Error: File {e.args[1]} contains sql that does not belong to upgrade or downgrade:\n{e.args[0]}''', fg='red', bg='white')
        raise typer.Abort()
