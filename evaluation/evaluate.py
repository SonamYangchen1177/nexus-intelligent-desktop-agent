import json
import time
import logging

from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt

from agent.planner import TaskPlanner
from agent.decision_maker import AgentController

from evaluation.metrics import (
    tool_selection_accuracy,
    calculate_metrics
)


# ==========================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TEST_CASES_PATH = (
    BASE_DIR / "evaluation" / "test_cases.json"
)

RESULTS_PATH = (
    BASE_DIR / "evaluation" / "results.json"
)

CHART_PATH = (
    BASE_DIR / "reports" / "evaluation_metrics.png"
)

BASE_DIR.joinpath("reports").mkdir(
    parents=True,
    exist_ok=True
)

logger = logging.getLogger(__name__)

# Keep this at 2 while testing.
# Increase it after confirming that repeated evaluations
# do not interfere with existing workspace files.

TEST_LIMIT = 2


# ==========================================================
# 2. LOAD TEST CASES
# ==========================================================

def load_test_cases():
    """Load evaluation scenarios from the JSON file."""

    if not TEST_CASES_PATH.exists():
        raise FileNotFoundError(
            f"Test cases file not found: {TEST_CASES_PATH}"
        )

    with open(
        TEST_CASES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        test_cases = json.load(file)

    if not isinstance(test_cases, list):
        raise ValueError(
            "Test cases must be stored as a JSON list."
        )

    return test_cases


# ==========================================================
# 3. EXTRACT EXECUTION INFORMATION
# ==========================================================

def extract_execution_steps(execution_history):
    """
    Extract relevant information from the actual
    AgentController execution history.
    """

    evaluated_steps = []

    for step in execution_history:

        verification = step.get(
            "verification",
            {}
        )

        attempts = step.get("attempts", 1)

        status = step.get(
            "status",
            "failed"
        )

        evaluated_steps.append({

            "step_id": step.get("step_id"),

            "tool": step.get(
                "tool",
                "unknown"
            ),

            "status": status,

            "attempts": attempts,

            "verified": (
                verification.get("verified") is True
            ),

            "verification_message": (
                verification.get("message", "")
            ),

            # A retry indicates that an earlier attempt failed.
            "initial_failure": attempts > 1,

            # The retried step recovered if it eventually succeeded.
            "recovered": (
                attempts > 1
                and status == "success"
            ),

            "error": step.get(
                "result",
                {}
            ).get("error")
            if isinstance(step.get("result"), dict)
            else None

        })

    return evaluated_steps


# ==========================================================
# 4. RUN AGENT EVALUATION
# ==========================================================

def run_evaluation():

    test_cases = load_test_cases()

    if TEST_LIMIT is not None:
        test_cases = test_cases[:TEST_LIMIT]

    planner = TaskPlanner()
    controller = AgentController()

    evaluation_records = []

    print("\nNEXUS DESKTOP AGENT EVALUATION")
    print("=" * 60)

    print("Total test cases:", len(test_cases))

    try:

        for index, test_case in enumerate(
            test_cases,
            start=1
        ):

            print("\n" + "=" * 60)

            print(
                f"TEST CASE {index}/{len(test_cases)}"
            )

            print("Test ID:", test_case.get("id"))
            print("Goal:", test_case["goal"])

            start_time = time.perf_counter()

            predicted_tools = []
            evaluated_steps = []

            selection_accuracy = 0.0
            task_status = "failed"
            error_message = None

            execution_history = []

            expected_tools = test_case.get(
                "expected_tools",
                []
            )

            try:

                # --------------------------------------------------
                # 1. GENERATE EXECUTION PLAN
                # --------------------------------------------------

                print("\nGenerating execution plan...")

                plan = planner.create_plan(
                    test_case["goal"]
                )

                predicted_tools = [
                    step.tool
                    for step in plan.steps
                ]

                # --------------------------------------------------
                # 2. EVALUATE TOOL SELECTION
                # --------------------------------------------------

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

                # --------------------------------------------------
                # 3. EXECUTE THE PLAN
                # --------------------------------------------------

                print("\nExecuting agent plan...")

                execution_result = controller.execute_plan(
                    plan
                )

                # --------------------------------------------------
                # 4. EXTRACT ACTUAL CONTROLLER RESULT
                # --------------------------------------------------

                if not isinstance(execution_result, dict):

                    raise TypeError(
                        "AgentController returned an unexpected "
                        "execution result. Expected a dictionary."
                    )

                execution_history = execution_result.get(
                    "execution_history",
                    []
                )

                # Use the actual overall status.
                # AgentController already checks execution
                # and verification before returning this value.

                task_status = execution_result.get(
                    "overall_status",
                    "failed"
                )

                if task_status not in ["success", "failed"]:

                    task_status = "failed"

                    error_message = (
                        "AgentController returned an invalid "
                        "overall task status."
                    )

                # --------------------------------------------------
                # 5. EXTRACT VERIFICATION AND RECOVERY DATA
                # --------------------------------------------------

                evaluated_steps = extract_execution_steps(
                    execution_history
                )

                print(
                    "\nCompleted steps:",
                    execution_result.get(
                        "completed_steps",
                        0
                    )
                )

                print(
                    "Failed steps:",
                    execution_result.get(
                        "failed_steps",
                        0
                    )
                )

                print(
                    "Overall agent status:",
                    task_status
                )

            except Exception as error:

                error_message = str(error)

                task_status = "failed"

                logger.exception(
                    "Evaluation failed for test case %s",
                    test_case.get("id")
                )

                print(
                    "\nEvaluation error:",
                    error_message
                )

            # ------------------------------------------------------
            # 6. CALCULATE EXECUTION DURATION
            # ------------------------------------------------------

            duration = (
                time.perf_counter() - start_time
            )

            # ------------------------------------------------------
            # 7. STORE EVALUATION RECORD
            # ------------------------------------------------------

            record = {

                "test_id": test_case.get("id"),

                "goal": test_case["goal"],

                "expected_tools": expected_tools,

                "predicted_tools": predicted_tools,

                "tool_selection_accuracy": (
                    selection_accuracy
                ),

                "status": task_status,

                "duration_seconds": round(
                    duration,
                    2
                ),

                "error": error_message,

                "steps": evaluated_steps

            }

            evaluation_records.append(record)

            print("\nTEST CASE RESULT")
            print("-" * 40)

            print("Task status:", task_status)

            print(
                "Execution time:",
                f"{duration:.2f} seconds"
            )

            print(
                "Recorded steps:",
                len(evaluated_steps)
            )

    finally:

        controller.close()

    # ==========================================================
    # 5. CALCULATE PERFORMANCE METRICS
    # ==========================================================

    metrics = calculate_metrics(
        evaluation_records
    )

    # ==========================================================
    # 6. PREPARE EVALUATION REPORT
    # ==========================================================

    evaluation_report = {

        "project": "Nexus Intelligent Desktop Agent",

        "evaluation_date": datetime.now().isoformat(),

        "total_test_cases": len(test_cases),

        "completed_test_cases": len(
            evaluation_records
        ),

        "metrics": metrics,

        "results": evaluation_records

    }

    # ==========================================================
    # 7. SAVE RESULTS AS JSON
    # ==========================================================

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

    # ==========================================================
    # 8. DISPLAY EVALUATION SUMMARY
    # ==========================================================

    print("\nEVALUATION SUMMARY")
    print("=" * 60)

    percentage_metrics = [
        "task_success_rate",
        "tool_selection_accuracy",
        "verification_accuracy",
        "recovery_rate"
    ]

    for metric, value in metrics.items():

        if metric in percentage_metrics:

            print(
                f"{metric}: {value * 100:.2f}%"
            )

        elif metric == "average_execution_time":

            print(
                f"{metric}: {value:.2f} seconds"
            )

        else:

            print(
                f"{metric}: {value}"
            )

    print("\nResults saved to:")
    print(RESULTS_PATH)

    # ==========================================================
    # 9. GENERATE PERFORMANCE CHART
    # ==========================================================

    generate_chart(metrics)

    return evaluation_report


# ==========================================================
# 10. GENERATE PERFORMANCE VISUALIZATION
# ==========================================================

def generate_chart(metrics):
    """
    Generate a bar chart showing the main
    performance metrics of Nexus.
    """

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
        "Nexus Desktop Agent Performance Evaluation"
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


# ==========================================================
# 11. MAIN ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    run_evaluation()