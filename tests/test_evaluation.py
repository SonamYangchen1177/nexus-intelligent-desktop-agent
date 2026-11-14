
from evaluation.metrics import (
    tool_selection_accuracy,
    task_success_rate,
    verification_accuracy,
    recovery_rate,
    average_execution_time,
    calculate_metrics
)


# Test tool selection accuracy
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

print("Tool selection accuracy test passed.")


# Sample records for testing metric calculations
# These are test inputs, not actual agent performance results.
sample_records = [

    {
        "status": "success",
        "duration_seconds": 4.5,
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
        "steps": [
            {
                "verified": True,
                "initial_failure": True,
                "recovered": True
            }
        ]
    }
]


# Test individual metrics
assert task_success_rate(sample_records) == 2 / 3

assert verification_accuracy(sample_records) == 3 / 4

assert recovery_rate(sample_records) == 1 / 2

assert average_execution_time(sample_records) == (4.5 + 6.5 + 5.0) / 3

print("Task success rate test passed.")
print("Verification accuracy test passed.")
print("Recovery rate test passed.")
print("Average execution time test passed.")


# Calculate all metrics
results = calculate_metrics(sample_records)

print("\nEVALUATION METRICS")
print("=" * 40)

for metric, value in results.items():

    if "rate" in metric or "accuracy" in metric:
        print(f"{metric}: {value * 100:.2f}%")
    else:
        print(f"{metric}: {value:.2f} seconds")

print("\nAll evaluation tests passed.")
