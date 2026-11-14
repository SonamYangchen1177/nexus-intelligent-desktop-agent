
import pytest

from safety import guardrails


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Create an isolated workspace for safety tests."""

    test_workspace = tmp_path / "workspace"
    test_workspace.mkdir()

    monkeypatch.setattr(
        guardrails,
        "WORKSPACE",
        test_workspace
    )

    return test_workspace


def test_valid_relative_path(workspace):
    result = guardrails.validate_path("documents")

    assert result == workspace / "documents"


def test_valid_absolute_path(workspace):
    target = workspace / "report.txt"

    result = guardrails.validate_path(target)

    assert result == target


def test_parent_directory_traversal_is_rejected(workspace):
    with pytest.raises(PermissionError):
        guardrails.validate_path("../outside")


def test_multiple_parent_traversal_is_rejected(workspace):
    with pytest.raises(PermissionError):
        guardrails.validate_path("../../important")


def test_external_absolute_path_is_rejected(
    workspace,
    tmp_path
):
    outside = tmp_path / "outside.txt"

    with pytest.raises(PermissionError):
        guardrails.validate_path(outside)


def test_empty_path_is_rejected(workspace):
    with pytest.raises(ValueError):
        guardrails.validate_path("")


def test_missing_file_is_rejected(workspace):
    with pytest.raises(FileNotFoundError):
        guardrails.validate_existing_file("missing.txt")


def test_directory_is_rejected_as_file(workspace):
    folder = workspace / "documents"
    folder.mkdir()

    with pytest.raises(ValueError):
        guardrails.validate_existing_file("documents")


def test_existing_file_is_accepted(workspace):
    file_path = workspace / "report.txt"
    file_path.write_text("Test report", encoding="utf-8")

    result = guardrails.validate_existing_file("report.txt")

    assert result == file_path
    assert result.is_file()


def test_symbolic_link_outside_workspace_is_rejected(
    workspace,
    tmp_path
):
    outside_folder = tmp_path / "outside"
    outside_folder.mkdir()

    link = workspace / "external_link"

    try:
        link.symlink_to(outside_folder, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symbolic link creation is not permitted.")

    with pytest.raises(PermissionError):
        guardrails.validate_path("external_link/secret.txt")
