from __future__ import annotations

import base64
import html
import json
import os
from pathlib import Path
from typing import Any

from visual.comparator import VisualComparisonResult


def relative_path(
    source_path: Path,
    target_path: Path,
) -> str:
    """
    Возвращает относительный путь от source_path к target_path.
    """

    return os.path.relpath(
        target_path.resolve(),
        source_path.parent.resolve(),
    ).replace("\\", "/")


def image_to_data_uri(
    path: Path,
) -> str:
    """
    Преобразует PNG в data URI для HTML.
    """

    if not path.exists():
        return ""

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("ascii")

    return f"data:image/png;base64,{encoded}"


class VisualReporter:
    """
    Формирует visual regression reports
    и отдельные bug reports для FAIL.
    """

    def __init__(
        self,
        reports_directory: Path,
    ) -> None:

        self.reports_directory = reports_directory

        self.bugs_directory = (
            reports_directory / "bugs"
        )

        self.reports_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.bugs_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.results: list[dict[str, Any]] = []

    def add_result(
        self,
        screen_id: str,
        reference_path: Path,
        actual_path: Path,
        result: VisualComparisonResult,
    ) -> Path | None:
        """
        Добавляет результат проверки.

        Если результат FAIL:
            создаётся bug report.

        После каждого результата:
            обновляются HTML и JSON отчёты.
        """

        status = (
            "PASS"
            if result.passed
            else "FAIL"
        )

        bug_report_path = None

        if not result.passed:
            bug_report_path = (
                self.create_bug_report(
                    screen_id=screen_id,
                    reference_path=reference_path,
                    actual_path=actual_path,
                    result=result,
                )
            )

        result_data = {
            "screen": screen_id,
            "status": status,
            "similarity": round(
                result.similarity,
                5,
            ),
            "diff_percent": round(
                result.diff_percent,
                5,
            ),
            "expected_size": result.expected_size,
            "actual_size": result.actual_size,
            "bounding_boxes": result.bounding_boxes,
            "reference_path": str(
                reference_path
            ),
            "actual_path": str(
                actual_path
            ),
            "diff_image_path": str(
                result.diff_image_path
            ),
            "overlay_image_path": str(
                result.overlay_image_path
            ),
            "bug_report_path": (
                str(bug_report_path)
                if bug_report_path
                else None
            ),
        }

        self.results.append(
            result_data
        )

        self._write_json_report()
        self._write_html_report()

        return bug_report_path

    def create_bug_report(
        self,
        screen_id: str,
        reference_path: Path,
        actual_path: Path,
        result: VisualComparisonResult,
    ) -> Path:
        """
        Создаёт Markdown bug report.
        """

        bug_report_path = (
            self.bugs_directory
            / f"BUG-{screen_id}.md"
        )

        reference_rel = relative_path(
            bug_report_path,
            reference_path,
        )

        actual_rel = relative_path(
            bug_report_path,
            actual_path,
        )

        diff_rel = relative_path(
            bug_report_path,
            result.diff_image_path,
        )

        overlay_rel = relative_path(
            bug_report_path,
            result.overlay_image_path,
        )

        if result.bounding_boxes:

            bounding_boxes = "\n".join(
                (
                    f"- x={x}, y={y}, "
                    f"width={width}, height={height}"
                )
                for x, y, width, height
                in result.bounding_boxes
            )

        else:

            bounding_boxes = (
                "- Significant difference region "
                "was not localized"
            )

        report_lines = [
            f"# BUG-{screen_id.upper()}",
            "",
            "## Summary",
            "",
            (
                f"UI of **{screen_id}** does not match "
                "the Figma reference design."
            ),
            "",
            "## Status",
            "",
            "**FAIL**",
            "",
            "## Severity",
            "",
            "**Major**",
            "",
            "## Environment",
            "",
            "- Execution mode: Demo",
            "- Framework: Python / Pytest",
            "- Reference source: Figma",
            "- Actual source: simulated runtime screenshot",
            "",
            "## Steps to Reproduce",
            "",
            "1. Run:",
            "",
            "   `pytest -m visual -v`",
            "",
            (
                f"2. Execute the visual comparison "
                f"for `{screen_id}`."
            ),
            "",
            (
                "3. Compare the runtime screenshot "
                "with the Figma reference."
            ),
            "",
            "## Expected Result",
            "",
            (
                "The application screen should visually "
                "correspond to the Figma design."
            ),
            "",
            "No additional UI element should be present.",
            "",
            "## Actual Result",
            "",
            (
                "The actual screen differs from the "
                "Figma reference."
            ),
            "",
            "An unexpected UI element was detected.",
            "",
            "## Visual Metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| SSIM | {result.similarity:.5f} |",
            (
                f"| Different pixels | "
                f"{result.diff_percent:.3f}% |"
            ),
            (
                f"| Expected size | "
                f"{result.expected_size[0]} × "
                f"{result.expected_size[1]} |"
            ),
            (
                f"| Actual size | "
                f"{result.actual_size[0]} × "
                f"{result.actual_size[1]} |"
            ),
            "",
            "## Detected Defect Regions",
            "",
            bounding_boxes,
            "",
            "## Evidence",
            "",
            "### Expected — Figma",
            "",
            f"![Expected]({reference_rel})",
            "",
            "### Actual — Runtime",
            "",
            f"![Actual]({actual_rel})",
            "",
            "### Difference",
            "",
            f"![Diff]({diff_rel})",
            "",
            "### Detected Region",
            "",
            f"![Overlay]({overlay_rel})",
            "",
            "## Result",
            "",
            (
                "The visual regression test detected that:"
            ),
            "",
            "`expected != actual`",
            "",
            (
                "The detected difference was localized "
                "to the reported bounding box(es)."
            ),
            "",
        ]

        report = "\n".join(
            report_lines
        )

        bug_report_path.write_text(
            report,
            encoding="utf-8",
        )

        return bug_report_path

    def _write_json_report(self) -> None:
        """
        Записывает общий JSON report.
        """

        json_path = (
            self.reports_directory
            / "visual_report.json"
        )

        json_path.write_text(
            json.dumps(
                self.results,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _write_html_report(self) -> None:
        """
        Записывает общий HTML report.
        """

        html_path = (
            self.reports_directory
            / "visual_report.html"
        )

        sections: list[str] = []

        for result in self.results:

            status = result["status"]

            status_class = (
                "pass"
                if status == "PASS"
                else "fail"
            )

            reference_uri = image_to_data_uri(
                Path(
                    result["reference_path"]
                )
            )

            actual_uri = image_to_data_uri(
                Path(
                    result["actual_path"]
                )
            )

            diff_uri = image_to_data_uri(
                Path(
                    result["diff_image_path"]
                )
            )

            overlay_uri = image_to_data_uri(
                Path(
                    result["overlay_image_path"]
                )
            )

            boxes = result[
                "bounding_boxes"
            ]

            if boxes:

                boxes_html = "".join(
                    (
                        "<li>"
                        f"x={box[0]}, "
                        f"y={box[1]}, "
                        f"width={box[2]}, "
                        f"height={box[3]}"
                        "</li>"
                    )
                    for box in boxes
                )

            else:

                boxes_html = (
                    "<li>None</li>"
                )

            bug_report_html = ""

            if result["bug_report_path"]:

                bug_path = Path(
                    result["bug_report_path"]
                )

                bug_rel = relative_path(
                    html_path,
                    bug_path,
                )

                bug_report_html = (
                    "<p>"
                    "<strong>Bug report:</strong> "
                    f'<a href="{html.escape(bug_rel)}">'
                    f"{html.escape(bug_path.name)}"
                    "</a>"
                    "</p>"
                )

            section = f"""
<section class="screen">

<h2>
Screen: {html.escape(result["screen"])}
</h2>

<div class="{status_class}">
{status}
</div>

<p>
<strong>SSIM:</strong>
{result["similarity"]:.5f}
</p>

<p>
<strong>Different pixels:</strong>
{result["diff_percent"]:.3f}%
</p>

{bug_report_html}

<p>
<strong>Bounding boxes:</strong>
</p>

<ul>
{boxes_html}
</ul>

<div class="images">

<div>
<h3>Expected</h3>
<img src="{reference_uri}">
</div>

<div>
<h3>Actual</h3>
<img src="{actual_uri}">
</div>

<div>
<h3>Diff</h3>
<img src="{diff_uri}">
</div>

<div>
<h3>Detected regions</h3>
<img src="{overlay_uri}">
</div>

</div>

</section>
"""

            sections.append(section)

        total = len(
            self.results
        )

        passed = sum(
            result["status"] == "PASS"
            for result in self.results
        )

        failed = sum(
            result["status"] == "FAIL"
            for result in self.results
        )

        html_content = f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<title>
iOS / Figma Visual Regression
</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    background: #f7f7f7;
}}

.summary {{
    background: white;
    padding: 20px;
    margin-bottom: 30px;
    border-radius: 10px;
}}

.screen {{
    background: white;
    padding: 25px;
    margin-bottom: 30px;
    border-radius: 10px;
}}

.pass {{
    color: green;
    font-size: 24px;
    font-weight: bold;
}}

.fail {{
    color: red;
    font-size: 24px;
    font-weight: bold;
}}

.images {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
}}

.images img {{
    max-width: 100%;
    border: 1px solid #ccc;
}}

</style>

</head>

<body>

<div class="summary">

<h1>
iOS / Figma Visual Regression Report
</h1>

<p>
<strong>Total:</strong>
{total}
</p>

<p>
<strong>Passed:</strong>
{passed}
</p>

<p>
<strong>Failed:</strong>
{failed}
</p>

</div>

{"".join(sections)}

</body>

</html>
"""

        html_path.write_text(
            html_content,
            encoding="utf-8",
        )