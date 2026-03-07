import asyncio

from app.utils.retry import retry_async


async def test_retry_async_backoff():
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary")
        return attempts["count"]

    result = await retry_async(flaky, retries=3, initial_delay=0, max_delay=0)
    assert result == 3
    assert attempts["count"] == 3
