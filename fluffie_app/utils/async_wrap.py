from functools import wraps, partial
from typing import TypeVar, Callable, Coroutine, Any
from asyncio import get_running_loop

from typing_extensions import ParamSpec

_P = ParamSpec('_P')
_R = TypeVar('_R')

def to_async(func: Callable[_P, _R]) -> Callable[_P, Coroutine[Any, Any, _R]]:
    @wraps(func)  # Makes sure that function is returned for e.g. func.__name__ etc.
    async def run(*args, **kwargs):
        loop = get_running_loop()
        pfunc = partial(func, *args, **kwargs)  # Return function with variables (event) filled in
        return await loop.run_in_executor(None, pfunc)
    return run
