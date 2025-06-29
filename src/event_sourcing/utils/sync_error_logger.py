import asyncio
from functools import wraps
from logging import getLogger
from typing import Callable, ParamSpec, TypeVar

T = TypeVar("T")
P = ParamSpec("P")


def sync_error_logger(func: Callable[P, T]) -> Callable[P, T]:
    """
    A decorator that logs the start, end, and any errors of a synchronous function execution.

    This decorator will:
    1. Log the start of the function execution with its arguments
    2. Execute the function
    3. Log the successful completion
    4. Log any errors that occur during execution and re-raise them

    :param func: The function to decorate
    :return: The decorated function
    :raises TypeError: If the function is an async function
    """
    if asyncio.iscoroutinefunction(func):
        raise TypeError(f"Function {func.__name__} must be a sync function")

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        logger = getLogger(func.__module__)

        id_str = ""
        for key in ("task_id", "job_id"):
            if key in kwargs:
                id_str = f" for {key}: {kwargs[key]}"
                break

        try:
            logger.debug(
                f"Starting {func.__name__}{id_str}",
                extra={"input": {"args": args, "kwargs": kwargs}},
            )
            result = func(*args, **kwargs)
            logger.info(
                f"Finished {func.__name__} successfully{id_str}",
                extra={"input": {"args": args, "kwargs": kwargs}},
            )
            return result
        except Exception as e:
            logger.exception(
                f"Error in {func.__name__}{id_str}",
                extra={
                    "input": {"args": args, "kwargs": kwargs},
                    "error": str(e),
                },
            )
            raise

    return wrapper
