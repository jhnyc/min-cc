import json
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from min_cc.agent import CodingAgent
from min_cc.cli.commands import get_command, load_commands
from min_cc.cli.commands.base import CommandContext
from min_cc.cli.completer import SlashCommandCompleter
from min_cc.cli.style import CLI_STYLE, RICH_THEME
from min_cc.compaction import CompactionService, CompactionStrategy
from min_cc.constants import MODEL, TOKEN_LIMIT_FALLBACK, TOKEN_LIMIT_PERCENTAGE
from min_cc.utils import format_number, get_model_context_length, trim_tool_call_args

console = Console(theme=RICH_THEME)
# Rebuild CommandContext now that CodingAgent and Console are available in the namespace
CommandContext.model_rebuild()


def setup_agent():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print(
            "[error]Error:[/error] OPENROUTER_API_KEY not found in environment or .env file."
        )
        sys.exit(1)

    strategy_name = os.getenv("COMPACTION", "truncate").lower()
    strategy = (
        CompactionStrategy.SUMMARIZE
        if strategy_name == "summarize"
        else CompactionStrategy.TRUNCATE
    )

    context_window = get_model_context_length(MODEL)
    token_limit = (
        int(context_window * TOKEN_LIMIT_PERCENTAGE)
        if isinstance(context_window, int) and context_window > 0
        else TOKEN_LIMIT_FALLBACK
    )

    service = CompactionService(token_limit=token_limit, strategy=strategy)
    agent = CodingAgent(api_key=api_key, model=MODEL, compaction_service=service)

    return agent, context_window, token_limit, strategy_name


def handle_event(event_type: str, data: Dict[str, Any]):
    if event_type == "tool_call":
        console.print(f"[tool]Executing Tool:[/tool] [accent]{data['name']}[/accent]")
        try:
            args = json.loads(data["arguments"])
            trimmed_args = trim_tool_call_args(args)
            console.print(f"   [dim]Args: {json.dumps(trimmed_args)}[/dim]")
        except Exception:
            console.print(f"   [dim]Args: {data['arguments']}[/dim]")


def main():
    agent, context_window, token_limit, strategy_name = setup_agent()
    load_commands()

    ctx_str = (
        format_number(context_window) if isinstance(context_window, int) else "unknown"
    )
    limit_str = format_number(token_limit)
    banner_text = (
        f"[banner]Min-CC: Mini Claude Code[/banner]\n"
        f"[dim]Model: {MODEL} ({ctx_str} ctx)[/dim]\n"
        f"[dim]Compaction: {strategy_name} @ {limit_str}[/dim]"
    )

    console.print(Panel.fit(banner_text, border_style="accent"))
    console.print(
        "[dim]Type '/help' for commands, or '/exit' to end the session.[/dim]\n"
    )

    session = PromptSession(style=CLI_STYLE)
    completer = SlashCommandCompleter()

    while True:
        try:
            if sys.stdin.isatty():
                user_input = session.prompt(
                    HTML("<prompt>User</prompt>: "),
                    completer=completer,
                    complete_while_typing=True,
                ).strip()
            else:
                # Fallback for non-TTY
                print("User: ", end="", flush=True)
                user_input = sys.stdin.readline().strip()
                if not user_input:
                    break
        except EOFError:
            console.print("\n[warning]Goodbye![/warning]")
            break
        except KeyboardInterrupt:
            continue
        except Exception as e:
            console.print(f"[error]Prompt error: {e}[/error]")
            continue

        if not user_input:
            continue

        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd_name = parts[0]
            cmd_args = parts[1] if len(parts) > 1 else ""

            command = get_command(cmd_name)
            if command:
                context = CommandContext(
                    agent=agent,
                    console=console,
                    banner_text=banner_text,
                    token_limit=token_limit,
                    strategy_name=strategy_name,
                )
                if command.execute(cmd_args, context) is False:
                    break
                continue
            else:
                console.print(f"[error]Unknown command: {cmd_name}[/error]")
                continue

        with console.status(
            "[thinking]Thinking...[/thinking]", spinner_style="thinking"
        ):
            try:
                response = agent.run(user_input, on_event=handle_event)
                console.print("\n" + "─" * console.width)
                console.print(Markdown(response or ""))
                console.print("─" * console.width + "\n")
            except Exception as e:
                console.print(f"[error]Error during execution:[/error] {str(e)}")


if __name__ == "__main__":
    main()
