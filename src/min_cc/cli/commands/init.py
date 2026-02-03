from typing import Optional

from min_cc.cli.commands import register_command
from min_cc.cli.commands.base import Command, CommandContext
from min_cc.constants import INIT_PROMPT


@register_command
class InitCommand(Command):
    @property
    def name(self) -> str:
        return "/init"

    @property
    def description(self) -> str:
        return "Initialize a new Min-CC.md file with codebase documentation"

    def execute(self, args: str, context: CommandContext) -> Optional[bool]:
        context.console.print("[banner]Initializing Min-CC.md...[/banner]")

        with context.console.status(
            "[banner]Analyzing codebase...[/banner]", spinner_style="accent"
        ):
            try:
                response = context.agent.run(INIT_PROMPT)

                from rich.markdown import Markdown

                context.console.print("\n" + "─" * context.console.width)
                context.console.print(Markdown(response or ""))
                context.console.print("─" * context.console.width + "\n")
            except Exception as e:
                context.console.print(
                    f"[error]Error during initialization:[/error] {str(e)}"
                )

        return True
