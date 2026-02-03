# Min-CC: Mini Claude Code

An extremely minimal but capable cli coding agent. The core is only ~2-300 LOC. No magic, no fluff, just a bunch of tool calls in a while loop. 

Co-Authored by Min-CC :)

## Quick Start

1. Set your OpenRouter API key in `.env`

    *(Supports any OpenAI-compatible model.)*

2. Run the agent
```bash
uv sync
uv run min-cc
```

3. Start coding!
```
╭────────────────────────────────────╮
│ Min-CC: Mini Claude Code           │
│ Model: x-ai/grok-4.1-fast (2M ctx) │
│ Compaction: truncate @ 800k        │
╰────────────────────────────────────╯
Type 'exit' or 'quit' to end the session.

User: 
```