
from pathlib import Path
from config import WORKSPACE

def validate_path(path):
    """
    Ensure that a path remains inside the approved workspace.
    """

    workspace = WORKSPACE.resolve()
    target = Path(path)

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
    target = validate_path(path)

    if not target.exists():
        raise FileNotFoundError(f"File not found: {target}")

    if not target.is_file():
        raise ValueError(f"Not a file: {target}")

    return target