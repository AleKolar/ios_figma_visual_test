iOS / Figma Visual Regression Demo

Цель

Проект демонстрирует автоматизированную проверку соответствия интерфейса мобильного приложения дизайну в Figma.

Финальная production-схема должна выглядеть так:

Figma frame
   |
   v
expected.png
   |
   |        iOS application
   |             |
   |          Appium
   |             |
   |             v
   +------ actual.png
          |
          v
   image normalization
          |
          v
     visual comparison
          |
          +--> PASS / FAIL
          |
          +--> diff image
          |
          +--> HTML report

Почему в демонстрации нет реального iPhone / Simulator

Основная цель тестового задания — показать работающий visual-regression кейс. Привязка к конкретному Mac, Xcode, модели iPhone, версии iOS и simulator-compatible .app сделала бы демонстрацию зависимой от локального окружения.

Поэтому по умолчанию проект работает в Demo Mode.

В Demo Mode:

reference_images/screen_1.png и screen_2.png считаются эталонами из Figma;

SimulatedRuntimeImageProvider создаёт предсказуемый аналог runtime screenshot;

для screen_1 runtime image совпадает с Figma;

для screen_2 автоматически добавляется дополнительный UI-элемент, имитирующий дефект из тестового задания;

visual comparator должен определить отличие и отметить второй экран как FAIL.

Это именно симуляция источника actual, а не утверждение, что screenshot был получен из работающего iOS-приложения.

Быстрый запуск Demo Mode

Требования: Python 3.10+.

python -m venv .venv

Windows:

.venv\\Scripts\\activate

macOS/Linux:

source .venv/bin/activate

Установить зависимости:

pip install -r requirements.txt

Запустить:

pytest -m visual -v

Ожидаемый результат

При execution.inject_demo_defect: true ожидается:

screen_1 -> PASS
screen_2 -> FAIL

Это намеренный FAIL, необходимый для демонстрации того, что система действительно умеет обнаруживать визуальный дефект.

После выполнения будут созданы:

actual_images/
    screen_1.png
    screen_2.png

diff_images/
    screen_1_diff.png
    screen_1_overlay.png
    screen_2_diff.png
    screen_2_overlay.png

reports/
    visual_report.html
    visual_report.json

Откройте reports/visual_report.html в браузере. В нём будут:

Expected — эталон из Figma;

Actual — эмулированный runtime screenshot;

Diff — карта отличий;

Overlay — фактический screenshot с выделенными областями отличий;

SSIM;

процент отличающихся пикселей;

bounding boxes найденных областей.

Как сделать Demo полностью зелёным

В config.yaml:

execution:
  mode: "demo"
  inject_demo_defect: false

После этого simulated runtime images будут соответствовать Figma, и тест должен завершиться успешно.

Как это переносится на реальный iOS

Demo Mode специально изолирован от visual comparison. В production вместо SimulatedRuntimeImageProvider подключается AppiumImageProvider.

Тогда источник actual меняется:

Demo Mode:
Figma PNG -> SimulatedRuntimeImageProvider -> actual PNG

Production:
Figma PNG -> Appium + XCUITest -> actual PNG

При этом модули FigmaClient, ImageNormalizer, ImageComparator, VisualReporter и основная идея теста не меняются.

Для реального iOS запуска потребуются Mac + Xcode + iOS Simulator или physical iPhone, а также Simulator-compatible build приложения. Эти требования не входят в Demo Mode.

Опциональная Appium-зависимость вынесена в:

requirements-appium.txt

Она устанавливается только при переходе к реальному iOS runtime.

Структура проекта

ios_figma_visual_test/
|
+-- tests/
|   +-- conftest.py
|   +-- test_figma_match.py
|
+-- app/
|   +-- actual_image_provider.py
|   +-- appium_driver.py
|
+-- figma/
|   +-- figma_client.py
|
+-- visual/
|   +-- comparator.py
|   +-- image_normalizer.py
|   +-- reporter.py
|
+-- reference_images/
|   +-- screen_1.png
|   +-- screen_2.png
|
+-- actual_images/
+-- diff_images/
+-- reports/
|
+-- config.yaml
+-- pytest.ini
+-- requirements.txt
+-- requirements-appium.txt
+-- README.md

Важное ограничение Demo Mode

Demo Mode проверяет алгоритм visual comparison и формирование доказательств дефекта, но не проверяет реальный iOS UI.

Поэтому в итоговом резюме тестового задания следует явно написать:

Для воспроизводимой демонстрации реализован Demo Mode с эмулированным источником runtime screenshot. Архитектура предусматривает замену этого источника на Appium/XCUITest без изменения visual comparison engine.

Такое разделение позволяет показать рабочий автоматизированный кейс уже сейчас и отдельно описать production-интеграцию с iOS.