import asyncio
import logging
import random
from collections import Counter

import click
from aiohttp import web
from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient
from tqdm import tqdm

from .common import TqdmHandler, generic_mongo_batch_inserter
from .const import *
from .multiapp import MultiApp
from .udpserver import start_server

_LOGGER = logging.getLogger(__name__)


class HTTPResponder:
    def __init__(self, stats=None):
        self.queue = asyncio.Queue()
        loop = asyncio.get_event_loop()
        if stats is None:
            stats = Counter()
        self.stats = stats

        self.addr_cache = TTLCache(1000, 600)

        self.ma = MultiApp(loop=loop)
        for port in set(HTTP_PORTS):
            app = web.Application(middlewares=[self.error_middleware])
            scd_routes = [web.get(path, self.return_scd) for path in SCD_PATHS]
            post_routes = [web.post(path, self.handle_post) for path in CTL_PATHS]

            self.ma.configure_app(app, port=port)
            _LOGGER.info("Listening on port: %s" % port)
            app.add_routes(scd_routes + post_routes)

    def run(self):
        """Call multiapp to run forever."""
        self.ma.run_all()

    def return_port_mapping(self, req, data):
        self.queue.put_nowait(data)
        d = {
            "external_port": random.randint(30000, 60000),
            "internal_port": random.randint(1024, 65535),
            "protocol": "TCP",
        }
        return web.Response(
            status=200,
            headers=SSDP_MAPPING_HEADERS,
            body=SSDP_MAPPING_RESPONSE.substitute(d),
        )

    def add_port_mapping(self, req, data):
        self.queue.put_nowait(data)
        if "AddPortMapping" in data["body"]:
            return web.Response(
                status=200,
                headers=SSDP_ADD_MAPPING_HEADERS,
                body=SSDP_ADD_MAPPING_RESPONSE,
            )
        else:
            err_headers = {"EXT": "", "Server": "RomPager/4.07 UPnP/1.0"}
            return web.Response(status=400, headers=err_headers)

    def return_end_of_list(self, req, data):
        self.queue.put_nowait(data)
        return web.Response(status=500, headers=ERROR_HEADERS, body=SSDP_MAPPING_END)

    def get_data_from_req(self, req):
        peername = req.transport.get_extra_info("peername")
        sockname = req.transport.get_extra_info("sockname")
        host = port = dstport = dstip = None
        if peername is not None:
            host, port = peername

        if sockname is not None:
            dstip, dstport = sockname

        data = {
            "headers": req.headers,
            "path": req.path,
            "method": req.method,
            "srcip": host,
            "srcport": port,
            "dstport": dstport,
            "dstip": dstip,
        }
        return data

    async def handle_post(self, req: web.Request):
        def return_error(data, error):
            data["error"] = error
            self.queue.put_nowait(data)
            return web.Response(status=500)

        data = self.get_data_from_req(req)
        if data["srcport"] is None:
            return return_error()

        self.stats["posts_seen"] += 1

        text = await req.text()
        _LOGGER.debug("POST called: %s" % text)
        data["body"] = text

        srcip = data["srcip"]
        dstport = data["dstport"]
        addr_cache_key = (srcip, dstport)
        if addr_cache_key not in self.addr_cache:
            self.addr_cache[addr_cache_key] = 0

        if "SOAPACTION" not in req.headers:
            data["no_action"] = True
            _LOGGER.info("<< POST %s on %s - no soapaction", srcip, dstport)
            return return_error(data, "no action")
        else:
            act = req.headers["SOAPACTION"]
            _LOGGER.info("<< POST %s on %s - soapaction: %s", srcip, dstport, act)
            self.stats[act] += 1
            data["soap_action"] = act

            if "GetGenericPortMappingEntry" in act:
                self.addr_cache[addr_cache_key] += 1
                if self.addr_cache[addr_cache_key] > 5:
                    data["too_many_getmappings"] = True
                    self.stats["too_many_getmappings"] += 1
                    return self.return_end_of_list(req, data)

                return self.return_port_mapping(req, data)
            elif "AddPortMapping" in act:
                return self.add_port_mapping(req, data)
            else:
                data["unsupported_action"] = True
                return return_error(data, "unsupported action")

    async def return_scd(self, req):
        self.stats["scds_requested"] += 1
        data = self.get_data_from_req(req)

        self.queue.put_nowait(data)

        data["body"] = await req.text()
        return web.Response(body=SSDP_WEB_RESPONSE, headers=SSDP_WEB_HEADERS)

    @web.middleware
    async def error_middleware(self, request, handler):
        """Override 404 errors
        from https://docs.aiohttp.org/en/stable/web_advanced.html#aiohttp-web-middlewares"""
        try:
            response = await handler(request)
            if response.status != 404:
                return response
        except web.HTTPException as ex:
            if ex.status != 404:
                raise

        return web.Response(status=404, body="", headers=ERROR_HEADERS)


async def update_stats(udp_bar, udp_stats, http_bar, http_stats):
    while True:
        # print(udp_stats)
        udp_bar.update()
        udp_bar.set_postfix(udp_stats)
        udp_bar.refresh()

        http_bar.update()
        http_bar.set_postfix(http_stats)
        http_bar.update()
        await asyncio.sleep(10)


@click.group()
def cli():
    """SSDPPot -- UPnP IGD honeypot"""
    pass


@cli.command()
@click.option("--ip", required=False)
@click.option("--full", default=False)
@click.option("--interface", required=True)
def tcpdump(ip, full, interface):
    """Dump command-line filter for tcpdump"""
    port_flt = (
        " or ".join([f"tcp dst port {port}" for port in HTTP_PORTS.keys()])
        + " or udp dst port 1900"
    )
    if ip:
        port_flt = f"dst {ip} and ({port_flt})"

    cmd = port_flt
    if full:
        cmd = f"tcpdump -i {interface} -s0 -v {port_flt}"

    click.echo(cmd)


@cli.command()
@click.option("--connstring", default="mongodb://localhost")
@click.option("--database", default="ssdppot")
@click.option("-d", "--debug", is_flag=True)
def run(connstring, database, debug):
    """Start the honeypot"""
    lvl = logging.INFO
    if debug:
        lvl = logging.DEBUG

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    [logging.root.removeHandler(handler) for handler in logging.root.handlers[:]]

    formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s")

    stdout_handler = TqdmHandler()
    stdout_handler.setLevel(lvl)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    errorlog_handler = logging.FileHandler("ssdppot_errors.log")
    errorlog_handler.setLevel(logging.WARNING)
    errorlog_handler.setFormatter(formatter)
    logger.addHandler(errorlog_handler)

    print(HTTP_PORTS)
    _LOGGER.info(
        "SCD/POST ports (%s): %s", len(HTTP_PORTS), ",".join(map(str, HTTP_PORTS))
    )
    _LOGGER.info("SCD endpoints (%s): %s", len(SCD_PATHS), SCD_PATHS)
    _LOGGER.info("POST endpoints (%s) %s", len(CTL_PATHS), CTL_PATHS)

    client = AsyncIOMotorClient(connstring)
    db = client[database]
    coll = db["http"]

    # start udp server
    udp_stats = Counter()  # need to pass separately...
    udp = start_server(connstring, database, udp_stats)
    asyncio.ensure_future(udp)
    udp_bar = tqdm(desc="UDP", position=0, total=0)

    # start http server and mongoinsert
    http_stats = Counter()
    http = HTTPResponder(http_stats)
    http_bar = tqdm(desc="HTTP", position=1, total=0)
    # Need to initialize before http.run to keep updating
    asyncio.ensure_future(update_stats(udp_bar, udp_stats, http_bar, http_stats))

    asyncio.ensure_future(generic_mongo_batch_inserter(http.queue, coll))
    asyncio.ensure_future(http.run())


if __name__ == "__main__":
    cli()
