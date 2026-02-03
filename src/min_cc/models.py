from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: str

class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    is_error: bool = False

class Message(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool result messages

class AgentState(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
