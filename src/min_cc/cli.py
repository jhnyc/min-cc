import json
import os
import sys
from typing import Any, Dict

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from min_cc.agent import CodingAgent
from min_cc.compaction import CompactionService, CompactionStrategy
from min_cc.constants import MODEL, TOKEN_LIMIT_FALLBACK, TOKEN_LIMIT_PERCENTAGE
from min_cc.utils import format_number, get_model_context_length, trim_tool_call_args

console = Console()


def setup_agent():
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print(
            "[red]Error:[/red] OPENROUTER_API_KEY not found in environment or .env file."
        )
        sys.exit(1)

    strategy_name = os.getenv("COMPACTION", "truncate").lower()
    strategy = (
        CompactionStrategy.SUMMARIZE
        if strategy_name == "summarize"
        else CompactionStrategy.TRUNCATE
    )

    # Dynamically determine token limit
    context_window = get_model_context_length(MODEL)
    if isinstance(context_window, int) and context_window > 0:
        token_limit = int(context_window * TOKEN_LIMIT_PERCENTAGE)
    else:
        token_limit = TOKEN_LIMIT_FALLBACK

    service = CompactionService(token_limit=token_limit, strategy=strategy)
    agent = CodingAgent(
        api_key=api_key,
        model=MODEL,
        compaction_service=service,
    )
    return agent, context_window, token_limit, strategy_name


def main():
    agent, context_window, token_limit, strategy_name = setup_agent()

    ctx_str = (
        format_number(context_window) if isinstance(context_window, int) else "unknown"
    )
    limit_str = format_number(token_limit)

    banner_text = (
        f"[bold blue]Min-CC: Mini Claude Code[/bold blue]\n"
        f"[dim]Model: {MODEL} ({ctx_str} ctx)[/dim]\n"
        f"[dim]Compaction: {strategy_name} @ {limit_str}[/dim]"
    )

    console.print(Panel.fit(banner_text, border_style="blue"))

    console.print("[dim]Type 'exit' or 'quit' to end the session.[/dim]\n")

    def handle_event(event_type: str, data: Dict[str, Any]):
        if event_type == "tool_call":
            console.print(
                f"[bold cyan]Executing Tool:[/bold cyan] [green]{data['name']}[/green]"
            )
            try:
                args = json.loads(data["arguments"])
                trimmed_args = trim_tool_call_args(args)
                console.print(f"   [dim]Args: {json.dumps(trimmed_args)}[/dim]")
            except Exception:
                console.print(f"   [dim]Args: {data['arguments']}[/dim]")

    while True:
        user_input = Prompt.ask("[bold green]User[/bold green]")

        with console.status("[bold blue]Thinking...[/bold blue]"):
            try:
                response = agent.run(user_input, on_event=handle_event)

                console.print("\n" + "─" * console.width)
                console.print(Markdown(response or ""))
                console.print("─" * console.width + "\n")
            except Exception as e:
                console.print(f"[red]Error during execution:[/red] {str(e)}")


if __name__ == "__main__":
    main()
