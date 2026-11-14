
from safety.guardrails import validate_path

def search_files(directory=".", keyword=None, extension=None):
    """
    Search for files inside the approved workspace.
    """

    search_directory = validate_path(directory)

    if not search_directory.exists():
        raise FileNotFoundError("Search directory does not exist.")

    if not search_directory.is_dir():
        raise ValueError("Search path must be a directory.")

    results = []

    for file_path in search_directory.rglob("*"):

        if not file_path.is_file():
            continue

        if keyword and keyword.lower() not in file_path.name.lower():
            continue

        if extension and file_path.suffix.lower() != extension.lower():
            continue

        results.append({
            "name": file_path.name,
            "path": str(file_path.relative_to(search_directory)),
            "full_path": str(file_path)
        })

    return results