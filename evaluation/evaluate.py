
import json
import time

from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt

from agent.planner import TaskPlanner
from agent.decision_maker import AgentController

from evaluation.metrics import (
    tool_selection_accuracy,
    calculate_metrics
)


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

TEST_CASES_PATH = BASE_DIR / "evaluation" / "test_cases.json"
RESULTS_PATH = BASE_DIR / "evaluation" / "results.json"
CHART_PATH = BASE_DIR / "reports" / "evaluation_metrics.png"

BASE_DIR.joinpath("reports").mkdir(
    parents=True,
    exist_ok=True
)


# Set to 2 for initial testing.
# Change to None to evaluate all scenarios.
TEST_LIMIT = 2


def load_test_cases():

    with open(
        TEST_CASES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def run_evaluation():

    test_cases = load_test_cases()

    if TEST_LIMIT is not None:
        test_cases = test_cases[:TEST_LIMIT]

    planner = TaskPlanner()
    controller = AgentController()

    evaluation_records = []

    print("\nDESKTOP AGENT EVALUATION")
    print("=" * 55)

    print("Total test cases:", len(test_cases))

    try:

        for index, test_case in enumerate(
            test_cases,
            start=1
        ):

            print("\n" + "=" * 55)

            print(
                f"TEST CASE {index}/{len(test_cases)}"
            )

            print("Goal:", test_case["goal"])

            start_time = time.perf_counter()

            predicted_tools = []
            selection_accuracy = 0.0
            task_status = "failed"
            evaluated_steps = []

            try:

                # Generate plan using the LLM
                plan = planner.create_plan(
                    test_case["goal"]
                )

                # Extract selected tools
                predicted_tools = [
                    step.tool
                    for step in plan.steps
                ]

                expected_tools = test_case[
                    "expected_tools"
                ]

                # Evaluate tool selection
                selection_accuracy = (
                    tool_selection_accuracy(
                        expected_tools,
                        predicted_tools
                    )
                )

                print(
                    "Expected tools:",
                    expected_tools
                )

                print(
                    "Selected tools:",
                    predicted_tools
                )

                print(
                    "Tool selection accuracy:",
                    f"{selection_accuracy * 100:.2f}%"
                )

                # Execute generated plan
                execution_history = (
                    controller.execute_plan(plan)
                )

                # Determine task status
                task_status = (
                    "success"
                    if len(execution_history) == len(plan.steps)
                    and all(
                        step["status"] == "success"
                        for step in execution_history
                    )
                    else "failed"
                )

                # Extract verification and recovery details
                for step in execution_history:

                    attempts = step.get("attempts", 1)

                    evaluated_steps.append({

                        "tool": step["tool"],

                        "verified": step.get(
                            "verification", {}
                        ).get("verified", False),

                        "initial_failure": (
                            attempts > 1
                            or step["status"] == "failed"
                        ),

                        "recovered": (
                            attempts > 1
                            and step["status"] == "success"
                        )

                    })

            except Exception as error:

                print(
                    "Evaluation error:",
                    str(error)
                )

                task_status = "failed"

            duration = (
                time.perf_counter() - start_time
            )

            # Store evaluation record
            record = {

                "test_id": test_case["id"],

                "goal": test_case["goal"],

                "expected_tools": test_case[
                    "expected_tools"
                ],

                "predicted_tools": predicted_tools,

                "tool_selection_accuracy": (
                    selection_accuracy
                ),

                "status": task_status,

                "duration_seconds": round(
                    duration,
                    2
                ),

                "steps": evaluated_steps

            }

            evaluation_records.append(record)

            print("Task status:", task_status)

            print(
                "Execution time:",
                f"{duration:.2f} seconds"
            )

    finally:

        controller.close()

    # Calculate performance metrics
    metrics = calculate_metrics(
        evaluation_records
    )

    # Prepare evaluation report
    evaluation_report = {

        "evaluation_date": datetime.now().isoformat(),

        "total_test_cases": len(test_cases),

        "completed_test_cases": len(
            evaluation_records
        ),

        "metrics": metrics,

        "results": evaluation_records

    }

    # Save results as JSON
    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            evaluation_report,
            file,
            indent=4
        )

    # Display evaluation summary
    print("\nEVALUATION SUMMARY")
    print("=" * 55)

    for metric, value in metrics.items():

        if metric == "average_execution_time":

            print(
                f"{metric}: {value:.2f} seconds"
            )

        else:

            print(
                f"{metric}: {value * 100:.2f}%"
            )

    print("\nResults saved to:")
    print(RESULTS_PATH)

    # Generate performance visualization
    generate_chart(metrics)

    return evaluation_report


def generate_chart(metrics):

    chart_metrics = {

        "Task Success":
            metrics["task_success_rate"] * 100,

        "Tool Selection":
            metrics["tool_selection_accuracy"] * 100,

        "Verification":
            metrics["verification_accuracy"] * 100,

        "Recovery":
            metrics["recovery_rate"] * 100

    }

    plt.figure(figsize=(10, 6))

    bars = plt.bar(
        chart_metrics.keys(),
        chart_metrics.values()
    )

    plt.title(
        "Desktop Agent Performance Evaluation"
    )

    plt.ylabel("Performance (%)")

    plt.xlabel("Evaluation Metrics")

    plt.ylim(0, 100)

    plt.bar_label(
        bars,
        fmt="%.1f%%",
        padding=3
    )

    plt.tight_layout()

    plt.savefig(
        CHART_PATH,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print("\nPerformance chart saved to:")
    print(CHART_PATH)


if __name__ == "__main__":

    run_evaluation()
