from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class NormalizedImages:
    expected: np.ndarray
    actual: np.ndarray


class ImageNormalizer:

    def __init__(
        self,
        resize_actual_to_reference: bool = True,
        crop_top_percent: float = 0.0,
        crop_bottom_percent: float = 0.0,
    ) -> None:

        if not 0.0 <= crop_top_percent < 1.0:
            raise ValueError(
                "crop_top_percent must be "
                "between 0 and 1."
            )

        if not 0.0 <= crop_bottom_percent < 1.0:
            raise ValueError(
                "crop_bottom_percent must be "
                "between 0 and 1."
            )

        if (
            crop_top_percent
            + crop_bottom_percent
            >= 1.0
        ):
            raise ValueError(
                "Total crop percentage "
                "must be less than 1."
            )

        self.resize_actual_to_reference = (
            resize_actual_to_reference
        )

        self.crop_top_percent = (
            crop_top_percent
        )

        self.crop_bottom_percent = (
            crop_bottom_percent
        )

    def normalize(
        self,
        expected_path: Path,
        actual_path: Path,
    ) -> NormalizedImages:

        expected = self._load(
            expected_path
        )

        actual = self._load(
            actual_path
        )

        actual = self._crop_actual(
            actual
        )

        if self.resize_actual_to_reference:

            actual = self._resize_to_reference(
                actual,
                expected,
            )

        if expected.shape != actual.shape:

            raise ValueError(
                "Images have different shapes "
                "after normalization: "
                f"expected={expected.shape}, "
                f"actual={actual.shape}"
            )

        return NormalizedImages(
            expected=expected,
            actual=actual,
        )

    @staticmethod
    def _load(
        path: Path,
    ) -> np.ndarray:

        if not path.exists():
            raise FileNotFoundError(
                path
            )

        image = Image.open(path).convert(
            "RGB"
        )

        return np.asarray(
            image,
            dtype=np.uint8,
        )

    def _crop_actual(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        height = image.shape[0]

        top = int(
            height * self.crop_top_percent
        )

        bottom = int(
            height * self.crop_bottom_percent
        )

        end = (
            height - bottom
            if bottom > 0
            else height
        )

        return image[top:end, :]

    @staticmethod
    def _resize_to_reference(
        actual: np.ndarray,
        expected: np.ndarray,
    ) -> np.ndarray:

        expected_height, expected_width = (
            expected.shape[:2]
        )

        image = Image.fromarray(actual)

        resized = image.resize(
            (
                expected_width,
                expected_height,
            ),
            Image.Resampling.LANCZOS,
        )

        return np.asarray(
            resized,
            dtype=np.uint8,
        )