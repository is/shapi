from hypercorn.asyncio import serve
import hypercorn
import asyncio

from shapi.api import app


def main():
    """Entry point for running the app."""
    config = hypercorn.Config()
    config.bind = ["0.0.0.0:9080"]
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    main()