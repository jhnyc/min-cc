import pytest

from min_cc.tools import (
    BashTool,
    GlobTool,
    GrepTool,
    ReadFileTool,
    ReplaceFileContentTool,
    ToolRegistry,
    WriteFileTool,
)


@pytest.fixture
def chdir_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_glob_tool(chdir_tmp):
    (chdir_tmp / "test1.py").write_text("print(1)")
    (chdir_tmp / "test2.py").write_text("print(2)")
    (chdir_tmp / "other.txt").write_text("text")

    tool = GlobTool()
    result = tool.execute(pattern="*.py")
    assert "test1.py" in result
    assert "test2.py" in result
    assert "other.txt" not in result


def test_bash_tool():
    tool = BashTool()
    result = tool.execute(command="echo 'hello world'")
    assert "hello world" in result


def test_read_file_tool(tmp_path):
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text("content")

    tool = ReadFileTool()
    result = tool.execute(path=str(p))
    assert result == "content"


def test_replace_file_content_tool(tmp_path):
    p = tmp_path / "hello.py"
    p.write_text("print('hello')")

    tool = ReplaceFileContentTool()
    result = tool.execute(path=str(p), old_content="hello", new_content="world")

    assert "Successfully updated" in result
    assert p.read_text() == "print('world')"


def test_tool_registry():
    registry = ToolRegistry()
    registry.register_tool(BashTool())

    defs = registry.get_tool_definitions()
    assert len(defs) == 1
    assert defs[0]["function"]["name"] == "bash"


def test_grep_tool(chdir_tmp):
    p = chdir_tmp / "search.txt"
    p.write_text("find me here\nnot here")

    tool = GrepTool()
    result = tool.execute(pattern="find me", directory=".")
    assert "search.txt:1:find me here" in result


def test_grep_tool_exclude_dir_patterns(chdir_tmp):
    d = chdir_tmp / ".dot_dir"
    d.mkdir()
    p = d / "search.txt"
    p.write_text("find me here\nnot here")

    tool = GrepTool()
    result = tool.execute(pattern="find me", directory=".", exclude_dir_pattern=r"^\.")
    assert "search.txt:1:find me here" not in result


def test_grep_tool_not_exclude_dir_patterns(chdir_tmp):
    d = chdir_tmp / ".dot_dir"
    d.mkdir()
    p = d / "search.txt"
    p.write_text("find me here\nnot here")

    tool = GrepTool()
    result = tool.execute(pattern="find me", directory=".", exclude_dir_pattern="$^")
    assert "search.txt:1:find me here" in result


def test_write_file_tool(tmp_path):
    p = tmp_path / "new_file.txt"
    tool = WriteFileTool()
    result = tool.execute(path=str(p), content="hello from write file")

    assert "Successfully wrote to" in result
    assert p.read_text() == "hello from write file"
