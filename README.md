# iOS / Figma Visual Regression Demo

Автоматизированная проверка соответствия интерфейса мобильного приложения дизайну в Figma.

Проект демонстрирует подход **visual regression testing** для iOS-приложения: сравнение эталонного изображения из Figma с runtime-скриншотом приложения, локализацию отличий и формирование отчётов.

---

## Содержание

- [Цель](#цель)
- [Как работает visual regression](#как-работает-visual-regression)
- [Demo Mode](#demo-mode)
- [Почему в демонстрации нет реального iPhone / Simulator](#почему-в-демонстрации-нет-реального-iphone--simulator)
- [Что проверяет Demo Mode](#что-проверяет-demo-mode)
- [Быстрый запуск Demo Mode](#быстрый-запуск-demo-mode)
- [Ожидаемый результат Demo Mode](#ожидаемый-результат-demo-mode)
- [Артефакты после запуска](#артефакты-после-запуска)
- [Настройки visual comparison](#настройки-visual-comparison)
- [Как сделать Demo полностью зелёным](#как-сделать-demo-полностью-зелёным)
- [Перенос на реальный iOS](#перенос-на-реальный-ios)
- [Реальный iOS runtime](#реальный-ios-runtime)
- [Структура проекта](#структура-проекта)
- [Роль модулей](#роль-модулей)
- [Важное ограничение Demo Mode](#важное-ограничение-demo-mode)
- [Результат тестового задания](#результат-тестового-задания)

---

## Цель

Проект демонстрирует автоматизированную проверку соответствия интерфейса мобильного приложения дизайну в Figma.

## Как работает visual regression

Основная идея visual regression:

```text
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
           +--> bug report
           |
           +--> HTML / JSON report
```

Финальная production-схема предполагает получение `actual.png` непосредственно из запущенного iOS-приложения.

В текущем демонстрационном варианте источник `actual` эмулируется локально, чтобы проект можно было воспроизводимо запустить без конкретного Mac, Xcode, iPhone или Simulator.

---

## Demo Mode

По умолчанию проект работает в **Demo Mode**.

В Demo Mode:

- `reference_images/screen_1.png` и `reference_images/screen_2.png` считаются эталонными изображениями, экспортированными из Figma;
- `DemoImageProvider` создаёт предсказуемый аналог runtime screenshot;
- для `screen_1` runtime image совпадает с Figma;
- для `screen_2` автоматически добавляется дополнительный UI-элемент, имитирующий дефект из тестового задания;
- `ImageComparator` должен определить визуальное отличие и отметить второй экран как `FAIL`;
- дополнительно проверяется, что найденная область отличия действительно пересекается с ожидаемой областью демонстрационного `DEMO`-элемента.

Это именно симуляция источника `actual`, а не утверждение, что screenshot был получен из работающего iOS-приложения.

---

## Почему в демонстрации нет реального iPhone / Simulator

Основная цель тестового задания — показать работающий visual-regression кейс.

Привязка к конкретному Mac, Xcode, модели iPhone, версии iOS и simulator-compatible `.app` сделала бы демонстрацию зависимой от локального окружения.

Поэтому по умолчанию проект работает в Demo Mode.

---

## Что проверяет Demo Mode

Для каждого экрана выполняется следующий pipeline:

```text
Figma reference PNG
        |
        v
   FigmaClient
        |
        v
expected image
        |
        +------------------+
                           |
                           v
                    DemoImageProvider
                           |
                           v
                    simulated actual
                           |
                           v
                    ImageNormalizer
                           |
                           v
                    ImageComparator
                      /           \
                     /             \
                  SSIM          Pixel Diff
                     \             /
                      \           /
                       v         v
                       PASS / FAIL
                           |
                           +--> bounding boxes
                           |
                           +--> diff image
                           |
                           +--> overlay image
                           |
                           +--> bug report
```

---

## Быстрый запуск Demo Mode

### Требования

- Python 3.10+
- Git
- PyCharm или любая другая Python IDE

### 1. Создание virtual environment

```bash
python -m venv .venv
```

### 2. Активация environment

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows CMD**

```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Запуск visual tests

```bash
pytest -m visual -v
```

---

## Ожидаемый результат Demo Mode

При следующей конфигурации:

```yaml
execution:
  mode: "demo"
  inject_demo_defect: true
```

и:

```yaml
screens:
  screen_1:
    reference: "screen_1.png"
    demo_defect: false

  screen_2:
    reference: "screen_2.png"
    demo_defect: true
```

ожидается:

```text
screen_1 -> PASS
screen_2 -> FAIL
```

`screen_2 -> FAIL` является намеренным результатом. Второй экран специально получает дополнительный элемент, чтобы продемонстрировать способность visual-regression механизма обнаруживать дефект.

Ожидаемый пример результата:

```text
Screen: screen_2
Status: FAIL
SSIM: 0.98967
Different pixels: 1.700%
Defect regions: [(885, 2087, 238, 216)]
```

Значения SSIM, процента отличий и bounding box могут измениться после замены эталонных изображений или изменения настроек сравнения.

---

## Артефакты после запуска

После выполнения тестов создаются:

```text
actual_images/
├── screen_1.png
└── screen_2.png


diff_images/
├── screen_1_diff.png
├── screen_1_overlay.png
├── screen_2_diff.png
└── screen_2_overlay.png


reports/
├── visual_report.html
├── visual_report.json
└── bugs/
    └── BUG-screen_2.md
```

### `actual_images/`

Simulated runtime screenshots, созданные `DemoImageProvider`.

### `diff_images/`

Изображения, показывающие обнаруженные различия.

- `*_diff.png` — карта отличий;
- `*_overlay.png` — фактический screenshot с выделенными bounding boxes.

### `reports/visual_report.html`

Основной визуальный отчёт.

В нём отображаются:

- Expected — эталон из Figma;
- Actual — simulated runtime screenshot;
- Diff — карта отличий;
- Overlay — фактический screenshot с выделенными областями отличий;
- SSIM;
- процент отличающихся пикселей;
- bounding boxes;
- ссылка на bug report для `FAIL`.

### `reports/visual_report.json`

Машиночитаемый результат visual comparison.

### `reports/bugs/BUG-screen_2.md`

Автоматически сформированный bug report для обнаруженного визуального дефекта.

Пример bug report:

При обнаружении отличия автоматически создаётся файл:

```text
reports/bugs/BUG-screen_2.md
```

Он содержит:

- Summary;
- Status;
- Severity;
- Steps to Reproduce;
- Expected Result;
- Actual Result;
- SSIM;
- процент отличающихся пикселей;
- размеры Expected / Actual;
- координаты найденных областей;
- ссылки на Expected / Actual / Diff / Overlay.

Таким образом результат теста можно использовать как основу для QA bug report, а не только как `AssertionError` в консоли.

---

## Настройки visual comparison

Основные параметры находятся в `config.yaml`:

```yaml
visual:
  ssim_threshold: 0.98
  max_diff_percent: 0.5
  pixel_diff_threshold: 25
  min_component_area: 30
  resize_actual_to_reference: true

  crop_actual:
    top_percent: 0.0
    bottom_percent: 0.0
```

| Параметр | Описание |
|---|---|
| `ssim_threshold` | Минимально допустимый SSIM между Expected и Actual. Чем ближе значение к `1.0`, тем более похожими должны быть изображения. |
| `max_diff_percent` | Максимальный допустимый процент отличающихся пикселей. |
| `pixel_diff_threshold` | Минимальная разница яркости пикселя, которую считаем значимым изменением при построении diff. |
| `min_component_area` | Минимальная площадь области отличия, учитываемая при поиске bounding boxes. Позволяет отбрасывать мелкий шум. |
| `resize_actual_to_reference` | Приводит Actual к размеру Figma reference перед сравнением. |

---

## Как сделать Demo полностью зелёным

Чтобы Demo Mode проверял совпадение без специально внесённого дефекта, в `config.yaml` нужно отключить инъекцию и сам сценарий демонстрационного дефекта:

```yaml
execution:
  mode: "demo"
  inject_demo_defect: false

screens:
  screen_1:
    reference: "screen_1.png"
    demo_defect: false

  screen_2:
    reference: "screen_2.png"
    demo_defect: false
```

После этого:

```bash
pytest -m visual -v
```

должен завершиться успешно:

```text
2 passed
```

---

## Перенос на реальный iOS

Demo Mode изолирован от visual comparison.

В production вместо `DemoImageProvider` подключается `AppiumImageProvider`.

Источник actual тогда меняется следующим образом:

**Demo Mode**

```text
Figma PNG
   |
   v
DemoImageProvider
   |
   v
actual PNG
```

**Production**

```text
iOS application
   |
   v
Appium + XCUITest
   |
   v
AppiumImageProvider
   |
   v
actual PNG
```

При этом основной visual comparison engine остаётся тем же:

```text
FigmaClient
      |
      v
expected.png
      |
      +-----------------------+
                              |
                              v
                       ImageNormalizer
                              |
                              v
                       ImageComparator
                              |
                +-------------+-------------+
                |             |             |
              PASS/FAIL     Diff        Bounding box
                              |
                              v
                       VisualReporter
```

Таким образом меняется только источник `actual`, а не сам механизм visual comparison.

---

## Реальный iOS runtime

Для production-интеграции потребуется:

- Mac;
- Xcode;
- iOS Simulator или physical iPhone;
- Appium;
- XCUITest driver;
- Simulator-compatible build приложения либо доступное установленное приложение/устройство.

Эти требования не нужны для Demo Mode.

Опциональные Appium-зависимости вынесены отдельно:

```text
requirements-appium.txt
```

Они устанавливаются только при переходе к реальному iOS runtime.

---

## Структура проекта

```text
ios_figma_visual_test/
│
├── tests/
│   ├── conftest.py
│   └── test_figma_match.py
│
├── app/
│   ├── demo_image_provider.py
│   └── appium_driver.py
│
├── figma/
│   └── figma_client.py
│
├── visual/
│   ├── comparator.py
│   ├── image_normalizer.py
│   └── reporter.py
│
├── reference_images/
│   ├── screen_1.png
│   └── screen_2.png
│
├── actual_images/
├── diff_images/
├── reports/
│   └── bugs/
│
├── config.yaml
├── pytest.ini
├── requirements.txt
├── requirements-appium.txt
└── README.md
```

---

## Роль модулей

### `tests/test_figma_match.py`

Основной тестовый сценарий. Для каждого экрана:

- получает reference из Figma;
- создаёт simulated runtime screenshot;
- нормализует изображения;
- запускает visual comparison;
- проверяет локализацию демонстрационного дефекта;
- сохраняет результат;
- завершает тест PASS или FAIL.

### `app/demo_image_provider.py`

Создаёт simulated actual screenshot для Demo Mode.

Для `screen_2` может добавить искусственный `DEMO`-элемент.

### `app/appium_driver.py`

Будущий слой управления настоящим iOS-приложением через Appium/XCUITest.

В Demo Mode не используется.

### `figma/figma_client.py`

Источник reference images, экспортированных из Figma.

На текущем этапе используются локальные PNG. В будущем этот слой можно расширить до Figma REST API.

### `visual/image_normalizer.py`

Приводит Expected и Actual к сопоставимой геометрии.

### `visual/comparator.py`

Сравнивает изображения с использованием SSIM и pixel difference, а также локализует области отличий.

### `visual/reporter.py`

Формирует HTML/JSON visual report и отдельный Markdown bug report для FAIL.

---

## Важное ограничение Demo Mode

Demo Mode проверяет:

- алгоритм visual comparison;
- image normalization;
- обнаружение визуального отличия;
- локализацию дефекта;
- формирование доказательств;
- генерацию bug report.

Demo Mode **не проверяет** реальный iOS UI.

Поэтому в итоговом резюме тестового задания следует явно указать:

> Для воспроизводимой демонстрации реализован Demo Mode с эмулированным источником runtime screenshot. Архитектура предусматривает замену этого источника на Appium/XCUITest без изменения visual comparison engine.

Такое разделение позволяет показать работающий автоматизированный кейс уже сейчас и отдельно описать production-интеграцию с iOS.

---

## Результат тестового задания

В демонстрационном сценарии система должна автоматически определить, что второй экран отличается от Figma из-за добавленного UI-элемента.

Итоговая цепочка:

```text
Figma
  |
  v
Expected
  |
  v
Simulated Runtime
  |
  v
Image Normalization
  |
  v
SSIM + Pixel Diff
  |
  v
Defect Localization
  |
  +----> PASS / FAIL
  |
  +----> Diff / Overlay
  |
  +----> Bug Report
  |
  +----> HTML / JSON Report
```