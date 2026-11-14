
from safety.guardrails import validate_path


def search_files(directory=".", keyword=None, extension=None):
    """
    Search for files inside the approved workspace.

    Each discovered file is independently validated
    to prevent external symbolic-link access.
    """

    search_directory = validate_path(directory)

    if not search_directory.exists():
        raise FileNotFoundError(
            "Search directory does not exist."
        )

    if not search_directory.is_dir():
        raise ValueError(
            "Search path must be a directory."
        )

    results = []

    for file_path in search_directory.rglob("*"):

        try:
            # Validate every discovered path.
            safe_file = validate_path(file_path)

        except (PermissionError, OSError):
            # Ignore paths that resolve outside the workspace.
            continue

        if not safe_file.is_file():
            continue

        if keyword and keyword.lower() not in safe_file.name.lower():
            continue

        if extension and safe_file.suffix.lower() != extension.lower():
            continue

        results.append({
            "name": safe_file.name,
            "path": str(safe_file.relative_to(search_directory)),
            "full_path": str(safe_file)
        })

    return results
