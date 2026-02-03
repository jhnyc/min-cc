from typing import Optional

from rich.panel import Panel

from min_cc.cli.commands import register_command
from min_cc.cli.commands.base import Command, CommandContext


@register_command
class ClearCommand(Command):
    @property
    def name(self) -> str:
        return "/clear"

    @property
    def description(self) -> str:
        return "Clear terminal screen and agent context"

    def execute(self, args: str, context: CommandContext) -> Optional[bool]:
        # 1. Clear Agent Context
        context.agent.clear_history()

        # 2. Clear Terminal
        context.console.clear()
        context.console.print(Panel.fit(context.banner_text, border_style="blue"))

        return True
