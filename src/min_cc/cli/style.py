from prompt_toolkit.styles import Style
from rich.theme import Theme

ACCENT_COLOR = "#F44F00"
ACCENT_MUTED = "#7a391a"

CLI_STYLE = Style.from_dict(
    {
        "prompt": f"bold {ACCENT_COLOR}",
        "completion-menu.completion": "bg:#222222 #cccccc",
        "completion-menu.completion.current": f"bg:{ACCENT_COLOR} #ffffff bold",
        "completion-menu.meta.completion": "bg:#333333 #aaaaaa",
        "completion-menu.meta.completion.current": f"bg:#331B0B {ACCENT_COLOR}",
    }
)

RICH_THEME = Theme(
    {
        "accent": ACCENT_COLOR,
        "info": ACCENT_MUTED,
        "warning": "dim",
        "error": "bold red",
        "success": "bold green",
        "tool": f"bold {ACCENT_COLOR}",
        "banner": f"bold {ACCENT_COLOR}",
        "thinking": f"bold {ACCENT_MUTED}",
    }
)
