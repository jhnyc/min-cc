import json
from typing import Any, Callable, Dict, List, Optional

from openai import OpenAI

from .compaction import CompactionService
from .constants import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    FALLBACK_MODELS,
    MAX_ITERATIONS,
)
from .models import AgentState, Message, ToolCall
from .tools import ToolRegistry, get_default_registry
from .utils import get_full_system_prompt


class CodingAgent:
    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        registry: ToolRegistry = None,
        compaction_service: CompactionService = None,
        fallback_models: List[str] = None,
    ):
        self.client = OpenAI(
            api_key=api_key, base_url=DEFAULT_BASE_URL, max_retries=4
        )
        self.model = model
        self.registry = registry or get_default_registry()
        self.compaction_service = compaction_service or CompactionService()

        candidates = FALLBACK_MODELS if fallback_models is None else fallback_models
        self._fallbacks = [m for m in candidates if m != model]
        self._on_event = None

        self.state = AgentState(
            messages=[Message(role="system", content=get_full_system_prompt())]
        )

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

    def _notify(self, message: str):
        if self._on_event:
            self._on_event("notice", {"message": message})

    def _switch_model(self, reason: str):
        self.model = self._fallbacks.pop(0)
        self._notify(f"Model unavailable ({reason}); falling back to {self.model}")

    def _chat(self, **kwargs):
        """Call the LLM, falling back on deprecation or upstream provider errors."""
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model, **kwargs
                )
            except Exception as e:
                status = getattr(e, "status_code", None)
                if (status == 404 or (status is not None and status >= 500)) and self._fallbacks:
                    self._switch_model(str(e))
                    continue
                raise

            error = getattr(response, "error", None)
            if getattr(response, "choices", None):
                return response
            if self._fallbacks:
                reason = error.get("message") if isinstance(error, dict) else error
                self._switch_model(reason or "empty response")
                continue
            raise RuntimeError(f"LLM provider error: {error or 'empty response'}")

    def _prepare_messages(self) -> List[Dict[str, Any]]:
        messages = []
        for msg in self.state.messages:
            m = {"role": msg.role}
            if msg.content:
                m["content"] = msg.content
            elif msg.tool_calls:
                m["content"] = ""
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
        return messages

    def _final_response(self, note: str) -> str:
        messages = self._prepare_messages()
        messages.append(
            {
                "role": "user",
                "content": f"{note} Summarize what you accomplished and what remains. Do not call tools.",
            }
        )
        try:
            response = self._chat(messages=messages)
            content = response.choices[0].message.content or note
        except Exception as e:
            content = f"{note} (summary request failed: {e})"
        self.add_message("assistant", content=content)
        return content

    def _execute_tool_call(self, tool_call) -> str:
        try:
            args = json.loads(tool_call.function.arguments or "{}")
            if not isinstance(args, dict):
                raise ValueError("arguments must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            return (
                f"Error: invalid JSON arguments for tool "
                f"{tool_call.function.name}: {e}"
            )
        return self.registry.call_tool(tool_call.function.name, args)

    def run(
        self,
        user_input: str,
        on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        max_iterations: int = MAX_ITERATIONS,
    ):
        self.add_message("user", user_input)
        self._on_event = on_event

        for _ in range(max_iterations):
            # 1. Compact if necessary
            self.state.messages = self.compaction_service.compact(
                self.state.messages, llm_client=self.client, model=self.model
            )

            # 2. Call LLM
            try:
                response = self._chat(
                    messages=self._prepare_messages(),
                    tools=self.registry.get_tool_definitions(),
                    tool_choice="auto",
                )
            except Exception as e:
                return f"Error: LLM request failed: {e}"

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

            # 3. Handle tool calls
            for tool_call in assistant_msg.tool_calls:
                if on_event:
                    on_event(
                        "tool_call",
                        {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    )

                result_content = self._execute_tool_call(tool_call)

                self.add_message(
                    role="tool", content=result_content, tool_call_id=tool_call.id
                )

        return self._final_response(f"Step limit reached ({max_iterations} iterations).")

    def clear_history(self):
        """Reset the conversation history, keeping only the system prompt."""
        self.state.messages = [Message(role="system", content=get_full_system_prompt())]
