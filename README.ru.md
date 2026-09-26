<div align="center">

[![English](https://img.shields.io/badge/English-0a0a0a?style=for-the-badge)](README.md)
[![Русский](https://img.shields.io/badge/%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-e4e4e4?style=for-the-badge)](README.ru.md)

<picture><source media="(prefers-color-scheme: dark)" srcset="screenshots/header-dark.svg"><img src="screenshots/header-light.svg" alt="LUCI PIXEL: монохромная пиксельная тема для OpenWrt"></picture>

**Монохромная тема веб-интерфейса OpenWrt (LuCI), нарисованная по пиксельной сетке.**<br>
Пиксельный шрифт, рамки со срезанными углами, строки развёртки ЭЛТ и ступенчатые анимации на каждой странице.

[![Релиз](https://img.shields.io/github/v/release/Trendorin/luci-theme-pixel?style=flat-square&label=%D1%80%D0%B5%D0%BB%D0%B8%D0%B7&labelColor=0a0a0a&color=e4e4e4)](https://github.com/Trendorin/luci-theme-pixel/releases/latest)
[![Загрузки](https://img.shields.io/github/downloads/Trendorin/luci-theme-pixel/total?style=flat-square&label=%D0%B7%D0%B0%D0%B3%D1%80%D1%83%D0%B7%D0%BA%D0%B8&labelColor=0a0a0a&color=e4e4e4)](https://github.com/Trendorin/luci-theme-pixel/releases)
[![Лицензия](https://img.shields.io/github/license/Trendorin/luci-theme-pixel?style=flat-square&label=%D0%BB%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D1%8F&labelColor=0a0a0a&color=e4e4e4)](LICENSE)
<br>
[![OpenWrt](https://img.shields.io/badge/OpenWrt-23.05_%C2%B7_24.10_%C2%B7_25.12-e4e4e4?style=flat-square&logo=openwrt&logoColor=e4e4e4&labelColor=0a0a0a)](#совместимость)
[![Пакет](https://img.shields.io/badge/%D0%BF%D0%B0%D0%BA%D0%B5%D1%82-apk_%C2%B7_ipk_%C2%B7_noarch-e4e4e4?style=flat-square&labelColor=0a0a0a)](#установка)
[![Размер](https://img.shields.io/badge/%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%80-36_%D0%9A%D0%91-e4e4e4?style=flat-square&labelColor=0a0a0a)](https://github.com/Trendorin/luci-theme-pixel/releases/latest)
[![Внешние запросы](https://img.shields.io/badge/%D0%B2%D0%BD%D0%B5%D1%88%D0%BD%D0%B8%D0%B5_%D0%B7%D0%B0%D0%BF%D1%80%D0%BE%D1%81%D1%8B-%D0%BD%D0%B5%D1%82-e4e4e4?style=flat-square&labelColor=0a0a0a)](#возможности)

<img src="screenshots/login.gif" width="600" alt="Экран входа: имя роутера проявляется из пиксельного шума, по нему пробегает блик, подзаголовок печатается сам">

[![Скачать](https://img.shields.io/badge/%D1%81%D0%BA%D0%B0%D1%87%D0%B0%D1%82%D1%8C-%D0%BF%D0%BE%D1%81%D0%BB%D0%B5%D0%B4%D0%BD%D0%B8%D0%B9_%D1%80%D0%B5%D0%BB%D0%B8%D0%B7-e4e4e4?style=for-the-badge&labelColor=0a0a0a)](https://github.com/Trendorin/luci-theme-pixel/releases/latest)
[![Установка](https://img.shields.io/badge/%D1%83%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BA%D0%B0-3_%D0%BA%D0%BE%D0%BC%D0%B0%D0%BD%D0%B4%D1%8B-0a0a0a?style=for-the-badge&labelColor=0a0a0a)](#установка)
[![Скриншоты](https://img.shields.io/badge/%D1%81%D0%BA%D1%80%D0%B8%D0%BD%D1%88%D0%BE%D1%82%D1%8B-11-0a0a0a?style=for-the-badge&labelColor=0a0a0a)](#скриншоты)

</div>

## Установка

Пакет не зависит от архитектуры роутера. Команды выполняются на роутере (по SSH):

**OpenWrt 25.12 и новее** (apk)

```sh
cd /tmp
wget https://github.com/Trendorin/luci-theme-pixel/releases/latest/download/luci-theme-pixel.apk
apk add --allow-untrusted luci-theme-pixel.apk
```

**OpenWrt 23.05 и 24.10** (opkg)

```sh
cd /tmp
wget https://github.com/Trendorin/luci-theme-pixel/releases/latest/download/luci-theme-pixel_all.ipk
opkg install luci-theme-pixel_all.ipk
```

Обновите страницу веб-интерфейса. Первая установка делает Pixel активной темой; при обновлении остаётся та тема,
которую вы выбрали. Файлы с номером версии и контрольные суммы (`SHA256SUMS`) — на [странице релизов](https://github.com/Trendorin/luci-theme-pixel/releases).

<details>
<summary><b>Переключить, обновить или удалить</b></summary>

- **Переключить тему:** System → System → Language and Style → Design. Из консоли:
  `uci set luci.main.mediaurlbase=/luci-static/bootstrap && uci commit luci`.
- **Обновить:** выполнить те же команды ещё раз. Выбранная тема не меняется.
- **Удалить:** `apk del luci-theme-pixel` или `opkg remove luci-theme-pixel`. Если Pixel была активной, LuCI вернётся к Bootstrap.
- **Видны куски старой темы?** Обновите страницу один раз с <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>.
- **Иконка на телефоне:** откройте LuCI в Chrome или Samsung Internet → меню → **Добавить на главный экран**.

</details>

## Скриншоты

Все страницы — стандартные страницы LuCI, отличается только тема. Адреса, имена и журналы на картинках вымышленные.

### Тёмная и светлая

Кнопка в верхней панели переключает **авто → тёмная → светлая**. «Экраны» (картинка входа, журналы, графики)
остаются тёмными в обеих темах.

| Обзор состояния, тёмная | Та же страница, светлая |
|---|---|
| <img src="screenshots/overview-dark.png" alt="Обзор состояния в тёмной теме"> | <img src="screenshots/overview-light.png" alt="Обзор состояния в светлой теме"> |

### Повседневные страницы

| Network → Interfaces | Network → Wireless |
|---|---|
| <img src="screenshots/interfaces-dark.png" alt="Интерфейсы с пиксельными значками"> | <img src="screenshots/wireless-light.png" alt="Обзор Wi-Fi"> |

### Окна и журналы

| Окно настройки: однобитное окно с полосатым заголовком | System Log — прокручиваемый «экран» |
|---|---|
| <img src="screenshots/dialog-dark.png" alt="Окно настройки интерфейса"> | <img src="screenshots/syslog-dark.png" alt="Системный журнал"> |

### Графики и настройки

| Графики в реальном времени на тёмном экране | Language and Style: выбор темы |
|---|---|
| <img src="screenshots/graphs-dark.png" alt="График трафика в реальном времени"> | <img src="screenshots/style-light.png" alt="Выбор темы Pixel в настройках"> |

### На телефоне

| Вход | Состояние | Меню |
|---|---|---|
| <img src="screenshots/phone-login.png" alt="Вход на телефоне"> | <img src="screenshots/phone-status.png" alt="Состояние на телефоне"> | <img src="screenshots/phone-menu.png" alt="Выезжающее меню на телефоне"> |

## Возможности

- **Пиксельный шрифт 5×7** с латиницей, кириллицей и знаками интерфейса (%, °, стрелки, «», ✓…), собранный из
  битмап-глифов. Размеры кратны 10 px, поэтому каждый пиксель шрифта ложится на целые пиксели экрана и текст остаётся
  чётким; каждый глиф — один контур, без тонких швов на телефонах с дробным масштабом.
- **«Экранная» палитра:** почти чёрный и светло-серые тона, рамки со срезанными углами, пунктирные линейки и строки
  развёртки ЭЛТ. Красный — только для ошибок и опасных кнопок.
- **Анимации, все ступенчатые:** имя роутера проявляется из шума буква за буквой и по нему пробегает блик,
  подзаголовки печатаются за мигающим курсором, страницы появляются с мерцанием старого монитора, индикатор загрузки —
  бегущий пиксельный блок. `prefers-reduced-motion` отключает всё.
- **Перерисованы все стандартные элементы LuCI:** формы, вкладки, таблицы, выпадающие списки, динамические списки,
  пиксельные чекбоксы и переключатели, сегментные прогресс-бары, модальные окна, блоки состояния, значки зон,
  журналы и графики.
- **Боковая и верхняя панели:** живые память и нагрузка в боковой панели, время работы в верхней (стандартный вызов `system info`).
- **Вёрстка для телефона** с выезжающим меню, иконки для главного экрана и манифест веб-приложения.
- **Автономность:** шрифты и графику отдаёт сам роутер. Никаких внешних запросов, бэкенда и дополнительных прав доступа.

## Совместимость

| OpenWrt | Пакет | Состояние |
|---|---|---|
| 25.12 | `.apk` | Проверено на 25.12.5 (LuCI 26.267), Cudy TR3000: установка, обновление, удаление, повторная установка |
| 24.10 | `.ipk` | Собрано SDK 24.10; тот же API тем на ucode, на роутере с 24.10 ещё не ставилось |
| 23.05 | `.ipk` | Тот же API тем на ucode; на роутере с 23.05 ещё не ставилось |

Нужен LuCI с шаблонами на ucode. Подходит любой современный браузер (тема использует CSS `clip-path`, `color-mix`
и пользовательские свойства). Отчёты с других роутеров и версий — в [issues](https://github.com/Trendorin/luci-theme-pixel/issues).

## Сборка из исходников

С OpenWrt SDK или buildroot:

```sh
cp -r luci-theme-pixel <sdk>/package/
cd <sdk> && make defconfig && make package/luci-theme-pixel/compile
```

Без SDK: `tools/build_pkg.py [ПАПКА]` собирает те же `.apk` и `.ipk` (раскладка, метаданные и скрипты установки
из Makefile; для `.apk` нужен apk-tools 3, например `dnf install apk-tools`).

| Инструмент | Что делает |
|---|---|
| `tools/profile_glyphs.py` | глифы 5×7 и 12-строчный шрифт для крупных надписей |
| `tools/extra_glyphs.py` | кириллица и знаки интерфейса |
| `tools/build_font.py` | собирает `fonts/pixel-5x7.woff2` (нужны `fonttools` и `brotli`) |
| `tools/build_art.py` | фавикон, иконки для главного экрана и манифест (только стандартная библиотека) |
| `tools/build_pkg.py` | `.apk` и `.ipk` без SDK |
| `tools/preview/` | локальный стенд: файлы темы из репозитория, стандартные страницы LuCI и запросы только на чтение к настоящему роутеру по SSH. `SANITIZE=1` заменяет MAC, IP, SSID, имена и секреты, `DEMO=1` показывает вымышленные журналы; `shot.py` делает скриншоты, `anim.py` записывает GIF экрана входа |

## Изменения

- **1.0.2** — графики в реальном времени (нагрузка, трафик, Wi‑Fi, соединения) рисуются на тёмном экране с видимой
  сеткой вместо белого прямоугольника с почти невидимыми линиями; ссылки на скачивание без номера версии; документация
  на русском и новые скриншоты.
- **1.0.1** — журналы (System Log, Kernel Log, Travelmate) стали тёмным прокручиваемым экраном вместо поля высотой во
  весь журнал; полосатый заголовок модальных окон доходит до правого края; пакеты собираются без SDK.
- **1.0.0** — первый релиз.

Подробности и файлы каждой версии — на [странице релизов](https://github.com/Trendorin/luci-theme-pixel/releases).

## Авторы и лицензия

Глифы 5×7 и крупного шрифта взяты из пиксельного профиля [Trendon (@Trendorin)](https://github.com/Trendorin).
Лицензия — [Apache License 2.0](LICENSE).
