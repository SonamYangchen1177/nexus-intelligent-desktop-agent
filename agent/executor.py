
import logging

from tools.file_search import search_files
from tools.folder_manager import create_folder
from tools.file_manager import move_file, rename_file
from tools.report_generator import generate_report

logger = logging.getLogger(__name__)


class ToolExecutor:

    def __init__(self):

        self.tool_registry = {
            "search_files": search_files,
            "create_folder": create_folder,
            "move_file": move_file,
            "rename_file": rename_file,
            "generate_report": generate_report,
            "verify_files": self.verify_files
        }

    def verify_files(self, paths):

        from safety.guardrails import validate_path

        results = []

        for path in paths:

            target = validate_path(path)

            results.append({
                "path": str(target),
                "exists": target.exists(),
                "is_file": target.is_file(),
                "is_directory": target.is_dir()
            })

        return {
            "success": all(
                item["exists"] for item in results
            ),
            "results": results
        }

    def execute_tool(self, tool_name, parameters):

        if tool_name not in self.tool_registry:

            logger.error(
                "Unknown tool requested: %s",
                tool_name
            )

            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        logger.info(
            "Tool execution started | Tool: %s",
            tool_name
        )

        try:

            tool_function = self.tool_registry[tool_name]

            result = tool_function(**parameters)

            logger.info(
                "Tool execution completed | Tool: %s",
                tool_name
            )

            return result

        except Exception:

            logger.exception(
                "Tool execution failed | Tool: %s",
                tool_name
            )

            raise
