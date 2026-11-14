# ==========================================================
# NEXUS DESKTOP AGENT - EVALUATION METRICS
# ==========================================================


def tool_selection_accuracy(expected_tools, predicted_tools):
    """
    Measure how accurately the planner selects the expected
    tools in the expected sequence.

    This is positional sequence accuracy, not semantic similarity.
    """

    if not expected_tools:
        return 1.0 if not predicted_tools else 0.0

    total_positions = max(
        len(expected_tools),
        len(predicted_tools)
    )

    correct_positions = sum(
        1
        for index in range(
            min(len(expected_tools), len(predicted_tools))
        )
        if expected_tools[index] == predicted_tools[index]
    )

    return correct_positions / total_positions


def average_tool_selection_accuracy(records):
    """Calculate the average tool-selection accuracy."""

    if not records:
        return 0.0

    scores = [
        record.get("tool_selection_accuracy", 0.0)
        for record in records
    ]

    return sum(scores) / len(scores)


def task_success_rate(records):
    """
    Calculate the proportion of tasks successfully completed.

    Uses the overall_status returned by AgentController,
    which already considers execution and verification.
    """

    if not records:
        return 0.0

    successful_tasks = sum(
        1
        for record in records
        if record.get("status") == "success"
    )

    return successful_tasks / len(records)


def verification_accuracy(records):
    """
    Calculate the proportion of executed steps that
    passed verification.
    """

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


def recovery_opportunities(records):
    """
    Count the number of steps that required at least
    one retry.
    """

    return sum(
        1
        for record in records
        for step in record.get("steps", [])
        if step.get("initial_failure") is True
    )


def recovered_steps(records):
    """
    Count retried steps that eventually succeeded.
    """

    return sum(
        1
        for record in records
        for step in record.get("steps", [])
        if (
            step.get("initial_failure") is True
            and step.get("recovered") is True
        )
    )


def recovery_rate(records):
    """
    Calculate the proportion of retried steps
    that eventually recovered successfully.

    Returns 0.0 when no recovery opportunities occurred.
    Check recovery_opportunities separately to interpret
    this value correctly.
    """

    opportunities = recovery_opportunities(records)

    if opportunities == 0:
        return 0.0

    return recovered_steps(records) / opportunities


def total_executed_steps(records):
    """Count all execution steps recorded during evaluation."""

    return sum(
        len(record.get("steps", []))
        for record in records
    )


def total_verified_steps(records):
    """Count execution steps that passed verification."""

    return sum(
        1
        for record in records
        for step in record.get("steps", [])
        if step.get("verified") is True
    )


def average_execution_time(records):
    """Calculate the average task execution time in seconds."""

    if not records:
        return 0.0

    durations = [
        record.get("duration_seconds", 0.0)
        for record in records
    ]

    return sum(durations) / len(durations)


def calculate_metrics(records):
    """
    Calculate all evaluation metrics and supporting counts.
    """

    return {

        "task_success_rate": task_success_rate(records),

        "tool_selection_accuracy": (
            average_tool_selection_accuracy(records)
        ),

        "verification_accuracy": (
            verification_accuracy(records)
        ),

        "recovery_rate": recovery_rate(records),

        "average_execution_time": (
            average_execution_time(records)
        ),

        # Supporting counts help interpret the percentages.

        "total_executed_steps": (
            total_executed_steps(records)
        ),

        "verified_steps": (
            total_verified_steps(records)
        ),

        "recovery_opportunities": (
            recovery_opportunities(records)
        ),

        "recovered_steps": (
            recovered_steps(records)
        )
    }