
from pathlib import Path

import pytest

from tools import file_search
from tools import folder_manager
from tools import file_manager
from tools import report_generator
from safety import guardrails

# --------------------------------------------------
# TEST PATH SETUP
# --------------------------------------------------

@pytest.fixture
def tool_workspace(tmp_path, monkeypatch):
    """
    Redirect tool paths to a temporary directory.
    This protects the real project workspace.
    """

    def safe_path(path):

        target = Path(path)

        if not target.is_absolute():
            target = tmp_path / target

        target = target.resolve()

        try:
            target.relative_to(tmp_path.resolve())
        except ValueError:
            raise ValueError("Path is outside test workspace.")

        return target

    def safe_existing_file(path):

        target = safe_path(path)

        if not target.exists():
            raise FileNotFoundError("File not found.")

        if not target.is_file():
            raise ValueError("Path must be a file.")

        return target

    monkeypatch.setattr(
        file_search,
        "validate_path",
        safe_path
    )

    monkeypatch.setattr(
        folder_manager,
        "validate_path",
        safe_path
    )

    monkeypatch.setattr(
        file_manager,
        "validate_path",
        safe_path
    )

    monkeypatch.setattr(
        file_manager,
        "validate_existing_file",
        safe_existing_file
    )

    monkeypatch.setattr(
        report_generator,
        "validate_path",
        safe_path
    )

    return tmp_path


# --------------------------------------------------
# FOLDER CREATION TESTS
# --------------------------------------------------

def test_create_folder_success(tool_workspace):

    result = folder_manager.create_folder("test_project")

    assert result["success"] is True
    assert result["message"] == "Folder created successfully."
    assert (tool_workspace / "test_project").is_dir()


def test_create_existing_folder(tool_workspace):

    (tool_workspace / "existing_folder").mkdir()

    result = folder_manager.create_folder("existing_folder")

    assert result["success"] is False
    assert "already exists" in result["message"].lower()


def test_create_nested_folder(tool_workspace):

    result = folder_manager.create_folder(
        "projects/DAT404"
    )

    assert result["success"] is True
    assert (tool_workspace / "projects" / "DAT404").is_dir()


# --------------------------------------------------
# FILE SEARCH TESTS
# --------------------------------------------------

def test_search_files_by_keyword(tool_workspace):

    (tool_workspace / "assignment.txt").write_text(
        "DAT404 assignment",
        encoding="utf-8"
    )

    (tool_workspace / "notes.txt").write_text(
        "General notes",
        encoding="utf-8"
    )

    results = file_search.search_files(
        keyword="assignment"
    )

    assert len(results) == 1
    assert results[0]["name"] == "assignment.txt"


def test_search_files_by_extension(tool_workspace):

    (tool_workspace / "report.txt").write_text(
        "Text report",
        encoding="utf-8"
    )

    (tool_workspace / "script.py").write_text(
        "print('Hello')",
        encoding="utf-8"
    )

    results = file_search.search_files(
        extension=".py"
    )

    assert len(results) == 1
    assert results[0]["name"] == "script.py"


def test_search_files_by_keyword_and_extension(tool_workspace):

    (tool_workspace / "DAT404_report.txt").write_text(
        "Assignment report",
        encoding="utf-8"
    )

    (tool_workspace / "DAT404_script.py").write_text(
        "print('test')",
        encoding="utf-8"
    )

    results = file_search.search_files(
        keyword="DAT404",
        extension=".txt"
    )

    assert len(results) == 1
    assert results[0]["name"] == "DAT404_report.txt"


def test_search_files_returns_empty_list(tool_workspace):

    results = file_search.search_files(
        keyword="nonexistent"
    )

    assert results == []


def test_search_files_rejects_missing_directory(tool_workspace):

    with pytest.raises(
        FileNotFoundError,
        match="does not exist"
    ):

        file_search.search_files(
            directory="missing_folder"
        )


def test_search_files_rejects_file_as_directory(tool_workspace):

    (tool_workspace / "sample.txt").write_text(
        "Sample",
        encoding="utf-8"
    )

    with pytest.raises(
        ValueError,
        match="must be a directory"
    ):

        file_search.search_files(
            directory="sample.txt"
        )


# --------------------------------------------------
# FILE MOVEMENT TESTS
# --------------------------------------------------

def test_move_file_success(tool_workspace):

    source = tool_workspace / "sample.txt"
    source.write_text("Sample content", encoding="utf-8")

    result = file_manager.move_file(
        "sample.txt",
        "documents/sample.txt"
    )

    destination = tool_workspace / "documents" / "sample.txt"

    assert result["success"] is True
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "Sample content"
    assert not source.exists()


def test_move_file_does_not_overwrite(tool_workspace):

    source = tool_workspace / "source.txt"
    destination = tool_workspace / "destination.txt"

    source.write_text("Original source", encoding="utf-8")
    destination.write_text("Existing destination", encoding="utf-8")

    with pytest.raises(
        FileExistsError,
        match="Overwriting is not allowed"
    ):

        file_manager.move_file(
            "source.txt",
            "destination.txt"
        )

    assert destination.read_text(encoding="utf-8") == "Existing destination"


# --------------------------------------------------
# FILE RENAMING TESTS
# --------------------------------------------------

def test_rename_file_success(tool_workspace):

    source = tool_workspace / "old_name.txt"
    source.write_text("Assignment content", encoding="utf-8")

    result = file_manager.rename_file(
        "old_name.txt",
        "DAT404_assignment.txt"
    )

    destination = tool_workspace / "DAT404_assignment.txt"

    assert result["success"] is True
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "Assignment content"
    assert not source.exists()


def test_rename_file_rejects_invalid_name(tool_workspace):

    source = tool_workspace / "sample.txt"
    source.write_text("Sample", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="valid filename"
    ):

        file_manager.rename_file(
            "sample.txt",
            "../outside.txt"
        )


def test_rename_file_does_not_overwrite(tool_workspace):

    source = tool_workspace / "source.txt"
    destination = tool_workspace / "existing.txt"

    source.write_text("Source content", encoding="utf-8")
    destination.write_text("Existing content", encoding="utf-8")

    with pytest.raises(
        FileExistsError,
        match="already exists"
    ):

        file_manager.rename_file(
            "source.txt",
            "existing.txt"
        )

    assert destination.read_text(encoding="utf-8") == "Existing content"


# --------------------------------------------------
# REPORT GENERATION TESTS
# --------------------------------------------------

def test_generate_report_success(tool_workspace):

    result = report_generator.generate_report(
        title="DAT404 Test Report",
        content="All desktop agent tools were tested.",
        output_path="reports/test_report.txt"
    )

    report_path = tool_workspace / "reports" / "test_report.txt"

    assert result["success"] is True
    assert report_path.exists()

    report_content = report_path.read_text(
        encoding="utf-8"
    )

    assert "DAT404 Test Report" in report_content
    assert "All desktop agent tools were tested." in report_content


def test_generate_report_does_not_overwrite(tool_workspace):

    report_path = tool_workspace / "existing_report.txt"

    report_path.write_text(
        "Original report",
        encoding="utf-8"
    )

    with pytest.raises(
        FileExistsError,
        match="already exists"
    ):

        report_generator.generate_report(
            title="New Report",
            content="New content",
            output_path="existing_report.txt"
        )

    assert report_path.read_text(
        encoding="utf-8"
    ) == "Original report"
def test_search_files_ignores_external_symbolic_link(
    tool_workspace,
    monkeypatch
):
    """
    Ensure search does not expose files linked from
    outside the approved workspace.
    """

    # Use the real guardrail validator for this test.
    monkeypatch.setattr(
        guardrails,
        "WORKSPACE",
        tool_workspace
    )

    monkeypatch.setattr(
        file_search,
        "validate_path",
        guardrails.validate_path
    )

    # Create a file outside the workspace.
    outside_folder = tool_workspace.parent / (
        f"{tool_workspace.name}_outside"
    )
    outside_folder.mkdir()

    outside_file = outside_folder / "secret.txt"
    outside_file.write_text(
        "Sensitive external content",
        encoding="utf-8"
    )

    # Create a symbolic link inside the workspace.
    link = tool_workspace / "external_secret.txt"

    try:
        link.symlink_to(outside_file)

    except (OSError, NotImplementedError):
        pytest.skip(
            "Symbolic link creation is not permitted."
        )

    # Search the workspace.
    results = file_search.search_files()

    # The external file must not appear in results.
    assert all(
        result["name"] != "external_secret.txt"
        for result in results
    )

    assert all(
        result["name"] != "secret.txt"
        for result in results
    )