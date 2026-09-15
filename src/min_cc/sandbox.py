import os
import sys
from pathlib import Path
from typing import List, Optional

SANDBOX_EXEC = "/usr/bin/sandbox-exec"

_DEFAULT_WRITABLE = [
    Path("/private/tmp"),
    Path("/private/var/folders"),
    Path.home() / ".cache",
]

_TRUE_VALUES = {"1", "on", "true", "yes"}


def is_available() -> bool:
    return sys.platform == "darwin" and os.path.exists(SANDBOX_EXEC)


def is_enabled() -> bool:
    return is_available() and os.getenv("MIN_CC_SANDBOX", "on").lower() not in {
        "0",
        "off",
        "false",
        "no",
    }


def _escape(path: str) -> str:
    return path.replace("\\", "\\\\").replace('"', '\\"')


def _extra_writable() -> List[Path]:
    raw = os.getenv("MIN_CC_SANDBOX_WRITABLE", "")
    return [Path(p) for p in raw.split(os.pathsep) if p]


def build_profile(
    workspace: Path,
    allow_network: bool = False,
    extra_writable: Optional[List[Path]] = None,
) -> str:
    writable = [workspace, *_DEFAULT_WRITABLE, *(extra_writable or [])]
    write_rules = "\n".join(f'    (subpath "{_escape(str(p))}")' for p in writable)
    network_rule = "(allow network*)" if allow_network else "(deny network*)"
    return (
        "(version 1)\n"
        "(deny default)\n"
        "(allow process*)\n"
        "(allow sysctl-read)\n"
        "(allow mach-lookup)\n"
        "(allow file-read*)\n"
        "(allow file-write*\n"
        f"{write_rules})\n"
        f"{network_rule}\n"
    )


def wrap_command(command: str, workspace: Path) -> List[str]:
    profile = build_profile(
        workspace,
        allow_network=os.getenv("MIN_CC_SANDBOX_NETWORK", "").lower() in _TRUE_VALUES,
        extra_writable=_extra_writable(),
    )
    return [SANDBOX_EXEC, "-p", profile, "/bin/sh", "-c", command]
