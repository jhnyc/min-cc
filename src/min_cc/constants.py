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
    "You are a Min-CC (Mini Claude Code), an extremely minimal but capable coding agent."
    "Use your tools to help the user with their tasks. "
)

# Init Prompt
INIT_PROMPT = """
Please analyze this codebase and create a Min-CC.md file, which will be given to future instances of Min-CC to operate in this repository.

What to add:

1. Commands that will be commonly used, such as how to build, lint, and run tests. Include the necessary commands to develop in this codebase, such as how to run a single test.
2. High-level code architecture and structure so that future instances can be productive more quickly. Focus on the "big picture" architecture that requires reading multiple files to understand

Usage notes:

- If there's already a Min-CC.md, suggest improvements to it.
- When you make the initial Min-CC.md, do not repeat yourself and do not include obvious instructions like "Provide helpful error messages to users", "Write unit tests for all new utilities", "Never include sensitive information (API keys, tokens) in code or commits"
- Avoid listing every component or file structure that can be easily discovered
- Don't include generic development practices
- If there are Cursor rules (in .cursor/rules/ or .cursorrules) or Copilot rules (in .github/copilot-instructions.md), make sure to include the important parts.
- If there is a README.md, make sure to include the important parts.
- Do not make up information such as "Common Development Tasks", "Tips for Development", "Support and Documentation" unless this is expressly included in other files that you read.
- Be sure to prefix the file with the following text:

# Min-CC.md
"""
