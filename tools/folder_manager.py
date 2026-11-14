
from safety.guardrails import validate_path

def create_folder(folder_path):
    """
    Create a folder inside the approved workspace.
    """

    target = validate_path(folder_path)

    if target.exists():
        return {
            "success": False,
            "message": "Folder already exists.",
            "path": str(target)
        }

    target.mkdir(parents=True, exist_ok=False)

    return {
        "success": True,
        "message": "Folder created successfully.",
        "path": str(target)
    }