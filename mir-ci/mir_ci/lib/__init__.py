import asyncio
from unittest.mock import Mock, call

from mir_ci import SLOWDOWN


async def await_call(mock: Mock, *args, timeout=5, **kwargs):
    """Helper function to await a call."""
    timeout = int(timeout * SLOWDOWN)

    for i in range(timeout):
        try:
            for call_args in mock.call_args_list:
                if call_args == call(*args, **kwargs):
                    return call_args
            else:
                mock.assert_any_call(*args, **kwargs)

        except AssertionError:
            if i == timeout - 1:
                raise
        await asyncio.sleep(1)
