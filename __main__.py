import os
import asyncio
import json
import logging.config

from hypercorn.asyncio import serve
import hypercorn

from shapi.main import app

def load_logging_config():
    if os.path.exists('logging.ini'):
        os.makedirs("log", exist_ok=True)
        logging.config.fileConfig("logging.ini", disable_existing_loggers=False)

def main():
    """Entry point for running the app."""

    if os.path.exists('hypercorn.toml'):
        config = hypercorn.Config.from_toml('hypercorn.toml')
    else:
        config = hypercorn.Config()
        config.bind = ["0.0.0.0:9080"]
        config.use_reloader = True
        config.worker_class = "uvloop"
        config.workers = 1
        config.accesslog = '-'
        config.ca_certs = 'server.crt'
        config.certfile = 'server.crt'
        config.keyfile = 'server.key'

    if False:
        from shapi.misc.logutils import print_all_logging_config
        print_all_logging_config(formatted=True)
    
    asyncio.run(serve(app, config)) # type: ignore

if __name__ == "__main__":
    main()