
from pathlib import Path

from config import WORKSPACE


def validate_path(path):
    """
    Ensure that a path remains inside the approved workspace.

    Relative paths are interpreted from the workspace.
    Absolute paths are accepted only if they are inside it.
    Symbolic links are resolved before validation.
    """

    if not path:
        raise ValueError("Path cannot be empty.")

    workspace = WORKSPACE.resolve()

    target = Path(path).expanduser()

    if not target.is_absolute():
        target = workspace / target

    target = target.resolve()

    try:
        target.relative_to(workspace)

    except ValueError:
        raise PermissionError(
            "Access denied: path is outside the approved workspace."
        )

    return target


def validate_existing_file(path):
    """
    Validate that a path points to an existing file
    inside the approved workspace.
    """

    target = validate_path(path)

    if not target.exists():
        raise FileNotFoundError(
            f"File not found: {target}"
        )

    if not target.is_file():
        raise ValueError(
            f"Not a file: {target}"
        )

    return target
