from typing import Optional

from min_cc.cli.commands import register_command
from min_cc.cli.commands.base import Command, CommandContext


@register_command
class ExitCommand(Command):
    @property
    def name(self) -> str:
        return "/exit"

    @property
    def description(self) -> str:
        return "End the session"

    def execute(self, args: str, context: CommandContext) -> Optional[bool]:
        context.console.print("[warning]Goodbye![/warning]")
        return False
