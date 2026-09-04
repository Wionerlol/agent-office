import logging
from collections.abc import Callable

import httpx

from backend.models import AgentEvent
from backend.runtime.storage import EventStorage

logger = logging.getLogger(__name__)


class JsonlEventEmitter:
    def __init__(self, storage: EventStorage) -> None:
        self.storage = storage

    def __call__(self, event: AgentEvent) -> None:
        self.storage.append(event)


class HttpEventEmitter:
    def __init__(self, endpoint: str, timeout: float = 2.0) -> None:
        self.endpoint = endpoint
        self.timeout = timeout

    def __call__(self, event: AgentEvent) -> None:
        response = httpx.post(
            self.endpoint,
            json=event.model_dump(mode="json"),
            timeout=self.timeout,
        )
        response.raise_for_status()


class FallbackEventEmitter:
    def __init__(
        self,
        primary: Callable[[AgentEvent], None],
        fallback: Callable[[AgentEvent], None],
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    def __call__(self, event: AgentEvent) -> None:
        try:
            self.primary(event)
        except (httpx.HTTPError, OSError):
            logger.debug("Live event endpoint unavailable; writing to JSONL", exc_info=True)
            self.fallback(event)
