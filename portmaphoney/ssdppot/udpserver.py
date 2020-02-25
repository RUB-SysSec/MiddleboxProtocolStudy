import asyncio
import logging
import random
from base64 import b64encode
from collections import Counter
from datetime import datetime
from pprint import pprint as pp
from time import sleep

import click
from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient

from .common import read_data_file

_LOGGER = logging.getLogger()


class SSDPResponder:
    """Simple SSDP responder for all M-SEARCH queries."""

    def __init__(self, collection, stats):
        payload_files = [
            "upnp-udp-payload.txt",
            "upnp-udp-payload-wanip.txt",
            "upnp-udp-payload-wanppp.txt",
        ]
        self.responses = [read_data_file(f) for f in payload_files]
        self.stats = stats
        self.collection = collection

    def connection_made(self, transport):
        self.transport = transport
        self.addr_cache = TTLCache(10000, 3600)

    def parse_ssdp(self, data):
        if "M-SEARCH" in data:
            return data

        raise Exception("not msearch..")

    def datagram_received(self, data, addr_):
        self.stats["udp_received"] += 1
        parsed_correctly = False
        too_many_tries = False
        try:
            payload = self.parse_ssdp(data.decode())
            parsed_correctly = True
            self.stats["successfully_parsed"] += 1
        except Exception as ex:
            _LOGGER.error("Unable to decode data: %s", ex)
            payload = b64encode(data)

        addr, port = addr_
        _LOGGER.info("<< %s:%s: %s" % (addr, port, data))

        if addr not in self.addr_cache:
            self.addr_cache[addr] = 0

        self.addr_cache[addr] += 1

        data = {
            "ip": addr,
            "src_port": port,
            "request": payload,
            "ts": datetime.utcnow(),
            "valid_request": parsed_correctly,
        }

        if self.addr_cache[addr] > 2:
            data["too_many_tries"] = True
            too_many_tries = True

        if not parsed_correctly:
            data["failed_to_parse"] = True
            self.stats["failed_to_parse"] += 1

        try:
            asyncio.ensure_future(self.collection.insert_one(data))
        except Exception as ex:
            _LOGGER.error("Unable to insert to collection: %s" % ex)

        if not parsed_correctly:
            return

        if too_many_tries:
            _LOGGER.warning("Too many tries from %s, not responding", addr)
            return

        self.stats["responses_sent"] += 1

        for reply in self.responses:
            sleep(random.randint(0, 2))
            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug(">> %s:%s - %s", addr, port, reply)
            else:
                _LOGGER.info(">> %s:%s sent", addr, port)
            try:
                self.transport.sendto(reply.encode(), addr_)
            except Exception as ex:
                _LOGGER.error(">> %s: %s unable to send data: %s", addr, port, ex)

    def connection_lost(self, ex):
        _LOGGER.error("Lost connection: %s" % ex)


async def status(stats):
    """Loop forever and print stats when changed."""
    prev_stats = None
    while True:
        if prev_stats != stats:
            pp(stats)

        prev_stats = stats

        await asyncio.sleep(60)


async def start_server(connstring, database, stats=None):
    loop = asyncio.get_event_loop()

    if stats is None:
        stats = Counter()
    client = AsyncIOMotorClient(connstring)
    db = client[database]
    coll = db["discoveries"]

    udpserver = loop.create_datagram_endpoint(
        lambda: SSDPResponder(coll, stats), local_addr=("0.0.0.0", 1900)
    )

    _LOGGER.info("Trying to start UDP server")
    await udpserver
    _LOGGER.info("Server started!")


@click.command()
@click.option("--connstring", default="mongodb://localhost")
@click.option("--database", default="ssdppot")
@click.option("-d", "--debug", is_flag=True)
def cli(connstring, database, debug):
    loop = asyncio.get_event_loop()

    lvl = logging.INFO
    if debug:
        lvl = logging.DEBUG
    logging.basicConfig(level=lvl)

    asyncio.ensure_future(start_server(connstring, database))
    _LOGGER.info("started the server, running forever.")
    loop.run_forever()


if __name__ == "__main__":
    cli()
