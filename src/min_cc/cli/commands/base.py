from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from rich.console import Console

    from min_cc.agent import CodingAgent


class CommandContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    agent: "CodingAgent"
    console: "Console"
    banner_text: str
    token_limit: int
    strategy_name: str


class Command(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def execute(self, args: str, context: CommandContext) -> Optional[bool]:
        pass
