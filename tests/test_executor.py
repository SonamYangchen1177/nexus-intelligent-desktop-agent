
import pytest

from pathlib import Path

from agent.executor import ToolExecutor


def test_executor_has_registered_tools():

    executor = ToolExecutor()

    expected_tools = [
        "search_files",
        "create_folder",
        "move_file",
        "rename_file",
        "generate_report",
        "verify_files"
    ]

    for tool in expected_tools:
        assert tool in executor.tool_registry


def test_execute_registered_tool(monkeypatch):

    executor = ToolExecutor()

    def fake_search_files(**parameters):

        return {
            "success": True,
            "files": ["assignment.txt"],
            "query": parameters.get("query")
        }

    monkeypatch.setitem(
        executor.tool_registry,
        "search_files",
        fake_search_files
    )

    result = executor.execute_tool(
        "search_files",
        {"query": "*.txt"}
    )

    assert result["success"] is True
    assert result["files"] == ["assignment.txt"]
    assert result["query"] == "*.txt"


def test_unknown_tool_raises_error():

    executor = ToolExecutor()

    with pytest.raises(
        ValueError,
        match="Unknown tool"
    ):

        executor.execute_tool(
            "unknown_tool",
            {}
        )


def test_tool_execution_error_is_propagated(monkeypatch):

    executor = ToolExecutor()

    def failing_tool(**parameters):
        raise PermissionError("Permission denied")

    monkeypatch.setitem(
        executor.tool_registry,
        "search_files",
        failing_tool
    )

    with pytest.raises(
        PermissionError,
        match="Permission denied"
    ):

        executor.execute_tool(
            "search_files",
            {}
        )


def test_verify_files_with_existing_file(
    tmp_path,
    monkeypatch
):

    import safety.guardrails

    executor = ToolExecutor()

    test_file = tmp_path / "assignment.txt"
    test_file.write_text(
        "DAT404 assignment",
        encoding="utf-8"
    )

    # Allow this isolated test to use pytest's temporary directory.
    monkeypatch.setattr(
        safety.guardrails,
        "validate_path",
        lambda path: Path(path)
    )

    result = executor.execute_tool(
        "verify_files",
        {"paths": [str(test_file)]}
    )

    assert result["success"] is True
    assert result["results"][0]["exists"] is True
    assert result["results"][0]["is_file"] is True


def test_verify_files_with_missing_file(
    tmp_path,
    monkeypatch
):

    import safety.guardrails

    executor = ToolExecutor()

    missing_file = tmp_path / "missing.txt"

    monkeypatch.setattr(
        safety.guardrails,
        "validate_path",
        lambda path: Path(path)
    )

    result = executor.execute_tool(
        "verify_files",
        {"paths": [str(missing_file)]}
    )

    assert result["success"] is False
    assert result["results"][0]["exists"] is False


def test_verify_files_with_empty_paths():

    executor = ToolExecutor()

    result = executor.execute_tool(
        "verify_files",
        {"paths": []}
    )

    assert result["success"] is True
    assert result["results"] == []
