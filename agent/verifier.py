
from safety.guardrails import validate_path


class ExecutionVerifier:

    def verify(self, tool_name, result):

        # --------------------------------------------------
        # 1. Verify file search
        # --------------------------------------------------
        if tool_name == "search_files":

            if isinstance(result, list):
                return {
                    "verified": True,
                    "message": (
                        f"Search completed. "
                        f"Found {len(result)} items."
                    )
                }

            return {
                "verified": False,
                "message": "Search returned an unexpected result."
            }

        # --------------------------------------------------
        # 2. Validate result format
        # --------------------------------------------------
        if not isinstance(result, dict):
            return {
                "verified": False,
                "message": "Unexpected tool result format."
            }

        if result.get("success") is False:
            return {
                "verified": False,
                "message": result.get(
                    "message",
                    "Tool execution failed."
                )
            }

        if result.get("error"):
            return {
                "verified": False,
                "message": result["error"]
            }

        # --------------------------------------------------
        # 3. Verify folder creation
        # --------------------------------------------------
        if tool_name == "create_folder":

            path = result.get("path")

            verified = (
                path is not None
                and validate_path(path).is_dir()
            )

        # --------------------------------------------------
        # 4. Verify file movement
        # --------------------------------------------------
        elif tool_name == "move_file":

            path = result.get("destination_path")

            verified = (
                path is not None
                and validate_path(path).is_file()
            )

        # --------------------------------------------------
        # 5. Verify file renaming
        # --------------------------------------------------
        elif tool_name == "rename_file":

            path = result.get("new_path")

            verified = (
                path is not None
                and validate_path(path).is_file()
            )

        # --------------------------------------------------
        # 6. Verify report generation
        # --------------------------------------------------
        elif tool_name == "generate_report":

            path = result.get("path")

            verified = (
                path is not None
                and validate_path(path).is_file()
            )

        # --------------------------------------------------
        # 7. Verify requested paths
        # --------------------------------------------------
        elif tool_name == "verify_files":

            verified = result.get("success") is True

        else:

            verified = result.get("success") is True

        # --------------------------------------------------
        # 8. Return verification result
        # --------------------------------------------------
        return {
            "verified": verified,
            "message": (
                "Execution verified successfully."
                if verified
                else "Execution could not be verified."
            )
        }
