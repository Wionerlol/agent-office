from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from backend.models import Agent, AgentEvent


class AgentAdapter(ABC):
    @abstractmethod
    async def detect(self) -> list[Agent]:
        """Return agents currently visible through this adapter."""

    @abstractmethod
    async def observe(self, agent: Agent) -> AsyncIterator[AgentEvent]:
        """Yield normalized events until the underlying agent stops."""
        if False:
            yield AgentEvent.model_construct()
