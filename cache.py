import time

import os
import pickle
from typing import Set

from config import CACHE_DIR, DEFAULT_CACHE_EXPIRE, VERY_VERY_BEGINING


class Cache:
    cached_files: Set[str] = set()

    @classmethod
    def cached(cls, cachefile, expire=DEFAULT_CACHE_EXPIRE, logger=None):
        """
        A decorator which will use "cachefile" for caching the results of the decorated function "fn".
        """
        cachefile = cls._get_path(cachefile)
        log = logger.info if logger else print

        def decorator(fn):  # define a decorator for a function "fn"
            def wrapped(*args, **kwargs):  # define a wrapper that will finally call "fn" with all arguments
                # if cache exists -> load it and return its content
                if os.path.getsize(cachefile) == 0:
                    cls.refresh(cachefile)
                elapsed_time = time.monotonic() - VERY_VERY_BEGINING
                if os.path.exists(cachefile) and elapsed_time < expire:
                    with open(cachefile, 'rb') as cachehandle:
                        log("using cached result from '%s'" % cachefile)
                        return pickle.load(cachehandle)

                # execute the function with all arguments passed
                res = fn(*args, **kwargs)
                cls.cached_files.add(cachefile)

                # write to cache file
                with open(cachefile, 'wb') as cachehandle:
                    log("saving result to cache '%s'" % cachefile)
                    pickle.dump(res, cachehandle)

                return res

            return wrapped

        return decorator

    @classmethod
    def refresh(cls, cachefile: str):
        if os.path.exists(cls._get_path(cachefile)):
            os.remove(cachefile)

    @classmethod
    def _get_path(cls, cachefile: str):
        return '{}/{}'.format(CACHE_DIR, cachefile)

    @classmethod
    def __del__(cls):
        for file in cls.cached_files:
            os.remove(file)
