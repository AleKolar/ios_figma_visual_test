from __future__ import annotations

from pathlib import Path

import pytest

from app.demo_image_provider import DemoImageProvider
from figma.figma_client import FigmaClient
from visual.comparator import ImageComparator
from visual.image_normalizer import ImageNormalizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.visual
@pytest.mark.parametrize(
    "screen_id",
    [
        "screen_1",
        "screen_2",
    ],
)
def test_screen_matches_figma(
    screen_id: str,
    project_config: dict,
    visual_reporter,
):
    # ==================================================
    # CONFIGURATION
    # ==================================================

    paths_config = project_config["paths"]
    visual_config = project_config["visual"]
    execution_config = project_config["execution"]

    screen_config = project_config["screens"][screen_id]

    # ==================================================
    # DIRECTORIES
    # ==================================================

    reference_directory = (
        PROJECT_ROOT
        / paths_config["reference_images"]
    )

    actual_directory = (
        PROJECT_ROOT
        / paths_config["actual_images"]
    )

    diff_directory = (
        PROJECT_ROOT
        / paths_config["diff_images"]
    )

    # ==================================================
    # FIGMA REFERENCE
    # ==================================================

    figma_client = FigmaClient(
        reference_directory
    )

    reference_path = (
        figma_client.get_reference_image(
            screen_id=screen_id,
            file_name=screen_config["reference"],
        )
    )

    # ==================================================
    # DEMO RUNTIME SCREENSHOT
    # ==================================================

    image_provider = DemoImageProvider(
        reference_directory=reference_directory,
        output_directory=actual_directory,
        inject_demo_defect=execution_config.get(
            "inject_demo_defect",
            True,
        ),
    )

    actual_path = image_provider.capture(
        screen_id=screen_id,
        reference_filename=screen_config["reference"],
        demo_defect=screen_config.get(
            "demo_defect",
            False,
        ),
    )

    # ==================================================
    # NORMALIZE
    # ==================================================

    crop_config = visual_config.get(
        "crop_actual",
        {},
    )

    normalizer = ImageNormalizer(
        resize_actual_to_reference=visual_config.get(
            "resize_actual_to_reference",
            True,
        ),
        crop_top_percent=crop_config.get(
            "top_percent",
            0.0,
        ),
        crop_bottom_percent=crop_config.get(
            "bottom_percent",
            0.0,
        ),
    )

    normalized = normalizer.normalize(
        expected_path=reference_path,
        actual_path=actual_path,
    )

    # ==================================================
    # COMPARE
    # ==================================================

    comparator = ImageComparator(
        ssim_threshold=visual_config[
            "ssim_threshold"
        ],
        max_diff_percent=visual_config[
            "max_diff_percent"
        ],
        pixel_diff_threshold=visual_config[
            "pixel_diff_threshold"
        ],
        min_component_area=visual_config[
            "min_component_area"
        ],
    )

    diff_path = (
        diff_directory
        / f"{screen_id}_diff.png"
    )

    overlay_path = (
        diff_directory
        / f"{screen_id}_overlay.png"
    )

    result = comparator.compare(
        expected=normalized.expected,
        actual=normalized.actual,
        diff_image_path=diff_path,
        overlay_image_path=overlay_path,
    )

    # ==================================================
    # DEMO DEFECT LOCATION CHECK
    # ==================================================

    demo_location_ok = True
    expected_bbox = None

    if (
        execution_config.get("mode") == "demo"
        and screen_config.get("demo_defect", False)
    ):
        actual_width = normalized.actual.shape[1]
        actual_height = normalized.actual.shape[0]

        expected_bbox = (
            DemoImageProvider.get_demo_defect_bbox(
                (
                    actual_width,
                    actual_height,
                )
            )
        )

        demo_location_ok = (
            _bbox_overlaps_detected_region(
                expected_bbox,
                result.bounding_boxes,
            )
        )

    # ==================================================
    # SAVE RESULT TO REPORT
    # ==================================================

    bug_report_path = visual_reporter.add_result(
        screen_id=screen_id,
        reference_path=reference_path,
        actual_path=actual_path,
        result=result,
    )

    # ==================================================
    # DEMO LOCATION ASSERTION
    # ==================================================

    assert demo_location_ok, (
        f"\n"
        f"[DEMO DEFECT CHECK FAILED]\n"
        f"Expected DEMO region: "
        f"{expected_bbox}\n"
        f"Detected regions: "
        f"{result.bounding_boxes}\n"
    )

    # ==================================================
    # VISUAL REGRESSION ASSERTION
    # ==================================================

    assert result.passed, (
        f"\n"
        f"[VISUAL REGRESSION]\n"
        f"Screen: {screen_id}\n"
        f"Status: FAIL\n"
        f"SSIM: {result.similarity:.5f}\n"
        f"Different pixels: "
        f"{result.diff_percent:.3f}%\n"
        f"Defect regions: "
        f"{result.bounding_boxes}\n"
        f"Diff: {diff_path}\n"
        f"Overlay: {overlay_path}\n"
        f"Bug report: {bug_report_path}\n"
    )


def _bbox_overlaps_detected_region(
    expected_bbox: tuple[int, int, int, int],
    detected_boxes: list[
        tuple[int, int, int, int]
    ],
    min_overlap_ratio: float = 0.5,
) -> bool:
    """
    Проверяет, что одна из найденных областей
    существенно пересекается с ожидаемым DEMO-элементом.

    Формат bbox:
        x, y, width, height
    """

    ex, ey, ew, eh = expected_bbox

    expected_left = ex
    expected_top = ey
    expected_right = ex + ew
    expected_bottom = ey + eh

    expected_area = ew * eh

    if expected_area <= 0:
        return False

    for dx, dy, dw, dh in detected_boxes:
        detected_left = dx
        detected_top = dy
        detected_right = dx + dw
        detected_bottom = dy + dh

        overlap_width = max(
            0,
            min(
                expected_right,
                detected_right,
            )
            - max(
                expected_left,
                detected_left,
            ),
        )

        overlap_height = max(
            0,
            min(
                expected_bottom,
                detected_bottom,
            )
            - max(
                expected_top,
                detected_top,
            ),
        )

        overlap_area = (
            overlap_width
            * overlap_height
        )

        overlap_ratio = (
            overlap_area
            / expected_area
        )

        if overlap_ratio >= min_overlap_ratio:
            return True

    return False

# pytest -m visual -v