"""
Run aiohttp apps in multiple ports.

Heavily adapted from https://stackoverflow.com/a/44854812
and https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web.py#L55
"""

import asyncio
import logging

from aiohttp import web, web_runner

_LOGGER = logging.getLogger(__name__)


class AppWrapper:
    def __init__(self, aioapp, port, ssl_context, loop):
        self.port = port
        self.aioapp = aioapp
        self.loop = loop
        self.ssl_context = ssl_context
        self.runner = None

    def initialize(self):
        self.runner = web_runner.AppRunner(self.aioapp)

        self.loop.run_until_complete(self.runner.setup())
        for host in ["::", "0.0.0.0"]:
            site = web_runner.TCPSite(
                self.runner, host=host, port=self.port, ssl_context=self.ssl_context
            )

            _LOGGER.debug("Starting for port %s ..", self.port)
            self.loop.run_until_complete(site.start())
        # _LOGGER.info("  done!")

    def shutdown(self):
        _LOGGER.info("Shutting down the servers.")
        self.loop.run_until_complete(self.runner.cleanup())

    def cleanup(self):
        self.loop.run_until_complete(self.aioapp.cleanup())

    def show_info(self):
        _LOGGER.info("======== Running on {} ========".format(self.port))


class MultiApp:
    def __init__(self, loop=None):
        self._apps = []
        self.user_supplied_loop = loop is not None
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

    def configure_app(self, app, port, ssl_context=None):
        app._set_loop(self.loop)
        self._apps.append(AppWrapper(app, port, ssl_context, self.loop))

    def run_all(self):
        _LOGGER.info("Initializing %s apps", len(self._apps))
        try:
            for app in self._apps:
                app.initialize()
            try:
                for app in self._apps:
                    app.show_info()
                print("(Press CTRL+C to quit)")
                self.loop.run_forever()
            except KeyboardInterrupt:  # pragma: no cover
                pass
            except Exception as ex:
                _LOGGER.error("Got exception: %s", ex, exc_info=True)
            finally:
                for app in self._apps:
                    app.shutdown()
        except Exception as ex:
            _LOGGER.error("Failed to initialize: %s", ex, exc_info=True)
        finally:
            _LOGGER.info("Cleaning up the apps.")
            for app in self._apps:
                app.cleanup()

        if not self.user_supplied_loop:
            self.loop.close()
