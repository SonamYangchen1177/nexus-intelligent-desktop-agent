
from datetime import datetime
from safety.guardrails import validate_path

def generate_report(title, content, output_path):
    output_file = validate_path(output_path)

    if output_file.exists():
        raise FileExistsError(
            "Report already exists. Choose another filename."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    report = f"""
{title}
{'=' * len(title)}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{content}
"""

    output_file.write_text(report, encoding="utf-8")

    return {
        "success": True,
        "message": "Report generated successfully.",
        "path": str(output_file)
    }