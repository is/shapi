from hypercorn.asyncio import serve
import hypercorn
import asyncio

from shapi.app import app

def main():
    """Entry point for running the app."""
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:9080"]
    config.use_reloader = True
    config.worker_class = "uvloop"
    config.workers = 1
    asyncio.run(serve(app, config)) # type: ignore

if __name__ == "__main__":
    main()