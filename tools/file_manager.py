
from pathlib import Path
import shutil
from safety.guardrails import (
    validate_path,
    validate_existing_file
)

def move_file(source_path, destination_path):
    source = validate_existing_file(source_path)
    destination = validate_path(destination_path)

    if destination.exists():
        raise FileExistsError(
            "Destination already exists. Overwriting is not allowed."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(source), str(destination))

    return {
        "success": True,
        "message": "File moved successfully.",
        "source": str(source),
        "destination": str(destination)
    }

def rename_file(file_path, new_name):
    source = validate_existing_file(file_path)

    if not new_name or Path(new_name).name != new_name:
        raise ValueError("Please provide a valid filename.")

    destination = source.with_name(new_name)
    destination = validate_path(destination)

    if destination.exists():
        raise FileExistsError("A file with that name already exists.")

    source.rename(destination)

    return {
        "success": True,
        "message": "File renamed successfully.",
        "old_path": str(source),
        "new_path": str(destination)
    }