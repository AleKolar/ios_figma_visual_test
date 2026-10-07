from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from visual.reporter import VisualReporter


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)


@pytest.fixture(scope="session")
def project_config() -> dict:
    config_path = (
        PROJECT_ROOT
        / "config.yaml"
    )

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return yaml.safe_load(file)


@pytest.fixture(scope="session")
def visual_reporter(
    project_config: dict,
) -> VisualReporter:

    reports_directory = (
        PROJECT_ROOT
        / project_config["paths"]["reports"]
    )

    return VisualReporter(
        reports_directory
    )