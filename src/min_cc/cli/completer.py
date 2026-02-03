from prompt_toolkit.completion import Completer, Completion

from min_cc.cli.commands import list_commands


class SlashCommandCompleter(Completer):
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/"):
            # Get fresh list of commands from registry
            for cmd in list_commands():
                if cmd.name.startswith(text):
                    yield Completion(
                        cmd.name,
                        start_position=-len(text),
                        display_meta=cmd.description,
                    )
