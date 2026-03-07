import asyncio
import random
from collections.abc import Awaitable, Callable
from typing import Type


async def retry_async(
    fn: Callable[[], Awaitable],
    *,
    retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
) -> object:
    attempt = 0
    while True:
        try:
            return await fn()
        except exceptions as exc:
            if attempt >= retries:
                raise exc
            delay = min(max_delay, initial_delay * (2**attempt))
            if jitter:
                delay = delay * random.uniform(0.85, 1.15)
            await asyncio.sleep(delay)
            attempt += 1


async def noop_backoff_wait(_: float) -> None:
    return None
