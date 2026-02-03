import json
from enum import Enum
from typing import List

from .constants import (
    CHARS_PER_TOKEN,
    SUMMARIZE_PRESERVE_COUNT,
    TOKEN_LIMIT_FALLBACK,
    TRUNCATE_KEEP_COUNT,
)
from .models import Message


class CompactionStrategy(str, Enum):
    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"


class CompactionService:
    def __init__(
        self,
        token_limit: int = TOKEN_LIMIT_FALLBACK,
        strategy: CompactionStrategy = CompactionStrategy.TRUNCATE,
    ):
        self.token_limit = token_limit
        self.strategy = strategy

    def _estimate_tokens(self, messages: List[Message]) -> float:
        return (
            sum(
                len(m.content or "")
                + len(json.dumps([tc.model_dump() for tc in (m.tool_calls or [])]))
                for m in messages
            )
            / CHARS_PER_TOKEN
        )

    def compact(
        self, messages: List[Message], llm_client=None, model: str = None
    ) -> List[Message]:
        current_tokens = self._estimate_tokens(messages)
        if current_tokens <= self.token_limit:
            return messages

        print(
            f"Compacting history using {self.strategy}... estimated {current_tokens} tokens."
        )

        if self.strategy == CompactionStrategy.TRUNCATE:
            return self._truncate(messages)
        elif self.strategy == CompactionStrategy.SUMMARIZE:
            return self._summarize(messages, llm_client, model)
        return messages

    def _truncate(self, messages: List[Message]) -> List[Message]:
        system_msg = [m for m in messages if m.role == "system"]
        others = [m for m in messages if m.role != "system"]
        # Keep system message and most recent TRUNCATE_KEEP_COUNT messages
        return system_msg + others[-TRUNCATE_KEEP_COUNT:]

    def _summarize(
        self, messages: List[Message], llm_client, model: str
    ) -> List[Message]:
        if not llm_client or not model:
            return self._truncate(messages)

        system_msg = [m for m in messages if m.role == "system"]
        to_summarize = [m for m in messages if m.role != "system"]

        # Keep the last SUMMARIZE_PRESERVE_COUNT messages as intact context, summarize the rest
        preserved = to_summarize[-SUMMARIZE_PRESERVE_COUNT:]
        old_history = to_summarize[:-SUMMARIZE_PRESERVE_COUNT]

        history_str = "\n".join(
            [f"{m.role}: {m.content or 'Tool calls...'}" for m in old_history]
        )

        try:
            summary_response = llm_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Summarize the following conversation history concisely while preserving key details, decisions, and outcomes.",
                    },
                    {"role": "user", "content": history_str},
                ],
            )
            summary_content = summary_response.choices[0].message.content
            summary_msg = Message(
                role="assistant", content=f"[CONVERSATION SUMMARY]: {summary_content}"
            )
            return system_msg + [summary_msg] + preserved
        except Exception as e:
            print(f"Summarization failed: {e}. Falling back to truncation.")
            return self._truncate(messages)
