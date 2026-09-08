import logging

import httpx

from backend.models import AgentEvent

logger = logging.getLogger(__name__)


class HttpEventEmitter:
    def __init__(self, endpoint: str, timeout: float = 2.0) -> None:
        self.endpoint = endpoint
        self.timeout = timeout

    def __call__(self, event: AgentEvent) -> None:
        try:
            response = httpx.post(
                self.endpoint,
                json=event.model_dump(mode="json"),
                timeout=self.timeout,
            )
            response.raise_for_status()
        except (httpx.HTTPError, OSError):
            logger.warning("Agent Office is unavailable; live event was dropped")
