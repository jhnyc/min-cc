import importlib
import pkgutil
from typing import Dict, List, Optional, Type

from min_cc.cli.commands.base import Command

_commands: Dict[str, Command] = {}


def register_command(command_cls: Type[Command]):
    instance = command_cls()
    _commands[instance.name] = instance
    return command_cls


def get_command(name: str) -> Optional[Command]:
    return _commands.get(name)


def list_commands() -> List[Command]:
    return list(_commands.values())


def load_commands():
    """Dynamically load all command modules in this package."""
    for _, name, _ in pkgutil.iter_modules(__path__):
        if name != "base":
            importlib.import_module(f".{name}", __package__)
