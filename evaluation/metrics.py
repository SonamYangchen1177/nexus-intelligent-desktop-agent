
def tool_selection_accuracy(expected_tools, predicted_tools):

    if not expected_tools:
        return 1.0 if not predicted_tools else 0.0

    total_positions = max(
        len(expected_tools),
        len(predicted_tools)
    )

    correct = sum(
        1
        for i in range(min(
            len(expected_tools),
            len(predicted_tools)
        ))
        if expected_tools[i] == predicted_tools[i]
    )

    return correct / total_positions


def average_tool_selection_accuracy(records):

    if not records:
        return 0.0

    scores = [
        record["tool_selection_accuracy"]
        for record in records
    ]

    return sum(scores) / len(scores)


def task_success_rate(records):

    if not records:
        return 0.0

    successful = sum(
        1 for record in records
        if record["status"] == "success"
    )

    return successful / len(records)


def verification_accuracy(records):

    total_steps = 0
    verified_steps = 0

    for record in records:

        for step in record.get("steps", []):

            total_steps += 1

            if step.get("verified") is True:
                verified_steps += 1

    if total_steps == 0:
        return 0.0

    return verified_steps / total_steps


def recovery_rate(records):

    failed_attempts = 0
    recovered_attempts = 0

    for record in records:

        for step in record.get("steps", []):

            if step.get("initial_failure") is True:

                failed_attempts += 1

                if step.get("recovered") is True:
                    recovered_attempts += 1

    if failed_attempts == 0:
        return 0.0

    return recovered_attempts / failed_attempts


def average_execution_time(records):

    if not records:
        return 0.0

    durations = [
        record["duration_seconds"]
        for record in records
    ]

    return sum(durations) / len(durations)


def calculate_metrics(records):

    return {
        "task_success_rate": task_success_rate(records),

        "tool_selection_accuracy": (
            average_tool_selection_accuracy(records)
        ),

        "verification_accuracy": verification_accuracy(records),

        "recovery_rate": recovery_rate(records),

        "average_execution_time": average_execution_time(records)
    }
