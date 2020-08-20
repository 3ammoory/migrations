import os
import typer
from dotenv import load_dotenv
from .base2 import Migrator as mgr
from .exceptions import UnidentifiedSQLError, NoMigrationsError
from .utils import coro, getenv, check_dir
from asyncpg.exceptions import InvalidPasswordError
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
    load_dotenv()


@ app.command()
@ coro
async def init(name: str, dsn: str = typer.Option(..., '--dsn', '-d', envvar='DB_URL', show_default=False), schemaTable: str = typer.Option(..., '--table', '-t', envvar='SCHEMA_TABLE'), schemaRow: str = typer.Option(..., '--row', '-r', envvar='SCHEMA_ROW')):
    try:
        await mgr.new_project(dsn, schemaTable, schemaRow, name)
    except InvalidPasswordError as e:
        typer.secho('Error: Incorrect database password', color='red')


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
