import json
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI

from .compaction import CompactionService
from .constants import DEFAULT_BASE_URL, DEFAULT_MODEL, SYSTEM_PROMPT
from .models import AgentState, Message, ToolCall
from .tools import ToolRegistry, get_default_registry


class CodingAgent:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        registry: ToolRegistry = None,
        compaction_service: CompactionService = None,
    ):
        self.client = OpenAI(api_key=api_key, base_url=DEFAULT_BASE_URL)
        self.model = model
        self.state = AgentState(
            messages=[Message(role="system", content=SYSTEM_PROMPT)]
        )
        self.registry = registry or get_default_registry()
        self.compaction_service = compaction_service or CompactionService()

    def add_message(
        self,
        role: str,
        content: str = None,
        tool_calls: List[ToolCall] = None,
        tool_call_id: str = None,
    ):
        self.state.messages.append(
            Message(
                role=role,
                content=content,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
            )
        )

    def run(
        self,
        user_input: str,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.add_message("user", user_input)

        while True:
            # 1. Compact if necessary
            self.state.messages = self.compaction_service.compact(
                self.state.messages, llm_client=self.client, model=self.model
            )

            # 2. Prepare messages
            messages = []
            for msg in self.state.messages:
                m = {"role": msg.role}
                if msg.content:
                    m["content"] = msg.content
                if msg.tool_calls:
                    m["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": tc.arguments},
                        }
                        for tc in msg.tool_calls
                    ]
                if msg.tool_call_id:
                    m["tool_call_id"] = msg.tool_call_id
                messages.append(m)

            # 3. Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.registry.get_tool_definitions(),
                tool_choice="auto",
            )

            assistant_msg = response.choices[0].message

            # Format tool calls for our internal model
            internal_tool_calls = None
            if assistant_msg.tool_calls:
                internal_tool_calls = [
                    ToolCall(
                        id=tc.id, name=tc.function.name, arguments=tc.function.arguments
                    )
                    for tc in assistant_msg.tool_calls
                ]

            self.add_message(
                role="assistant",
                content=assistant_msg.content,
                tool_calls=internal_tool_calls,
            )

            if not assistant_msg.tool_calls:
                # Agent is finished with this turn
                return assistant_msg.content

            # 4. Handle tool calls
            for tool_call in assistant_msg.tool_calls:
                if on_event:
                    on_event(
                        "tool_call",
                        {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    )

                args = json.loads(tool_call.function.arguments)
                result_content = self.registry.call_tool(tool_call.function.name, args)

                self.add_message(
                    role="tool", content=result_content, tool_call_id=tool_call.id
                )
