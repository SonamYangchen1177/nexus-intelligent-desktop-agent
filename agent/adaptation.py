
class AdaptiveBehaviour:

    def adapt_result(self, tool_name, result):

        # Avoid failing when the requested folder
        # already exists.
        if (
            tool_name == "create_folder"
            and isinstance(result, dict)
            and result.get("success") is False
            and "already exists" in result.get(
                "message", ""
            ).lower()
        ):

            from pathlib import Path

            folder = Path(result["path"])

            if folder.is_dir():
                return {
                    "success": True,
                    "message": (
                        "Folder already existed. "
                        "Existing folder will be reused."
                    ),
                    "path": str(folder),
                    "adapted": True
                }

        return result

    def generate_guidance(self, experiences):

        guidance = []

        for experience in experiences:

            if experience["status"] == "failed":

                guidance.append(
                    "A previous task failed: "
                    + experience["goal"]
                )

                for step in experience.get(
                    "execution_history", []
                ):

                    if step["status"] == "failed":

                        guidance.append(
                            "Previous failure: "
                            + str(step.get("result", {}))
                        )

        if not guidance:
            return (
                "No previous failures found. "
                "Follow the current execution plan."
            )

        return "\n".join(guidance)

    def process_feedback(self, feedback):

        feedback = feedback.strip()

        if not feedback:
            raise ValueError(
                "Feedback cannot be empty."
            )

        return {
            "feedback": feedback,
            "status": "recorded"
        }
