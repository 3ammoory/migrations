import asyncio
from functools import wraps
from dotenv import load_dotenv
import os
import typer


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def getval(obj, key):
    try:
        return obj[key]
    except KeyError:
        typer.secho(f'''Key {key} is not not configured.
        Please make sure you have included in your environment variables or your config.env or set them as cli optional parameters''', fg='red')


def getenv(key, config_path=None):
    if not config_path:
        load_dotenv('config.env')
        return getval(os.environ, key)
    else:
        load_dotenv(config_path)
        return getval(os.environ, key)


def is_projectdir():
    return all(x in os.listdir() for x in ['config.json', 'public', 'tenant'])


def check_dir():
    if not is_projectdir():
        typer.secho(
            f'Error: folder {os.path.basename(os.getcwd())} is not a project directory.', fg='red')
        raise typer.Abort()


def check_locals(scope: dict):
    '''
    Can be used to check the args of a function
    as long as no other variable has been declared inside the function
    yet
    '''
    null_args = [key for key, val in scope.items() if not val]
    if null_args:
        [typer.secho(
            f'Error: Parameter {key} has not been set', fg='red') for key in null_args]
        raise typer.Abort()
