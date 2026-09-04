import logging
import os

import uvicorn

from backend.api.app import create_app
from backend.config import Settings

logging.basicConfig(
    level=os.getenv("AGENT_OFFICE_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

settings = Settings.load(os.getenv("AGENT_OFFICE_CONFIG", "config/office.yaml"))
app = create_app(settings)


def run() -> None:
    uvicorn.run("backend.main:app", host=settings.server.host, port=settings.server.port)


if __name__ == "__main__":
    run()
