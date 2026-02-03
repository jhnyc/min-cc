import glob
import os
import re
import shutil
import subprocess
from typing import Any, Dict, List

from pydantic import BaseModel

from .constants import BASH_TIMEOUT, GREP_LINE_CHAR


class Tool(BaseModel):
    name: str
    description: str
    parameters_schema: Dict[str, Any]

    def execute(self, **kwargs) -> str:
        raise NotImplementedError


class BashTool(Tool):
    name: str = "bash"
    description: str = "Execute a bash command in the current directory."
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The command to run"}
        },
        "required": ["command"],
    }

    def execute(self, command: str) -> str:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=BASH_TIMEOUT,
            )
            output = result.stdout
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            return output or "Command executed with no output."
        except Exception as e:
            return f"Error executing command: {str(e)}"


class ReadFileTool(Tool):
    name: str = "read_file"
    description: str = "Read the content of a file."
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Path to the file"}},
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Error: File {path} not found."
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"


class ReplaceFileContentTool(Tool):
    name: str = "replace_file_content"
    description: str = "Replace a section of a file with new content."
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "old_content": {
                "type": "string",
                "description": "The content to be replaced",
            },
            "new_content": {"type": "string", "description": "The new content"},
        },
        "required": ["path", "old_content", "new_content"],
    }

    def execute(self, path: str, old_content: str, new_content: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Error: File {path} not found."
            with open(path, "r") as f:
                content = f.read()

            if old_content not in content:
                return "Error: old_content not found in file."

            new_total_content = content.replace(old_content, new_content, 1)
            with open(path, "w") as f:
                f.write(new_total_content)
            return f"Successfully updated {path}."
        except Exception as e:
            return f"Error replacing content: {str(e)}"


class WriteFileTool(Tool):
    name: str = "write_file"
    description: str = (
        "Create a new file or overwrite an existing file with new content."
    )
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file"},
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        "required": ["path", "content"],
    }

    def execute(self, path: str, content: str) -> str:
        try:
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {path}."
        except Exception as e:
            return f"Error writing file: {str(e)}"


class GrepTool(Tool):
    name: str = "grep"
    description: str = "Search for a pattern in files within a directory."
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "directory": {
                "type": "string",
                "description": "Directory to search in",
                "default": ".",
            },
            "exclude_dir_pattern": {
                "type": "string",
                "description": "Regex pattern for directories to exclude",
                "default": "^\.",
            },
        },
        "required": ["pattern"],
    }

    def execute(
        self,
        pattern: str,
        directory: str = ".",
        exclude_dir_pattern: str = "^\.",
    ) -> str:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Error: Invalid regex pattern: {str(e)}"
        try:
            exclude_dir_regex = re.compile(exclude_dir_pattern)
        except re.error as e:
            return f"Error: Invalid regex pattern: {str(e)}"

        results = []

        def search_file(file_path: str):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            line_display = line.rstrip()
                            if len(line_display) > GREP_LINE_CHAR:
                                line_display = line_display[:GREP_LINE_CHAR] + "..."
                            results.append(f"{file_path}:{i}:{line_display}")
            except Exception:
                pass

        if os.path.isfile(directory):
            search_file(directory)

        elif os.path.isdir(directory):
            for root, dirs, files in os.walk(directory):
                # Skip if dirs match exclude_dir_patterns]
                dirs[:] = [d for d in dirs if not exclude_dir_regex.search(d)]

                for file in files:
                    search_file(os.path.join(root, file))
        else:
            return f"Error: {directory} is not a valid file or directory."

        return "\n".join(results) if results else "No matches found."


class GlobTool(Tool):
    name: str = "glob"
    description: str = "List files matching a glob pattern (e.g., '**/*.py')."
    parameters_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match"},
            "recursive": {
                "type": "boolean",
                "description": "Whether to search recursively",
                "default": True,
            },
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, recursive: bool = True) -> str:
        try:
            files = glob.glob(pattern, recursive=recursive)
            if not files:
                return "No files matched the pattern."
            return "\n".join(files)
        except Exception as e:
            return f"Error running glob: {str(e)}"


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        self._tools[tool.name] = tool

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters_schema,
                },
            }
            for t in self._tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        if name not in self._tools:
            return f"Error: Tool {name} not found."
        return self._tools[name].execute(**arguments)


def get_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    if shutil.which("bash"):
        registry.register_tool(BashTool())
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ReplaceFileContentTool())
    registry.register_tool(GrepTool())
    registry.register_tool(GlobTool())
    return registry
