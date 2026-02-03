# Min-CC.md

## Development Commands

- Sync dependencies: \`uv sync\`
- Run agent: \`uv run min-cc\`
- Run all tests: \`uv run pytest\`
- Run tests in file: \`uv run pytest tests/test_compaction.py\`
- Run single test: \`uv run pytest tests/test_compaction.py::test_name\` or \`uv run pytest -k test_name\`

## Code Architecture

CLI coding agent with tool-using conversation loop (~200-300 LOC core).

**Core Components:**
- `CodingAgent`: Manages `AgentState` (messages list). Loop: compact history → LLM call (OpenAI-compatible, tools=auto) → execute tools serially → repeat until non-tool response.
- `ToolRegistry`: Defines/handles tools: `bash` (subprocess), `read_file`, `write_file`, `replace_file_content`, `grep` (regex search), `glob`.
- `CompactionService`: Pre-LLM: truncate (system + last N messages) or summarize (LLM old history, keep recent intact) if over token limit (~80% model ctx).

**Flow:**
```
User → add_message → compact → prepare OpenAI msgs → chat.completions → parse → add assistant → if tools: execute each → add tool result → loop
```
Final assistant content returned to CLI (prompt-toolkit input loop).

**Entrypoint:** `min_cc.cli:main` (rich UI, dotenv API key).

**Key Files:** `agent.py` (core loop), `tools.py` (tools/impl), `compaction.py` (history mgmt), `models.py`/`utils.py`/`constants.py`.

Tests: `tests/test_compaction.py`, `test_tools.py`, `test_agent_integration.py`.