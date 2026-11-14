
from tools.file_search import search_files
from tools.folder_manager import create_folder
from tools.file_manager import move_file, rename_file
from tools.report_generator import generate_report
from config import WORKSPACE

def main():
    print("\nTESTING DESKTOP AGENT TOOLS")
    print("=" * 45)

    # 1. Create a test folder
    result = create_folder("test_project")
    print("\nFolder creation:", result)

    # 2. Create a sample file
    sample_file = WORKSPACE / "sample_assignment.txt"
    sample_file.write_text(
        "This is a sample DAT404 assignment.",
        encoding="utf-8"
    )

    # 3. Search for files
    results = search_files(keyword="assignment")
    print("\nSearch results:", results)

    # 4. Move the file
    move_result = move_file(
        "sample_assignment.txt",
        "test_project/sample_assignment.txt"
    )
    print("\nMove result:", move_result)

    # 5. Rename the file
    rename_result = rename_file(
        "test_project/sample_assignment.txt",
        "DAT404_assignment.txt"
    )
    print("\nRename result:", rename_result)

    # 6. Generate a report
    report_result = generate_report(
        "Desktop Agent Test Report",
        "Folder creation, file searching, moving and renaming were tested.",
        "reports/tool_test_report.txt"
    )
    print("\nReport result:", report_result)

    print("\nAll tool tests completed.")

if __name__ == "__main__":
    main()