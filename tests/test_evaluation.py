
import pytest

from evaluation.metrics import (
    tool_selection_accuracy,
    task_success_rate,
    verification_accuracy,
    recovery_rate,
    average_execution_time,
    average_tool_selection_accuracy,
    calculate_metrics
)


# ==========================================================
# 1. SAMPLE EVALUATION RECORDS
# ==========================================================

# These records are illustrative test inputs.
# They are NOT actual Nexus agent performance results.

sample_records = [

    {
        "status": "success",
        "duration_seconds": 4.5,
        "tool_selection_accuracy": 1.0,

        "steps": [
            {
                "verified": True,
                "initial_failure": False,
                "recovered": False
            },
            {
                "verified": True,
                "initial_failure": False,
                "recovered": False
            }
        ]
    },

    {
        "status": "failed",
        "duration_seconds": 6.5,
        "tool_selection_accuracy": 0.5,

        "steps": [
            {
                "verified": False,
                "initial_failure": True,
                "recovered": False
            }
        ]
    },

    {
        "status": "success",
        "duration_seconds": 5.0,
        "tool_selection_accuracy": 1.0,

        "steps": [
            {
                "verified": True,
                "initial_failure": True,
                "recovered": True
            }
        ]
    }
]


# ==========================================================
# 2. TEST TOOL SELECTION ACCURACY
# ==========================================================

def test_tool_selection_accuracy():

    expected = [
        "search_files",
        "generate_report"
    ]

    predicted = [
        "search_files",
        "generate_report"
    ]

    accuracy = tool_selection_accuracy(
        expected,
        predicted
    )

    assert accuracy == 1.0


def test_tool_selection_with_incorrect_tool():

    expected = [
        "search_files",
        "generate_report"
    ]

    predicted = [
        "search_files",
        "create_folder"
    ]

    accuracy = tool_selection_accuracy(
        expected,
        predicted
    )

    assert accuracy == 0.5


# ==========================================================
# 3. TEST TASK SUCCESS RATE
# ==========================================================

def test_task_success_rate():

    result = task_success_rate(
        sample_records
    )

    assert result == pytest.approx(2 / 3)


# ==========================================================
# 4. TEST AVERAGE TOOL SELECTION ACCURACY
# ==========================================================

def test_average_tool_selection_accuracy():

    result = average_tool_selection_accuracy(
        sample_records
    )

    assert result == pytest.approx(2.5 / 3)


# ==========================================================
# 5. TEST VERIFICATION ACCURACY
# ==========================================================

def test_verification_accuracy():

    result = verification_accuracy(
        sample_records
    )

    assert result == pytest.approx(3 / 4)


# ==========================================================
# 6. TEST RECOVERY RATE
# ==========================================================

def test_recovery_rate():

    result = recovery_rate(
        sample_records
    )

    assert result == pytest.approx(1 / 2)


# ==========================================================
# 7. TEST AVERAGE EXECUTION TIME
# ==========================================================

def test_average_execution_time():

    result = average_execution_time(
        sample_records
    )

    expected = (
        4.5 + 6.5 + 5.0
    ) / 3

    assert result == pytest.approx(expected)


# ==========================================================
# 8. TEST COMPLETE METRIC CALCULATION
# ==========================================================

def test_calculate_all_metrics():

    results = calculate_metrics(
        sample_records
    )

    assert results["task_success_rate"] == pytest.approx(
        2 / 3
    )

    assert results["tool_selection_accuracy"] == pytest.approx(
        2.5 / 3
    )

    assert results["verification_accuracy"] == pytest.approx(
        3 / 4
    )

    assert results["recovery_rate"] == pytest.approx(
        1 / 2
    )

    assert results["average_execution_time"] == pytest.approx(
        (4.5 + 6.5 + 5.0) / 3
    )


# ==========================================================
# 9. TEST EMPTY RECORDS
# ==========================================================

def test_empty_records():

    results = calculate_metrics([])

    assert results["task_success_rate"] == 0.0

    assert results["tool_selection_accuracy"] == 0.0

    assert results["verification_accuracy"] == 0.0

    assert results["recovery_rate"] == 0.0

    assert results["average_execution_time"] == 0.0
