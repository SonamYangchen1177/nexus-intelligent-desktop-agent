
import logging

from agent.executor import ToolExecutor
from agent.verifier import ExecutionVerifier
from agent.recovery import ErrorRecovery
from agent.adaptation import AdaptiveBehaviour

from memory.short_term import ShortTermMemory
from memory.episodic import EpisodicMemory


logger = logging.getLogger(__name__)


class AgentController:

    def __init__(self):

        self.executor = ToolExecutor()
        self.verifier = ExecutionVerifier()
        self.recovery = ErrorRecovery(max_retries=2)
        self.adaptation = AdaptiveBehaviour()

        # Initialize memory systems
        self.short_memory = ShortTermMemory(
            max_messages=10
        )

        self.episodic_memory = EpisodicMemory()

        logger.info(
            "AgentController initialized successfully."
        )

    # ======================================================
    # EXECUTE PLAN
    # ======================================================

    def execute_plan(self, plan):

        execution_history = []

        logger.info(
            "New task started | Goal: %s",
            plan.goal
        )

        # --------------------------------------------------
        # UPDATE SHORT-TERM MEMORY
        # --------------------------------------------------

        self.short_memory.set_goal(plan.goal)

        self.short_memory.set_plan(
            plan.model_dump()
        )

        self.short_memory.add_message(
            "user",
            plan.goal
        )

        # --------------------------------------------------
        # RETRIEVE PREVIOUS EXPERIENCES
        # --------------------------------------------------

        previous_experiences = (
            self.episodic_memory.get_recent_experiences(
                limit=5
            )
        )

        previous_feedback = (
            self.episodic_memory.get_recent_feedback(
                limit=5
            )
        )

        print("\nPREVIOUS TASK EXPERIENCES")
        print("=" * 45)

        if previous_experiences:

            for experience in previous_experiences:

                print(
                    f"Goal: {experience['goal']} | "
                    f"Status: {experience['status']}"
                )

        else:

            print("No previous experiences found.")

        # --------------------------------------------------
        # GENERATE ADAPTIVE GUIDANCE
        # --------------------------------------------------

        guidance = self.adaptation.generate_guidance(
            previous_experiences
        )

        print("\nADAPTIVE GUIDANCE")
        print("=" * 45)
        print(guidance)

        logger.info(
            "Adaptive guidance generated."
        )

        # --------------------------------------------------
        # DISPLAY PREVIOUS FEEDBACK
        # --------------------------------------------------

        print("\nPREVIOUS USER FEEDBACK")
        print("=" * 45)

        if previous_feedback:

            for item in previous_feedback:

                print("-", item["feedback"])

        else:

            print("No previous feedback found.")

        # --------------------------------------------------
        # EXECUTE PLANNED STEPS
        # --------------------------------------------------

        for step in plan.steps:

            logger.info(
                "Executing step %s | Tool: %s | Description: %s",
                step.step_id,
                step.tool,
                step.description
            )

            print(f"\nExecuting Step {step.step_id}")
            print("Description:", step.description)
            print("Tool:", step.tool)

            retries = 0

            result = None

            verification = {
                "verified": False,
                "message": "Step has not been verified."
            }

            status = "failed"

            # --------------------------------------------------
            # EXECUTION AND RECOVERY LOOP
            # --------------------------------------------------

            while True:

                try:

                    # ------------------------------------------
                    # 1. EXECUTE SELECTED TOOL
                    # ------------------------------------------

                    result = self.executor.execute_tool(
                        step.tool,
                        step.parameters
                    )

                    # ------------------------------------------
                    # 2. APPLY ADAPTIVE BEHAVIOUR
                    # ------------------------------------------

                    # Adapt the result before checking failure.
                    # This allows Nexus to handle known situations,
                    # such as reusing an existing folder.

                    result = self.adaptation.adapt_result(
                        step.tool,
                        result
                    )

                    # ------------------------------------------
                    # 3. CHECK TOOL-LEVEL SUCCESS
                    # ------------------------------------------

                    if isinstance(result, dict):

                        if result.get("success") is False:

                            raise RuntimeError(
                                result.get(
                                    "message",
                                    "Tool execution was unsuccessful."
                                )
                            )

                    # ------------------------------------------
                    # 4. VERIFY ACTUAL EXECUTION RESULT
                    # ------------------------------------------

                    verification = self.verifier.verify(
                        step.tool,
                        result
                    )

                    if not verification.get("verified", False):

                        raise RuntimeError(
                            verification.get(
                                "message",
                                "Execution verification failed."
                            )
                        )

                    status = "success"

                    logger.info(
                        "Step %s completed successfully.",
                        step.step_id
                    )

                    break

                # ----------------------------------------------
                # 5. ERROR HANDLING AND RECOVERY
                # ----------------------------------------------

                except Exception as error:

                    error_type = (
                        self.recovery.classify_error(error)
                    )

                    logger.exception(
                        "Step %s failed | Error type: %s",
                        step.step_id,
                        error_type
                    )

                    print("Error:", error)
                    print("Error type:", error_type)

                    # Check whether the failed operation
                    # should be retried.

                    if self.recovery.should_retry(
                        error,
                        retries
                    ):

                        retries += 1

                        logger.warning(
                            "Retrying step %s | Attempt %s/%s",
                            step.step_id,
                            retries,
                            self.recovery.max_retries
                        )

                        print(
                            f"Retrying: {retries}/"
                            f"{self.recovery.max_retries}"
                        )

                        continue

                    # No more retries available.
                    status = "failed"

                    result = {
                        "success": False,
                        "error": str(error)
                    }

                    verification = {
                        "verified": False,
                        "message": str(error)
                    }

                    break

            # --------------------------------------------------
            # RECORD EXECUTION RESULT
            # --------------------------------------------------

            record = {

                "step_id": step.step_id,

                "description": step.description,

                "tool": step.tool,

                "status": status,

                "result": result,

                "verification": verification,

                "attempts": retries + 1
            }

            execution_history.append(record)

            # --------------------------------------------------
            # UPDATE SHORT-TERM MEMORY
            # --------------------------------------------------

            self.short_memory.add_execution(
                record
            )

            self.short_memory.add_message(
                "agent",
                f"Step {step.step_id}: {status}"
            )

            print("Status:", status)
            print("Verification:", verification)

            # Stop execution if a step fails.
            if status == "failed":

                logger.error(
                    "Execution stopped because step %s failed.",
                    step.step_id
                )

                print("Execution stopped.")

                break

        # --------------------------------------------------
        # DETERMINE OVERALL TASK STATUS
        # --------------------------------------------------

        all_steps_completed = (
            len(execution_history) == len(plan.steps)
            and all(
                item["status"] == "success"
                and item["verification"].get(
                    "verified", False
                )
                for item in execution_history
            )
        )

        overall_status = (
            "success"
            if all_steps_completed
            else "failed"
        )

        # --------------------------------------------------
        # SAVE EPISODIC MEMORY
        # --------------------------------------------------

        self.episodic_memory.save_experience(
            goal=plan.goal,
            status=overall_status,
            execution_history=execution_history
        )

        # --------------------------------------------------
        # UPDATE SHORT-TERM MEMORY
        # --------------------------------------------------

        self.short_memory.add_message(
            "agent",
            f"Task completed with status: {overall_status}"
        )

        # --------------------------------------------------
        # FINAL LOGGING
        # --------------------------------------------------

        logger.info(
            "Task finished | Goal: %s | Status: %s",
            plan.goal,
            overall_status
        )

        print("\nTASK COMPLETED")
        print("Overall status:", overall_status)

        # --------------------------------------------------
        # RETURN COMPLETE EXECUTION RESULT
        # --------------------------------------------------

        return {

            "goal": plan.goal,

            "overall_status": overall_status,

            "execution_history": execution_history,

            "total_steps": len(plan.steps),

            "completed_steps": sum(
                1
                for item in execution_history
                if item["status"] == "success"
            ),

            "failed_steps": sum(
                1
                for item in execution_history
                if item["status"] == "failed"
            )
        }

    # ======================================================
    # SHORT-TERM MEMORY
    # ======================================================

    def get_memory_context(self):

        return self.short_memory.get_context()

    # ======================================================
    # PREVIOUS TASK EXPERIENCES
    # ======================================================

    def get_previous_experiences(self, limit=5):

        return (
            self.episodic_memory.get_recent_experiences(
                limit=limit
            )
        )

    # ======================================================
    # RECORD USER FEEDBACK
    # ======================================================

    def record_feedback(self, feedback):

        processed = self.adaptation.process_feedback(
            feedback
        )

        self.episodic_memory.save_feedback(
            processed["feedback"]
        )

        logger.info(
            "User feedback saved successfully."
        )

        return processed

    # ======================================================
    # RETRIEVE USER FEEDBACK
    # ======================================================

    def get_user_feedback(self, limit=5):

        return (
            self.episodic_memory.get_recent_feedback(
                limit=limit
            )
        )

    # ======================================================
    # CLOSE MEMORY CONNECTION
    # ======================================================

    def close(self):

        if self.episodic_memory:

            self.episodic_memory.close()

        logger.info(
            "AgentController database connection closed."
        )
