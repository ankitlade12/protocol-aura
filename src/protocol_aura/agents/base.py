from abc import ABC, abstractmethod
from typing import Optional
from protocol_aura.protocol import (
    AuraMessage,
    AuraProfile,
    AuraQuery,
    AuraCounteroffer,
)


class BaseAgent(ABC):
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.conversation_history: list[AuraMessage] = []
    
    @abstractmethod
    async def process_message(self, message: AuraMessage) -> Optional[AuraMessage]:
        pass
    
    def log_message(self, message: AuraMessage):
        self.conversation_history.append(message)
