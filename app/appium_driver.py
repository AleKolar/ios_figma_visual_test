from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException


class AppiumDriver:
    """
    Обертка над Appium WebDriver для iOS.

    Отвечает только за:
    - запуск Appium-сессии;
    - работу с приложением;
    - UI actions;
    - screenshots.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.driver = None

    def start(self) -> None:
        options = XCUITestOptions()

        capabilities: dict[str, Any] = {
            "platformName": self.config["platform_name"],
            "appium:automationName": self.config["automation_name"],
            "appium:deviceName": self.config["device_name"],
            "appium:platformVersion": self.config["platform_version"],
            "appium:bundleId": self.config["bundle_id"],
            "appium:noReset": self.config.get(
                "no_reset",
                True,
            ),
            "appium:newCommandTimeout": self.config.get(
                "new_command_timeout",
                120,
            ),
        }

        # Для Simulator может использоваться .app.
        app_path = self.config.get("app")

        if app_path:
            capabilities["appium:app"] = app_path

        # Для реального iPhone можно передать UDID.
        udid = self.config.get("udid")

        if udid:
            capabilities["appium:udid"] = udid

        options.load_capabilities(capabilities)

        self.driver = webdriver.Remote(
            self.config["server_url"],
            options=options,
        )

    def activate_app(self) -> None:
        self._check_driver()

        self.driver.activate_app(
            self.config["bundle_id"]
        )

    def terminate_app(self) -> None:
        self._check_driver()

        self.driver.terminate_app(
            self.config["bundle_id"]
        )

    def save_screenshot(
        self,
        path: Path,
    ) -> None:

        self._check_driver()

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        success = self.driver.get_screenshot_as_file(
            str(path)
        )

        if not success:
            raise RuntimeError(
                f"Failed to save screenshot: {path}"
            )

    def tap_by_coordinates(
        self,
        x: float,
        y: float,
    ) -> None:

        self._check_driver()

        self.driver.execute_script(
            "mobile: tap",
            {
                "x": x,
                "y": y,
            },
        )

    def tap_by_accessibility_id(
        self,
        value: str,
    ) -> None:

        self._check_driver()

        element = self.driver.find_element(
            AppiumBy.ACCESSIBILITY_ID,
            value,
        )

        element.click()

    def tap_by_predicate(
        self,
        predicate: str,
    ) -> None:

        self._check_driver()

        element = self.driver.find_element(
            AppiumBy.IOS_PREDICATE,
            predicate,
        )

        element.click()

    def wait_seconds(
        self,
        seconds: float,
    ) -> None:

        time.sleep(seconds)

    def wait_for_accessibility_id(
        self,
        value: str,
        timeout: int = 10,
    ) -> None:

        self._check_driver()

        try:
            WebDriverWait(
                self.driver,
                timeout,
            ).until(
                lambda driver: driver.find_element(
                    AppiumBy.ACCESSIBILITY_ID,
                    value,
                )
            )

        except TimeoutException as exc:
            raise TimeoutException(
                f"Element with accessibility_id "
                f"'{value}' was not found "
                f"within {timeout} seconds."
            ) from exc

    def run_actions(
        self,
        actions: list[dict[str, Any]],
    ) -> None:

        for action in actions:

            action_type = action["type"]

            if action_type == "tap":

                self.tap_by_coordinates(
                    x=action["x"],
                    y=action["y"],
                )

            elif action_type == "accessibility_id":

                self.tap_by_accessibility_id(
                    action["value"]
                )

            elif action_type == "predicate":

                self.tap_by_predicate(
                    action["value"]
                )

            elif action_type == "wait":

                self.wait_seconds(
                    action["seconds"]
                )

            elif action_type == "wait_for_accessibility_id":

                self.wait_for_accessibility_id(
                    value=action["value"],
                    timeout=action.get(
                        "timeout",
                        10,
                    ),
                )

            else:
                raise ValueError(
                    f"Unknown action type: "
                    f"{action_type}"
                )

    def quit(self) -> None:

        if self.driver is not None:
            self.driver.quit()
            self.driver = None

    def _check_driver(self) -> None:

        if self.driver is None:
            raise RuntimeError(
                "Appium driver is not started."
            )