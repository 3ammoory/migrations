import asyncio
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv('config.env')


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def getenv(key):
    return os.environ[key]
