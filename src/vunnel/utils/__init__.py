import datetime
import errno
import json
import logging
import os
import random
import shutil
import time
from typing import Any, Callable

import rfc3339


def retry_with_backoff(retries: int = 10, backoff_in_seconds: int = 1) -> Callable[[Any], Any]:
    def rwb(f: Callable[[Any], Any]) -> Callable[[Any], Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger("utils:retry-with-backoff")
            attempt = 0
            while attempt < retries:
                try:
                    return f(*args, **kwargs)
                except KeyboardInterrupt:
                    logger.warning("keyboard interrupt, cancelling request...")
                    raise
                except:  # noqa: E722,B001
                    if attempt >= retries:
                        logger.exception(f"failed after {retries} retries")
                        raise

                sleep = backoff_in_seconds * 2**attempt + random.uniform(0, 1)  # nosec
                logger.warning(f"{f} failed. Retrying in {sleep} seconds (attempt {attempt+1} of {retries})")
                time.sleep(sleep)
                attempt += 1

        return wrapper

    return rwb


def silent_remove(path: str, tree: bool = False) -> None:
    try:
        if tree:
            shutil.rmtree(path)
        else:
            os.remove(path)
    except OSError as e:
        # note: errno.ENOENT = no such file or directory
        if e.errno != errno.ENOENT:
            raise


class DTEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        # if passed in object is datetime object
        # convert it to a string
        if isinstance(o, datetime.datetime):
            return rfc3339.rfc3339(o)
        # otherwise use the default behavior
        return json.JSONEncoder.default(self, o)
