from __future__ import annotations

from pathlib import Path


class FigmaClient:
    """
    Источник reference images.

    Сейчас:
        локальные PNG, экспортированные из Figma.

    Позже:
        здесь можно добавить Figma REST API.
    """

    def __init__(
        self,
        reference_directory: Path,
    ) -> None:

        self.reference_directory = (
            reference_directory
        )

    def get_reference_image(
        self,
        screen_id: str,
        file_name: str,
    ) -> Path:

        path = (
            self.reference_directory
            / file_name
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Reference image for "
                f"{screen_id} was not found: "
                f"{path}"
            )

        return path

    def validate_reference_images(
        self,
        screens: dict,
    ) -> None:

        for screen_id, screen_config in screens.items():

            self.get_reference_image(
                screen_id=screen_id,
                file_name=screen_config[
                    "reference"
                ],
            )