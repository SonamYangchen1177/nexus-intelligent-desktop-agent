
from agent.recovery import ErrorRecovery


def test_classify_file_not_found():

    recovery = ErrorRecovery()

    result = recovery.classify_error(
        FileNotFoundError("File not found")
    )

    assert result == "FILE_NOT_FOUND"


def test_classify_file_already_exists():

    recovery = ErrorRecovery()

    result = recovery.classify_error(
        FileExistsError("File already exists")
    )

    assert result == "FILE_ALREADY_EXISTS"


def test_classify_permission_error():

    recovery = ErrorRecovery()

    result = recovery.classify_error(
        PermissionError("Permission denied")
    )

    assert result == "PERMISSION_ERROR"


def test_classify_safety_violation():

    recovery = ErrorRecovery()

    error = Exception(
        "Path is outside the approved workspace"
    )

    result = recovery.classify_error(error)

    assert result == "SAFETY_VIOLATION"


def test_classify_timeout():

    recovery = ErrorRecovery()

    result = recovery.classify_error(
        TimeoutError("Request timeout")
    )

    assert result == "TIMEOUT"


def test_classify_unknown_error():

    recovery = ErrorRecovery()

    result = recovery.classify_error(
        Exception("Unexpected issue")
    )

    assert result == "UNKNOWN_ERROR"


def test_retry_timeout_before_maximum_attempt():

    recovery = ErrorRecovery(max_retries=2)

    error = TimeoutError("Request timeout")

    assert recovery.should_retry(
        error,
        1
    ) is True


def test_no_retry_after_maximum_attempt():

    recovery = ErrorRecovery(max_retries=2)

    error = TimeoutError("Request timeout")

    assert recovery.should_retry(
        error,
        2
    ) is False


def test_file_not_found_is_not_retryable():

    recovery = ErrorRecovery(max_retries=2)

    error = FileNotFoundError("File not found")

    assert recovery.should_retry(
        error,
        1
    ) is False


def test_permission_error_is_not_retryable():

    recovery = ErrorRecovery(max_retries=2)

    error = PermissionError("Permission denied")

    assert recovery.should_retry(
        error,
        1
    ) is False


def test_unknown_error_can_be_retried():

    recovery = ErrorRecovery(max_retries=3)

    error = Exception("Unexpected issue")

    assert recovery.should_retry(
        error,
        1
    ) is True
