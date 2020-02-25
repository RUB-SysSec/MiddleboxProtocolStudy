import asyncio
import json
import logging
import os
import time

import tqdm

_LOGGER = logging.getLogger(__name__)

# from https://stackoverflow.com/a/5423147
_ROOT = os.path.abspath(os.path.dirname(__file__))


def get_data(path):
    return os.path.join(_ROOT, "data", path)


def read_data_file(name):
    return open(get_data(name)).read()


class FlushEveryX:
    """Asynchronous list implementation for batching inserts per interval.

    The given `flush_coro` will be called (on earliest) when the given interval has elapsed
    since last flush.
    Simply call push(), the list will be flushed based on the ctor given `interval`.

    To make sure the list gets flushed even when no new elements are pushed to the list,
    use asyncio.wait_for() and call the flush manually on timeout.

    Based on https://gist.github.com/gcbirzan/cb6a96a9c5fd2b136b2bfa51fc60d2a3
    """

    def __init__(self, flush_coro, interval=5):
        self.interval = interval
        self.data = []
        self.last_flush = None
        self._flush = flush_coro

    async def push(self, item):
        self.data.append(item)
        await self.flush()

    async def flush(self, force=False):
        """Flush the list if `interval` has elapsed since the last run."""
        if self.last_flush is None:
            self.last_flush = time.time()
        if self.last_flush < time.time() - self.interval or force:
            try:
                await self._flush(self.data)
                _LOGGER.debug("Flushed %s entries", len(self.data))
            except Exception as ex:
                _LOGGER.error("Unable to flush: %s", ex, exc_info=True)
            self.last_flush = time.time()
            self.data.clear()


async def generic_mongo_batch_inserter(queue, collection):
    """Reads the result queue from crawler and inserts entries periodically to mongodb.

    Requires json serializable data."""

    async def insert_results(results):
        if not len(results):
            return
        try:
            await collection.insert_many(results, ordered=False)
        except Exception as ex:
            _LOGGER.error("Unable to insert to mongodb: %s", ex)
            with open("unable_to_save", "a") as f:
                f.write(json.dumps(results) + "\n")

        _LOGGER.info("Added %s results to mongo", len(results))

    interval = 5
    res_queue = FlushEveryX(interval=interval, flush_coro=insert_results)
    while True:
        try:
            res = await asyncio.wait_for(queue.get(), timeout=interval)
            await res_queue.push(res)
            queue.task_done()
        except asyncio.TimeoutError:
            await res_queue.flush(force=True)


class TqdmHandler(logging.Handler):
    """Logging handler to unbreak the stdout output.

    From https://github.com/tqdm/tqdm/issues/313#issuecomment-347960988
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
