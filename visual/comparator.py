from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from skimage.metrics import structural_similarity


@dataclass
class VisualComparisonResult:
    passed: bool

    similarity: float
    diff_percent: float

    expected_size: tuple[int, int]
    actual_size: tuple[int, int]

    diff_image_path: Path
    overlay_image_path: Path

    bounding_boxes: list[
        tuple[int, int, int, int]
    ]


class ImageComparator:

    def __init__(
        self,
        ssim_threshold: float = 0.98,
        max_diff_percent: float = 0.5,
        pixel_diff_threshold: int = 25,
        min_component_area: int = 30,
    ) -> None:

        self.ssim_threshold = ssim_threshold
        self.max_diff_percent = max_diff_percent
        self.pixel_diff_threshold = (
            pixel_diff_threshold
        )
        self.min_component_area = (
            min_component_area
        )

    def compare(
        self,
        expected: np.ndarray,
        actual: np.ndarray,
        diff_image_path: Path,
        overlay_image_path: Path,
    ) -> VisualComparisonResult:

        if expected.shape != actual.shape:
            raise ValueError(
                "Image dimensions don't match: "
                f"{expected.shape} vs "
                f"{actual.shape}"
            )

        expected_gray = cv2.cvtColor(
            expected,
            cv2.COLOR_RGB2GRAY,
        )

        actual_gray = cv2.cvtColor(
            actual,
            cv2.COLOR_RGB2GRAY,
        )

        # Небольшое сглаживание уменьшает
        # влияние anti-aliasing.
        expected_blurred = cv2.GaussianBlur(
            expected_gray,
            (5, 5),
            0,
        )

        actual_blurred = cv2.GaussianBlur(
            actual_gray,
            (5, 5),
            0,
        )

        # ----------------------------------
        # SSIM
        # ----------------------------------

        similarity = structural_similarity(
            expected_blurred,
            actual_blurred,
            data_range=255,
        )

        # ----------------------------------
        # Pixel difference
        # ----------------------------------

        difference = cv2.absdiff(
            expected_blurred,
            actual_blurred,
        )

        _, binary_diff = cv2.threshold(
            difference,
            self.pixel_diff_threshold,
            255,
            cv2.THRESH_BINARY,
        )

        # ----------------------------------
        # Noise reduction
        # ----------------------------------

        kernel = np.ones(
            (3, 3),
            dtype=np.uint8,
        )

        binary_diff = cv2.morphologyEx(
            binary_diff,
            cv2.MORPH_OPEN,
            kernel,
        )

        binary_diff = cv2.morphologyEx(
            binary_diff,
            cv2.MORPH_CLOSE,
            kernel,
        )

        # ----------------------------------
        # Difference percentage
        # ----------------------------------

        diff_pixels = cv2.countNonZero(
            binary_diff
        )

        total_pixels = (
            binary_diff.shape[0]
            * binary_diff.shape[1]
        )

        diff_percent = (
            diff_pixels / total_pixels
        ) * 100.0

        # ----------------------------------
        # Bounding boxes
        # ----------------------------------

        bounding_boxes = (
            self._find_bounding_boxes(
                binary_diff
            )
        )

        # ----------------------------------
        # Final verdict
        # ----------------------------------

        passed = (
            similarity >= self.ssim_threshold
            and diff_percent
            <= self.max_diff_percent
        )

        # ----------------------------------
        # Artifacts
        # ----------------------------------

        diff_image_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        overlay_image_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._save_diff(
            binary_diff,
            diff_image_path,
        )

        self._save_overlay(
            actual,
            bounding_boxes,
            overlay_image_path,
        )

        return VisualComparisonResult(
            passed=passed,
            similarity=float(similarity),
            diff_percent=float(diff_percent),
            expected_size=(
                expected.shape[1],
                expected.shape[0],
            ),
            actual_size=(
                actual.shape[1],
                actual.shape[0],
            ),
            diff_image_path=diff_image_path,
            overlay_image_path=overlay_image_path,
            bounding_boxes=bounding_boxes,
        )

    def _find_bounding_boxes(
        self,
        binary_diff: np.ndarray,
    ) -> list[
        tuple[int, int, int, int]
    ]:

        contours, _ = cv2.findContours(
            binary_diff,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        boxes: list[
            tuple[int, int, int, int]
        ] = []

        for contour in contours:

            area = cv2.contourArea(
                contour
            )

            if area < self.min_component_area:
                continue

            x, y, width, height = (
                cv2.boundingRect(contour)
            )

            boxes.append(
                (
                    x,
                    y,
                    width,
                    height,
                )
            )

        boxes.sort(
            key=lambda box: (
                box[2] * box[3]
            ),
            reverse=True,
        )

        return boxes

    @staticmethod
    def _save_diff(
        binary_diff: np.ndarray,
        path: Path,
    ) -> None:

        cv2.imwrite(
            str(path),
            binary_diff,
        )

    @staticmethod
    def _save_overlay(
        actual: np.ndarray,
        bounding_boxes: list[
            tuple[int, int, int, int]
        ],
        path: Path,
    ) -> None:

        overlay = cv2.cvtColor(
            actual,
            cv2.COLOR_RGB2BGR,
        )

        for x, y, width, height in (
            bounding_boxes
        ):

            cv2.rectangle(
                overlay,
                (x, y),
                (
                    x + width,
                    y + height,
                ),
                (0, 0, 255),
                3,
            )

        cv2.imwrite(
            str(path),
            overlay,
        )