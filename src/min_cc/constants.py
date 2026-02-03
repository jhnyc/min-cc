# Agent Defaults
MODEL = "x-ai/grok-4.1-fast"  # cheap + fast + pretty good at tool calls
DEFAULT_MODEL = MODEL
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# Compaction Constants
TOKEN_LIMIT_FALLBACK = 12800
TOKEN_LIMIT_PERCENTAGE = 0.4
CHARS_PER_TOKEN = 4  # for quick token estimation
TRUNCATE_KEEP_COUNT = 10
SUMMARIZE_PRESERVE_COUNT = 3

# UI Constants
TRIM_TOOL_CALL_ARGS = 50

# Tool Constants
BASH_TIMEOUT = 30
GREP_LINE_CHAR = 50


# Prompts
SYSTEM_PROMPT = (
    "You are a Mini Claude Code, an extremely minimal but capable coding agent."
    "Use your tools to help the user with their tasks. "
)
