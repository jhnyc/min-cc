from typing import Optional

from rich.panel import Panel

from min_cc.cli.commands import list_commands, register_command
from min_cc.cli.commands.base import Command, CommandContext


@register_command
class HelpCommand(Command):
    @property
    def name(self) -> str:
        return "/help"

    @property
    def description(self) -> str:
        return "Show this help message"

    def execute(self, args: str, context: CommandContext) -> Optional[bool]:
        commands = list_commands()
        help_text = "[bold]Available Commands:[/bold]\n"
        for cmd in sorted(commands, key=lambda c: c.name):
            help_text += f"- {cmd.name}: {cmd.description}\n"

        context.console.print(Panel(help_text, title="Help", border_style="accent"))
        return True
