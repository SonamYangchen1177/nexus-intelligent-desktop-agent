
class ErrorRecovery:

    def __init__(self, max_retries=2):
        self.max_retries = max_retries

    def classify_error(self, error):

        message = str(error).lower()

        if "not found" in message:
            return "FILE_NOT_FOUND"

        if "already exists" in message:
            return "FILE_ALREADY_EXISTS"

        if "permission" in message or "access denied" in message:
            return "PERMISSION_ERROR"

        if "outside the approved workspace" in message:
            return "SAFETY_VIOLATION"

        if "timeout" in message:
            return "TIMEOUT"

        return "UNKNOWN_ERROR"

    def should_retry(self, error, attempt):

        error_type = self.classify_error(error)

        retryable_errors = [
            "TIMEOUT",
            "UNKNOWN_ERROR"
        ]

        return (
            error_type in retryable_errors
            and attempt < self.max_retries
        )
