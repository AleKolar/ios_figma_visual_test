from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


class DemoImageProvider:
    """
    Создаёт simulated runtime screenshots
    для демонстрационного visual regression теста.

    Screen 1:
        actual = копия reference

    Screen 2:
        actual = reference + искусственный
        лишний UI-элемент
    """

    def __init__(
        self,
        reference_directory: Path,
        output_directory: Path,
        inject_demo_defect: bool = True,
    ) -> None:

        self.reference_directory = reference_directory
        self.output_directory = output_directory
        self.inject_demo_defect = inject_demo_defect

    def capture(
        self,
        screen_id: str,
        reference_filename: str,
        demo_defect: bool = False,
    ) -> Path:

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        reference_path = (
            self.reference_directory
            / reference_filename
        )

        if not reference_path.exists():
            raise FileNotFoundError(
                f"Reference image not found: "
                f"{reference_path}"
            )

        image = Image.open(
            reference_path
        ).convert("RGB")

        if (
            self.inject_demo_defect
            and demo_defect
        ):
            self._add_demo_defect(image)

        output_path = (
            self.output_directory
            / f"{screen_id}.png"
        )

        image.save(output_path)

        return output_path

    @staticmethod
    def get_demo_defect_bbox(
        image_size: tuple[int, int],
    ) -> tuple[int, int, int, int]:
        """
        Возвращает ожидаемый bounding box
        демонстрационного DEMO-элемента.

        Формат:
            x, y, width, height
        """

        width, height = image_size

        element_width = max(
            80,
            width // 5,
        )

        element_height = max(
            40,
            height // 12,
        )

        x = (
            width
            - element_width
            - max(20, width // 20)
        )

        y = (
            height
            - element_height
            - max(50, height // 10)
        )

        return (
            x,
            y,
            element_width,
            element_height,
        )

    @classmethod
    def _add_demo_defect(
        cls,
        image: Image.Image,
    ) -> None:

        draw = ImageDraw.Draw(image)

        x, y, element_width, element_height = (
            cls.get_demo_defect_bbox(
                image.size
            )
        )

        draw.rounded_rectangle(
            (
                x,
                y,
                x + element_width,
                y + element_height,
            ),
            radius=10,
            fill=(255, 0, 0),
        )

        draw.text(
            (
                x + 10,
                y + element_height // 3,
            ),
            "DEMO",
            fill=(255, 255, 255),
        )