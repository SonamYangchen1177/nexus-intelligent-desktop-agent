
from agent.verifier import ExecutionVerifier
from agent.recovery import ErrorRecovery


def main():

    verifier = ExecutionVerifier()
    recovery = ErrorRecovery(max_retries=2)

    print("\nTESTING VERIFICATION")
    print("=" * 40)

    result = {
        "success": True,
        "message": "Folder created successfully.",
        "path": "workspace/test_project"
    }

    verification = verifier.verify(
        "create_folder",
        result
    )

    print("Verification:", verification)

    print("\nTESTING ERROR CLASSIFICATION")
    print("=" * 40)

    errors = [
        FileNotFoundError("File not found"),
        FileExistsError("File already exists"),
        PermissionError("Permission denied"),
        TimeoutError("Request timeout")
    ]

    for error in errors:

        error_type = recovery.classify_error(error)

        print(
            f"{error}: {error_type}"
        )

    print("\nTESTING RETRY DECISIONS")
    print("=" * 40)

    error = TimeoutError("Request timeout")

    for attempt in range(1, 4):

        retry = recovery.should_retry(
            error,
            attempt
        )

        print(
            f"Attempt {attempt}: Retry = {retry}"
        )


if __name__ == "__main__":
    main()
